import numpy as np
import pandas as pd
from portfolio.prices import get_daily_returns
from portfolio.stats import covariance_annualized_return, mean_annualized_return
ONE_YEAR = 252

def test_daily_return_formula():
    prices = pd.DataFrame({"A": [100.0, 110.0, 99.0]})
    r = get_daily_returns(prices)
    np.testing.assert_allclose(r["A"].values, [0.10, -0.10])


def test_mean_constant_returns():
    df = pd.DataFrame({"A": [0.01] * 20, "B": [-0.02] * 20})
    mu = mean_annualized_return(df, span=5)
    np.testing.assert_allclose(mu.values, [0.01 * ONE_YEAR, -0.02 * ONE_YEAR])


def test_mean_weights_recent_more():
    df = pd.DataFrame({"A": [0.0] * 50 + [1.0] * 5})
    mu = mean_annualized_return(df, span=5)
    assert mu["A"] > 0.5 * ONE_YEAR  # EWM leans toward the recent 1.0s


def test_array_input_is_stocks_by_days():
    arr = np.array([[0.01, 0.02, 0.03],   # stock 0
                    [-0.01, 0.0, 0.01]])  # stock 1
    df = pd.DataFrame(arr.T)
    np.testing.assert_allclose(mean_annualized_return(arr, span=2).values,
                               mean_annualized_return(df, span=2).values)
    cov = covariance_annualized_return(arr)
    assert cov.shape == (2, 2)
    np.testing.assert_allclose(cov.values, np.cov(arr) * ONE_YEAR, rtol=1e-4)


def test_covariance_matrix_shape_and_symmetry():
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.normal(size=(100, 4)), columns=list("ABCD"))
    cov = covariance_annualized_return(df)
    assert cov.shape == (4, 4)
    np.testing.assert_allclose(cov.values, cov.values.T)
