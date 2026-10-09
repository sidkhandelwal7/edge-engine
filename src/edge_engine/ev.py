"""Edge, expected value, Kelly sizing, thresholds and the "don't bet past" price."""

from __future__ import annotations

from dataclasses import dataclass

from .odds import decimal_to_american, implied_prob

# Minimum edge (fair probability minus break-even probability) required per market type.
# Softer, noisier markets demand a bigger cushion because the fair estimate is less certain.
THRESHOLDS: dict[str, float] = {
    "main": 0.020,  # NFL/NBA/MLB/NHL sides and totals
    "college": 0.025,  # CFB/CBB sides and totals
    "prop": 0.035,  # player props
    "alt": 0.040,  # alternate lines and ladders
    "future": 0.050,  # futures and outrights
    "live": 0.040,  # in-play, only with a stated thesis
}

TOO_GOOD_TO_BE_TRUE = 0.05


def edge(p_fair: float, decimal: float) -> float:
    """Fair probability minus the break-even probability of the price you are getting."""
    return p_fair - implied_prob(decimal)


def ev_per_dollar(p_fair: float, decimal: float) -> float:
    """Expected profit per $1 staked when the stake is returned on a win."""
    return p_fair * decimal - 1


def kelly_fraction(p_fair: float, decimal: float) -> float:
    """Full Kelly fraction of bankroll. Negative means the bet is -EV."""
    b = decimal - 1
    return (b * p_fair - (1 - p_fair)) / b


def recommended_stake(
    p_fair: float,
    decimal: float,
    bankroll: float,
    kelly_multiplier: float = 0.25,
    cap: float = 0.02,
) -> float:
    """Fractional Kelly stake in dollars, never above cap * bankroll, never negative."""
    f = max(0.0, kelly_fraction(p_fair, decimal)) * kelly_multiplier
    return round(min(f, cap) * bankroll, 2)


def dont_bet_past(p_fair: float, threshold: float) -> float | None:
    """Worst American price at which the edge still meets the threshold.

    Solves p_fair - 1/d >= threshold for d. Returns None if no price works.
    """
    required_breakeven = p_fair - threshold
    if required_breakeven <= 0:
        return None
    return decimal_to_american(1 / required_breakeven)


@dataclass
class Verdict:
    p_fair: float
    breakeven: float
    edge: float
    ev_per_100: float
    kelly_full: float
    stake: float
    threshold: float
    decision: str
    dont_bet_past: float | None
    flags: list[str]


def evaluate(
    p_fair: float,
    decimal: float,
    market_type: str = "main",
    bankroll: float = 100.0,
    kelly_multiplier: float = 0.25,
    cap: float = 0.02,
) -> Verdict:
    """Run one candidate bet through the full decision rule: BET, LEAN, or PASS."""
    if market_type not in THRESHOLDS:
        raise ValueError(f"Unknown market type {market_type!r}; choose from {list(THRESHOLDS)}")
    threshold = THRESHOLDS[market_type]
    e = edge(p_fair, decimal)
    flags: list[str] = []
    if e > TOO_GOOD_TO_BE_TRUE:
        flags.append("TOO_GOOD_TO_BE_TRUE: re-check injuries, lineups, weather and palpable-error risk")
    if e >= threshold:
        decision = "BET"
    elif e > 0:
        decision = "LEAN (no bet)"
    else:
        decision = "PASS"
    return Verdict(
        p_fair=p_fair,
        breakeven=implied_prob(decimal),
        edge=e,
        ev_per_100=100 * ev_per_dollar(p_fair, decimal),
        kelly_full=kelly_fraction(p_fair, decimal),
        stake=recommended_stake(p_fair, decimal, bankroll, kelly_multiplier, cap) if decision == "BET" else 0.0,
        threshold=threshold,
        decision=decision,
        dont_bet_past=dont_bet_past(p_fair, threshold),
        flags=flags,
    )
