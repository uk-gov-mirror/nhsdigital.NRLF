import hashlib
import logging
import os
import sys
import time
import timeit

import boto3
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from botocore.config import Config
from delta.tables import DeltaTable
from pyspark.context import SparkContext
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, desc, lit, row_number, udf, when
from pyspark.sql.types import StringType, StructField, StructType
from pyspark.sql.window import Window

spark_context = SparkContext.getOrCreate()
glue_context = GlueContext(spark_context)
session = glue_context.spark_session

MSG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=MSG_FORMAT, datefmt=DATETIME_FORMAT)
logger = logging.getLogger("ETLLogger")
logger.setLevel(logging.INFO)

region = os.environ.get("AWS_REGION", "eu-west-2")
glue = boto3.client(
    service_name="glue",
    region_name=region,
    config=Config(connect_timeout=5, read_timeout=5),
)
ssm = boto3.client(
    "ssm",
    config=Config(connect_timeout=5, read_timeout=5),
)

ARGS = getResolvedOptions(
    sys.argv,
    [
        "SOURCE_BUCKET",
        "DDB_TABLE_ARN",
        "TARGET_BUCKET",
        "GLUE_CRAWLER_NAME",
        "EXPORT_TYPE",
        "SLACK_WEBHOOK_URL_SSM_PARAMETER_NAME",
        "ENVIRONMENT",
    ],
)

KEYS = [
    "pk",
    "sk",
    "author",
    "category",
    "category_id",
    "created_on",
    "custodian",
    "custodian_suffix",
    "id",
    "master_identifier",
    "nhs_number",
    "patient_key",
    "patient_sort",
    "producer_id",
    "source",
    "type",
    "type_id",
    "updated_on",
    "version",
]

MAP_KEYS = [
    "document",
]

DERIVED_KEYS = [
    "date",
    "test_patient",
]


# def get_ssm_parameter(parameter):
#     """Get ssm parameter value"""
#     return ssm.get_parameter(Name=parameter, WithDecryption=True)["Parameter"]["Value"]


# def send_slack_notification(webhook_url: str, exception: Optional[Exception]):
#     """Send a message to Slack via webhook."""
#     alert_message = {
#         "blocks": [
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": f"*Dynamo Export Processing Failed in {ARGS['ENVIRONMENT']} environment*\nUncaught exception: {exception}",
#                 },
#             },
#         ]
#     }
#     response = requests.post(
#         webhook_url,
#         data=json.dumps(alert_message),
#         headers={"Content-Type": "application/json"},
#     )

#     if response.status_code != 200:
#         raise ValueError(
#             f"Request to Slack returned {response.status_code}, {response.text}"
#         )


@udf
def hash_nhs(nhs_number: str) -> str:
    """Hash the NHS number using SHA-256."""
    if not nhs_number:
        return ""

    return hashlib.sha256(nhs_number.encode()).hexdigest()


def validate_df_schema(df: DataFrame) -> DataFrame:
    """Ensure that the DataFrame has the expected schema for NewImage and OldImage."""
    logger.info("Validating DataFrame schema for NewImage and OldImage columns.")
    image_schema = StructType(
        [StructField(k, StructType([StructField("S", StringType())])) for k in KEYS]
        + [
            StructField(k, StructType([StructField("M", StructType([]))]))
            for k in MAP_KEYS
        ]
    )

    for column in ["NewImage", "OldImage"]:
        if column not in df.columns:
            logger.info(
                f"{column} column is missing from DataFrame. Adding empty column."
            )
            df = df.withColumn(column, lit(None).cast(image_schema))

    return df


def run_crawler(
    crawler: str, *, timeout_minutes: int = 120, retry_seconds: int = 5
) -> None:
    """Run the specified AWS Glue crawler, waiting until completion."""
    timeout_seconds = timeout_minutes * 60
    start_time = timeit.default_timer()
    abort_time = start_time + timeout_seconds

    def wait_until_ready() -> None:
        state_previous = None
        while True:
            response_get = glue.get_crawler(Name=crawler)
            state = response_get["Crawler"]["State"]
            if state != state_previous:
                logger.info(f"Crawler {crawler} is {state.lower()}.")
                state_previous = state
            if state == "READY":
                return
            if timeit.default_timer() > abort_time:
                raise TimeoutError(
                    f"Failed to crawl {crawler}. The allocated time of {timeout_minutes:,} minutes has elapsed."
                )
            time.sleep(retry_seconds)

    wait_until_ready()
    try:
        response_start = glue.start_crawler(Name=crawler)
        assert response_start["ResponseMetadata"]["HTTPStatusCode"] == 200
    except glue.exceptions.CrawlerRunningException as e:
        logger.info(f"{crawler} is already running: {e}")
    logger.info(f"Crawling {crawler}.")
    wait_until_ready()
    logger.info(f"Crawled {crawler}.")


def process_full_export(df: DataFrame) -> None:
    """Process full export DataFrame."""
    fields = [field for field in KEYS + MAP_KEYS if field in df.columns]

    df = df.withColumnRenamed("nhs_number", "nhs_number_raw")
    df = (
        df.withColumn(
            "test_patient",
            when(
                col("nhs_number_raw").startswith("9")
                | col("nhs_number_raw").startswith("5"),
                True,
            ).otherwise(False),
        )
        .withColumn("nhs_number", hash_nhs(col("nhs_number_raw")))
        .withColumn("date", df["last_updated"].cast("date"))
        .select(*fields, *DERIVED_KEYS)
    )

    df.write.format("delta").mode("append").partitionBy("date").save(
        f"s3://{ARGS['TARGET_BUCKET']}/processed/dynamo_export_pointers"
    )

    run_crawler(ARGS["GLUE_CRAWLER_NAME"])


def safe_select(df: DataFrame, field: str, dtype: str, image: str) -> col:
    """Safely select a field from the DataFrame, returning None if the field does not exist"""
    try:
        df.select(f"{image}.{field}.{dtype}")
        return col(f"{image}.{field}.{dtype}").alias(field)
    except Exception:
        logger.info(
            f"Field {field} of type {dtype} is missing in {image}. Returning null for this field."
        )
        return lit(None).alias(field)


def process_incremental_export(df: DataFrame) -> None:
    """Process incremental export DataFrame"""
    df = validate_df_schema(df).cache()
    df = df.withColumn(
        "eventName",
        when(col("NewImage").isNotNull() & col("OldImage").isNull(), "INSERT")
        .when(col("NewImage").isNotNull() & col("OldImage").isNotNull(), "MODIFY")
        .when(col("NewImage").isNull() & col("OldImage").isNotNull(), "REMOVE")
        .otherwise(None),
    ).cache()

    window = (
        Window.partitionBy("nhs_number", "path")
        .orderBy(desc("last_updated"))
        .rowsBetween(Window.unboundedPreceding, Window.currentRow)
    )
    upserted = (
        df.filter(col("eventName").isin("INSERT", "MODIFY"))
        .select(
            *[safe_select(df, field, "S", "NewImage") for field in KEYS],
            *[safe_select(df, field, "M", "NewImage") for field in MAP_KEYS],
        )
        .withColumn("rn", row_number().over(window))
        .filter(col("rn") == 1)
        .drop("rn")
        .cache()
    )
    logger.info(f"Upserted DataFrame has {upserted.count()} rows.")

    deleted = (
        df.filter(col("eventName") == "REMOVE")
        .select(
            safe_select(df, "nhs_number", "S", "OldImage"),
            safe_select(df, "path", "S", "OldImage"),
        )
        .dropDuplicates(subset=["nhs_number", "path"])
        .cache()
    )
    logger.info(f"Deleted DataFrame has {deleted.count()} rows.")

    delta_table = DeltaTable.forPath(
        session,
        f"s3://{ARGS['TARGET_BUCKET']}/processed/dynamo_export_pointers",
    )

    if not upserted.isEmpty():
        run_upsert_logic(delta_table, upserted, KEYS + MAP_KEYS)

    if not deleted.isEmpty():
        run_delete_logic(delta_table, deleted)

    run_crawler(ARGS["GLUE_CRAWLER_NAME"])


def run_delete_logic(delta_table: DeltaTable, deleted: DataFrame) -> None:
    """Delete records from Delta table based on deleted DataFrame"""
    logger.info("Running delete logic for removed records.")
    deleted = deleted.withColumnRenamed("nhs_number", "nhs_number_raw")
    deleted = deleted.withColumn("nhs_number", hash_nhs(col("nhs_number_raw")))
    delta_table.alias("t").merge(
        deleted.alias("d"),
        "t.nhs_number = d.nhs_number AND t.path = d.path",
    ).whenMatchedDelete().execute()


def run_upsert_logic(
    delta_table: DeltaTable, upserted: DataFrame, fields: list[str]
) -> None:
    """Upsert records into Delta table based on upserted DataFrame"""
    logger.info("Running upsert logic for inserted/modified records.")
    upserted = upserted.withColumnRenamed("nhs_number", "nhs_number_raw")
    upserted = (
        upserted.withColumn(
            "test_patient",
            when(
                col("nhs_number_raw").startswith("9")
                | col("nhs_number_raw").startswith("5"),
                True,
            ).otherwise(False),
        )
        .withColumn("nhs_number", hash_nhs(col("nhs_number_raw")))
        .withColumn(
            "date",
            upserted["last_updated"].cast("date"),
        )
        .select(*fields, *DERIVED_KEYS)
    )

    delta_table.alias("t").merge(
        upserted.alias("u"),
        "t.nhs_number = u.nhs_number AND t.path = u.path",
    ).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()


def main():
    """Process DynamoDB export data and write to Delta Lake."""
    if ARGS["EXPORT_TYPE"] == "FULL_EXPORT":
        logger.info("Starting full export processing.")
        df = glue_context.create_dynamic_frame.from_options(
            connection_type="dynamodb",
            connection_options={
                "dynamodb.export": "s3",
                "dynamodb.tableArn": ARGS["DDB_TABLE_ARN"],
                "dynamodb.s3.bucket": ARGS["SOURCE_BUCKET"],
                "dynamodb.s3.prefix": "AWSDynamoDB/",
                "dynamodb.simplifyDDBJson": True,  # Only applicable for the full export
            },
        ).toDF()

        if df.isEmpty():
            return

        process_full_export(df)
        return

    if ARGS["EXPORT_TYPE"] == "INCREMENTAL_EXPORT":
        logger.info("Starting incremental export processing.")
        df = (
            glue_context.create_dynamic_frame.from_options(
                connection_type="dynamodb",
                connection_options={
                    "dynamodb.export": "s3",
                    "dynamodb.tableArn": ARGS["DDB_TABLE_ARN"],
                    "dynamodb.s3.bucket": ARGS["SOURCE_BUCKET"],
                    "dynamodb.s3.prefix": "AWSDynamoDB/data/",
                },
            )
            .toDF()
            .dropDuplicates()
        )

        if df.isEmpty():
            return

        process_incremental_export(df)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # send_slack_notification(
        #     webhook_url=get_ssm_parameter(ARGS["SLACK_WEBHOOK_URL_SSM_PARAMETER_NAME"]),
        #     exception=e,
        # )
        raise
