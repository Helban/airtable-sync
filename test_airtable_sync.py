"""Unit tests for AirtableSync, run against a fake table (no network)."""
from typing import Any

import pytest

from airtable_sync import AirtableSync, SyncReport


class FakeTable:
    """Stands in for a pyairtable Table, recording what would be written."""

    def __init__(self, existing_records: list[dict[str, Any]]) -> None:
        self._existing_records = existing_records
        self.created_rows: list[dict[str, Any]] = []
        self.updated_rows: list[dict[str, Any]] = []

    def all(self) -> list[dict[str, Any]]:
        return self._existing_records

    def batch_create(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.created_rows.extend(rows)
        return [{"id": f"recNEW{index}", "fields": fields} for index, fields in enumerate(rows)]

    def batch_update(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self.updated_rows.extend(records)
        return records


def _record(record_id: str, fields: dict[str, Any]) -> dict[str, Any]:
    return {"id": record_id, "createdTime": "2026-01-01T00:00:00.000Z", "fields": fields}


def test_all_new_rows_are_created() -> None:
    table = FakeTable(existing_records=[])
    sync = AirtableSync(table, key_field="Coin ID")

    report = sync.sync([{"Coin ID": "bitcoin", "Price USD": 95000.0}])

    assert report == SyncReport(created=1, updated=0, unchanged=0)
    assert table.created_rows == [{"Coin ID": "bitcoin", "Price USD": 95000.0}]


def test_unchanged_row_is_skipped() -> None:
    table = FakeTable([_record("rec1", {"Coin ID": "bitcoin", "Price USD": 95000.0})])
    sync = AirtableSync(table, key_field="Coin ID")

    report = sync.sync([{"Coin ID": "bitcoin", "Price USD": 95000.0}])

    assert report == SyncReport(created=0, updated=0, unchanged=1)
    assert table.updated_rows == []


def test_changed_row_is_updated_with_its_record_id() -> None:
    table = FakeTable([_record("rec1", {"Coin ID": "bitcoin", "Price USD": 95000.0})])
    sync = AirtableSync(table, key_field="Coin ID")

    report = sync.sync([{"Coin ID": "bitcoin", "Price USD": 96000.0}])

    assert report == SyncReport(created=0, updated=1, unchanged=0)
    assert table.updated_rows == [
        {"id": "rec1", "fields": {"Coin ID": "bitcoin", "Price USD": 96000.0}}
    ]


def test_unmanaged_columns_do_not_trigger_an_update() -> None:
    table = FakeTable(
        [_record("rec1", {"Coin ID": "bitcoin", "Price USD": 95000.0, "Notes": "hand-typed"})]
    )
    sync = AirtableSync(table, key_field="Coin ID")

    report = sync.sync([{"Coin ID": "bitcoin", "Price USD": 95000.0}])

    assert report.unchanged == 1
    assert table.updated_rows == []


def test_missing_key_field_raises_value_error() -> None:
    table = FakeTable(existing_records=[])
    sync = AirtableSync(table, key_field="Coin ID")

    with pytest.raises(ValueError, match="Coin ID"):
        sync.sync([{"Price USD": 1.0}])


def test_mixed_batch_reports_each_bucket() -> None:
    table = FakeTable(
        [
            _record("rec1", {"Coin ID": "bitcoin", "Price USD": 95000.0}),
            _record("rec2", {"Coin ID": "ethereum", "Price USD": 3000.0}),
        ]
    )
    sync = AirtableSync(table, key_field="Coin ID")

    report = sync.sync(
        [
            {"Coin ID": "bitcoin", "Price USD": 95000.0},  # unchanged
            {"Coin ID": "ethereum", "Price USD": 3200.0},  # updated
            {"Coin ID": "solana", "Price USD": 150.0},  # created
        ]
    )

    assert report == SyncReport(created=1, updated=1, unchanged=1)
