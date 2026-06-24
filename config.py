"""Load Airtable credentials from the .env file."""
import os
import re
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Resolve .env next to this module so the scripts work from any cwd.
_ENV_PATH = Path(__file__).resolve().parent / ".env"


@dataclass(frozen=True)
class AirtableConfig:
    token: str
    base_id: str
    table_name: str


def _extract_base_id(pasted_value: str) -> str:
    # People paste the whole browser URL (app.../tbl.../viw...). The base id
    # is just the leading "app..." segment, so pull that out of whatever
    # they gave us instead of failing on a malformed value.
    base_id_match = re.search(r"app[a-zA-Z0-9]+", pasted_value)
    return base_id_match.group(0) if base_id_match else pasted_value


def load_config() -> AirtableConfig:
    load_dotenv(_ENV_PATH)
    token = os.environ.get("AIRTABLE_TOKEN", "").strip()
    base_id = _extract_base_id(os.environ.get("AIRTABLE_BASE_ID", "").strip())
    table_name = os.environ.get("AIRTABLE_TABLE_NAME", "Crypto").strip()

    unfilled = [
        env_name
        for env_name, value in (("AIRTABLE_TOKEN", token), ("AIRTABLE_BASE_ID", base_id))
        if not value or "XXXX" in value
    ]
    if unfilled:
        raise SystemExit(f"These values are still missing in .env: {', '.join(unfilled)}")

    return AirtableConfig(token=token, base_id=base_id, table_name=table_name)
