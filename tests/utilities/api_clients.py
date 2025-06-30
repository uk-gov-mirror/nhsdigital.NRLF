import json
import logging
from typing import Any, Callable

import requests
from pydantic import BaseModel
from requests import Response

from nrlf.core.constants import Categories, PointerTypes
from nrlf.core.model import ConnectionMetadata

logger = logging.getLogger(__name__)


class ClientConfig(BaseModel):
    base_url: str
    auth_token: str = "TestToken"
    api_path: str = ""
    client_cert: tuple[str, str] | None = None
    connection_metadata: ConnectionMetadata | None = None
    custom_headers: dict[str, str] | None = {}


class SearchQuery:
    nhs_number: str = "UNSET"
    custodian: str | None = None
    pointer_type: PointerTypes | None = None

    def add_nhs_number(self, nhs_number: str):
        self.nhs_number = nhs_number
        return self

    def add_custodian(self, custodian: str):
        self.custodian = custodian
        return self

    def add_pointer_type(self, pointer_type: PointerTypes):
        self.pointer_type = pointer_type
        return self


def retry_if(status_codes: list[int]) -> Callable[..., Any]:
    """
    Decorator to retry a function call if it returns certain errors
    """

    def wrapped_func(func: Callable[..., Response]) -> Callable[..., Response]:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt_responses: list[Response] = []
            for attempt in range(3):
                response = func(*args, **kwargs)
                if not response.status_code or response.status_code not in status_codes:
                    return response
                attempt_responses.append(response)
                logger.warning(
                    f"Attempt {attempt + 1} failed with status code {response.status_code}"
                )

            logger.error(f"All attempts failed with responses: {attempt_responses}")
            raise RuntimeError(
                f"Function failed after retries with responses: {attempt_responses}"
            )

        return wrapper

    return wrapped_func


class ConsumerTestClient:

    def __init__(self, config: ClientConfig):
        self.config = config
        self.api_url = f"{self.config.base_url}consumer{self.config.api_path}"

        self.request_headers = {
            "Authorization": f"Bearer {self.config.auth_token}",
            "X-Request-Id": "test-request-id",
        }

        if self.config.client_cert:
            connection_metadata = self.config.connection_metadata.model_dump(
                by_alias=True
            )
            client_rp_details = connection_metadata.pop("client_rp_details")
            self.request_headers.update(
                {
                    "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                    "NHSD-Client-RP-Details": json.dumps(client_rp_details),
                    "NHSD-Correlation-Id": "test-correlation-id",
                }
            )

        self.request_headers.update(self.config.custom_headers)

    @retry_if([502])
    def read(self, doc_ref_id: str) -> Response:
        return requests.get(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def count(self, params: dict[str, str]) -> Response:
        return requests.get(
            f"{self.api_url}/DocumentReference/_count",
            params=params,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def search(
        self,
        nhs_number: str | None = None,
        custodian: str | None = None,
        pointer_type: PointerTypes | None = None,
        category: Categories | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> Response:
        params = {**(extra_params or {})}

        if nhs_number:
            params["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if custodian:
            params["custodian:identifier"] = (
                "https://fhir.nhs.uk/Id/ods-organization-code|" + custodian
            )

        if pointer_type:
            if "|" in pointer_type:
                params["type"] = pointer_type
            else:
                params["type"] = f"http://snomed.info/sct|{pointer_type}"

        if category:
            if "|" in category:
                params["category"] = category
            else:
                params["category"] = f"http://snomed.info/sct|{category}"

        return requests.get(
            f"{self.api_url}/DocumentReference",
            params=params,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def search_post(
        self,
        nhs_number: str | None = None,
        custodian: str | None = None,
        pointer_type: PointerTypes | None = None,
        category: Categories | None = None,
        extra_fields: dict[str, str] | None = None,
    ) -> Response:
        body = {**(extra_fields or {})}

        if nhs_number:
            body["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if custodian:
            body["custodian:identifier"] = (
                "https://fhir.nhs.uk/Id/ods-organization-code|" + custodian
            )

        if pointer_type:
            if "|" in pointer_type:
                body["type"] = pointer_type
            else:
                body["type"] = f"http://snomed.info/sct|{pointer_type}"

        if category:
            if "|" in category:
                body["category"] = category
            else:
                body["category"] = f"http://snomed.info/sct|{category}"

        return requests.post(
            f"{self.api_url}/DocumentReference/_search",
            json=body,
            headers={
                "Content-Type": "application/json",
                **self.request_headers,
            },
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def head(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> Response:
        headers = {**(headers or {}), **self.request_headers}
        params = {**(extra_params or {})}
        url = f"{self.api_url}/{endpoint}"
        return requests.head(
            url,
            params=params,
            headers=headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def read_capability_statement(self) -> Response:
        return requests.get(
            f"{self.api_url}/metadata",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )


class ProducerTestClient:
    def __init__(self, config: ClientConfig):
        self.config = config
        self.api_url = f"{self.config.base_url}producer{self.config.api_path}"

        self.request_headers = {
            "Authorization": f"Bearer {self.config.auth_token}",
            "X-Request-Id": "test-request-id",
        }

        if self.config.client_cert:
            connection_metadata = self.config.connection_metadata.model_dump(
                by_alias=True
            )
            client_rp_details = connection_metadata.pop("client_rp_details")
            self.request_headers.update(
                {
                    "NHSD-Connection-Metadata": json.dumps(connection_metadata),
                    "NHSD-Client-RP-Details": json.dumps(client_rp_details),
                    "NHSD-Correlation-Id": "test-correlation-id",
                }
            )

        self.request_headers.update(self.config.custom_headers)

    @retry_if([502])
    def create(self, doc_ref) -> Response:
        return requests.post(
            f"{self.api_url}/DocumentReference",
            json=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def create_text(self, doc_ref) -> Response:
        return requests.post(
            f"{self.api_url}/DocumentReference",
            data=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def upsert(self, doc_ref) -> Response:
        return requests.put(
            f"{self.api_url}/DocumentReference",
            json=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def upsert_text(self, doc_ref) -> Response:
        return requests.put(
            f"{self.api_url}/DocumentReference",
            data=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def update(self, doc_ref, doc_ref_id: str) -> Response:
        return requests.put(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            json=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def update_text(self, doc_ref, doc_ref_id: str) -> Response:
        return requests.put(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            data=doc_ref,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def delete(self, doc_ref_id: str) -> Response:
        return requests.delete(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def read(self, doc_ref_id: str) -> Response:
        return requests.get(
            f"{self.api_url}/DocumentReference/{doc_ref_id}",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def search(
        self,
        nhs_number: str | None = None,
        pointer_type: PointerTypes | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> Response:
        params = {**(extra_params or {})}

        if nhs_number:
            params["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if pointer_type:
            if "|" in pointer_type:
                params["type"] = pointer_type
            else:
                params["type"] = f"http://snomed.info/sct|{pointer_type}"

        return requests.get(
            f"{self.api_url}/DocumentReference",
            params=params,
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def search_post(
        self,
        nhs_number: str | None = None,
        pointer_type: PointerTypes | None = None,
        extra_fields: dict[str, str] | None = None,
    ) -> Response:
        body = {**(extra_fields or {})}

        if nhs_number:
            body["subject:identifier"] = (
                "https://fhir.nhs.uk/Id/nhs-number|" + nhs_number
            )

        if pointer_type:
            if "|" in pointer_type:
                body["type"] = pointer_type
            else:
                body["type"] = f"http://snomed.info/sct|{pointer_type}"

        return requests.post(
            f"{self.api_url}/DocumentReference/_search",
            json=body,
            headers={
                "Content-Type": "application/json",
                **self.request_headers,
            },
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def read_capability_statement(self) -> Response:
        return requests.get(
            f"{self.api_url}/metadata",
            headers=self.request_headers,
            cert=self.config.client_cert,
        )

    @retry_if([502])
    def head(
        self,
        endpoint: str,
        headers: dict[str, str] | None = None,
        extra_params: dict[str, str] | None = None,
    ) -> Response:
        headers = {**(headers or {}), **self.request_headers}
        params = {**(extra_params or {})}
        url = f"{self.api_url}/{endpoint}"
        return requests.head(
            url,
            params=params,
            headers=headers,
            cert=self.config.client_cert,
        )
