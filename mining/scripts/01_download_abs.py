"""Download ABS data: 8412.0 Mineral and Petroleum Exploration (all time series) and the latest CPI table.

The file links carry the release month (e.g. .../jun-2026/...), so they are read from each
publication's latest-release page rather than hard-coded.
"""
import io
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import RAW  # noqa: E402
from download_utils import fetch  # noqa: E402

ABS = "https://www.abs.gov.au"
EXPLORATION = ABS + "/statistics/industry/mining/mineral-and-petroleum-exploration-australia/latest-release"
CPI = ABS + "/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release"


def link(page, pattern):
    html = fetch(page).text
    found = re.findall(r'href="([^"]*' + pattern + ')"', html)
    if not found:
        raise RuntimeError(f"no link matching {pattern} on {page}")
    return ABS + found[0] if found[0].startswith("/") else found[0]


if __name__ == "__main__":
    out = RAW / "abs"
    out.mkdir(parents=True, exist_ok=True)

    url = link(EXPLORATION, r"All-time-series-spreadsheets\.zip")
    with zipfile.ZipFile(io.BytesIO(fetch(url).content)) as z:
        z.extractall(out / "8412")
    print(f"  8412.0 from {url.split('/')[-2]}: {sorted(p.name for p in (out / '8412').iterdir())}")

    url = link(CPI, r"/640101\.xlsx")
    (out / "640101.xlsx").write_bytes(fetch(url).content)
    print(f"  CPI table 1 from {url.split('/')[-2]}")
