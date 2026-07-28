#!/usr/bin/env python3
"""Download one MOEX trading day and write a typed Parquet file."""

from __future__ import annotations

import argparse
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import requests

BASE_URL = "https://iss.moex.com/iss"

SCHEMA = pa.schema(
    [
        ("boardid", pa.string()),
        ("board_name", pa.string()),
        ("isin", pa.string()),
        ("isqualifiedinvestors", pa.int16()),
        ("secid", pa.string()),
        ("price", pa.decimal128(20, 6)),
        ("value", pa.decimal128(24, 6)),
        ("quantity", pa.int64()),
        ("deal_type", pa.string()),
        # Old PXF/Parquet readers do not reliably recognize Arrow timestamp
        # logical annotations. Keep ISO text in raw HDFS and cast in the mart.
        ("deal_time", pa.string()),
        ("trade_session_date", pa.date32()),
    ]
)


def get_json(
    session: requests.Session, url: str, params: dict[str, Any]
) -> dict[str, Any]:
    response = session.get(url, params=params, timeout=60)
    response.raise_for_status()
    return response.json()


def resolve_security(
    session: requests.Session, ticker: str
) -> tuple[str, str, str | None, int]:
    payload = get_json(
        session,
        f"{BASE_URL}/engines/stock/markets/shares/boards/TQBR/securities.json",
        {"iss.meta": "off", "iss.only": "securities", "securities": ticker},
    )
    block = payload["securities"]
    candidates = [
        dict(zip(block["columns"], row))
        for row in block["data"]
        if row[block["columns"].index("SECID")] == ticker
    ]
    if not candidates:
        raise RuntimeError(f"Ticker {ticker!r} was not found on board TQBR")
    item = candidates[0]
    return (
        item["BOARDID"],
        item.get("BOARDNAME") or item["BOARDID"],
        item.get("ISIN"),
        int(item.get("ISQUALIFIEDINVESTORS") or 0),
    )


def fetch_trades(
    session: requests.Session, ticker: str, trade_date: str
) -> list[dict[str, Any]]:
    boardid, board_name, isin, qualified = resolve_security(session, ticker)
    url = (
        f"{BASE_URL}/engines/stock/markets/shares/"
        f"securities/{ticker}/trades.json"
    )
    rows: list[dict[str, Any]] = []
    start = 0

    while True:
        payload = get_json(
            session,
            url,
            {
                "iss.meta": "off",
                "iss.only": "trades",
                "trades.columns": (
                    "BOARDID,SECID,PRICE,VALUE,QUANTITY,BUYSELL,TRADETIME,TRADEDATE"
                ),
                "tradingsession": 1,
                "date": trade_date,
                "start": start,
            },
        )
        block = payload["trades"]
        page = [dict(zip(block["columns"], row)) for row in block["data"]]
        if not page:
            break

        for item in page:
            if item.get("TRADEDATE") != trade_date:
                continue
            rows.append(
                {
                    "boardid": item.get("BOARDID") or boardid,
                    "board_name": board_name,
                    "isin": isin,
                    "isqualifiedinvestors": qualified,
                    "secid": item.get("SECID") or ticker,
                    "price": (
                        Decimal(str(item["PRICE"]))
                        if item.get("PRICE") is not None
                        else None
                    ),
                    "value": (
                        Decimal(str(item["VALUE"]))
                        if item.get("VALUE") is not None
                        else None
                    ),
                    "quantity": (
                        int(item["QUANTITY"])
                        if item.get("QUANTITY") is not None
                        else None
                    ),
                    "deal_type": item.get("BUYSELL"),
                    "deal_time": (
                        f"{trade_date}T{item['TRADETIME']}"
                        if item.get("TRADETIME")
                        else None
                    ),
                    "trade_session_date": date.fromisoformat(trade_date),
                }
            )
        start += len(page)

    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ticker", default="RASP")
    parser.add_argument("--date", required=True, dest="trade_date")
    parser.add_argument("--output-dir", default="data/moex")
    args = parser.parse_args()

    date.fromisoformat(args.trade_date)
    ticker = args.ticker.upper()
    with requests.Session() as session:
        session.headers["User-Agent"] = "moex-cloudberry-lab/1.0"
        rows = fetch_trades(session, ticker, args.trade_date)
    if not rows:
        raise RuntimeError(
            f"No trades returned for {ticker} on {args.trade_date}. "
            "Choose an actual MOEX trading session; the trades endpoint may "
            "not retain arbitrary historical dates."
        )
    if any(row["deal_time"] is None for row in rows):
        raise RuntimeError("MOEX returned trades without TRADETIME")

    destination = (
        Path(args.output_dir)
        / f"secid={ticker}"
        / f"trade_session_date={args.trade_date}"
        / "trades.parquet"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(
        pa.Table.from_pylist(rows, schema=SCHEMA),
        destination,
        # PXF 1.6.0 ships Hadoop 2.10 without the native Zstandard codec.
        # Snappy is supported by that runtime and remains columnar/compressed.
        compression="snappy",
        use_dictionary=True,
    )
    print(
        json.dumps(
            {"rows": len(rows), "file": str(destination)}, ensure_ascii=False
        )
    )


if __name__ == "__main__":
    main()
