import numpy as np
import pandas as pd
from omegaconf import OmegaConf

def greedy_portfolio(cfg: OmegaConf, pi, mu, cov) -> pd.DataFrame:
    pi = np.asarray(pi, dtype=float)
    mu = np.asarray(mu, dtype=float)
    cov = np.asarray(cov, dtype=float)
    n = pi.shape[0]
    labels = pi.index if isinstance(pi, pd.Series) else pd.RangeIndex(n)
    risk = np.diag(cov)
    if np.any(risk <= 0):
        raise ValueError("Covariance matrix diagonal must be strictly positive.")
    wt = np.maximum(0, mu / risk) 
    total = wt.sum()
    if total > 0: wt /= total 
    else: wt = np.full(n, 1.0 / n)
    share_values = wt * cfg.budget
    future_returns = share_values * (1 + mu)
    return pd.DataFrame({
        "share_value": share_values,
        "future_return": future_returns
    }, index=labels)