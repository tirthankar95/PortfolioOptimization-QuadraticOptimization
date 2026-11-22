"""Expected return and covariance estimates from daily returns.

Both functions accept either:
  * a DataFrame of shape (m days x n stocks), indexed by date with ticker columns
    (preferred), or
  * a 2D array of shape (n stocks x m days).
"""
import numpy as np
import pandas as pd

ONE_YEAR = 252

def _as_returns_frame(returns: pd.DataFrame | np.ndarray) -> pd.DataFrame:
    """Normalise input to a DataFrame of shape (days x stocks)."""
    if isinstance(returns, pd.DataFrame):
        return returns
    arr = np.asarray(returns, dtype=float)
    if arr.ndim != 2:
        raise ValueError(f"Expected a 2D array, got {arr.ndim}D")
    # Array layout is n stocks x m days -> transpose to days x stocks.
    return pd.DataFrame(arr.T)


def mean_annualized_return(
    returns: pd.DataFrame | np.ndarray,
    span: int = 126, # 6 months
    type: str = "weighted"
) -> pd.Series:
    """Expected annualized return per stock as an exponentially weighted (rolling) average.

    More recent days get more weight. ``span`` controls the decay
    (pandas ``ewm`` convention: alpha = 2 / (span + 1)).
    Returns a Series indexed by stock (ticker or integer position).
    """
    if type == "weighted":
        df = _as_returns_frame(returns)
        return df.ewm(span=span, adjust=True).mean().iloc[-1] * ONE_YEAR
    elif type == "normal":
        df = _as_returns_frame(returns)
        return df.mean() * ONE_YEAR


def covariance_annualized_return(returns: pd.DataFrame | np.ndarray, span: int = 126,
                                type: str = "weighted") -> pd.DataFrame:
    """Sample annualized covariance matrix of daily returns, shape (n stocks x n stocks)."""
    df = _as_returns_frame(returns)
    if type == "weighted":
        weighted_returns = df.ewm(span=span, adjust=True)
        weighted_cov = weighted_returns.cov()
        return weighted_cov.loc[df.index[-1]] * ONE_YEAR
    elif type == "normal":
        return df.cov() * ONE_YEAR
