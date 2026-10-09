"""Parlay and same-game-parlay pricing, including correlated legs via a Gaussian copula."""

from __future__ import annotations

from collections.abc import Sequence
from math import prod
from statistics import NormalDist

import numpy as np


def independent_decimal(decimals: Sequence[float]) -> float:
    """Price of a parlay if the legs were independent: the product of leg decimals."""
    return float(prod(decimals))


def independent_prob(probs: Sequence[float]) -> float:
    return float(prod(probs))


def parlay_hold(fair_probs: Sequence[float], decimals: Sequence[float]) -> float:
    """Book margin baked into a parlay. Compounds with every leg added."""
    return 1 - float(prod(p * d for p, d in zip(fair_probs, decimals, strict=True)))


def implied_correlation_adjustment(leg_decimals: Sequence[float], displayed_decimal: float) -> float:
    """How much the book shortened (or lengthened) an SGP versus the independent product.

    A value of -0.30 means the displayed payout is 30% below the independent product,
    which is the book pricing in positive correlation between the legs.
    """
    return displayed_decimal / independent_decimal(leg_decimals) - 1


def copula_joint_prob(
    marginals: Sequence[float],
    corr: Sequence[Sequence[float]],
    n_sims: int = 1_000_000,
    seed: int | None = 7,
) -> float:
    """Probability that every leg hits, given each leg's marginal and a correlation matrix.

    Each leg i hits when its latent normal Z_i falls below Phi^-1(p_i). Correlating the
    latent normals correlates the outcomes while keeping every marginal exactly right.
    """
    marginals = np.asarray(marginals, dtype=float)
    corr = np.asarray(corr, dtype=float)
    n = len(marginals)
    if corr.shape != (n, n):
        raise ValueError("Correlation matrix must be n x n")
    if not np.allclose(corr, corr.T):
        raise ValueError("Correlation matrix must be symmetric")
    if np.min(np.linalg.eigvalsh(corr)) < -1e-10:
        raise ValueError("Correlation matrix must be positive semi-definite")
    cutoffs = np.array([NormalDist().inv_cdf(p) for p in marginals])
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal(np.zeros(n), corr, size=n_sims)
    return float(np.mean(np.all(z < cutoffs, axis=1)))


def sgp_ev(joint_prob: float, displayed_decimal: float, boost: float = 0.0) -> float:
    """EV per $1 of an SGP at the displayed price, optionally after a profit boost."""
    boosted = 1 + (displayed_decimal - 1) * (1 + boost)
    return joint_prob * boosted - 1
