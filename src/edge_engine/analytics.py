"""Grading the process: closing line value, skill tests, shrinkage, and bankroll simulation."""

from __future__ import annotations

from collections.abc import Sequence
from math import sqrt

import numpy as np

from .odds import implied_prob


def clv(decimal_at_bet: float, p_close_fair: float) -> float:
    """Closing line value: how much the sharp closing fair probability beat your price.

    CLV = p_close_fair / implied(price you got) - 1. Positive average CLV over a few
    hundred bets is the fastest honest signal of real skill, far faster than win rate.
    """
    return p_close_fair / implied_prob(decimal_at_bet) - 1


def record_zscore(wins: int, n: int, breakeven: float) -> float:
    """z-score of a win/loss record against the break-even rate."""
    if n <= 0:
        raise ValueError("Need at least one bet")
    return (wins - n * breakeven) / sqrt(n * breakeven * (1 - breakeven))


def roi_tstat(profits_per_unit: Sequence[float]) -> float:
    """t-statistic of mean profit per bet. Needs many bets before it means anything."""
    x = np.asarray(profits_per_unit, dtype=float)
    if len(x) < 2:
        raise ValueError("Need at least two bets")
    sd = x.std(ddof=1)
    return float("inf") if sd == 0 else float(x.mean() / (sd / sqrt(len(x))))


def shrink(observed: float, n: float, prior: float, k: float) -> float:
    """Bayesian shrinkage toward a prior with stabilization sample k.

    A 3-point percentage over 40 attempts barely moves off the league prior; a strikeout
    rate over 200 batters moves a lot. k encodes how fast each stat becomes signal.
    """
    return (n * observed + k * prior) / (n + k)


def simulate_bankroll(
    p_win: float,
    decimal: float,
    stake_fraction: float,
    n_bets: int,
    n_sims: int = 100_000,
    start: float = 1.0,
    seed: int | None = 11,
) -> dict[str, float]:
    """Monte Carlo of a bankroll making the same bet repeatedly at a fixed fraction.

    Returns the median ending bankroll, the 5th and 95th percentiles, the probability of
    finishing down, and the median maximum drawdown.
    """
    rng = np.random.default_rng(seed)
    wins = rng.random((n_sims, n_bets)) < p_win
    growth = np.where(wins, 1 + stake_fraction * (decimal - 1), 1 - stake_fraction)
    paths = start * np.cumprod(growth, axis=1)
    running_peak = np.maximum.accumulate(np.concatenate([np.full((n_sims, 1), start), paths], axis=1), axis=1)[:, 1:]
    drawdowns = 1 - paths / running_peak
    final = paths[:, -1]
    return {
        "median_final": float(np.median(final)),
        "p05_final": float(np.percentile(final, 5)),
        "p95_final": float(np.percentile(final, 95)),
        "p_loss": float(np.mean(final < start)),
        "median_max_drawdown": float(np.median(drawdowns.max(axis=1))),
    }
