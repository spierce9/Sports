"""Download monthly commodity prices, AUD/USD, and CPIs.

FRED (St Louis Fed):
  IMF primary commodity prices, USD, monthly averages (series in config.COMMODITIES)
  EXUSAL           US$ per A$, monthly average
  CPIAUCSL         US CPI, monthly
  AUSCPIALLQINMEI  Australian CPI, quarterly (OECD; ends early 2025 - extended with ABS in 10_build)
Yahoo Finance:
  GC=F gold futures (COMEX, USD/oz), monthly closes - gold is no longer on FRED.
"""
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import COMMODITIES, RAW  # noqa: E402
from download_utils import fetch  # noqa: E402

# FRED drops connections that send a browser-like User-Agent, so FRED requests send none.
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1=0&period2={p2}&interval=1mo"

if __name__ == "__main__":
    out = RAW / "prices"
    out.mkdir(parents=True, exist_ok=True)
    fred = [s for _, src, s in COMMODITIES.values() if src == "fred"] + ["EXUSAL", "CPIAUCSL", "AUSCPIALLQINMEI"]
    for s in fred:
        df = pd.read_csv(io.StringIO(fetch(FRED.format(s), headers={}).text))
        df.to_csv(out / f"{s}.csv", index=False)
        print(f"  FRED  {s:16s} {df.iloc[0, 0]} to {df.iloc[-1, 0]}")

    for _, src, t in COMMODITIES.values():
        if src != "yahoo":
            continue
        res = fetch(YAHOO.format(t=t, p2=int(datetime.now(timezone.utc).timestamp()))).json()["chart"]["result"][0]
        dates = pd.to_datetime(res["timestamp"], unit="s", utc=True).tz_convert(res["meta"]["exchangeTimezoneName"])
        df = pd.DataFrame({"date": dates.strftime("%Y-%m-01"), "close": res["indicators"]["quote"][0]["close"]})
        df = df.dropna().drop_duplicates("date", keep="last")
        df.to_csv(out / f"{t.replace('=', '_')}.csv", index=False)
        print(f"  Yahoo {t:16s} {df.date.iloc[0]} to {df.date.iloc[-1]}")
