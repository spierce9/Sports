# Do exploration booms predict commodity price falls?

High prices bring exploration, but new supply from existing producers (expansions, restarts,
Indonesian nickel) can arrive before most explorers reach production. Test: does faster growth in
Australian exploration spending predict weaker commodity prices?

## Pipeline

    pip install -r ../requirements.txt
    python run_all.py              # analysis from the committed raw data
    python run_all.py --download   # re-download first

Settings (sample years, forecast horizon, nominal/real, US$/A$ prices, excluded years, drop
first N years, commodities) are in `config.py`.

| Script | Does |
|---|---|
| `01_download_abs.py` | ABS 8412.0 Mineral and Petroleum Exploration (all time series); ABS CPI table 1 |
| `02_download_prices.py` | FRED: IMF monthly commodity prices, AUD/USD, US and Australian CPI; Yahoo: gold futures |
| `10_build_data.py` | Quarterly and financial-year panels of exploration spend and prices by commodity |
| `20_boom_predicts_bust.py` | Next-year price change on exploration growth and past price change; by commodity; 1-3 yr horizons |

## Data

| Commodity | Exploration (ABS 8412.0 Table 5, Australia) | Price |
|---|---|---|
| Nickel | Nickel, cobalt (from Sep qtr 1999) | FRED PNICKUSDM |
| Copper | Copper (from Sep qtr 1999) | FRED PCOPPUSDM |
| Zinc-lead | Silver, lead, zinc (from Sep qtr 1999) | FRED PZINCUSDM (zinc) |
| Iron ore | Iron ore | FRED PIORECRUSDM |
| Uranium | Uranium (some quarters suppressed) | FRED PURANUSDM |
| Coal | Coal | FRED PCOALAUUSDM (Australian thermal) |
| Gold | Gold | Yahoo GC=F (COMEX futures, from Aug 2000) |

FRED commodity prices are IMF primary commodity prices, monthly from Jan 1992. Lithium has no
separate ABS series (it sits in "Other") and no free price series, so it is not in the tests.

## Caveats

- ABS exploration by mineral is only published unadjusted; annual (July-June) sums remove seasonality.
- Annual prices are averages of monthly prices. Averaging creates some positive autocorrelation in
  annual changes (Working 1960), which is one reason the past price change is a control.
- With horizons above one year, only every H-th year is used so the forward windows do not overlap.
- The Australian CPI on FRED ends in early 2025; it is extended with the ABS monthly CPI.
