import logging
import sys

from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pipeline import LogPipeline
from pyspark.sql import SparkSession
from transformations import dtype_conversion, format_ssp, rename_cols, resolve_dupes

# Spark and Glue Context initialization
spark = SparkSession.builder.config("spark.sql.caseSensitive", "true").getOrCreate()
glue_context = GlueContext(spark.sparkContext)

# Logger setup
MSG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(format=MSG_FORMAT, datefmt=DATETIME_FORMAT)
logger = logging.getLogger("ETLLogger")
logger.setLevel(logging.INFO)

# Get arguments from AWS Glue job
args = getResolvedOptions(
    sys.argv, ["job_name", "source_path", "target_path", "partition_cols"]
)

partition_cols = args["partition_cols"].split(",") if "partition_cols" in args else []

host_prefixes = [
    "consumer--countDocumentReference",
    "consumer--searchPostDocumentReference",
    "consumer--searchDocumentReference",
    "consumer--readDocumentReference",
    "producer--searchPostDocumentReference",
    "producer--searchDocumentReference",
    "producer--readDocumentReference",
    "producer--upsertDocumentReference",
    "producer--updateDocumentReference",
    "producer--deleteDocumentReference",
    "producer--createDocumentReference",
    "s2c",
]

# Initialize ETL process
etl_job = LogPipeline(
    glue_context=glue_context,
    spark=spark,
    logger=logger,
    source_path=args["source_path"],
    target_path=args["target_path"],
    host_prefixes=host_prefixes,
    job_name=args["job_name"],
    partition_cols=partition_cols,
    transformations=[rename_cols, resolve_dupes, dtype_conversion, format_ssp],
)

# Run the job
etl_job.run()
