"""Field layout for the crypto demo table.

Shared by setup_table.py (creates these columns) and crypto_monitor.py
(maps CoinGecko data onto them), so the field names never drift apart.
"""

COIN_ID = "Coin ID"
COIN = "Coin"
SYMBOL = "Symbol"
PRICE_USD = "Price USD"
MARKET_CAP = "Market Cap"
CHANGE_24H = "24h Change %"

# Decimal places the number columns store. The monitor rounds to the same
# precision before writing, so float noise below it cannot look like a change.
PRICE_PRECISION = 8
CHANGE_PRECISION = 2

# Airtable field model: the first entry becomes the table's primary field,
# so a text field (the coin id we dedupe on) has to come first.
TABLE_FIELDS = [
    {"name": COIN_ID, "type": "singleLineText"},
    {"name": COIN, "type": "singleLineText"},
    {"name": SYMBOL, "type": "singleLineText"},
    {"name": PRICE_USD, "type": "number", "options": {"precision": PRICE_PRECISION}},
    {"name": MARKET_CAP, "type": "number", "options": {"precision": 0}},
    {"name": CHANGE_24H, "type": "number", "options": {"precision": CHANGE_PRECISION}},
]
