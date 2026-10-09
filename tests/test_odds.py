import pytest

from edge_engine.odds import (
    american_to_decimal,
    decimal_to_american,
    format_american,
    parse_american,
    prob_to_american,
)


@pytest.mark.parametrize(
    "american, decimal",
    [(+175, 2.75), (-110, 1.909090909), (+100, 2.0), (-200, 1.5), (+386, 4.86)],
)
def test_american_to_decimal(american, decimal):
    assert american_to_decimal(american) == pytest.approx(decimal)


@pytest.mark.parametrize("american", [+175, -110, +100, -191, +772])
def test_round_trip(american):
    assert decimal_to_american(american_to_decimal(american)) == pytest.approx(american)


def test_breakevens_from_spec():
    assert 1 / american_to_decimal(-110) == pytest.approx(0.5238, abs=1e-4)
    assert 1 / american_to_decimal(-120) == pytest.approx(0.5455, abs=1e-4)
    assert 1 / american_to_decimal(-150) == pytest.approx(0.6000, abs=1e-4)


def test_prob_to_american():
    assert prob_to_american(0.5) == pytest.approx(-100)
    assert prob_to_american(0.25) == pytest.approx(300)
    assert prob_to_american(0.75) == pytest.approx(-300)


def test_invalid_american():
    with pytest.raises(ValueError):
        american_to_decimal(50)


def test_parse_and_format():
    assert parse_american("+175") == 175
    assert parse_american("EVEN") == 100
    assert format_american(771.6) == "+772"
    assert format_american(-191.2) == "-191"
