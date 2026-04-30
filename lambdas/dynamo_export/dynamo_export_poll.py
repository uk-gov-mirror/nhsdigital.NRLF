import boto3
from botocore.config import Config

ddb = boto3.client(
    "dynamodb",
    config=Config(connect_timeout=5, read_timeout=5),
)


def lambda_handler(event, _context):
    completed = []
    for arn in event["export_arns"]:
        response = ddb.describe_export(ExportArn=arn)
        if response["ExportDescription"]["ExportStatus"] == "FAILED":
            return {
                "status": "FAILED",
                "export_to_time": event["export_to_time"],
                "export_arns": event["export_arns"],
                "export_type": event["export_type"],
            }

        completed.append(response["ExportDescription"]["ExportStatus"])

    status = "COMPLETED" if all(s == "COMPLETED" for s in completed) else "IN_PROGRESS"

    return {
        "status": status,
        "export_to_time": event["export_to_time"],
        "export_arns": event["export_arns"],
        "export_type": event["export_type"],
    }
