import numpy as np
import pandas as pd

from portfolio.prices import get_daily_price
from portfolio.stats import covariance_stock_return, mean_stock_return


def test_daily_return_formula():
    prices = pd.DataFrame({"A": [100.0, 110.0, 99.0]})
    r = get_daily_price(prices)
    np.testing.assert_allclose(r["A"].values, [0.10, -0.10])


def test_mean_constant_returns():
    df = pd.DataFrame({"A": [0.01] * 20, "B": [-0.02] * 20})
    mu = mean_stock_return(df, span=5)
    np.testing.assert_allclose(mu.values, [0.01, -0.02])


def test_mean_weights_recent_more():
    df = pd.DataFrame({"A": [0.0] * 50 + [1.0] * 5})
    mu = mean_stock_return(df, span=5)
    assert mu["A"] > 0.5  # EWM leans toward the recent 1.0s


def test_array_input_is_stocks_by_days():
    arr = np.array([[0.01, 0.02, 0.03],   # stock 0
                    [-0.01, 0.0, 0.01]])  # stock 1
    df = pd.DataFrame(arr.T)
    np.testing.assert_allclose(mean_stock_return(arr, span=2).values,
                               mean_stock_return(df, span=2).values)
    cov = covariance_stock_return(arr)
    assert cov.shape == (2, 2)
    np.testing.assert_allclose(cov.values, np.cov(arr))


def test_covariance_matrix_shape_and_symmetry():
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.normal(size=(100, 4)), columns=list("ABCD"))
    cov = covariance_stock_return(df)
    assert cov.shape == (4, 4)
    np.testing.assert_allclose(cov.values, cov.values.T)
