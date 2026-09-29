"""Market model and abnormal returns.

For each country and period (2010-17, 2018-26), estimated on days that are NOT the trading day
after a match:

    ret_t = a + b1 world_t + b2 world_t-1 + e_t

Abnormal return: ar_t = ret_t - (a + b1 world_t + b2 world_t-1), for every day in that period.
"""
import sys
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import PROCESSED, TABLES  # noqa: E402

if __name__ == "__main__":
    panel = pd.read_csv(PROCESSED / "panel.csv", parse_dates=["date"])
    panel["ar"] = float("nan")
    betas = []
    for (country, late), g in panel.groupby(["country", "late"]):
        fit = smf.ols("ret ~ world + world_lag", data=g[g.match_day == 0]).fit()
        panel.loc[g.index, "ar"] = g.ret - fit.predict(g)
        betas.append({"country": country, "period": "2018-26" if late else "2010-17",
                      "alpha": fit.params["Intercept"], "beta_world": fit.params["world"],
                      "se_world": fit.bse["world"], "beta_world_lag": fit.params["world_lag"],
                      "se_world_lag": fit.bse["world_lag"], "r2": fit.rsquared, "n_days": int(fit.nobs)})
    betas = pd.DataFrame(betas)
    panel["abs_ar"] = panel.ar.abs()
    panel.to_csv(PROCESSED / "panel.csv", index=False)
    TABLES.mkdir(parents=True, exist_ok=True)
    betas.to_csv(TABLES / "market_model_betas.csv", index=False)
    print(betas.round(3).to_string(index=False))
