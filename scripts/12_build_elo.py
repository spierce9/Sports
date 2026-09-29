"""Pre-match Elo ratings and the expected result for each country-match.

eloratings.net cannot be downloaded from here, so the World Football Elo ratings are rebuilt
from every international result since 1872 with that site's formula:

  expected   We = 1 / (10^(-dr/400) + 1),  dr = own rating - opponent rating (+100 if at home)
  update     R_new = R_old + K * G * (W - We),  W = 1 win, 0.5 draw (incl. shootouts), 0 loss
  K          60 World Cup finals; 50 continental finals and Confederations Cup;
             40 qualifiers and Nations Leagues; 30 other tournaments; 20 friendlies
  G          1 if the goal difference is 0 or 1; 1.5 if 2; (11 + N) / 8 if N >= 3
New teams start at 1500. Surprise = actual result (1 / 0.5 / 0; a shootout counts as the
shootout result) minus We: negative means worse than expected.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROCESSED, RAW  # noqa: E402

CONTINENTAL = {"UEFA Euro", "Copa América", "AFC Asian Cup", "African Cup of Nations", "Gold Cup",
               "CONCACAF Championship", "Oceania Nations Cup", "Confederations Cup"}


def k_factor(t):
    if t == "FIFA World Cup":
        return 60
    if t in CONTINENTAL:
        return 50
    if "qualification" in t or "Nations League" in t:
        return 40
    if t == "Friendly":
        return 20
    return 30


def goal_weight(n):
    return 1.0 if n <= 1 else 1.5 if n == 2 else (11 + n) / 8


if __name__ == "__main__":
    res = pd.read_csv(RAW / "matches" / "results.csv", parse_dates=["date"])
    res = res.dropna(subset=["home_score", "away_score"]).sort_values("date", kind="stable")

    rating, pre_h, pre_a = {}, [], []
    for h, a, hs, as_, t, neutral in zip(res.home_team, res.away_team, res.home_score,
                                         res.away_score, res.tournament, res.neutral):
        rh, ra = rating.get(h, 1500.0), rating.get(a, 1500.0)
        pre_h.append(rh)
        pre_a.append(ra)
        dr = rh - ra + (0 if neutral else 100)
        we = 1 / (10 ** (-dr / 400) + 1)
        w = 1.0 if hs > as_ else 0.0 if hs < as_ else 0.5
        change = k_factor(t) * goal_weight(abs(hs - as_)) * (w - we)
        rating[h], rating[a] = rh + change, ra - change
    res["elo_home"], res["elo_away"] = pre_h, pre_a

    ev = pd.read_csv(PROCESSED / "match_events.csv", parse_dates=["date", "event_date"])
    ev = ev.drop(columns=[c for c in ev.columns if c.startswith(("elo_", "expected", "surprise", "upset"))])
    r = res[["date", "home_team", "away_team", "elo_home", "elo_away"]]
    home = ev.merge(r, left_on=["date", "team", "opponent"], right_on=["date", "home_team", "away_team"])
    home = home.assign(elo_team=home.elo_home, elo_opp=home.elo_away, at_home=1)
    away = ev.merge(r, left_on=["date", "team", "opponent"], right_on=["date", "away_team", "home_team"])
    away = away.assign(elo_team=away.elo_away, elo_opp=away.elo_home, at_home=-1)
    ev = pd.concat([home, away])[list(ev.columns) + ["elo_team", "elo_opp", "at_home"]]
    ev["at_home"] = np.where(ev.neutral, 0, ev.at_home)  # +100 to whichever side is at home
    ev["expected"] = 1 / (10 ** (-(ev.elo_team - ev.elo_opp + 100 * ev.at_home) / 400) + 1)
    ev["surprise"] = ev.outcome.map({"win": 1.0, "draw": 0.5, "loss": 0.0}) - ev.expected
    ev["upset_loss"] = ((ev.outcome == "loss") & (ev.expected >= 0.5)).astype(int)
    ev = ev.drop(columns="at_home").sort_values(["country", "date"])
    ev.to_csv(PROCESSED / "match_events.csv", index=False)

    print(f"  {len(ev)} country-matches with pre-match Elo")
    top = pd.Series(rating).sort_values(ascending=False).head(10).round(0)
    print("  current top 10:", ", ".join(f"{k} {v:.0f}" for k, v in top.items()))
    print("  mean expected score by outcome:", ev.groupby("outcome").expected.mean().round(2).to_dict())
    print(f"  losses as favourite (expected >= 0.5): {ev.upset_loss.sum()} of {(ev.outcome == 'loss').sum()}")
