"""Do football results move the country's stock market the next trading day?

Pooled over all countries and trading days (non-match days are the baseline):

  (A) Direction  ar_it     = a + bL loss_it + bW win_it + bD draw_it + e_it
  (B) Size       |ar_it|   = a + bL loss_it + bW win_it + bD draw_it + e_it

Each is run on the whole sample, 2010-17 and 2018-26, and with a period dummy (late = 1 from
2018) interacted with each outcome. Tests reported:
  loss - win     do losses and wins differ?                   (A and B)
  loss + win     is the fall after a loss bigger than the rise after a win?   (A; < 0 means yes)
Standard errors are OLS; t_HC1 (heteroskedasticity-robust) is saved alongside as a check.
"""
import sys
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROCESSED, TABLES  # noqa: E402

SAMPLES = {"All 2010-26": None, "2010-17": 0, "2018-26": 1}
TESTS = {"loss - win": "loss - win = 0", "loss + win": "loss + win = 0"}


def summarise(fit, fit_hc, name, dep):
    rows = [{"dep": dep, "model": name, "term": k, "coef": fit.params[k], "se": fit.bse[k],
             "t": fit.tvalues[k], "p": fit.pvalues[k], "t_HC1": fit_hc.tvalues[k]} for k in fit.params.index]
    for label, h in TESTS.items():
        if dep == "|ar|" and label == "loss + win":
            continue
        for suffix, pre in [("", ""), (" (2018-26 change)", "late_")] if "late" in fit.params else [("", "")]:
            hyp = h.replace("loss", pre + "loss").replace("win", pre + "win")
            t, th = fit.t_test(hyp), fit_hc.t_test(hyp)
            rows.append({"dep": dep, "model": name, "term": "test: " + label + suffix,
                         "coef": float(t.effect[0]), "se": float(t.sd[0][0]), "t": float(t.tvalue[0][0]),
                         "p": float(t.pvalue), "t_HC1": float(th.tvalue[0][0])})
    out = pd.DataFrame(rows)
    out["N"] = int(fit.nobs)
    return out


def fmt(tab):
    """Coefficient (standard error) with stars, one column per model."""
    tab = tab.copy()
    stars = tab.p.map(lambda p: "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.1 else "")
    tab["cell"] = tab.coef.map("{:.3f}".format) + stars + " (" + tab.se.map("{:.3f}".format) + ")"
    wide = tab.pivot(index="term", columns="model", values="cell")
    order = [t for t in tab.term.drop_duplicates()]
    wide = wide.reindex(order)[list(dict.fromkeys(tab.model))]
    wide.loc["N (country-days)"] = tab.groupby("model").N.first()[wide.columns].astype(str)
    return wide.fillna("")


if __name__ == "__main__":
    panel = pd.read_csv(PROCESSED / "panel.csv", parse_dates=["date"])
    for o in ["loss", "win", "draw"]:
        panel[f"late_{o}"] = panel.late * panel[o]

    # Means by outcome and period (the numbers behind the regressions).
    panel["day_type"] = panel.outcome.fillna("no match")
    panel["period"] = panel.late.map({0: "2010-17", 1: "2018-26"})
    means = []
    for per, g in [("All 2010-26", panel)] + list(panel.groupby("period")):
        for typ, h in g.groupby("day_type"):
            means.append({"period": per, "day_type": typ, "N": len(h), "mean_ar": h.ar.mean(),
                          "t_vs_0": h.ar.mean() / (h.ar.std() / len(h) ** 0.5),
                          "share_ar_negative": (h.ar < 0).mean(), "mean_abs_ar": h.abs_ar.mean()})
    means = pd.DataFrame(means)

    results = []
    for dep, y in [("ar", "ar"), ("|ar|", "abs_ar")]:
        for name, late in SAMPLES.items():
            d = panel if late is None else panel[panel.late == late]
            f = f"{y} ~ loss + win + draw"
            results.append(summarise(smf.ols(f, d).fit(), smf.ols(f, d).fit(cov_type="HC1"), name, dep))
        f = f"{y} ~ loss + win + draw + late + late_loss + late_win + late_draw"
        results.append(summarise(smf.ols(f, panel).fit(), smf.ols(f, panel).fit(cov_type="HC1"),
                                 "Interaction", dep))
    results = pd.concat(results, ignore_index=True)

    TABLES.mkdir(parents=True, exist_ok=True)
    means.to_csv(TABLES / "means_by_outcome.csv", index=False)
    results.to_csv(TABLES / "regressions.csv", index=False)

    pd.set_option("display.width", 200)
    lines = ["Abnormal return (%) on the first trading day after the match, by outcome",
             means.round(3).to_string(index=False), "",
             "(A) Direction: abnormal return (%) on outcome dummies; baseline = days after no match",
             fmt(results[results.dep == "ar"]).to_string(), "",
             "(B) Size: absolute abnormal return (%) on outcome dummies",
             fmt(results[results.dep == "|ar|"]).to_string(), "",
             "OLS coefficients (standard errors); * p<0.10, ** p<0.05, *** p<0.01.",
             "Robust (HC1) t-statistics are in output/tables/regressions.csv."]
    text = "\n".join(lines)
    (TABLES / "regressions.txt").write_text(text + "\n")
    print(text)
