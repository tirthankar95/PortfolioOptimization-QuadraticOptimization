"""Collect 3 years of S&P 500 top-50 prices and estimate return statistics."""

from pathlib import Path
from omegaconf import OmegaConf
from optimizer import optimize_portfolio
from portfolio.prices import collect_stock_prices, get_daily_returns
from portfolio.stats import covariance_annualized_return, mean_annualized_return

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def main() -> None:
    cfg = OmegaConf.load(ROOT / "config.yaml")
    print(f"Budget B = {cfg.budget:,.2f}, max shares = {cfg.total_shares_per_stock}, expected return = {cfg.yearly_return}")

    prices = collect_stock_prices(list(cfg.tickers), years=cfg.data.years)
    returns = get_daily_returns(prices)
    print(f"Prices: {prices.shape[0]} days x {prices.shape[1]} stocks "
        f"({prices.index[0].date()} to {prices.index[-1].date()})")

    mu = mean_annualized_return(returns, span=cfg.data.ewm_span, type=cfg.model_type)
    cov = covariance_annualized_return(returns, span=cfg.data.ewm_span, type=cfg.model_type)

    DATA_DIR.mkdir(exist_ok=True)
    prices.to_csv(DATA_DIR / "prices.csv")
    returns.to_csv(DATA_DIR / "daily_returns.csv")
    
    mu.to_csv(DATA_DIR / "expected_returns.csv", header=["expected_return"])
    cov.to_csv(DATA_DIR / "covariance.csv")

    print("\nExpected daily return:")
    print(mu.round(6).to_string())
    print(f"\nCovariance matrix: {cov.shape}")
    print(f"\nSaved outputs to {DATA_DIR}")

    x = optimize_portfolio(cfg, prices.iloc[-1], mu, cov)
    print(f"\nOptimized portfolio: {x}")


if __name__ == "__main__":
    main()
