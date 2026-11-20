# Portfolio Optimization

A Python project that collects three years of daily prices for the top 50 S&P 500
stocks, computes daily returns, and estimates the expected return and covariance
matrix that a portfolio optimizer needs.

## Contents

- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Software architecture](#software-architecture)
- [Outputs](#outputs)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)

## Quick start

Tested with Python 3.12 and internet access (prices come from Yahoo Finance).

```bash
cd PortfolioOptimization

# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Collect prices and compute statistics
python main.py

# 4. Run the unit tests
python -m pytest -q
```

`python main.py` prints the parameters, a summary of the downloaded prices, the
expected daily return of each stock, and the covariance matrix size. It also
writes CSV files to `data/`.

## Configuration

All parameters live in `config.yaml`, which is loaded with
[OmegaConf](https://omegaconf.readthedocs.io/).

| Key | Symbol | Default | Meaning |
|-----|--------|---------|---------|
| `B` | B | `100000` | Total investment budget (USD) |
| `K` | K | `100` | Maximum number of shares that may be bought per stock |
| `R` | R | `0.0005` | Expected portfolio return, per day (0.0005 = 0.05%/day) |
| `data.years` | — | `3` | Years of history to collect, counted back from today |
| `data.ewm_span` | — | `60` | Span of the exponentially weighted mean (pandas `ewm` convention) |
| `tickers` | — | 50 symbols | Stocks to include |

To change the universe, edit the `tickers` list. Yahoo Finance symbols use a dash
for share classes (for example `BRK-B`).

## Software architecture

### Overview

The code is organised as a small data pipeline with three layers:

```
config.yaml ──► main.py (orchestration)
                  │
                  ├──► portfolio/prices.py   data acquisition and returns
                  │       collect_stock_prices()  ──► prices (dates × stocks)
                  │       get_daily_price()        ──► returns (dates × stocks)
                  │
                  └──► portfolio/stats.py    return and risk estimates
                          mean_stock_return()        ──► expected return per stock
                          covariance_stock_return()  ──► covariance matrix
                  │
                  └──► data/*.csv            persisted outputs
```

### Components

| Path | Role |
|------|------|
| `config.yaml` | Declares the budget `B`, share limit `K`, target return `R`, data settings, and tickers. |
| `main.py` | Entry point. Loads the config, runs the pipeline in order, prints a summary, and saves CSVs. |
| `portfolio/prices.py` | Downloads adjusted closing prices and converts them to daily returns. |
| `portfolio/stats.py` | Estimates expected returns and the covariance matrix from returns. |
| `portfolio/__init__.py` | Marks `portfolio` as a package. |
| `tests/test_stats.py` | Unit tests for the return formula, weighting, input shapes, and covariance. |
| `data/` | Output directory, created on first run. |
| `requirements.txt` | Runtime and test dependencies. |

### Data flow

1. **Load configuration.** `main.py` reads `config.yaml` with `OmegaConf.load`.
2. **Collect prices.** `collect_stock_prices(tickers, years)` computes the date
   window from today, downloads daily data with `yfinance` (`auto_adjust=True`, so
   prices include splits and dividends), forward-fills gaps, and drops rows that
   are still incomplete. The result is a DataFrame with a date index and one
   column per ticker.
3. **Compute daily returns.** `get_daily_price(prices)` returns
   `r_t = (P_t − P_{t−1}) / P_{t−1}` for each stock.
4. **Estimate expected returns.** `mean_stock_return(returns, span)` returns the
   exponentially weighted mean of each stock's returns. Recent days carry more
   weight.
5. **Estimate risk.** `covariance_stock_return(returns)` returns the sample
   covariance matrix (stocks × stocks).
6. **Persist and report.** `main.py` writes the intermediate results to `data/` and
   prints a summary.

### Input conventions

The statistics functions accept either:

- a **DataFrame** of shape *(days × stocks)*, indexed by date with ticker columns
  (preferred, and what the pipeline uses), or
- a **2D NumPy array** of shape *(stocks × days)*. It is transposed internally.

Both forms return the same results for the same data.

### Design notes

- **Separation of concerns.** Network access lives only in `prices.py`. `stats.py`
  is pure computation with no I/O, so it can be tested without internet access.
- **Configuration over code.** Budget, share limit, target return, and the
  universe are not hard-coded, so experiments do not require code changes.
- **Units are daily.** Returns, expected returns, and covariances are per day. `R`
  uses the same unit. To annualize, multiply the mean by 252 and the covariance
  by 252.
- **Fail loudly.** The collector raises an error on an empty download, and on any
  ticker with no usable data, instead of silently producing a smaller universe.

## Outputs

Running `main.py` writes these files to `data/`:

| File | Contents |
|------|----------|
| `prices.csv` | Adjusted closing prices (date × stock) |
| `daily_returns.csv` | Daily simple returns (date × stock) |
| `expected_returns.csv` | Exponentially weighted mean daily return per stock |
| `covariance.csv` | Covariance matrix of daily returns (stock × stock) |

These files are regenerated on every run and are ignored by git.

## Testing

```bash
python -m pytest -q
```

The tests use synthetic data, so they run offline. They cover:

- the daily return formula;
- the exponential weighting, including that recent observations dominate;
- correct handling of array input (stocks × days);
- covariance shape and symmetry.

## Troubleshooting

- **`yfinance returned no data`.** Check your internet connection and retry.
  Yahoo Finance sometimes rate-limits or fails transiently.
- **`database is locked`** (from yfinance's local cache). Wait a few seconds and
  run again. Only one process should download at a time.
- **`No usable price data for: [...]`.** The ticker is wrong or has no history
  for the window. Check the symbol on Yahoo Finance.
- **`ModuleNotFoundError`.** The virtual environment is not active, or
  `pip install -r requirements.txt` has not been run.

## Roadmap

- Portfolio optimizer that uses `B`, `K`, and `R` to choose share counts that
  minimize risk subject to the expected-return target.
- Annualized statistics output.
- Optional caching of downloaded prices to avoid repeated network calls.
