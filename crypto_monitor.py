"""Fetch top crypto prices from CoinGecko and sync them into Airtable.

Run it repeatedly. The first run creates the rows; later runs update only
the coins whose price moved and skip the ones that did not.
"""
import argparse
import logging
import time
from typing import Any

import httpx

from airtable_sync import AirtableSync
from config import load_config
from crypto_schema import (
    CHANGE_24H,
    CHANGE_PRECISION,
    COIN,
    COIN_ID,
    MARKET_CAP,
    PRICE_PRECISION,
    PRICE_USD,
    SYMBOL,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # drop per-request noise
logger = logging.getLogger(__name__)

COINGECKO_MARKETS_URL = "https://api.coingecko.com/api/v3/coins/markets"
TOP_COINS = 20


def fetch_top_coins(coin_count: int) -> list[dict[str, Any]]:
    response = httpx.get(
        COINGECKO_MARKETS_URL,
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": coin_count,
            "page": 1,
            "price_change_percentage": "24h",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def to_airtable_row(coin: dict[str, Any]) -> dict[str, Any]:
    # Round to the precision the Airtable columns store. Without this, float
    # noise in the low digits of a re-fetch would look like a price change
    # and force a needless update.
    change_24h = coin.get("price_change_percentage_24h")
    return {
        COIN_ID: coin["id"],
        COIN: coin["name"],
        SYMBOL: coin["symbol"].upper(),
        PRICE_USD: round(coin["current_price"], PRICE_PRECISION),
        MARKET_CAP: coin["market_cap"],
        CHANGE_24H: round(change_24h, CHANGE_PRECISION) if change_24h is not None else None,
    }


def run_sync(sync: AirtableSync) -> None:
    coins = fetch_top_coins(TOP_COINS)
    rows = [to_airtable_row(coin) for coin in coins]
    report = sync.sync(rows)
    logger.info(
        "Done: %d created, %d updated, %d unchanged.",
        report.created,
        report.updated,
        report.unchanged,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync top crypto prices into Airtable.")
    parser.add_argument(
        "--interval",
        type=int,
        default=0,
        help="Seconds between runs. 0 (default) runs once and exits.",
    )
    interval_seconds = parser.parse_args().interval

    config = load_config()
    sync = AirtableSync.from_token(
        token=config.token,
        base_id=config.base_id,
        table_name=config.table_name,
        key_field=COIN_ID,
    )

    run_sync(sync)
    try:
        while interval_seconds > 0:
            time.sleep(interval_seconds)
            run_sync(sync)
    except KeyboardInterrupt:
        logger.info("Stopped.")


if __name__ == "__main__":
    main()
