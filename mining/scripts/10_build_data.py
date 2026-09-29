"""Quarterly and annual (financial-year) panels: exploration spend and prices by commodity.

Exploration: ABS 8412.0 Table 5, Australia, "Total deposits", A$ million, original (the ABS does
not publish seasonally adjusted series by mineral). Annual = sum of the four quarters of the
financial year (July-June); a year with a missing (suppressed) quarter is left missing.
Prices: quarterly and annual averages of monthly prices. A$ price = US$ price / (US$ per A$).
CPI: US CPI (monthly) for US$ prices; Australian CPI for A$ amounts. The FRED/OECD Australian
series ends in early 2025, so it is extended with the ABS monthly CPI, rescaled to match over
the quarters where both exist.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import COMMODITIES, PROCESSED, RAW  # noqa: E402


def read_abs(path):
    """ABS time-series workbook -> DataFrame (date index, one column per series)."""
    raw = pd.read_excel(path, sheet_name="Data1", header=None)
    df = raw.iloc[10:].set_index(0)
    df.columns = [" ".join(str(c).split()) for c in raw.iloc[0, 1:]]
    df.index = pd.to_datetime(df.index)
    return df.apply(pd.to_numeric, errors="coerce")


def fred(name):
    df = pd.read_csv(RAW / "prices" / f"{name}.csv")
    return pd.Series(df.iloc[:, 1].values, index=pd.to_datetime(df.iloc[:, 0]), name=name).astype(float)


def quarterly(monthly):
    return monthly.groupby(monthly.index.to_period("Q")).mean()


def fy(q):
    """Financial year (ending June) of a quarterly PeriodIndex."""
    return q.year + (q.quarter >= 3)


if __name__ == "__main__":
    t5 = read_abs(RAW / "abs" / "8412" / "8412005.xlsx")
    t5.index = t5.index.to_period("Q")

    usd_per_aud = quarterly(fred("EXUSAL"))
    us_cpi = quarterly(fred("CPIAUCSL"))
    au_oecd = fred("AUSCPIALLQINMEI")
    au_oecd.index = au_oecd.index.to_period("Q")
    au_abs = quarterly(read_abs(RAW / "abs" / "640101.xlsx")["Index Numbers ; All groups CPI ; Australia ;"].dropna())
    overlap = au_oecd.index.intersection(au_abs.index)
    au_cpi = pd.concat([au_oecd, au_abs[au_abs.index > au_oecd.index.max()] * (au_oecd[overlap] / au_abs[overlap]).mean()])

    rows = []
    for name, (mineral, src, series) in COMMODITIES.items():
        expl = t5[f"Expenditure ; Australia ; {mineral} ; Total deposits ;"]
        if src == "fred":
            p = fred(series)
        else:
            g = pd.read_csv(RAW / "prices" / f"{series.replace('=', '_')}.csv", parse_dates=["date"])
            p = g.set_index("date").close
        p = quarterly(p)
        q = pd.DataFrame({"expl": expl, "p_usd": p}).dropna(how="all")
        q["p_aud"] = q.p_usd / usd_per_aud.reindex(q.index)
        q["expl_real"] = q.expl / au_cpi.reindex(q.index) * au_cpi.iloc[-1]
        q["p_usd_real"] = q.p_usd / us_cpi.reindex(q.index) * us_cpi.iloc[-1]
        q["p_aud_real"] = q.p_aud / au_cpi.reindex(q.index) * au_cpi.iloc[-1]
        q["commodity"] = name
        q["quarter"] = q.index.astype(str)
        q["fy"] = fy(q.index)
        rows.append(q.reset_index(drop=True))
    qp = pd.concat(rows, ignore_index=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    qp.to_csv(PROCESSED / "quarterly.csv", index=False)

    value_cols = ["expl", "expl_real", "p_usd", "p_aud", "p_usd_real", "p_aud_real"]
    g = qp.groupby(["commodity", "fy"])[value_cols]
    ann = pd.concat([g.sum()[["expl", "expl_real"]], g.mean()[value_cols[2:]]], axis=1)
    ann = ann.where(g.count() == 4).reset_index()  # every value needs all four quarters
    ann.to_csv(PROCESSED / "annual.csv", index=False)

    cover = ann.dropna(subset=["expl", "p_usd"]).groupby("commodity").fy.agg(["min", "max", "count"])
    print("  Annual (financial years) with both exploration and price:")
    print(cover.to_string())
    print(f"  Australian CPI spliced at {au_oecd.index.max()} (ABS monthly from {au_abs.index.min()})")
