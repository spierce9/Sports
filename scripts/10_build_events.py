"""One row per (country, match): the result from that country's side and the trading day it hits.

Outcome: win / draw / loss after extra time; a match decided on penalties counts as a win for
the shootout winner and a loss for the other side.
Event day: the first trading day of the country's index strictly after the match date (as in
Edmans, Garcia and Norli 2007). The results data give the local date of the venue, not the
kick-off time, so a match that ends during trading hours is still assigned to the next day.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (COUNTRIES, INCLUDE_QUALIFIERS, PROCESSED, QUALIFIERS, RAW,  # noqa: E402
                    SAMPLE_END, SAMPLE_START, TOURNAMENTS)

if __name__ == "__main__":
    res = pd.read_csv(RAW / "matches" / "results.csv", parse_dates=["date"])
    so = pd.read_csv(RAW / "matches" / "shootouts.csv", parse_dates=["date"])
    tours = TOURNAMENTS + (QUALIFIERS if INCLUDE_QUALIFIERS else [])
    res = res[res.tournament.isin(tours) & res.date.between(SAMPLE_START, SAMPLE_END)]
    res = res.dropna(subset=["home_score", "away_score"])
    res = res.merge(so[["date", "home_team", "away_team", "winner"]], how="left",
                    on=["date", "home_team", "away_team"])

    rows = []
    for side, other in [("home", "away"), ("away", "home")]:
        m = res[res[f"{side}_team"].isin(COUNTRIES)].copy()
        m["team"], m["opponent"] = m[f"{side}_team"], m[f"{other}_team"]
        m["goals_for"], m["goals_against"] = m[f"{side}_score"], m[f"{other}_score"]
        rows.append(m)
    ev = pd.concat(rows, ignore_index=True)
    ev["outcome"] = np.select([ev.goals_for > ev.goals_against, ev.goals_for < ev.goals_against],
                              ["win", "loss"], "draw")
    pens = ev.outcome.eq("draw") & ev.winner.notna()
    ev.loc[pens, "outcome"] = np.where(ev.loc[pens, "winner"] == ev.loc[pens, "team"], "win", "loss")
    ev["penalties"] = pens
    ev["country"] = ev.team.map(lambda t: COUNTRIES[t][0])

    # Map each match to the first trading day after it on the country's own exchange.
    out = []
    for country, g in ev.groupby("country"):
        days = pd.to_datetime(pd.read_csv(RAW / "prices" / f"{country.replace(' ', '_')}.csv").date)
        idx = days.searchsorted(g.date, side="right")
        g = g[idx < len(days)].copy()  # drop matches after the last price
        g["event_date"] = days.values[idx[idx < len(days)]]
        out.append(g)
    ev = pd.concat(out)
    # Portugal's index starts in 2013; drop matches before a country's first price.
    first = {c: pd.read_csv(RAW / "prices" / f"{c.replace(' ', '_')}.csv").date.min() for c in ev.country.unique()}
    ev = ev[ev.date >= ev.country.map(first).pipe(pd.to_datetime)]

    cols = ["country", "team", "date", "event_date", "tournament", "opponent", "goals_for",
            "goals_against", "penalties", "outcome", "neutral", "city"]
    ev = ev[cols].sort_values(["country", "date"])
    clash = ev.duplicated(["country", "event_date"], keep=False)
    if clash.any():
        print("  two matches hit the same trading day; keeping the later match:")
        print(ev[clash].to_string(index=False))
        ev = ev.drop_duplicates(["country", "event_date"], keep="last")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    ev.to_csv(PROCESSED / "match_events.csv", index=False)

    print(f"  {len(ev)} country-matches, {ev.date.min().date()} to {ev.date.max().date()}")
    print(pd.crosstab(ev.country, ev.outcome, margins=True).to_string())
    print(pd.crosstab(ev.tournament, ev.outcome, margins=True).to_string())
