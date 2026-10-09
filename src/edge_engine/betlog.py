"""Read a bet log and summarize performance the way the framework grades it."""

from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LogSummary:
    bets: int
    cash_bets: int
    units_staked: float
    cash_units: float
    bonus_units: float
    roi: float
    avg_edge_pct: float | None
    grades: dict[str, int]


def _num(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def summarize(path: str | Path) -> LogSummary:
    """Summarize a log with columns stake_units, profit_units, edge_pct, process_grade, is_bonus."""
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    staked = cash = bonus = 0.0
    edges: list[float] = []
    grades: Counter[str] = Counter()
    cash_bets = 0
    for row in rows:
        profit = _num(row.get("profit_units", "")) or 0.0
        if row.get("is_bonus", "").strip().lower() in {"1", "true", "yes"}:
            bonus += profit
        else:
            cash_bets += 1
            staked += _num(row.get("stake_units", "")) or 0.0
            cash += profit
        e = _num(row.get("edge_pct", ""))
        if e is not None:
            edges.append(e)
        if row.get("process_grade"):
            grades[row["process_grade"]] += 1

    return LogSummary(
        bets=len(rows),
        cash_bets=cash_bets,
        units_staked=round(staked, 3),
        cash_units=round(cash, 3),
        bonus_units=round(bonus, 3),
        roi=round(cash / staked, 4) if staked else 0.0,
        avg_edge_pct=round(sum(edges) / len(edges), 2) if edges else None,
        grades=dict(sorted(grades.items())),
    )
