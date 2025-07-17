from collections import defaultdict
from functools import reduce

from pyspark.sql.functions import (
    coalesce,
    col,
    concat,
    from_unixtime,
    lit,
    regexp_replace,
    to_date,
    to_timestamp,
    when,
)
from pyspark.sql.types import NullType


def format_ssp(df, logger, name):
    if name != "s2c":
        logger.info(f"Not SSP logs, returning df: {name}")
        return df

    if df.rdd.isEmpty():
        logger.info(f"{name} dataframe has no rows. Skipping format_ssp.")
        return df

    logger.info("Processing SSP logs")
    noOdsCode = df.filter(col("logReference") != "SSP0001")
    odsCode = df.filter(col("logReference") == "SSP0001")

    noOdsCode = noOdsCode.select(
        "time",
        "host",
        "internalID",
        "logReference",
        "interaction",
        "responseCode",
        "responseErrorMessage",
        "totalDuration",
    )
    odsCode = odsCode.select(
        "sspFrom",
        "fromOrgName",
        "fromOdsCode",
        "fromPostCode",
        "sspTo",
        "toOrgName",
        "toOdsCode",
        "toPostCode",
        "internalID",
    )

    df = noOdsCode.join(odsCode, on="internalID", how="left")

    return df


def resolve_dupes(df, logger, name):
    if df.rdd.isEmpty():
        logger.info(f"{name} dataframe has no rows. Skipping resolve_dupes.")
        return df

    column_groups = defaultdict(list)
    for column_name in df.columns:
        normalised_name = column_name.lower().rstrip("_")
        column_groups[normalised_name].append(column_name)

    final_select_exprs = []
    for lower_name, original_names in column_groups.items():

        if len(original_names) == 1:
            final_select_exprs.append(col(original_names[0]).alias(lower_name))
        else:
            logger.info(
                f"Resolving duplicate group '{lower_name}': {original_names} for df: {name}"
            )

            merge_logic = lambda col1, col2: when(
                col1.isNull() | col2.isNull(), coalesce(col1, col2)
            ).otherwise(concat(col1, lit(", "), col2))

            merged_column_expr = reduce(merge_logic, [col(c) for c in original_names])

            final_select_exprs.append(merged_column_expr.alias(lower_name))

    return df.select(*final_select_exprs)


def rename_cols(df, logger, name):
    if df.rdd.isEmpty():
        logger.info(f"{name} dataframe has no rows. Skipping rename_cols.")
        return df

    logger.info(f"Replacing '.' with '_' for df: {name}")
    for col_name in df.columns:
        df = df.withColumnRenamed(col_name, col_name.replace(".", "_"))
    return df


def dtype_conversion(df, logger, name):
    if df.rdd.isEmpty():
        logger.info(f"{name} dataframe has no rows. Skipping dtype_conversion.")
        return df
    try:
        logger.info(f"Formatting event_timestamp, time and date columns for df: {name}")
        if "event_timestamp" in df.columns:
            df = df.withColumn(
                "event_timestamp_cleaned",
                regexp_replace(col("event_timestamp"), ",", "."),
            ).withColumn(
                "event_timestamp",
                to_timestamp(
                    col("event_timestamp_cleaned"), "yyyy-MM-dd HH:mm:ss.SSSZ"
                ),
            )

            df = df.drop("event_timestamp_cleaned")

        if "time" in df.columns:
            df = df.withColumn(
                "time", from_unixtime(col("time")).cast("timestamp")
            ).withColumn("date", to_date(col("time")))

        if "_time" in df.columns:
            df = df.withColumn(
                "time", to_timestamp(col("_time"), "yyyy-MM-dd HH:mm:ss.SSSZ")
            ).withColumn("date", to_date(col("time")))

            df = df.drop("_time")

    except Exception as e:
        logger.info(f"Failed formatting of timestamp columns with error: {e}")

    logger.info("Handling Null Type columns")
    select_exprs = []
    for column_name in df.columns:
        column_type = df.schema[column_name].dataType
        if isinstance(column_type, NullType):
            logger.info(f"Converting {column_name} to string")
            select_exprs.append(col(column_name).cast("string").alias(column_name))
        else:
            select_exprs.append(col(column_name))

    return df.select(*select_exprs)
