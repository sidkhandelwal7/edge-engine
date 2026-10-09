"""Profit boosts, bonus bets, and prediction-market fees.

Promotions are where a retail sportsbook most often hands out positive expected value,
so they get their own math.
"""

from __future__ import annotations

from math import ceil


def boosted_decimal(decimal: float, boost: float) -> float:
    """A profit boost multiplies the winnings, not the stake: d' = 1 + (d - 1)(1 + b).

    boost=0.5 is a 50% profit boost, boost=1.0 is a 100% boost.
    """
    if boost < 0:
        raise ValueError("Boost must be non-negative")
    return 1 + (decimal - 1) * (1 + boost)


def boost_ev(p_fair: float, decimal: float, boost: float) -> float:
    """EV per $1 of a boosted bet, using the sharp fair probability."""
    return p_fair * boosted_decimal(decimal, boost) - 1


def bonus_bet_value(p_fair: float, decimal: float) -> float:
    """Expected cash per $1 of bonus-bet face value. The stake is not returned on a win."""
    return p_fair * (decimal - 1)


def best_bonus_target(candidates: dict[str, tuple[float, float]]) -> tuple[str, float]:
    """Pick the bonus-bet target with the highest expected conversion.

    candidates maps a label to (p_fair, decimal_odds).
    """
    scored = {label: bonus_bet_value(p, d) for label, (p, d) in candidates.items()}
    best = max(scored, key=scored.get)
    return best, scored[best]


def kalshi_taker_fee(contracts: int, price: float, rate: float = 0.07) -> float:
    """Kalshi-style taker fee in dollars: round_up(rate * C * P * (1 - P)) to the next cent."""
    if not 0 < price < 1:
        raise ValueError("Contract price must be between 0 and 1 dollars")
    raw = rate * contracts * price * (1 - price)
    return ceil(round(raw * 100, 9)) / 100


def kalshi_breakeven(contracts: int, price: float, rate: float = 0.07) -> float:
    """Probability needed to break even on a contract after fees."""
    return price + kalshi_taker_fee(contracts, price, rate) / contracts
