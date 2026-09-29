"""Daily panel: one row per (country, trading day) with the index return, world return and match dummies.

Returns are 100 x log changes of the closing level (percent). The world index (ACWI, New York
close) is carried forward to each country's trading days, so the world return covers the same
calendar span as the country return. world_lag is the previous day's world return: Asian and
European markets close before New York, so part of a world move reaches them a day late.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (COUNTRIES, DROP_FIRST_N_DAYS, PROCESSED, RAW, SAMPLE_END,  # noqa: E402
                    SAMPLE_START, SPLIT_DATE)


def load(label):
    df = pd.read_csv(RAW / "prices" / f"{label.replace(' ', '_')}.csv", parse_dates=["date"])
    return df.set_index("date").close.sort_index()


if __name__ == "__main__":
    world = load("World")
    events = pd.read_csv(PROCESSED / "match_events.csv", parse_dates=["date", "event_date"])

    panel = []
    for label, _ in COUNTRIES.values():
        px = load(label)
        w = world.reindex(world.index.union(px.index)).ffill().reindex(px.index)
        df = pd.DataFrame({"ret": 100 * np.log(px).diff(), "world": 100 * np.log(w).diff()})
        df["world_lag"] = df.world.shift(1)
        df = df.loc[SAMPLE_START:SAMPLE_END].dropna().iloc[DROP_FIRST_N_DAYS:]
        df["country"] = label
        panel.append(df.reset_index())
    panel = pd.concat(panel, ignore_index=True)

    ev = events[["country", "event_date", "outcome", "tournament", "opponent"]].rename(columns={"event_date": "date"})
    panel = panel.merge(ev, how="left", on=["country", "date"])
    for o in ["loss", "win", "draw"]:
        panel[o] = (panel.outcome == o).astype(int)
    panel["match_day"] = panel.outcome.notna().astype(int)
    panel["late"] = (panel.date >= SPLIT_DATE).astype(int)
    panel.to_csv(PROCESSED / "panel.csv", index=False)

    lost = len(events) - panel.match_day.sum()
    print(f"  {len(panel)} country-days, {panel.date.min().date()} to {panel.date.max().date()}; "
          f"{panel.match_day.sum()} match days ({lost} events outside the return sample)")
    zero = (panel.ret == 0).groupby(panel.country).mean()
    print(f"  share of zero returns (stale prices) by country, max: {zero.max():.1%} ({zero.idxmax()})")
    big = panel[panel.ret.abs() > 10]
    print(f"  daily moves beyond +/-10%: {len(big)}")
    if len(big):
        print(big[["country", "date", "ret", "world"]].to_string(index=False))
