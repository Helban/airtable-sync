"""Create the crypto demo table in Airtable if it is not there yet.

Run once after filling .env. Safe to run again: it skips creation when a
table with the configured name already exists.
"""
import logging

from pyairtable import Api

from config import load_config
from crypto_schema import TABLE_FIELDS

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    config = load_config()
    base = Api(config.token).base(config.base_id)

    existing_table_names = [table.name for table in base.schema().tables]
    if config.table_name in existing_table_names:
        logger.info("Table %r already exists, nothing to create.", config.table_name)
        return

    base.create_table(name=config.table_name, fields=TABLE_FIELDS)
    logger.info("Created table %r with %d fields.", config.table_name, len(TABLE_FIELDS))


if __name__ == "__main__":
    main()
