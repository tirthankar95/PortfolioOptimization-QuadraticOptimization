import gurobipy as gp
import numpy as np
import pandas as pd
from gurobipy import GRB
from omegaconf import OmegaConf


def optimize_portfolio(cfg: OmegaConf, pi, mu, cov) -> pd.Series:
    """Solve the mixed-integer quadratic portfolio problem with Gurobi.

    Decision variables
        x_i >= 0      number of shares bought of stock i (continuous)
        y_i in {0,1}  1 if stock i is held / monitored

    Formulation
        min   (x * pi)^T cov (x * pi)
        s.t.  sum_i pi_i x_i                 <= cfg.budget
              sum_i mu_i pi_i x_i            >= (1 + cfg.yearly_return / 100) * cfg.budget
              sum_i y_i                      <= cfg.monitor_stocks
              x_i <= cfg.total_shares_per_stock * y_i   for all i

    Parameters
    ----------
    cfg : OmegaConf config with budget, monitor_stocks, yearly_return (percent),
          total_shares_per_stock.
    pi  : latest price per stock (Series or array), order matching mu and cov.
    mu  : annualized expected return per stock as a decimal (0.12 = 12%).
    cov : annualized covariance matrix of returns (stocks x stocks).

    Returns
    -------
    pd.Series of optimal share counts x_i, indexed by stock.

    Raises
    ------
    ValueError if the model is infeasible or the input shapes do not match.
    """
    pi_v = np.asarray(pi, dtype=float)
    mu_v = np.asarray(mu, dtype=float)
    cov_m = np.asarray(cov, dtype=float)

    n = pi_v.shape[0]
    if mu_v.shape != (n,) or cov_m.shape != (n, n):
        raise ValueError(
            f"Shape mismatch: pi {pi_v.shape}, mu {mu_v.shape}, cov {cov_m.shape}"
        )
    labels = pi.index if isinstance(pi, pd.Series) else pd.RangeIndex(n)

    # (x * pi)^T cov (x * pi) = x^T Q x with Q_ij = pi_i * pi_j * cov_ij
    Q = np.outer(pi_v, pi_v) * cov_m

    model = gp.Model("portfolio")
    # Without this, Gurobi often reports infeasible models as INF_OR_UNBD (status 4).
    model.Params.DualReductions = 0

    x = model.addMVar(n, lb=0.0, name="x")
    y = model.addMVar(n, vtype=GRB.BINARY, name="y")

    model.setObjective(x @ Q @ x, GRB.MINIMIZE)

    model.addConstr(pi_v @ x <= cfg.budget, name="budget")
    model.addConstr(
        (mu_v * pi_v) @ x >= (1 + cfg.yearly_return / 100) * cfg.budget,
        name="target_return",
    )
    model.addConstr(y.sum() <= cfg.monitor_stocks, name="monitor_stocks")
    model.addConstr(x <= cfg.total_shares_per_stock * y, name="share_limit")

    model.optimize()

    if model.Status == GRB.INFEASIBLE:
        raise ValueError("No portfolio satisfies the constraints (model is infeasible)")
    if model.Status != GRB.OPTIMAL:
        raise RuntimeError(f"Gurobi did not reach optimality (status {model.Status})")

    return pd.Series(x.X, index=labels, name="shares")
