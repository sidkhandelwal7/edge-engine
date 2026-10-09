"""edge-engine: pricing and risk tools for sports and prediction markets."""

from .analytics import clv, record_zscore, shrink, simulate_bankroll
from .devig import devig, devig_range
from .ev import edge, ev_per_dollar, evaluate, kelly_fraction
from .odds import american_to_decimal, decimal_to_american, prob_to_american
from .promos import bonus_bet_value, boost_ev, boosted_decimal, kalshi_taker_fee

__all__ = [
    "american_to_decimal",
    "boost_ev",
    "boosted_decimal",
    "bonus_bet_value",
    "clv",
    "decimal_to_american",
    "devig",
    "devig_range",
    "edge",
    "ev_per_dollar",
    "evaluate",
    "kalshi_taker_fee",
    "kelly_fraction",
    "prob_to_american",
    "record_zscore",
    "shrink",
    "simulate_bankroll",
]

__version__ = "0.1.0"
