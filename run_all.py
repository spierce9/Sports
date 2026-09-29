"""Run the whole pipeline in order.

  python run_all.py              # analysis only, from the data already in data/raw
  python run_all.py --download   # re-download the raw data first
"""
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent / "scripts"

if __name__ == "__main__":
    download = "--download" in sys.argv
    steps = sorted(p for p in SCRIPTS.glob("[0-9][0-9]_*.py"))
    for step in steps:
        if "download" in step.name and not download:
            continue
        print(f"\n=== {step.name} ===")
        subprocess.run([sys.executable, str(step)], check=True)
