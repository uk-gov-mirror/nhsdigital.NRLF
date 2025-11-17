from pathlib import Path
from typing import Optional, Tuple

TRUSTSTORE_PATH = Path(__file__).parent / "../../../truststore/"
CLIENT_CERT_PATH = TRUSTSTORE_PATH / "client"


def get_cert_path_for_environment(environment: Optional[str]) -> Tuple[str, str]:
    """
    This function returns the certificate for the given environment
    """
    if not environment:
        raise ValueError("Environment (env) not provided")

    # List only non-sandbox environments
    # Sandbox uses the same certs as their non-sandbox equivalents.
    ENVIRONMENTS = ["dev", "qa", "int", "ref", "perftest", "prod"]

    selected_env = "dev"  # default to dev (e.g: ci environments)
    for env in ENVIRONMENTS:
        # match dev-1, qa-2, etc. it works for sandbox too
        if environment == env or environment.startswith(f"{env}-"):
            selected_env = env
            break

    cert_path = CLIENT_CERT_PATH / f"{selected_env}.crt"
    key_path = CLIENT_CERT_PATH / f"{selected_env}.key"

    if not cert_path.exists() or not key_path.exists():
        raise FileNotFoundError(
            f"Client certificate not found at {cert_path} or {key_path}"
        )

    return (str(cert_path.resolve()), str(key_path.resolve()))
