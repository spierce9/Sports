"""Project settings. Change values here and re-run `python run_all.py`."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
TABLES = ROOT / "output" / "tables"
FIGURES = ROOT / "output" / "figures"

# Sample. Prices are downloaded from earlier so the first returns and lags exist in Jan 2010.
DOWNLOAD_START = "2009-06-01"
SAMPLE_START = "2010-01-01"
SAMPLE_END = "2026-09-30"

# Second period starts here: 2010-17 vs 2018-26.
SPLIT_DATE = "2018-01-01"

# Drop the first N trading days of each country's sample before estimating (for live re-runs).
DROP_FIRST_N_DAYS = 0

# Team name in the results data -> (country label, Yahoo ticker of its main stock index).
COUNTRIES = {
    "England": ("UK", "^FTSE"),
    "Germany": ("Germany", "^GDAXI"),
    "France": ("France", "^FCHI"),
    "Spain": ("Spain", "^IBEX"),
    "Italy": ("Italy", "FTSEMIB.MI"),
    "Netherlands": ("Netherlands", "^AEX"),
    "Belgium": ("Belgium", "^BFX"),
    "Portugal": ("Portugal", "PSI20.LS"),  # Yahoo history starts 30 Apr 2013
    "Brazil": ("Brazil", "^BVSP"),
    "Mexico": ("Mexico", "^MXX"),
    "Japan": ("Japan", "^N225"),
    "South Korea": ("South Korea", "^KS11"),
}

# World market: iShares MSCI ACWI ETF (USD, New York close).
WORLD_TICKER = "ACWI"

# Every match in the finals of these tournaments counts as an event.
TOURNAMENTS = ["FIFA World Cup", "UEFA Euro", "Copa América", "Gold Cup", "AFC Asian Cup"]
# Robustness: also count qualifiers for these tournaments.
INCLUDE_QUALIFIERS = False
QUALIFIERS = ["FIFA World Cup qualification", "UEFA Euro qualification", "AFC Asian Cup qualification"]

HTTP_HEADERS = {"User-Agent": "Mozilla/5.0 (research project; FINA5521)"}
