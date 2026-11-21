# Portfolio Optimization

A Python project that collects three years of daily prices for the top 50 S&P 500 stocks, computes daily returns, estimates the expected return and covariance matrix, and solves a portfolio optimization problem using mixed-integer quadratic programming with Gurobi.

## Table of Contents

- [Project Description](#project-description)
- [How to Run](#how-to-run)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Outputs](#outputs)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Project Description

This project implements an end-to-end portfolio optimization pipeline:

1. **Data Collection:** Downloads 3 years of adjusted closing prices for the top 50 S&P 500 stocks from Yahoo Finance.
2. **Return Estimation:** Computes daily returns and estimates annualized expected returns using exponentially weighted means.
3. **Risk Estimation:** Calculates the covariance matrix of stock returns to quantify portfolio risk.
4. **Portfolio Optimization:** Solves a constrained optimization problem using Gurobi to find the optimal portfolio allocation that:
   - Minimizes portfolio variance (risk)
   - Respects the budget constraint
   - Meets the target annual return requirement
5. **Greedy Optimization:** Provides an alternative solution using a greedy allocation algorithm for comparison.

The optimizer outputs portfolio allocations with share values and future expected returns for each stock in the optimal portfolio.

## How to Run

### Prerequisites

- Python 3.12+
- Internet access (prices are fetched from Yahoo Finance)
- Gurobi license (required for optimization; free academic licenses available)

### Setup and Execution

```bash
# 1. Navigate to the project directory
cd PortfolioOptimization

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Update configuration
# Edit config.yaml to adjust budget, target return, stock list, etc.

# 5. Run the main pipeline
python main.py

# 6. (Optional) Run unit tests
python -m pytest -v
```

**Output:** The script downloads historical prices, computes statistics, generates optimized and greedy portfolios, and saves all results to the `data/` directory.

## Project Structure

```
PortfolioOptimization/
├── README.md                           # This file
├── main.py                             # Entry point; orchestrates the full pipeline
├── config.yaml                         # Configuration parameters
├── requirements.txt                    # Python dependencies
├── optimizer.py                        # Gurobi-based portfolio optimizer (v0, v1 versions)
├── greedy.py                           # Greedy portfolio allocation algorithm
├── portfolio/                          # Core data processing package
│   ├── __init__.py                     # Package marker
│   ├── prices.py                       # Stock price data acquisition and returns computation
│   └── stats.py                        # Return and risk statistics estimation
├── tests/                              # Unit tests
│   └── test_stats.py                   # Tests for statistics functions
└── data/                               # Output directory (created on first run)
    ├── prices.csv                      # Historical adjusted closing prices
    ├── daily_returns.csv               # Daily simple returns
    ├── expected_returns.csv            # Annualized expected returns per stock
    ├── covariance.csv                  # Covariance matrix of returns
    ├── optimized_portfolio.csv         # Optimal portfolio allocation (Gurobi)
    └── greedy_portfolio.csv            # Greedy portfolio allocation
```

### Key Components

| File/Module | Purpose |
|---|---|
| **main.py** | Orchestrates the full pipeline: loads config, collects prices, computes statistics, optimizes portfolio, saves outputs. |
| **portfolio/prices.py** | Fetches historical prices via `yfinance`; computes daily percentage returns. |
| **portfolio/stats.py** | Calculates mean annualized returns and covariance matrix (supports weighted and normal methods). |
| **optimizer.py** | Solves the quadratic portfolio problem using Gurobi. `optimize_portfolio_v0` is the main version; returns a DataFrame with `share_value` and `future_return` columns. |
| **greedy.py** | Implements a greedy heuristic for portfolio allocation (for comparison). |
| **config.yaml** | Defines investment parameters (budget, target return, stock universe, etc.). |
| **tests/test_stats.py** | Unit tests for statistical functions (runs offline using synthetic data). |

### Data Flow

```
config.yaml ──► main.py ──┐
                          ├─► portfolio/prices.py    (collect_stock_prices, get_daily_returns)
                          ├─► portfolio/stats.py      (mean_annualized_return, covariance_annualized_return)
                          ├─► optimizer.py            (optimize_portfolio)
                          ├─► greedy.py               (greedy_portfolio)
                          └─► data/*.csv              (save results)
```

## Configuration

All parameters are defined in [config.yaml](/Users/tmittra/PortfolioOptimization/config.yaml). Key parameters:

| Parameter | Default | Meaning |
|---|---|---|
| `budget` | `300` | Total investment budget (USD) |
| `monitor_stocks` | `10` | Maximum number of stocks to monitor/hold |
| `yearly_return` | `12` | Target annual portfolio return (%) |
| `mx_share_price_percent` | `0.70` | Max budget fraction per single stock (70%) |
| `data.years` | `3` | Historical data window (years, counted back from today) |
| `data.ewm_span` | `252` | Span for exponentially weighted mean (1 trading year) |
| `model_type` | `"weighted"` | Return estimation: `"weighted"` (EWM) or `"normal"` (sample mean) |
| `tickers` | 50 symbols | S&P 500 constituents to analyze |

**To customize:** Edit `config.yaml` and re-run `python main.py`. No code changes needed.

## Outputs

Running `main.py` generates the following CSV files in `data/`:

| File | Rows × Columns | Contents |
|---|---|---|
| `prices.csv` | days × stocks | Adjusted closing prices for each stock over the historical window |
| `daily_returns.csv` | days × stocks | Daily percentage returns: (P_t - P_{t-1}) / P_{t-1} |
| `expected_returns.csv` | stocks × 1 | Annualized expected return per stock (from exponential weighting or sample mean) |
| `covariance.csv` | stocks × stocks | Annualized covariance matrix of returns |
| `optimized_portfolio.csv` | stocks × 2 | **Gurobi solution:** `share_value` (USD invested per stock), `future_return` (expected value after 1 year) |
| `greedy_portfolio.csv` | stocks × 2 | **Greedy solution:** same format as optimized portfolio |

All outputs are regenerated on each run and are ignored by git (see `.gitignore`).

## Testing

```bash
# Run all unit tests
python -m pytest -v

# Run only tests matching a pattern
python -m pytest tests/test_stats.py::test_daily_returns -v
```

**Test coverage:**

- Daily return formula correctness
- Exponential weighting bias toward recent observations
- Proper handling of DataFrame and NumPy array inputs
- Covariance matrix properties (shape, symmetry)
- Input validation and error handling

Tests use synthetic data and run entirely offline (no internet required).

## Troubleshooting

| Issue | Solution |
|---|---|
| `yfinance returned no data` | Check internet connection; Yahoo Finance may be rate-limiting. Retry after a few seconds. |
| `database is locked` | yfinance's local cache is locked by another process. Wait a few seconds and retry. Only run one instance at a time. |
| `No usable price data for: [ticker]` | The ticker symbol is incorrect or has insufficient history. Verify the symbol on Yahoo Finance. |
| `ModuleNotFoundError` | Virtual environment not activated, or `pip install -r requirements.txt` not run. |
| `Gurobi license error` | Gurobi is not licensed. Install a free academic license or obtain a commercial license. |
| `Model is infeasible` | The budget or constraints are too tight for the given stock universe. Increase the budget or lower the target return. |

## Future Enhancements

- Add portfolio performance backtesting
- Support for additional constraints (e.g., sector allocation, ESG filters)
- Annualized statistics output option
- Price data caching to reduce network calls
- Support for more optimization objectives (e.g., Sharpe ratio maximization)
