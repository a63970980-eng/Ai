import numpy as np

from forex_robot.research.validation import monte_carlo_bootstrap, walk_forward_windows


def test_walk_forward_windows_are_non_overlapping():
    windows = walk_forward_windows(100, 60, 20)
    assert windows[0].train_end == windows[0].test_start
    assert windows[0].test_end <= 100


def test_monte_carlo_is_deterministic():
    a = monte_carlo_bootstrap([0.01, -0.005, 0.002], simulations=100, seed=7)
    b = monte_carlo_bootstrap([0.01, -0.005, 0.002], simulations=100, seed=7)
    assert a == b
    assert np.isfinite(a.mean_total_return)
