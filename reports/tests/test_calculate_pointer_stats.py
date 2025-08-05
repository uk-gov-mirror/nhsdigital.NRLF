from typing import Any

from reports.calculate_pointer_stats import (
    _calc_date_stats,
    _calc_patient_counters,
    _calc_type_stats,
    _get_patient_stats,
)


def test_calc_type_stats_first_counts():
    stats: dict[str, Any] = {
        "type_counts": {},
        "producer_by_type_counts": {},
    }
    producer = "test_producer"
    type_str = "test_type"

    _calc_type_stats(producer, type_str, stats)

    assert stats["type_counts"] == {type_str: 1}
    assert stats["producer_by_type_counts"] == {producer: {type_str: 1}}


def test_calc_type_stats_increment_counts():
    stats: dict[str, Any] = {
        "type_counts": {"test_type": 1},
        "producer_by_type_counts": {"test_producer": {"test_type": 1}},
    }
    producer = "test_producer"
    type_str = "test_type"

    _calc_type_stats(producer, type_str, stats)

    assert stats["type_counts"] == {type_str: 2}
    assert stats["producer_by_type_counts"] == {producer: {type_str: 2}}


def test_calc_date_stats_first_counts():
    stats: dict[str, Any] = {
        "created_by_month": {},
    }
    created_on = "2025-01-01"

    _calc_date_stats(created_on, stats)

    assert stats["created_by_month"] == {"2025-01": 1}


def test_calc_date_stats_increment_counts():
    stats: dict[str, Any] = {
        "created_by_month": {"2025-01": 1},
    }
    created_on = "2025-01-01"

    _calc_date_stats(created_on, stats)

    assert stats["created_by_month"] == {"2025-01": 2}


def test_calc_patient_counters_first_counts():
    patient_counters: dict[str, Any] = {}
    patient_number = "12345"
    producer = "test_producer"
    type_str = "test_type"

    _calc_patient_counters(patient_number, producer, type_str, patient_counters)

    assert patient_counters == {
        patient_number: {
            "count": 1,
            "types": {type_str: 1},
            "orgs": {producer: {type_str: 1}},
        }
    }


def test_calc_patient_counters_increment_counts():
    patient_counters: dict[str, Any] = {
        "12345": {
            "count": 1,
            "types": {"test_type": 1},
            "orgs": {"test_producer": {"test_type": 1}},
        }
    }
    patient_number = "12345"
    producer = "test_producer"
    type_str = "test_type"

    _calc_patient_counters(patient_number, producer, type_str, patient_counters)

    assert patient_counters == {
        "12345": {
            "count": 2,
            "types": {"test_type": 2},
            "orgs": {"test_producer": {"test_type": 2}},
        }
    }


def test_calc_patient_counters_new_producer_same_type():
    patient_counters: dict[str, Any] = {
        "12345": {
            "count": 1,
            "types": {"test_type": 1},
            "orgs": {"test_producer": {"test_type": 1}},
        }
    }
    patient_number = "12345"
    producer = "new_producer"
    type_str = "test_type"

    _calc_patient_counters(patient_number, producer, type_str, patient_counters)

    assert patient_counters == {
        "12345": {
            "count": 2,
            "types": {"test_type": 2},
            "orgs": {
                "test_producer": {"test_type": 1},
                "new_producer": {"test_type": 1},
            },
        }
    }


def test_calc_patient_counters_new_producer_new_type():
    patient_counters: dict[str, Any] = {
        "12345": {
            "count": 1,
            "types": {"test_type": 1},
            "orgs": {"test_producer": {"test_type": 1}},
        }
    }
    patient_number = "12345"
    producer = "new_producer"
    type_str = "new_test_type"

    _calc_patient_counters(patient_number, producer, type_str, patient_counters)

    assert patient_counters == {
        "12345": {
            "count": 2,
            "types": {"test_type": 1, "new_test_type": 1},
            "orgs": {
                "test_producer": {"test_type": 1},
                "new_producer": {"new_test_type": 1},
            },
        }
    }


def test_calc_patient_counters_existing_producer_new_type():
    patient_counters: dict[str, Any] = {
        "12345": {
            "count": 1,
            "types": {"test_type": 1},
            "orgs": {"test_producer": {"test_type": 1}},
        }
    }
    patient_number = "12345"
    producer = "test_producer"
    type_str = "new_test_type"

    _calc_patient_counters(patient_number, producer, type_str, patient_counters)

    assert patient_counters == {
        "12345": {
            "count": 2,
            "types": {"test_type": 1, "new_test_type": 1},
            "orgs": {"test_producer": {"test_type": 1, "new_test_type": 1}},
        }
    }


def test_get_patient_stats():
    patient_counters: dict[str, Any] = {
        "12345": {
            "count": 3,
            "types": {"type1": 2, "type2": 1},
            "orgs": {"org1": {"type1": 1, "type2": 1}, "org2": {"type1": 1}},
        },
        "67890": {
            "count": 1,
            "types": {"type1": 1},
            "orgs": {"org1": {"type1": 1}},
        },
    }

    result = _get_patient_stats(patient_counters)

    assert result["avg_pointers_per_patient"] == 2
    assert result["max_pointers_per_patient"] == 3
    assert result["min_pointers_per_patient"] == 1
    assert result["patient_counts_with_pointers"] == {1: 1, 3: 1}
    assert result["patient_counts_with_types"] == {
        "type1": {1: 1, 2: 1},
        "type2": {1: 1},
    }
    assert result["patient_counts_with_org_types"] == {
        "org1": {"type1": {1: 2}, "type2": {1: 1}},
        "org2": {"type1": {1: 1}},
    }
