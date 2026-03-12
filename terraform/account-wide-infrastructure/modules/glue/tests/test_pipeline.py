from moto import mock_aws
from pipeline import LogPipeline


@mock_aws
def test_pipeline_init_defaults():
    glue_context = "mock_glue_context"
    spark = "mock_spark_session"
    logger = "mock_logger"
    source_path = "s3://mock-source-path"
    target_path = "s3://mock-target-path"
    host_prefixes = ["host1", "host2"]
    job_name = "test-job-name"

    pipeline = LogPipeline(
        glue_context, spark, logger, source_path, target_path, host_prefixes, job_name
    )

    assert pipeline.glue_context == glue_context
    assert pipeline.spark == spark
    assert pipeline.logger == logger
    assert pipeline.source_path == source_path
    assert pipeline.target_path == target_path
    assert pipeline.host_prefixes == host_prefixes
    assert pipeline.job_name == job_name
    assert pipeline.name_prefix == "test-job-name"
    assert pipeline.partition_cols == []
    assert pipeline.transformations == []


@mock_aws
def test_pipeline_init_with_custom_values():
    glue_context = "mock_glue_context"
    spark = "mock_spark_session"
    logger = "mock_logger"
    source_path = "s3://mock-source-path"
    target_path = "s3://mock-target-path"
    host_prefixes = ["host1", "host2"]
    job_name = "test-job-name"
    partition_cols = ["col1", "col2"]
    transformations = ["transformation1", "transformation2"]

    pipeline = LogPipeline(
        glue_context,
        spark,
        logger,
        source_path,
        target_path,
        host_prefixes,
        job_name,
        partition_cols=partition_cols,
        transformations=transformations,
    )

    assert pipeline.partition_cols == partition_cols
    assert pipeline.transformations == transformations
