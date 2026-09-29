"""Headline: does an exploration boom predict a fall in the commodity price?

Financial-year panel, one row per commodity and year t:

  fwd_t = 100 x ln(P_{t+H} / P_t)       price change over the next H years (H = HORIZON_YEARS)
  gx_t  = 100 x ln(E_t / E_{t-1})       exploration spend growth over the past year
  gp_t  = 100 x ln(P_t / P_{t-1})       price change over the past year

  (1) fwd = a + b gx
  (2) fwd = a + b gx + c gp                        prices mean-revert and exploration follows
                                                   price, so b alone could be mean reversion
  (3) fwd = a + b gx + c gp + commodity dummies    compares years within each commodity
  and (2) for each commodity separately.
b < 0: faster exploration growth is followed by weaker prices. With H > 1 only every H-th year
is kept so the forward windows do not overlap. OLS standard errors; HC1 t saved as a check.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import (DROP_FIRST_N_YEARS, EXCLUDE_FY, HORIZON_YEARS, PRICE_CURRENCY,  # noqa: E402
                    PROCESSED, REAL, SAMPLE_END_FY, SAMPLE_START_FY, TABLES)


def build(ann, h=HORIZON_YEARS):
    e_col = "expl_real" if REAL else "expl"
    p_col = f"p_{PRICE_CURRENCY.lower()}" + ("_real" if REAL else "")
    out = []
    for c, g in ann.groupby("commodity"):
        g = g.set_index("fy").sort_index().reindex(range(ann.fy.min(), ann.fy.max() + 1))
        d = pd.DataFrame({"commodity": c,
                          "gx": 100 * np.log(g[e_col] / g[e_col].shift(1)),
                          "gp": 100 * np.log(g[p_col] / g[p_col].shift(1)),
                          "fwd": 100 * np.log(g[p_col].shift(-h) / g[p_col])})
        d = d.loc[SAMPLE_START_FY:SAMPLE_END_FY - h].dropna()
        # Drop years whose past or forward window touches an excluded year.
        bad = {y + k for y in EXCLUDE_FY for k in range(-h, 1)} | set(EXCLUDE_FY)
        d = d[~d.index.isin(bad)].iloc[DROP_FIRST_N_YEARS:]
        d = d[(d.index - d.index.min()) % h == 0]  # non-overlapping forward windows
        out.append(d.rename_axis("fy").reset_index())
    return pd.concat(out, ignore_index=True)


def coef_rows(fit, fit_hc, model, terms):
    return [{"model": model, "term": t, "coef": fit.params[t], "se": fit.bse[t], "t": fit.tvalues[t],
             "p": fit.pvalues[t], "t_HC1": fit_hc.tvalues[t], "N": int(fit.nobs), "r2": fit.rsquared}
            for t in terms]


if __name__ == "__main__":
    ann = pd.read_csv(PROCESSED / "annual.csv")
    d = build(ann)
    d.to_csv(PROCESSED / "headline_sample.csv", index=False)

    specs = {"(1) gx": "fwd ~ gx", "(2) gx + gp": "fwd ~ gx + gp",
             "(3) + commodity dummies": "fwd ~ gx + gp + C(commodity)"}
    rows = []
    for name, f in specs.items():
        terms = ["gx"] + (["gp"] if "gp" in f else [])
        rows += coef_rows(smf.ols(f, d).fit(), smf.ols(f, d).fit(cov_type="HC1"), name, terms)
    pooled = pd.DataFrame(rows)

    per = []
    for c, g in d.groupby("commodity"):
        fit = smf.ols("fwd ~ gx + gp", g).fit()
        per.append({"commodity": c, "years": f"{g.fy.min()}-{g.fy.max()}", "b_gx": fit.params["gx"],
                    "se": fit.bse["gx"], "t": fit.tvalues["gx"], "p": fit.pvalues["gx"],
                    "c_gp": fit.params["gp"], "N": int(fit.nobs)})
    per = pd.DataFrame(per)

    horizons = []
    for h in [1, 2, 3]:
        dh = build(ann, h)
        f = "fwd ~ gx + gp + C(commodity)"
        fit, fit_hc = smf.ols(f, dh).fit(), smf.ols(f, dh).fit(cov_type="HC1")
        horizons += coef_rows(fit, fit_hc, f"(3), next {h} yr", ["gx"])
    horizons = pd.DataFrame(horizons)

    TABLES.mkdir(parents=True, exist_ok=True)
    horizons.to_csv(TABLES / "headline_horizons.csv", index=False)
    pooled.to_csv(TABLES / "headline_pooled.csv", index=False)
    per.to_csv(TABLES / "headline_by_commodity.csv", index=False)

    b = pooled[(pooled.model == "(3) + commodity dummies") & (pooled.term == "gx")].coef.iloc[0]
    boom = 100 * np.log(1.5)  # a 50% rise in exploration spend, in log points
    text = "\n".join([
        f"Settings: horizon {HORIZON_YEARS} yr, {'real' if REAL else 'nominal'}, prices in {PRICE_CURRENCY}, "
        f"FY{SAMPLE_START_FY}-FY{SAMPLE_END_FY}, excluded {EXCLUDE_FY or 'none'}, drop first {DROP_FIRST_N_YEARS}",
        f"Correlation of exploration growth with the past year's price change: {d.gx.corr(d.gp):.2f}", "",
        "Pooled: next-year price change (%) on exploration growth (gx) and past price change (gp)",
        pooled.round(3).to_string(index=False), "",
        "By commodity, specification (2)",
        per.round(3).to_string(index=False), "",
        "Robustness: horizon of 1, 2 and 3 years (spec 3, non-overlapping windows)",
        horizons.round(3).to_string(index=False), "",
        f"Economic size, spec (3): a 50% rise in exploration spend ({boom:.1f} log points) goes with a "
        f"{b * boom:+.1f} log-point ({100 * (np.exp(b * boom / 100) - 1):+.1f}%) price change over the next "
        f"{HORIZON_YEARS} year(s).",
        "Log changes x 100. OLS standard errors; HC1 t in the CSV files."])
    (TABLES / "headline.txt").write_text(text + "\n")
    print(text)
