#!/usr/bin/env python3
import json
import sys

from botocore.exceptions import ClientError

from scripts.aws_session_assume import get_account_name, get_boto_session
from tests.utilities.get_access_token import get_bearer_token


def get_secret(secret_name: str, session, region: str = "eu-west-2") -> dict:

    client = session.client("secretsmanager", region_name=region)

    try:
        response = client.get_secret_value(SecretId=secret_name)
        return json.loads(response["SecretString"])
    except ClientError as e:
        print(f"Error fetching secret {secret_name}: {e}", file=sys.stderr)  # noqa
        sys.exit(1)


def get_public_mode_config(env_name: str) -> dict:

    try:
        boto_session = get_boto_session(env_name)

        # TODO: Add secret specific to performance tests
        params_secret = f"nhsd-nrlf--{env_name}--smoke-test-parameters"
        params = get_secret(params_secret, boto_session)

        public_base_url = params.get("public_base_url")
        apigee_app_id = params.get("apigee_app_id")

        if not all([public_base_url, apigee_app_id]):
            print(  # noqa
                f"Error: Missing required parameters in {params_secret}",
                file=sys.stderr,
            )
            print(f"Required: public_base_url, apigee_app_id", file=sys.stderr)  # noqa
            sys.exit(1)

        account_name = get_account_name(env_name)
        bearer_token = get_bearer_token(account_name, apigee_app_id, env_name)

        if not bearer_token:
            print(f"Error: Missing required bearer token", file=sys.stderr)  # noqa
            sys.exit(1)

        config = {
            "public_base_url": public_base_url,
            "apigee_app_id": apigee_app_id,
            "bearer_token": bearer_token,
        }

        return config

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)  # noqa
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: get_test_config.py <env_name>", file=sys.stderr)  # noqa
        print("Example: get_test_config.py dev", file=sys.stderr)  # noqa
        sys.exit(1)

    env_name = sys.argv[1]

    config = get_public_mode_config(env_name)

    print(json.dumps(config))  # noqa


if __name__ == "__main__":
    main()
