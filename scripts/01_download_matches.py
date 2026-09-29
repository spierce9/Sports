"""Download every international football result (men's senior teams) and penalty shootout.

Source: Mart Jürisoo, "International football results from 1872", GitHub
martj42/international_results (also on Kaggle). Scores include extra time; shootouts
are in a separate file with the winner.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import RAW  # noqa: E402
from download_utils import fetch  # noqa: E402

BASE = "https://raw.githubusercontent.com/martj42/international_results/master/"

if __name__ == "__main__":
    out = RAW / "matches"
    out.mkdir(parents=True, exist_ok=True)
    for name in ["results.csv", "shootouts.csv"]:
        content = fetch(BASE + name).content
        (out / name).write_bytes(content)
        print(f"  saved {name} ({len(content) / 1024:.0f} KB)")
