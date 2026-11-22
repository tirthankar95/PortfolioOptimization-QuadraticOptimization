"""Collect 3 years of S&P 500 top-50 prices and estimate return statistics."""
import pandas as pd
from pathlib import Path
from omegaconf import OmegaConf, DictConfig
from greedy import greedy_portfolio
from optimizer import optimize_portfolio
from test_model import prepare_data
from portfolio.prices import collect_stock_prices, get_daily_returns
from portfolio.stats import covariance_annualized_return, mean_annualized_return

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"


def get_share_distributions(cfg: DictConfig, start_ts: pd.Timestamp, \
                            end_ts: pd.Timestamp, save_data = True):
    print(f"Budget B = {cfg.budget:,.2f}, expected return = {cfg.yearly_return}")

    prices = collect_stock_prices(list(cfg.tickers), start_ts, end_ts)
    returns = get_daily_returns(prices)
    mu = mean_annualized_return(returns, span=cfg.data.ewm_span, type=cfg.model_type)
    cov = covariance_annualized_return(prices, span=cfg.data.ewm_span, type=cfg.model_type)
    
    if save_data:
        DATA_DIR.mkdir(exist_ok=True)
        prices.to_csv(DATA_DIR / "prices.csv")
        mu.to_csv(DATA_DIR / "expected_returns.csv", header=["expected_return"])
        cov.to_csv(DATA_DIR / "covariance.csv")

    x = optimize_portfolio(cfg, prices.iloc[-1], mu, cov)
    if save_data:
        x.to_csv(DATA_DIR / "optimized_portfolio.csv")
        print(f"\nOptimized portfolio saved to {DATA_DIR / 'optimized_portfolio.csv'}")
    
    x_greed = greedy_portfolio(cfg, prices.iloc[-1], mu, cov)
    if save_data:
        x_greed.to_csv(DATA_DIR / "greedy_portfolio.csv")
        print(f"\nGreedy portfolio saved to {DATA_DIR / 'greedy_portfolio.csv'}")
    
    return x, x_greed


def main() -> None:
    cfg = OmegaConf.load(ROOT / "config.yaml")
    if not cfg.test:
        print("Running in normal mode.")
        today = pd.Timestamp.today()
        start_ts = today - pd.DateOffset(years=cfg.data.years)
        _, __ = get_share_distributions(cfg, start_ts, today)
    else:
        print("Test mode enabled.")
        df = prepare_data(cfg)
        weighted_x_return, weighted_x_greed_return = [], []
        normal_x_return, normal_x_greed_return = [], []
        
        # Test with both "weighted" and "normal" model types
        for _, row in df.iterrows():
            # Run with "weighted" model type
            cfg_weighted = OmegaConf.create(OmegaConf.to_container(cfg))
            cfg_weighted.model_type = "weighted"
            x_w, x_greed_w = get_share_distributions(cfg_weighted, pd.Timestamp(row["window_start"]), pd.Timestamp(row["window_end"]), save_data=False)
            weighted_x_return.append((x_w['future_return'].sum() - x_w['share_value'].sum()) * 100 / x_w['share_value'].sum())
            weighted_x_greed_return.append((x_greed_w['future_return'].sum() - x_greed_w['share_value'].sum()) * 100 / x_greed_w['share_value'].sum())
            
            # Run with "normal" model type
            cfg_normal = OmegaConf.create(OmegaConf.to_container(cfg))
            cfg_normal.model_type = "normal"
            x_n, x_greed_n = get_share_distributions(cfg_normal, pd.Timestamp(row["window_start"]), pd.Timestamp(row["window_end"]), save_data=False)
            normal_x_return.append((x_n['future_return'].sum() - x_n['share_value'].sum()) * 100 / x_n['share_value'].sum())
            normal_x_greed_return.append((x_greed_n['future_return'].sum() - x_greed_n['share_value'].sum()) * 100 / x_greed_n['share_value'].sum())
        
        # Add columns for both model types
        df['weighted_optimizer_return'] = weighted_x_return
        df['weighted_greedy_return'] = weighted_x_greed_return
        df['normal_optimizer_return'] = normal_x_return
        df['normal_greedy_return'] = normal_x_greed_return
        
        # Round all percentage columns to 2 decimal places
        df['max_return_pct'] = df['max_return_pct'].round(2)
        df['weighted_optimizer_return'] = df['weighted_optimizer_return'].round(2)
        df['weighted_greedy_return'] = df['weighted_greedy_return'].round(2)
        df['normal_optimizer_return'] = df['normal_optimizer_return'].round(2)
        df['normal_greedy_return'] = df['normal_greedy_return'].round(2)
        
        # Save to Excel instead of CSV
        DATA_DIR.mkdir(exist_ok=True)
        df.to_excel(DATA_DIR / "all_model_results.xlsx", index=False)
        print(f"Test results saved to {DATA_DIR / 'all_model_results.xlsx'}")
    

if __name__ == "__main__":
    main()
