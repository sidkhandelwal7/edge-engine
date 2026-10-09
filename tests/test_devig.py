import pytest

from edge_engine.devig import devig, devig_range, implied_from_american, overround


def test_multiplicative_sums_to_one():
    probs = devig([-110, -110])
    assert probs == pytest.approx([0.5, 0.5])


@pytest.mark.parametrize("method", ["multiplicative", "additive", "power", "shin"])
def test_every_method_sums_to_one(method):
    probs = devig([+167, -191], method)
    assert sum(probs) == pytest.approx(1.0, abs=1e-9)


def test_three_way_soccer_sums_to_one():
    for method in ("multiplicative", "power", "shin"):
        assert sum(devig([+350, -120, +260], method)) == pytest.approx(1.0, abs=1e-9)


def test_real_logged_market_hiroshima():
    # Pinnacle Hiroshima +167 / Hanshin -191, logged 2026-10-06.
    p = devig([+167, -191])[0]
    assert p == pytest.approx(0.3633, abs=5e-4)
    # The log applied a 0.982 no-tie factor for NPB to land at 0.357.
    assert p * 0.982 == pytest.approx(0.357, abs=1e-3)


def test_power_and_shin_shade_the_longshot():
    odds = [-400, +300]
    mult = devig(odds, "multiplicative")[1]
    assert devig(odds, "power")[1] < mult
    assert devig(odds, "shin")[1] < mult


def test_worst_case_is_most_conservative():
    r = devig_range([+270, -399], index=0)
    assert r["worst_case"] == r["min"]
    assert r["spread"] > 0


def test_overround():
    assert overround(implied_from_american([-110, -110])) == pytest.approx(1.0476, abs=1e-4)


def test_unknown_method():
    with pytest.raises(ValueError):
        devig([-110, -110], "magic")
