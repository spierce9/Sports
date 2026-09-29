# Do national football results still move stock markets?

Event study of the first trading day after World Cup, Euro, Copa América, Gold Cup and Asian
Cup matches for 12 countries, 2010–2026, split 2010–17 vs 2018–26.

## Pipeline

    pip install -r requirements.txt
    python run_all.py              # analysis from the committed raw data
    python run_all.py --download   # re-download the raw data first

Settings (sample, split date, drop first N days, countries, tournaments, qualifiers) are in
`config.py`.

| Script | Does |
|---|---|
| `01_download_matches.py` | International results and shootouts (GitHub martj42/international_results) |
| `02_download_prices.py` | Daily index closes (Yahoo Finance) and the world index (ACWI ETF) |
| `10_build_events.py` | One row per country-match: win/draw/loss (shootout decides), next trading day |
| `11_build_panel.py` | Country-day returns (100 × log change), world return and lag, match dummies |
| `20_market_model.py` | Betas on world (same day and lag) per country and period, on non-match days; abnormal returns |
| `30_regressions.py` | Abnormal and absolute abnormal return on loss/win/draw dummies; loss vs win tests; period interaction |

## Data

| Country | Team | Index (Yahoo ticker) | Notes |
|---|---|---|---|
| UK | England | FTSE 100 (^FTSE) | |
| Germany | Germany | DAX (^GDAXI) | total-return index |
| France | France | CAC 40 (^FCHI) | |
| Spain | Spain | IBEX 35 (^IBEX) | |
| Italy | Italy | FTSE MIB (FTSEMIB.MI) | |
| Netherlands | Netherlands | AEX (^AEX) | |
| Belgium | Belgium | BEL 20 (^BFX) | |
| Portugal | Portugal | PSI (PSI20.LS) | Yahoo history starts 30 Apr 2013 |
| Brazil | Brazil | Bovespa (^BVSP) | |
| Mexico | Mexico | IPC (^MXX) | |
| Japan | Japan | Nikkei 225 (^N225) | |
| South Korea | South Korea | KOSPI (^KS11) | |
| World | – | iShares MSCI ACWI ETF (ACWI) | USD, New York close |

## Caveats

- The results data give the match date (venue local time), not kick-off time. Each match is
  assigned to the first trading day strictly after the match date, as in Edmans, García and
  Norli (2007). Matches that finish during trading hours (e.g. Qatar 2022 afternoon games in
  Europe) or during the next Asian session (2026 World Cup evening games) are partly mistimed.
- Index returns are in local currency; the world index is in USD, so betas partly reflect FX.
- A match between two sample countries gives one event for each side.
