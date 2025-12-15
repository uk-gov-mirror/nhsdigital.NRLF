import csv
from datetime import datetime, timedelta, timezone
from itertools import cycle
from math import gcd
from random import shuffle
from typing import Any, Iterator

import boto3
import fire

# import json
import numpy as np

from nrlf.consumer.fhir.r4.model import DocumentReference
from nrlf.core.constants import (
    CATEGORY_ATTRIBUTES,
    SNOMED_SYSTEM_URL,
    TYPE_ATTRIBUTES,
    TYPE_CATEGORIES,
    Categories,
    PointerTypes,
)
from nrlf.core.dynamodb.model import DocumentPointer
from nrlf.core.logger import logger
from nrlf.tests.data import load_document_reference

dynamodb = boto3.client("dynamodb")
resource = boto3.resource("dynamodb")

logger.setLevel("ERROR")

DOC_REF_TEMPLATE = load_document_reference("NFT-template")

CHECKSUM_WEIGHTS = [i for i in range(10, 1, -1)]

# These are based on the Nov 7th 2025 pointer stats report
DEFAULT_TYPE_DISTRIBUTIONS = {
    "736253002": 65,  # mental health crisis plan
    "1382601000000107": 5,  # respect form
    "887701000000100": 15,  # emergency healthcare plan
    "861421000000109": 5,  # eol care coordination summary
    "735324008": 5,  # treatment escalation plan
    "824321000000109": 5,  # summary record
}

DEFAULT_CUSTODIAN_DISTRIBUTIONS = {
    "736253002": {
        "TRPG": 9,
        "TRHA": 1,
        "TRRE": 20,
        "TRAT": 10,
        "TWR4": 4,
        "TRKL": 9,
        "TRW1": 5,
        "TRH5": 1,
        "TRP7": 13,
        "TRWK": 8,
        "TRQY": 3,
        "TRV5": 3,
        "TRJ8": 2,
        "TRXA": 4,
        "T11X": 1,
        "TG6V": 2,
    },
    "1382601000000107": {"T8GX8": 3, "TQUY": 2},  # respect form
    "887701000000100": {
        "TV1": 1,
        "TV2": 2,
        "TV3": 1,
        "TV4": 1,
        "TV5": 3,
        "TV6": 1,
    },  # emergency healthcare plan
    "861421000000109": {
        "TV1": 2,
        "TV2": 2,
        "TV3": 1,
        "TV4": 1,
        "TV5": 3,
        "TV6": 1,
    },  # eol care coordination summary
    "735324008": {
        "TV1": 1,
        "TV2": 1,
        "TV3": 1,
        "TV4": 2,
        "TV5": 2,
        "TV6": 1,
    },  # treatment escalation plan
    "824321000000109": {
        "TRXT": 1,
    },  # summary record currently has only one supplier
}

DEFAULT_COUNT_DISTRIBUTIONS = {"1": 91, "2": 8, "3": 1}


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


def _populate_seed_table(
    table_name: str,
    px_with_pointers: int,
    pointers_per_px: float = 1.0,
    type_dists: dict[str, int] = DEFAULT_TYPE_DISTRIBUTIONS,
    custodian_dists: dict[str, dict[str, int]] = DEFAULT_CUSTODIAN_DISTRIBUTIONS,
):
    """
    Seeds a table with example data for non-functional testing.
    """
    if pointers_per_px < 1.0:
        raise ValueError("Cannot populate table with patients with zero pointers")
    # set up iterations
    type_iter = _set_up_cyclical_iterator(type_dists)
    custodian_iters = _set_up_custodian_iterators(custodian_dists)
    # count_iter = _set_up_cyclical_iterator(DEFAULT_COUNT_DISTRIBUTIONS)
    count_iter = _get_pointer_count_poisson_distributions(
        px_with_pointers, pointers_per_px
    )
    # count_iter = _get_pointer_count_negbinom_distributions(px_with_pointers, pointers_per_px)
    testnum_cls = TestNhsNumbersIterator()
    testnum_iter = iter(testnum_cls)

    px_counter = 0
    doc_ref_target = int(pointers_per_px * px_with_pointers)
    print(
        f"Will upsert ~{doc_ref_target} test pointers for {px_with_pointers} patients."
    )
    doc_ref_counter = 0
    batch_counter = 0

    pointer_data: list[list[str]] = []

    start_time = datetime.now(tz=timezone.utc)

    batch_upsert_items: list[dict[str, Any]] = []
    while px_counter < px_with_pointers:
        pointers_for_px = int(next(count_iter))

        if batch_counter + pointers_for_px > 25 or px_counter == px_with_pointers:
            response = resource.batch_write_item(
                RequestItems={table_name: batch_upsert_items}
            )

            if response.get("UnprocessedItems"):
                logger.error(
                    f"Unprocessed items in batch write: {len(response.get('UnprocessedItems'))}"
                )

            batch_upsert_items = []
            batch_counter = 0

        new_px = next(testnum_iter)
        for _ in range(pointers_for_px):
            new_type = next(type_iter)
            new_custodian = next(custodian_iters[new_type])
            doc_ref_counter += 1
            batch_counter += 1

            pointer = _make_seed_pointer(
                new_type, new_custodian, new_px, doc_ref_counter
            )
            put_req = {"PutRequest": {"Item": pointer.model_dump()}}
            batch_upsert_items.append(put_req)
            pointer_data.append(
                [
                    pointer.id,
                    pointer.type,
                    pointer.custodian,
                    pointer.nhs_number,
                ]
            )
        px_counter += 1

        if px_counter % 1000 == 0:
            print(".", end="", flush=True)
        if px_counter % 100000 == 0:
            print(f" {px_counter} patients processed")

    print(" Done.")

    end_time = datetime.now(tz=timezone.utc)
    print(
        f"Created {doc_ref_counter} pointers in {timedelta.total_seconds(end_time - start_time)} seconds."
    )

    with open("./dist/seed-nft-pointers.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["pointer_id", "pointer_type", "custodian", "nhs_number"])
        writer.writerows(pointer_data)
    print(f"Pointer data saved to ./dist/seed-nft-pointers.csv")  # noqa


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


# def _get_pointer_count_negbinom_distributions(num_of_patients: int, pointers_per_px: float) -> cycle:
#    dispersion = 2  # lower = more variance; higher = closer to Poisson
#    p = dispersion / (dispersion + pointers_per_px)
#    n = dispersion

#    p_count_distr = np.random.negative_binomial(n=n, p=p, size=num_of_patients)
#    return cycle(p_count_distr)


def _get_pointer_count_poisson_distributions(
    num_of_patients: int, pointers_per_px: float
) -> Iterator[int]:
    p_count_distr = np.random.poisson(lam=pointers_per_px - 1, size=num_of_patients) + 1
    p_count_distr = np.clip(p_count_distr, a_min=1, a_max=4)
    return cycle(p_count_distr)


def _set_up_custodian_iterators(
    custodian_dists: dict[str, dict[str, int]]
) -> dict[str, Iterator[str]]:
    custodian_iters: dict[str, Iterator[str]] = {}
    for pointer_type in custodian_dists:
        custodian_iters[pointer_type] = _set_up_cyclical_iterator(
            custodian_dists[pointer_type]
        )
    return custodian_iters


# def _set_up_count_iterator(pointers_per_px: float) -> iter:
#    """
#    Given a target average number of pointers per patient,
#    generates a distribution of counts per individual patient.
#    """
#
#    extra_per_hundred = int(
#        (pointers_per_px - 1.0) * 100
#    )  # no patients can have zero pointers
#    counts = {}
#    counts["3"] = extra_per_hundred // 10
#    counts["2"] = extra_per_hundred - 2 * counts["3"]
#    counts["1"] = 100 - counts[2] - counts[3]
#    return _set_up_cyclical_iterator(counts)


if __name__ == "__main__":
    fire.Fire(_populate_seed_table)
