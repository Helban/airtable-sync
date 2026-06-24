# Airtable Sync

Push scraped or monitored data into an Airtable base with change-aware upsert.

**Live demo:** https://airtable.com/appLRSprzirec0S5h/shrFbmtpNMrjxDG3H — the top 20
crypto prices, written and kept current by this connector.

Most "send data to Airtable" scripts either append a fresh copy every run (duplicates)
or rewrite every record (needless writes, a polluted revision history, and API rate
limits hit fast). This connector fetches the current rows, compares only the fields it
manages, and writes just the difference: new rows created, changed rows updated,
identical rows skipped.

## What's included

- `airtable_sync.py` — the reusable connector (`AirtableSync`, `SyncReport`). Drop it into any project.
- `crypto_monitor.py` — a working demo: pulls the top 20 coins from CoinGecko and syncs them into Airtable.
- `setup_table.py` — creates the demo table and its typed columns through the Airtable metadata API, so you don't set fields up by hand.
- `crypto_schema.py` — field layout shared by the setup script and the monitor.
- `config.py` — loads credentials from `.env`.
- `test_airtable_sync.py` — unit tests for the connector, no network.

## How the connector works

```python
from airtable_sync import AirtableSync

sync = AirtableSync.from_token(token, base_id, "Contacts", key_field="Email")
report = sync.sync([
    {"Email": "alice@example.com", "Name": "Alice"},
    {"Email": "bob@example.com",   "Name": "Bob"},
])
print(report.created, report.updated, report.unchanged)
```

`sync()` reads the table once, matches incoming rows against existing ones on
`key_field`, and batches the creates and updates. Columns a person added in
Airtable by hand are ignored when deciding whether a row changed, so manual notes
never trigger a phantom update.

## Setup

```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
```

Create a personal access token at https://airtable.com/create/tokens with scopes
`data.records:read`, `data.records:write`, `schema.bases:read`,
`schema.bases:write`, granted on your base. Put the token and the base id (the
`app...` part of the base URL) into `.env`.

```bash
venv/bin/python setup_table.py                    # creates the Crypto table
venv/bin/python crypto_monitor.py                 # fills it; run again to see the upsert
venv/bin/python crypto_monitor.py --interval 60   # keep it refreshing every 60s
```

First run prints `20 created, 0 updated, 0 unchanged`. A later run prints something
like `0 created, 16 updated, 4 unchanged`: no duplicates, only the coins whose price
moved get rewritten.

## Tests

```bash
venv/bin/python -m pytest
```

## Adapting it

Point `crypto_monitor.py` at your own source: replace `fetch_top_coins` and
`to_airtable_row`, set `key_field` to whatever uniquely identifies a row (an email,
an order id, a SKU), and adjust the columns in `crypto_schema.py`.
