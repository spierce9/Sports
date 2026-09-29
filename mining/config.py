"""Project settings. Change values here and re-run `python run_all.py` (from this folder)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"
FIGURES = ROOT / "output" / "figures"

# Years are Australian financial years (July-June), labelled by the year they end, so the
# latest ABS quarter (June) closes a full year. FY2026 = Jul 2025 - Jun 2026.
SAMPLE_START_FY = 1993  # first FY with monthly FRED prices (Jan 1992) and a prior-year change
SAMPLE_END_FY = 2026

# Headline test: price change over the next HORIZON_YEARS on exploration growth over the past year.
HORIZON_YEARS = 1

# Robustness switches.
DROP_FIRST_N_YEARS = 0      # drop the first N years of each commodity's sample
EXCLUDE_FY = []             # e.g. [2009, 2020] to drop the GFC and COVID years (by the year the change ends)
REAL = False                # deflate exploration by Australian CPI and prices by US CPI
PRICE_CURRENCY = "USD"      # "USD" or "AUD" (explorers are paid in A$)

# Commodity -> (ABS 8412.0 Table 5 "mineral sought", price source, price series).
# FRED series are IMF primary commodity prices (monthly, USD, from Jan 1992).
COMMODITIES = {
    "Nickel": ("Nickel, cobalt", "fred", "PNICKUSDM"),       # ABS series from Sep qtr 1999
    "Copper": ("Copper", "fred", "PCOPPUSDM"),               # ABS series from Sep qtr 1999
    "Zinc-lead": ("Silver, lead, zinc", "fred", "PZINCUSDM"),  # ABS from Sep qtr 1999; zinc price
    "Iron ore": ("Iron ore", "fred", "PIORECRUSDM"),
    "Uranium": ("Uranium", "fred", "PURANUSDM"),
    "Coal": ("Coal", "fred", "PCOALAUUSDM"),                 # Australian thermal coal
    "Gold": ("Gold", "yahoo", "GC=F"),                       # COMEX futures, from Aug 2000
}

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (research project; FINA5521)"}
