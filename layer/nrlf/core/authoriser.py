import json
import re
import sys
from os import path

from botocore.exceptions import ClientError

from nrlf.core.boto import get_s3_client
from nrlf.core.config import Config
from nrlf.core.logger import LogReference, logger
from nrlf.core.model import ConnectionMetadata


def get_pointer_permissions(
    connection_metadata: ConnectionMetadata, config: Config, request_path: str
):
    # This a good place for this?
    producer_or_consumer = (
        re.search("^/(producer|consumer)/", request_path).group().strip("/")
    )

    ods_code = connection_metadata.ods_code
    app_id = connection_metadata.nrl_app_id

    key = f"{producer_or_consumer}/{app_id}/{ods_code}.json"

    logger.log(LogReference.S3PERMISSIONS011, key=key)

    # nothing to retrieve yet!
    s3_client = get_s3_client()
    try:
        response = s3_client.get_object(Bucket=config.AUTH_STORE, Key=key)
        pointer_permissions = json.loads(response["Body"].read())
        logger.log(
            LogReference.S3PERMISSIONS012, pointer_permissions=pointer_permissions
        )
        return pointer_permissions

    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
            logger.log(LogReference.S3PERMISSIONS013, error=str(exc), key=key)
            return {}

        logger.log(
            LogReference.S3PERMISSIONS014,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
        raise exc

    except Exception as exc:
        logger.log(
            LogReference.S3PERMISSIONS014,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
        raise exc


def get_pointer_types(
    connection_metadata: ConnectionMetadata, config: Config
) -> list[str]:
    ods_code = ".".join(connection_metadata.ods_code)

    app_id = connection_metadata.nrl_app_id
    ods_code = connection_metadata.ods_code

    key = f"{app_id}/{ods_code}.json"

    logger.log(LogReference.S3PERMISSIONS001, bucket=config.AUTH_STORE, key=key)
    s3_client = get_s3_client()

    try:
        response = s3_client.get_object(Bucket=config.AUTH_STORE, Key=key)
        pointer_types = json.loads(response["Body"].read())
        logger.log(LogReference.S3PERMISSIONS002, pointer_types=pointer_types)
        return pointer_types

    except ClientError as exc:
        if exc.response.get("Error", {}).get("Code") == "NoSuchKey":
            logger.log(LogReference.S3PERMISSIONS003, error=str(exc))
            return []

        logger.log(
            LogReference.S3PERMISSIONS004,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
        raise exc

    except Exception as exc:
        logger.log(
            LogReference.S3PERMISSIONS004,
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
        raise exc


def parse_permissions_file(
    connection_metadata: ConnectionMetadata,
) -> list[str]:
    ods_code = ".".join(connection_metadata.ods_code)

    app_id = connection_metadata.nrl_app_id
    ods_code = connection_metadata.ods_code

    key = f"{app_id}/{ods_code}.json"

    file_path = f"/opt/python/nrlf_permissions/{key}"

    if connection_metadata.is_test_event:
        file_path = path.abspath(f"layer/test_permissions/{key}")

    pointer_types = []
    try:
        with open(file_path) as file:
            pointer_types = json.load(file)
    except Exception as exc:
        logger.log(
            LogReference.S3PERMISSIONS005,  # not s3 tho?
            exc_info=sys.exc_info(),
            stacklevel=5,
            error=str(exc),
        )
    return pointer_types
