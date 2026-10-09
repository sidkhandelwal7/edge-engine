"""Odds conversions between American, decimal, and probability formats."""

from __future__ import annotations


def american_to_decimal(american: float) -> float:
    """Convert American odds (+175, -191) to decimal odds (2.75, 1.5236)."""
    if -100 < american < 100:
        raise ValueError(f"American odds must be <= -100 or >= +100, got {american}")
    if american > 0:
        return 1 + american / 100
    return 1 + 100 / abs(american)


def decimal_to_american(decimal: float) -> float:
    """Convert decimal odds to American odds (unrounded)."""
    if decimal <= 1:
        raise ValueError(f"Decimal odds must be greater than 1, got {decimal}")
    if decimal >= 2:
        return (decimal - 1) * 100
    return -100 / (decimal - 1)


def implied_prob(decimal: float) -> float:
    """Break-even probability for a price, including the book's vig."""
    if decimal <= 1:
        raise ValueError(f"Decimal odds must be greater than 1, got {decimal}")
    return 1 / decimal


def prob_to_decimal(p: float) -> float:
    """Fair decimal odds for a probability."""
    if not 0 < p < 1:
        raise ValueError(f"Probability must be strictly between 0 and 1, got {p}")
    return 1 / p


def prob_to_american(p: float) -> float:
    """Fair American odds for a probability (unrounded)."""
    if not 0 < p < 1:
        raise ValueError(f"Probability must be strictly between 0 and 1, got {p}")
    if p >= 0.5:
        return -100 * p / (1 - p)
    return 100 * (1 - p) / p


def parse_american(text: str | float | int) -> float:
    """Parse '+175', '-191', '175', 'EVEN' or a number into American odds."""
    if isinstance(text, (int, float)):
        return float(text)
    cleaned = text.strip().upper().replace(" ", "")
    if cleaned in {"EVEN", "EV", "EVS"}:
        return 100.0
    return float(cleaned)


def format_american(american: float) -> str:
    """Format American odds the way a sportsbook displays them."""
    rounded = round(american)
    return f"+{rounded}" if rounded > 0 else f"{rounded}"
