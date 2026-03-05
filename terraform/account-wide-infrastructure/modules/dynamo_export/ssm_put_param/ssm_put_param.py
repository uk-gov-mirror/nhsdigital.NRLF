import boto3
from botocore.config import Config

ssm = boto3.client(
    "ssm",
    config=Config(connect_timeout=5, read_timeout=5),
)


def lambda_handler(event, _):
    param_name = "/exports/DynamoExportRuntime"
    param_value = event["export_to_time"]
    ssm.put_parameter(Name=param_name, Value=param_value, Type="String", Overwrite=True)
    return {
        "to_time": param_value,
        "export_arns": event["export_arns"],
        "export_type": event["export_type"],
    }
