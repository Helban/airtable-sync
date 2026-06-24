"""Reusable Airtable upsert connector.

Syncs a list of source rows into an Airtable table, keyed on one field.
The value over a bare ``Table.batch_upsert`` is change detection: rows
whose managed fields already match what is in Airtable are skipped, so a
monitor running every minute does not rewrite unchanged records or bloat
the table's revision history.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyairtable import Table

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SyncReport:
    """Outcome of one sync run, split by what happened to each source row."""

    created: int
    updated: int
    unchanged: int

    @property
    def written(self) -> int:
        return self.created + self.updated


class AirtableSync:
    """Upserts source rows into one Airtable table, matched on ``key_field``."""

    def __init__(self, table: "Table", key_field: str) -> None:
        self._table = table
        self._key_field = key_field

    @classmethod
    def from_token(
        cls,
        token: str,
        base_id: str,
        table_name: str,
        key_field: str,
    ) -> "AirtableSync":
        # Imported here so the unit tests can inject a fake table without
        # pulling in pyairtable or touching the network.
        from pyairtable import Api, retry_strategy

        # Airtable allows 5 requests/second per base and returns a 30s lockout
        # on 429. Let the client retry those instead of pacing requests by hand.
        airtable = Api(
            token,
            retry_strategy=retry_strategy(
                total=8, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503)
            ),
        )
        return cls(airtable.table(base_id, table_name), key_field)

    def sync(self, source_rows: list[dict[str, Any]]) -> SyncReport:
        for source_row in source_rows:
            if self._key_field not in source_row:
                raise ValueError(
                    f"Source row is missing key field {self._key_field!r}: {source_row!r}"
                )

        existing_by_key = {
            record["fields"].get(self._key_field): record
            for record in self._table.all()
            if self._key_field in record["fields"]
        }

        rows_to_create: list[dict[str, Any]] = []
        rows_to_update: list[dict[str, Any]] = []
        unchanged_count = 0

        for source_row in source_rows:
            key_value = source_row[self._key_field]
            existing_record = existing_by_key.get(key_value)
            if existing_record is None:
                rows_to_create.append(source_row)
            elif _differs(source_row, existing_record["fields"]):
                rows_to_update.append({"id": existing_record["id"], "fields": source_row})
            else:
                unchanged_count += 1

        if rows_to_create:
            self._table.batch_create(rows_to_create)
        if rows_to_update:
            self._table.batch_update(rows_to_update)

        report = SyncReport(
            created=len(rows_to_create),
            updated=len(rows_to_update),
            unchanged=unchanged_count,
        )
        logger.info(
            "Airtable sync: %s created, %s updated, %s unchanged",
            report.created,
            report.updated,
            report.unchanged,
        )
        return report

def _differs(source_row: dict[str, Any], existing_fields: dict[str, Any]) -> bool:
    # Compare only the fields we manage. Extra Airtable columns a person
    # added by hand (notes, a Last Modified Time field, formulas) must not
    # count as a change, or every row would look dirty on every run.
    return any(
        existing_fields.get(field_name) != field_value
        for field_name, field_value in source_row.items()
    )
