import csv
import os
from datetime import datetime, timedelta, timezone
from itertools import cycle
from math import gcd
from random import shuffle
from typing import Any, Iterator

import boto3
import fire
import numpy as np

from nrlf.core.boto import get_s3_client
from nrlf.core.constants import (
    CATEGORY_ATTRIBUTES,
    SNOMED_SYSTEM_URL,
    TYPE_ATTRIBUTES,
    TYPE_CATEGORIES,
)
from nrlf.core.dynamodb.model import DocumentPointer
from nrlf.core.logger import logger
from nrlf.tests.data import load_document_reference
from tests.performance.perftest_environment import create_extract_metadata_file
from tests.performance.seed_data_constants import (  # DEFAULT_COUNT_DISTRIBUTIONS,
    CHECKSUM_WEIGHTS,
    CUSTODIAN_DISTRIBUTION_PROFILES,
    TYPE_DISTRIBUTION_PROFILES,
)

dist_path = os.getenv("DIST_PATH", "./dist")
nft_dist_path = f"{dist_path}/nft"

dynamodb = boto3.client("dynamodb")
resource = boto3.resource("dynamodb")

logger.setLevel("ERROR")

DOC_REF_TEMPLATE = load_document_reference("NFT-template")


class TestNhsNumbersIterator:
    def __iter__(self):
        self.first9 = 900000000
        return self

    def __next__(self):
        if self.first9 > 999999999:
            raise StopIteration
        checksum = 10
        while checksum == 10:
            self.first9 += 1
            nhs_no_digits = list(map(int, str(self.first9)))
            checksum = (
                sum(
                    weight * digit
                    for weight, digit in zip(CHECKSUM_WEIGHTS, nhs_no_digits)
                )
                * -1
                % 11
            )
        nhs_no = str(self.first9) + str(checksum)
        return nhs_no


def _make_seed_pointer(
    type_code: str, custodian: str, nhs_number: str, counter: int
) -> DocumentPointer:
    """
    Populates the example pointer template with test data to create a valid NRL 3.0 pointer
    """
    doc_ref = DOC_REF_TEMPLATE
    doc_ref.id = f"{custodian}-{str(counter).zfill(12)}"  # deterministic to aid perftest script retrieval
    doc_ref.subject.identifier.value = nhs_number
    doc_ref.custodian.identifier.value = custodian
    doc_ref.author[0].identifier.value = "X26NFT"
    doc_ref.type.coding[0].code = type_code
    doc_ref.type.coding[0].display = TYPE_ATTRIBUTES.get(
        f"{SNOMED_SYSTEM_URL}|{type_code}"
    ).get("display")
    type_url = f"{SNOMED_SYSTEM_URL}|{type_code}"
    category = TYPE_CATEGORIES.get(type_url)
    doc_ref.category[0].coding[0].code = category.split("|")[-1]
    doc_ref.category[0].coding[0].display = CATEGORY_ATTRIBUTES.get(category).get(
        "display"
    )
    nft_pointer = DocumentPointer.from_document_reference(doc_ref, source="NFT-SEED")
    return nft_pointer


def _write_pointer_extract_to_file(table_name, pointer_data):
    local_csv_out = f"{nft_dist_path}/seed-pointers-extract.csv"
    local_meta_out = f"{nft_dist_path}/info.json"

    print(f"writing pointer extract to files {local_csv_out} {local_meta_out}")

    with open(local_csv_out, "w") as file:
        writer = csv.writer(file)
        writer.writerow(["pointer_id", "pointer_type", "custodian", "nhs_number"])
        writer.writerows(pointer_data)
    print(f"Pointer data saved to {local_csv_out}")

    create_extract_metadata_file(table_name, nft_dist_path)


def _populate_seed_table(
    table_name: str,
    patients_with_pointers: int,
    pointers_per_patient: float = 1.0,
    type_dist_profile: str = "default",
    custodian_dist_profile: str = "default",
):
    """
    Seeds a table with example data for non-functional testing.
    """
    if pointers_per_patient < 1.0:
        raise ValueError("Cannot populate table with patients with zero pointers")

    print(
        f"Populating table {table_name} with patients_with_pointers={patients_with_pointers} pointers_per_patient={pointers_per_patient}",
        type_dist_profile,
        custodian_dist_profile,
    )

    type_dists = TYPE_DISTRIBUTION_PROFILES[type_dist_profile]
    custodian_dists = CUSTODIAN_DISTRIBUTION_PROFILES[custodian_dist_profile]

    # set up iterations
    type_iter = _set_up_cyclical_iterator(type_dists)
    custodian_iters = _set_up_custodian_iterators(custodian_dists)
    count_iter = _get_pointer_count_poisson_distributions(
        patients_with_pointers, pointers_per_patient
    )
    testnum_cls = TestNhsNumbersIterator()
    testnum_iter = iter(testnum_cls)

    patient_counter = 0
    doc_ref_target = int(pointers_per_patient * patients_with_pointers)
    print(
        f"Will upsert ~{doc_ref_target} test pointers for {patients_with_pointers} patients."
    )
    doc_ref_counter = 0
    batch_counter = 0
    unprocessed_count = 0

    pointer_data: list[list[str]] = []
    batch_pointer_data: list[list[str]] = []

    start_time = datetime.now(tz=timezone.utc)
    batch_upsert_items: list[dict[str, Any]] = []

    while patient_counter <= patients_with_pointers:
        pointers_for_patient = int(next(count_iter))

        if (
            batch_counter + pointers_for_patient > 25
            or patient_counter == patients_with_pointers
        ):
            response = resource.batch_write_item(
                RequestItems={table_name: batch_upsert_items}
            )

            processed_pointers = batch_pointer_data

            if response.get("UnprocessedItems"):
                unprocessed_items = response.get("UnprocessedItems").get(table_name, [])
                unprocessed_count += len(unprocessed_items)

                def pointer_is_processed(pointer):
                    pointer_id = pointer[0]
                    matches = (
                        unprocessed_item
                        for unprocessed_item in unprocessed_items
                        if unprocessed_item["PutRequest"]["Item"].get("id")
                        == pointer_id
                    )
                    print(f"unprocessed matches:", matches)

                    return len(matches) == 0

                processed_pointers = filter(pointer_is_processed, batch_pointer_data)

            pointer_data.extend(processed_pointers)

            batch_pointer_data = []
            batch_upsert_items = []
            batch_counter = 0

        new_patient = next(testnum_iter)
        for _ in range(pointers_for_patient):
            new_type = next(type_iter)
            new_custodian = next(custodian_iters[new_type])
            doc_ref_counter += 1
            batch_counter += 1

            pointer = _make_seed_pointer(
                new_type, new_custodian, new_patient, doc_ref_counter
            )
            put_req = {"PutRequest": {"Item": pointer.model_dump()}}
            batch_upsert_items.append(put_req)
            batch_pointer_data.append(
                [
                    pointer.id,
                    new_type,  # not full type url
                    pointer.custodian,
                    pointer.nhs_number,
                ]
            )
        patient_counter += 1

        if patient_counter % 1000 == 0:
            print(".", end="", flush=True)
        if patient_counter % 100000 == 0:
            print(
                f" {patient_counter} patients processed ({doc_ref_counter} pointers)."
            )

    print("Done")

    end_time = datetime.now(tz=timezone.utc)
    print(
        f"Created {doc_ref_counter} pointers in {timedelta.total_seconds(end_time - start_time)} seconds (unprocessed: {unprocessed_count})."
    )

    _write_pointer_extract_to_file(table_name, pointer_data)


def _set_up_cyclical_iterator(dists: dict[str, int]) -> Iterator[str]:
    """
    Given a dict of values and their relative frequencies,
    returns an iterator that will cycle through a the reduced and shuffled set of values.
    This should result in more live-like data than e.g. creating a bulk amount of each pointer type/custodian in series.
    It also means each batch will contain a representative sample of the distribution.
    """
    d = gcd(*dists.values())
    value_list: list[str] = []
    for entry in dists:
        value_list.extend([entry] * (dists[entry] // d))
    shuffle(value_list)
    return cycle(value_list)


def _get_pointer_count_poisson_distributions(
    num_of_patients: int, pointers_per_px: float
) -> Iterator[int]:
    p_count_distr = np.random.poisson(lam=pointers_per_px - 1, size=num_of_patients) + 1
    p_count_distr = np.clip(p_count_distr, a_min=1, a_max=4)
    return cycle(p_count_distr)


def _set_up_custodian_iterators(
    custodian_dists: dict[str, dict[str, int]],
) -> dict[str, Iterator[str]]:
    custodian_iters: dict[str, Iterator[str]] = {}
    for pointer_type in custodian_dists:
        custodian_iters[pointer_type] = _set_up_cyclical_iterator(
            custodian_dists[pointer_type]
        )
    return custodian_iters


if __name__ == "__main__":
    fire.Fire(_populate_seed_table)
