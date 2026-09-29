"""Shared helpers for the download scripts."""
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import HTTP_HEADERS  # noqa: E402


def fetch(url, retries=4, timeout=60):
    """GET a URL with exponential backoff; raise on final failure."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HTTP_HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == retries - 1:
                raise
            wait = 2 ** (attempt + 1)
            print(f"  retry in {wait}s ({e})")
            time.sleep(wait)
