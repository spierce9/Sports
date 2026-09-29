"""Download daily closing levels of each country's stock index and the world index from Yahoo Finance.

Indices are price indices in local currency. The world index is the iShares MSCI ACWI ETF
(USD), the longest free daily series for the MSCI All Country World Index.
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import COUNTRIES, DOWNLOAD_START, RAW, WORLD_TICKER  # noqa: E402
from download_utils import fetch  # noqa: E402

URL = "https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1={p1}&period2={p2}&interval=1d"


def download(ticker, p1, p2):
    res = fetch(URL.format(t=ticker, p1=p1, p2=p2)).json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    # Yahoo timestamps are the session open; the trading date is in the exchange's time zone.
    tz = res["meta"]["exchangeTimezoneName"]
    dates = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert(tz).date
    df = pd.DataFrame({"close": q["close"]}, index=pd.Index(dates, name="date")).dropna()
    return df[~df.index.duplicated(keep="last")], tz


if __name__ == "__main__":
    out = RAW / "prices"
    out.mkdir(parents=True, exist_ok=True)
    p1 = int(datetime.fromisoformat(DOWNLOAD_START).replace(tzinfo=timezone.utc).timestamp())
    p2 = int(datetime.now(timezone.utc).timestamp())
    series = {label: ticker for label, ticker in COUNTRIES.values()} | {"World": WORLD_TICKER}
    for label, ticker in series.items():
        df, tz = download(ticker, p1, p2)
        df.to_csv(out / f"{label.replace(' ', '_')}.csv")
        print(f"  {label:12s} {ticker:11s} {df.index.min()} to {df.index.max()}, {len(df)} days ({tz})")
