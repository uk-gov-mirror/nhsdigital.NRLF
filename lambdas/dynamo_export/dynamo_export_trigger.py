import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

bucket = os.environ["BUCKET"]
ddb_table_arn = os.environ["DDB_TABLE_ARN"]
kms_key = os.environ["KMS_KEY"]
env = os.environ["ENVIRONMENT"]
ddb_table_name = os.environ["DDB_TABLE_NAME"]

SSM_PARAM = "/exports/DynamoExportRuntime"

ddb_client = boto3.client(
    "dynamodb",
    config=Config(connect_timeout=5, read_timeout=5),
)
ssm = boto3.client(
    "ssm",
    config=Config(connect_timeout=5, read_timeout=5),
)


def lambda_handler(_event, _context):
    to_time = datetime.now(timezone.utc).replace(microsecond=0, second=0, minute=0)
    export_arns = []

    try:
        from_time = ssm.get_parameter(Name=SSM_PARAM)["Parameter"]["Value"]
        from_time = datetime.fromisoformat(from_time).replace(
            microsecond=0, second=0, minute=0
        )

        # Handle exports longer than 24 hours by splitting into multiple exports
        earliest_pitr = ddb_client.describe_continuous_backups(
            TableName=ddb_table_name
        )["ContinuousBackupsDescription"]["PointInTimeRecoveryDescription"][
            "EarliestRestorableDateTime"
        ]
        from_time = max(from_time, earliest_pitr)
        days_difference = (to_time - from_time).days + 1
        from_times = [from_time + timedelta(days=i) for i in range(days_difference)]

        for base_time in from_times:
            end_time = min(base_time + timedelta(days=1), to_time)
            if end_time == base_time:
                continue
            response = ddb_client.export_table_to_point_in_time(
                TableArn=ddb_table_arn,
                S3Bucket=bucket,
                S3SseAlgorithm="KMS",
                S3SseKmsKeyId=kms_key,
                ExportFormat="DYNAMODB_JSON",
                ExportType="INCREMENTAL_EXPORT",
                IncrementalExportSpecification={
                    "ExportFromTime": base_time,
                    "ExportToTime": end_time,
                    "ExportViewType": "NEW_AND_OLD_IMAGES",
                },
            )
            export_arns.append(response["ExportDescription"]["ExportArn"])
            export_type = response["ExportDescription"]["ExportType"]
    except ClientError as e:
        if e.response["Error"]["Code"] != "ParameterNotFound":
            raise
        response = ddb_client.export_table_to_point_in_time(
            TableArn=ddb_table_arn,
            S3Bucket=bucket,
            S3SseAlgorithm="KMS",
            S3SseKmsKeyId=kms_key,
            ExportFormat="DYNAMODB_JSON",
            ExportType="FULL_EXPORT",
        )
        export_arns.append(response["ExportDescription"]["ExportArn"])
        export_type = response["ExportDescription"]["ExportType"]

    return {
        "export_to_time": to_time.isoformat(),
        "export_arns": export_arns,
        "export_type": export_type,
    }
