"""Timing check: when does the market react, if at all?

The results data have no kick-off times, so the headline assigns each match to the first trading
day after the match date. A match that ends before the close is priced the same day; an evening
match in the Americas reaches Asia during its next session. Abnormal returns around each match
(trading days on the country's own exchange):

  pre       last trading day before the match date                (placebo: result unknown)
  same      the match date itself, if it is a trading day         (daytime matches)
  next      first trading day after the match date                (headline)
  after     the trading day after that                            (slow reaction)
  car_same_next = same + next   (same = 0 for weekend matches)
  car_next_after = next + after

Each window is regressed on loss and draw dummies across matches (baseline = wins), so the
intercept is the mean after wins and the loss coefficient is loss minus win. Means are
tested against zero: abnormal returns average zero on ordinary days by construction.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROCESSED, SPLIT_DATE, TABLES  # noqa: E402

WINDOWS = ["pre", "same", "next", "after", "car_same_next", "car_next_after"]

if __name__ == "__main__":
    panel = pd.read_csv(PROCESSED / "panel.csv", parse_dates=["date"])
    ev = pd.read_csv(PROCESSED / "match_events.csv", parse_dates=["date", "event_date"])

    rows = []
    for country, g in ev.groupby("country"):
        p = panel[panel.country == country].sort_values("date").reset_index(drop=True)
        days, ar = p.date.values, p.ar.values
        g = g.copy()
        k = days.searchsorted(g.event_date.values)  # position of the "next" day
        ok = (k < len(days)) & (days[np.minimum(k, len(days) - 1)] == g.event_date.values)
        g, k = g[ok], k[ok]
        same = days[k - 1] == g.date.values  # the day before "next" is the match date itself
        g["same_trading_day"] = same
        g["same"] = np.where(same, ar[k - 1], np.nan)
        g["pre"] = np.where(same, ar[np.maximum(k - 2, 0)], ar[k - 1])
        g["next"] = ar[k]
        g["after"] = np.where(k + 1 < len(days), ar[np.minimum(k + 1, len(days) - 1)], np.nan)
        g["car_same_next"] = np.nan_to_num(g.same) + g.next
        g["car_next_after"] = g.next + g.after
        rows.append(g)
    ev = pd.concat(rows)
    ev["late"] = (ev.date >= SPLIT_DATE).astype(int)
    ev["loss"] = (ev.outcome == "loss").astype(int)
    ev["draw"] = (ev.outcome == "draw").astype(int)
    ev.to_csv(PROCESSED / "match_windows.csv", index=False)

    means, regs = [], []
    for per, d in [("All 2010-26", ev), ("2010-17", ev[ev.late == 0]), ("2018-26", ev[ev.late == 1])]:
        for w in WINDOWS:
            for o, h in d.groupby("outcome"):
                x = h[w].dropna()
                means.append({"period": per, "window": w, "outcome": o, "N": len(x), "mean_ar": x.mean(),
                              "t_vs_0": x.mean() / (x.std() / np.sqrt(len(x))), "share_negative": (x < 0).mean()})
            fit = smf.ols(f"{w} ~ loss + draw", d.dropna(subset=[w])).fit()
            regs.append({"period": per, "window": w, "mean_after_win": fit.params["Intercept"],
                         "loss_minus_win": fit.params["loss"], "se": fit.bse["loss"], "t": fit.tvalues["loss"],
                         "p": fit.pvalues["loss"], "N": int(fit.nobs)})
    means, regs = pd.DataFrame(means), pd.DataFrame(regs)
    means.to_csv(TABLES / "windows_means.csv", index=False)
    regs.to_csv(TABLES / "windows_loss_vs_win.csv", index=False)

    wide = means.pivot_table(index=["period", "window"], columns="outcome", values=["mean_ar", "t_vs_0"])
    wide = wide.reindex(pd.MultiIndex.from_product([["All 2010-26", "2010-17", "2018-26"], WINDOWS]))
    wide.columns = [f"{o} {s}" for s, o in wide.columns]
    wide = wide[[f"{o} {s}" for o in ["loss", "win", "draw"] for s in ["mean_ar", "t_vs_0"]]]
    text = "\n".join([
        f"Matches on a trading day (same-day window exists): {ev.same_trading_day.sum()} of {len(ev)}", "",
        "Mean abnormal return (%) by window and outcome, with t against zero",
        wide.round(3).to_string(), "",
        "Loss minus win by window (regression on loss and draw dummies across matches; OLS SE)",
        regs.round(3).to_string(index=False)])
    (TABLES / "windows.txt").write_text(text + "\n")
    print(text)
