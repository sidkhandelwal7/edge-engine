from pathlib import Path

import numpy as np
import pytest

from edge_engine.analytics import clv, record_zscore, roi_tstat, shrink, simulate_bankroll
from edge_engine.betlog import summarize
from edge_engine.odds import american_to_decimal
from edge_engine.parlay import (
    copula_joint_prob,
    implied_correlation_adjustment,
    independent_decimal,
    parlay_hold,
)

ROOT = Path(__file__).resolve().parents[1]


def test_independent_parlay():
    assert independent_decimal([2.0, 2.0, 2.0]) == pytest.approx(8.0)


def test_parlay_hold_compounds():
    one = parlay_hold([0.5], [1.909])
    three = parlay_hold([0.5] * 3, [1.909] * 3)
    assert three > one > 0


def test_copula_zero_correlation_matches_product():
    p = copula_joint_prob([0.5, 0.4], np.eye(2), n_sims=400_000)
    assert p == pytest.approx(0.20, abs=0.004)


def test_positive_correlation_raises_joint_prob():
    corr = [[1, 0.5], [0.5, 1]]
    assert copula_joint_prob([0.5, 0.4], corr, n_sims=400_000) > 0.22


def test_copula_rejects_bad_matrix():
    with pytest.raises(ValueError):
        copula_joint_prob([0.5, 0.5], [[1, 2], [2, 1]])


def test_sgp_adjustment_sign():
    assert implied_correlation_adjustment([2.0, 2.0], 3.2) == pytest.approx(-0.2)


def test_clv_from_logged_bet():
    # MIL@SD Under 6.5 taken at +143 pre-boost; Pinnacle closing fair 0.4199.
    assert clv(american_to_decimal(+143), 0.4199) == pytest.approx(0.0204, abs=5e-4)


def test_record_zscore():
    assert record_zscore(55, 100, 0.5238) == pytest.approx(0.52, abs=0.01)


def test_roi_tstat():
    assert roi_tstat([1, -1, 1, -1]) == pytest.approx(0)


def test_shrink():
    assert shrink(0.45, 40, 0.36, 750) == pytest.approx(0.3646, abs=1e-4)


def test_simulation_positive_edge_grows():
    out = simulate_bankroll(0.55, 2.0, 0.025, 1000, n_sims=5000)
    assert out["median_final"] > 1
    assert 0 < out["median_max_drawdown"] < 1


def test_sample_log_summary():
    s = summarize(ROOT / "examples" / "sample_log.csv")
    assert s.bets == 12
    assert s.cash_bets == 11
    assert s.bonus_units == pytest.approx(13.13)
    assert s.units_staked == pytest.approx(19.5)
    assert s.cash_units == pytest.approx(4.49, abs=1e-3)
