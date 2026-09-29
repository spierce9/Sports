"""Do unexpected results move the market more? (pre-match Elo expectations)

  (E1) Across matches:  ar_i = a + b surprise_i + e_i
       surprise = actual result (1 / 0.5 / 0) - Elo expected score; b > 0 means markets rise
       after better-than-expected results and fall after worse-than-expected ones.
       Run for the next-day abnormal return and the two-day windows (see 31_event_windows.py).
  (E2) All country-days: ar = a + b1 upset_loss + b2 expected_loss + b3 win + b4 draw + e
       upset_loss = lost as the favourite (expected >= 0.5); baseline = days after no match.
"""
import sys
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROCESSED, TABLES  # noqa: E402

PERIODS = {"All 2010-26": None, "2010-17": 0, "2018-26": 1}
WINDOWS = {"next": "next day", "car_same_next": "same + next day", "car_next_after": "next + day after"}


def row(fit, term, **info):
    return {**info, "term": term, "coef": fit.params[term], "se": fit.bse[term], "t": fit.tvalues[term],
            "p": fit.pvalues[term], "N": int(fit.nobs)}


if __name__ == "__main__":
    ev = pd.read_csv(PROCESSED / "match_windows.csv", parse_dates=["date", "event_date"])
    panel = pd.read_csv(PROCESSED / "panel.csv", parse_dates=["date"])
    up = ev[["country", "event_date", "upset_loss"]].rename(columns={"event_date": "date"})
    panel = panel.merge(up, how="left", on=["country", "date"]).fillna({"upset_loss": 0})
    panel["expected_loss"] = panel.loss - panel.upset_loss

    e1, e2 = [], []
    for per, late in PERIODS.items():
        d = ev if late is None else ev[ev.late == late]
        for w, label in WINDOWS.items():
            fit = smf.ols(f"{w} ~ surprise", d.dropna(subset=[w])).fit()
            e1.append(row(fit, "surprise", period=per, window=label))
        p = panel if late is None else panel[panel.late == late]
        fit = smf.ols("ar ~ upset_loss + expected_loss + win + draw", p).fit()
        for term in ["upset_loss", "expected_loss", "win", "draw"]:
            e2.append(row(fit, term, period=per))
        t = fit.t_test("upset_loss - expected_loss = 0")
        e2.append({"period": per, "term": "test: upset - expected loss", "coef": float(t.effect[0]),
                   "se": float(t.sd[0][0]), "t": float(t.tvalue[0][0]), "p": float(t.pvalue), "N": int(fit.nobs)})
    e1, e2 = pd.DataFrame(e1), pd.DataFrame(e2)
    e1.to_csv(TABLES / "surprise_slope.csv", index=False)
    e2.to_csv(TABLES / "upset_losses.csv", index=False)

    counts = ev.assign(kind=ev.outcome.where(ev.outcome != "loss",
                                             ev.upset_loss.map({1: "upset loss", 0: "expected loss"})))
    text = "\n".join([
        "Match counts: " + counts.kind.value_counts().to_string().replace("\n", "; "), "",
        "(E1) Abnormal return (%) on Elo surprise (actual - expected result), across matches",
        e1.round(3).to_string(index=False), "",
        "(E2) Next-day abnormal return (%) on outcome dummies, losses split by pre-match favourite",
        e2.round(3).to_string(index=False)])
    (TABLES / "surprise.txt").write_text(text + "\n")
    print(text)
