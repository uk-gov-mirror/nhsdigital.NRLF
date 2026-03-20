import os
import time

import boto3

AWS_REGION = os.getenv("AWS_REGION", "eu-west-2")


class LogPipeline:
    def __init__(
        self,
        glue_context,
        spark,
        logger,
        source_path,
        target_path,
        host_prefixes,
        job_name,
        partition_cols=None,
        transformations=None,
    ):
        """Initialize Glue context, Spark session, logger, and paths"""
        self.glue_context = glue_context
        self.spark = spark
        self.logger = logger
        self.source_path = source_path
        self.target_path = target_path
        self.host_prefixes = host_prefixes
        self.partition_cols = partition_cols if partition_cols else []
        self.transformations = transformations if transformations else []
        self.glue = boto3.client(
            service_name="glue",
            region_name=AWS_REGION,
            endpoint_url=f"https://glue.{AWS_REGION}.amazonaws.com",
        )
        self.job_name = job_name
        self.name_prefix = "-".join(job_name.split("-")[:4])

    def run(self):
        """Runs ETL"""
        try:
            self.logger.info("ETL Process started.")
            data = self.extract_dynamic()
            self.logger.info(f"Data extracted from {self.source_path}.")
            for name, df in data.items():
                data[name] = self.transform(df, name)
            self.logger.info("Data transformed successfully.")
            self.load(data)
            self.logger.info(f"Data loaded into {self.target_path}.")
            self.logger.info("Trigger glue crawler")
            self.trigger_crawler()
        except Exception as e:
            self.logger.error(f"ETL process failed: {e}")
            raise e

    def get_last_run(self):
        self.logger.info("Retrieving last successful runtime.")
        all_runs = self.glue.get_job_runs(JobName=self.job_name)
        if not all_runs["JobRuns"]:
            return None

        for run in all_runs["JobRuns"]:
            if run["JobRunState"] == "SUCCEEDED":
                return time.mktime(run["StartedOn"].timetuple())

        return None

    def extract_dynamic(self):
        """Extract JSON data from S3"""
        last_runtime = self.get_last_run()
        data = {}
        data_source = self.glue_context.getSource("s3", paths=[self.source_path])
        data_source.setFormat("json")
        self.logger.info(f"Extracting data from {self.source_path} as JSON")
        for name in self.host_prefixes:
            if last_runtime:
                data[name] = self.glue_context.create_dynamic_frame.from_options(
                    connection_type="s3",
                    connection_options={
                        "paths": [self.source_path],
                        "recurse": True,
                        "groupFiles": "inPartition",
                        "groupSize": "134217728",
                    },
                    format="json",
                ).filter(
                    f=lambda x, n=name: (x["host"] is not None and n in x["host"])
                    and (x["time"] > last_runtime)
                )

            else:
                data[name] = self.glue_context.create_dynamic_frame.from_options(
                    connection_type="s3",
                    connection_options={
                        "paths": [self.source_path],
                        "recurse": True,
                        "groupFiles": "inPartition",
                        "groupSize": "134217728",
                    },
                    format="json",
                ).filter(f=lambda x, n=name: (x["host"] is not None and n in x["host"]))

        return data

    def transform(self, dataframe, name):
        """Apply a list of transformations on the dataframe"""
        self.spark.conf.set("spark.sql.caseSensitive", True)
        dataframe = (
            dataframe.relationalize("root", f"./tmp/{name}").select("root").toDF()
        )
        for transformation in self.transformations:
            self.logger.info(f"Applying transformation: {transformation.__name__}")
            dataframe = transformation(dataframe, self.logger, name)
        return dataframe

    def load(self, data):
        """Load transformed data into Parquet format"""
        self.logger.info(f"Loading data into {self.target_path} as Parquet")
        for name, dataframe in data.items():
            name = name.replace("--", "_")
            if name == "s2c":
                name = "spine_sspDocumentRetrieval"
            try:
                if dataframe.rdd.isEmpty():
                    self.logger.info(f"{name} dataframe has no rows. Skipping.")
                    continue

                self.logger.info(
                    f"Attempting to load dataframe {name} into {self.target_path}{name}"
                )
                dataframe.write.mode("append").partitionBy(
                    *self.partition_cols
                ).parquet(f"{self.target_path}{name}")
            except Exception as e:
                self.logger.info(f"{name} failed to write with error: {e}")

    def trigger_crawler(self):
        self.glue.start_crawler(Name=f"{self.name_prefix}-log-crawler")
