import pandas as pd 
import yfinance as yf
from omegaconf import DictConfig

def prepare_data(cfg: DictConfig):
        end_ts = pd.Timestamp.today()
        start_ts = end_ts - pd.DateOffset(years=cfg.data.years)
        raw = yf.download(
            list(cfg.tickers),
            start=start_ts.strftime("%Y-%m-%d"),
            end=end_ts.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
        )
        
        # Extract Close prices (yfinance returns multi-level columns)
        prices = raw["Close"]
        
        window = 252       # 1 year in trading days
        data_window = 42   
        window_start, window_end, max_stock_name, max_return_pct = [], [], [], []
        
        for ts in range(0, len(prices) - 2 * window, data_window):
            # Get prices at the start and end of the 6-month window
            price_start = prices.iloc[ts + window]
            price_end = prices.iloc[ts + 2 * window]
            
            # Calculate percentage return for each stock
            pct_returns = ((price_end - price_start) / price_start) * 100
            
            # Find stock with maximum percentage return
            max_stock = pct_returns.idxmax()
            max_return = pct_returns.max()
            
            window_start.append(prices.index[ts])
            window_end.append(prices.index[ts + window])
            max_stock_name.append(max_stock)
            max_return_pct.append(max_return)
            
        return pd.DataFrame({
            "window_start": window_start,
            "window_end": window_end,
            "max_stock_name": max_stock_name,
            "max_return_pct": max_return_pct
        })