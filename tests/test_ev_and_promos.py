import pytest

from edge_engine.ev import dont_bet_past, edge, ev_per_dollar, evaluate, kelly_fraction, recommended_stake
from edge_engine.odds import american_to_decimal
from edge_engine.promos import (
    best_bonus_target,
    bonus_bet_value,
    boost_ev,
    boosted_decimal,
    kalshi_breakeven,
    kalshi_taker_fee,
)


def test_boost_formula_matches_book_display():
    # +175 with a 100% profit boost displayed as +350 on the slip.
    assert boosted_decimal(american_to_decimal(+175), 1.0) == pytest.approx(4.50)
    # +386 parlay with a 100% boost displayed as +772.
    assert boosted_decimal(american_to_decimal(+386), 1.0) == pytest.approx(8.72)


def test_logged_hiroshima_ev():
    assert boost_ev(0.357, american_to_decimal(+175), 1.0) == pytest.approx(0.6065, abs=1e-3)


def test_logged_rays_guardians_ev():
    assert boost_ev(0.1934, american_to_decimal(+386), 1.0) == pytest.approx(0.6864, abs=1e-3)


def test_bonus_bet_conversion_from_log():
    # Planned Tajikistan single: +350 at fair 0.2137 -> about 74.8% expected conversion.
    assert bonus_bet_value(0.2137, american_to_decimal(+350)) == pytest.approx(0.748, abs=1e-3)


def test_bonus_targets_prefer_plus_money():
    label, value = best_bonus_target({"fav": (0.75, 1.30), "dog": (0.30, 3.60)})
    assert label == "dog"
    assert value == pytest.approx(0.78)


def test_edge_and_ev_at_fair_price_are_zero():
    assert edge(0.5, 2.0) == pytest.approx(0)
    assert ev_per_dollar(0.5, 2.0) == pytest.approx(0)


def test_kelly():
    assert kelly_fraction(0.55, 2.0) == pytest.approx(0.10)
    assert kelly_fraction(0.45, 2.0) < 0


def test_stake_is_capped():
    assert recommended_stake(0.70, 2.0, bankroll=1000) == pytest.approx(20.0)


def test_negative_ev_stake_is_zero():
    assert recommended_stake(0.40, 2.0, bankroll=1000) == 0


def test_dont_bet_past():
    worst = dont_bet_past(0.55, 0.02)
    assert worst == pytest.approx(-112.77, abs=0.01)
    assert dont_bet_past(0.01, 0.02) is None


def test_evaluate_decisions():
    assert evaluate(0.55, american_to_decimal(+100)).decision == "BET"
    assert evaluate(0.53, american_to_decimal(-110), "main").decision == "LEAN (no bet)"
    assert evaluate(0.50, american_to_decimal(-110)).decision == "PASS"


def test_too_good_to_be_true_flag():
    v = evaluate(0.60, american_to_decimal(+150))
    assert v.flags and "TOO_GOOD" in v.flags[0]


def test_kalshi_fee():
    assert kalshi_taker_fee(1, 0.50) == pytest.approx(0.02)
    assert kalshi_taker_fee(100, 0.50) == pytest.approx(1.75)
    assert kalshi_breakeven(100, 0.50) == pytest.approx(0.5175)
