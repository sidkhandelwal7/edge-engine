"""Remove the bookmaker's margin (vig) from a market to estimate fair probabilities.

Every method takes the raw implied probabilities q_i = 1 / decimal_i of every
outcome in the market. Their sum (the overround) is above 1 because of the vig.
Each method makes a different assumption about how the book spread that margin.
"""

from __future__ import annotations

from collections.abc import Sequence
from math import sqrt

from .odds import american_to_decimal, implied_prob

METHODS = ("multiplicative", "additive", "power", "shin")


def implied_from_american(odds: Sequence[float]) -> list[float]:
    return [implied_prob(american_to_decimal(a)) for a in odds]


def overround(q: Sequence[float]) -> float:
    """Sum of implied probabilities. 1.045 means a 4.5% book margin."""
    return float(sum(q))


def multiplicative(q: Sequence[float]) -> list[float]:
    """Scale every outcome by the same factor. Good default for near-even two-way markets."""
    total = overround(q)
    return [qi / total for qi in q]


def additive(q: Sequence[float]) -> list[float]:
    """Subtract an equal share of the margin from each outcome. Breaks on longshots."""
    n = len(q)
    excess = (overround(q) - 1) / n
    probs = [qi - excess for qi in q]
    if any(p <= 0 for p in probs):
        raise ValueError("Additive de-vig produced a non-positive probability; use power or shin.")
    return probs


def power(q: Sequence[float], tol: float = 1e-12) -> list[float]:
    """Solve sum(q_i ** k) = 1. Puts more margin on longshots (favorite-longshot bias)."""
    total = overround(q)
    if abs(total - 1) < tol:
        return list(q)

    def excess(k: float) -> float:
        return sum(qi**k for qi in q) - 1

    if total > 1:
        lo, hi = 1.0, 2.0
        while excess(hi) > 0:
            hi *= 2
    else:
        lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if excess(mid) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    k = (lo + hi) / 2
    return [qi**k for qi in q]


def shin(q: Sequence[float], tol: float = 1e-12) -> list[float]:
    """Shin (1993) model: margin comes from protecting against a share z of insiders.

    Best suited to multi-way outrights (golf, futures) with a big favorite-longshot bias.
    """
    total = overround(q)
    if total <= 1:
        return multiplicative(q)

    def probs(z: float) -> list[float]:
        return [(sqrt(z * z + 4 * (1 - z) * qi * qi / total) - z) / (2 * (1 - z)) for qi in q]

    lo, hi = 0.0, 0.999
    for _ in range(200):
        mid = (lo + hi) / 2
        if sum(probs(mid)) > 1:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return probs((lo + hi) / 2)


def worst_case(q: Sequence[float], index: int) -> float:
    """Assign the entire margin to the side you are betting. The most conservative estimate."""
    return q[index] - (overround(q) - 1)


def devig(odds_american: Sequence[float], method: str = "multiplicative") -> list[float]:
    """De-vig a full market quoted in American odds."""
    q = implied_from_american(odds_american)
    if method == "multiplicative":
        return multiplicative(q)
    if method == "additive":
        return additive(q)
    if method == "power":
        return power(q)
    if method == "shin":
        return shin(q)
    raise ValueError(f"Unknown method {method!r}; choose from {METHODS}")


def devig_range(odds_american: Sequence[float], index: int) -> dict[str, float]:
    """Fair probability of one outcome under every method, plus the spread between them.

    The framework rule: if methods disagree by more than 1.5 points, report the range
    and size the bet off the most conservative number.
    """
    q = implied_from_american(odds_american)
    out: dict[str, float] = {
        "multiplicative": multiplicative(q)[index],
        "power": power(q)[index],
        "shin": shin(q)[index],
        "worst_case": worst_case(q, index),
    }
    try:
        out["additive"] = additive(q)[index]
    except ValueError:
        pass
    values = list(out.values())
    out["min"] = min(values)
    out["max"] = max(values)
    out["spread"] = out["max"] - out["min"]
    return out
