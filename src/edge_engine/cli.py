"""Command line interface: price a bet in one line from your phone's terminal or laptop."""

from __future__ import annotations

import argparse
import sys

from .analytics import clv, simulate_bankroll
from .betlog import summarize
from .devig import devig_range
from .ev import THRESHOLDS, evaluate
from .odds import american_to_decimal, decimal_to_american, format_american, parse_american, prob_to_american
from .promos import bonus_bet_value, boosted_decimal, kalshi_breakeven


def _pct(x: float) -> str:
    return f"{100 * x:.2f}%"


def cmd_price(args: argparse.Namespace) -> None:
    sharp = [parse_american(s) for s in args.sharp]
    fair = devig_range(sharp, args.side)
    p = fair["min"] if args.conservative else fair[args.method]
    if args.tie_factor:
        p *= args.tie_factor
    mine = american_to_decimal(parse_american(args.mine))
    if args.boost:
        mine = boosted_decimal(mine, args.boost)
    v = evaluate(p, mine, args.market, args.bankroll, args.kelly, args.cap)

    print(f"Sharp market     {' / '.join(args.sharp)}  (side {args.side})")
    for name in ("multiplicative", "power", "shin", "additive", "worst_case"):
        if name in fair:
            print(f"  {name:<15}{_pct(fair[name])}")
    print(f"  method spread  {_pct(fair['spread'])}")
    print(f"Fair prob used   {_pct(p)}  (fair odds {format_american(prob_to_american(p))})")
    if args.boost:
        price_label = f"{args.mine} boosted {int(args.boost * 100)}% -> {format_american(decimal_to_american(mine))}"
    else:
        price_label = args.mine
    print(f"Your price       {price_label}  (break-even {_pct(v.breakeven)})")
    print(f"Edge             {_pct(v.edge)}  vs {args.market} threshold {_pct(v.threshold)}")
    print(f"EV per $100      ${v.ev_per_100:.2f}")
    print(f"Full Kelly       {_pct(v.kelly_full)}")
    print(f"Stake            ${v.stake:.2f}")
    if v.dont_bet_past is not None:
        print(f"Don't bet past   {format_american(v.dont_bet_past)} (effective price)")
    print(f"Decision         {v.decision}")
    for flag in v.flags:
        print(f"FLAG             {flag}")


def cmd_bonus(args: argparse.Namespace) -> None:
    d = american_to_decimal(parse_american(args.odds))
    value = bonus_bet_value(args.fair, d)
    print(f"Bonus bet at {args.odds} with fair {_pct(args.fair)}: expected conversion {_pct(value)}")
    if args.face:
        print(f"Expected cash from a ${args.face:.2f} bonus bet: ${value * args.face:.2f}")


def cmd_clv(args: argparse.Namespace) -> None:
    d = american_to_decimal(parse_american(args.odds))
    print(f"CLV {_pct(clv(d, args.close_fair))}")


def cmd_kalshi(args: argparse.Namespace) -> None:
    be = kalshi_breakeven(args.contracts, args.price)
    print(f"Break-even after taker fee: {_pct(be)}")


def cmd_sim(args: argparse.Namespace) -> None:
    d = american_to_decimal(parse_american(args.odds))
    out = simulate_bankroll(args.p, d, args.fraction, args.bets, args.sims)
    for key, value in out.items():
        print(f"{key:<22}{value:.4f}")


def cmd_log(args: argparse.Namespace) -> None:
    s = summarize(args.path)
    print(f"Bets logged         {s.bets} ({s.cash_bets} cash, {s.bets - s.cash_bets} bonus)")
    print(f"Units staked        {s.units_staked}")
    print(f"Cash P&L (units)    {s.cash_units:+}")
    print(f"Bonus P&L (units)   {s.bonus_units:+}")
    print(f"Cash ROI            {_pct(s.roi)}")
    if s.avg_edge_pct is not None:
        print(f"Avg modeled edge    {s.avg_edge_pct}%")
    print(f"Process grades      {s.grades}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="edge-engine", description="Price bets against the sharp market.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("price", help="De-vig a sharp market and grade your price")
    p.add_argument("--mine", required=True, help="Your book's American odds, e.g. +175")
    p.add_argument("--sharp", required=True, nargs="+", help="Sharp market, every outcome, e.g. +167 -191")
    p.add_argument("--side", type=int, default=0, help="Index of your outcome in --sharp")
    p.add_argument(
        "--method",
        default="multiplicative",
        choices=["multiplicative", "power", "shin", "additive", "worst_case"],
    )
    p.add_argument("--conservative", action="store_true", help="Use the lowest fair prob across methods")
    p.add_argument("--tie-factor", type=float, default=None, help="Multiply fair prob, e.g. 0.982 for NPB ties")
    p.add_argument("--boost", type=float, default=0.0, help="Profit boost, 0.5 = 50%%")
    p.add_argument("--market", default="main", choices=list(THRESHOLDS))
    p.add_argument("--bankroll", type=float, default=100.0)
    p.add_argument("--kelly", type=float, default=0.25)
    p.add_argument("--cap", type=float, default=0.02)
    p.set_defaults(func=cmd_price)

    b = sub.add_parser("bonus", help="Expected conversion of a bonus bet")
    b.add_argument("--odds", required=True)
    b.add_argument("--fair", type=float, required=True)
    b.add_argument("--face", type=float, default=None)
    b.set_defaults(func=cmd_bonus)

    c = sub.add_parser("clv", help="Closing line value of a bet")
    c.add_argument("--odds", required=True, help="Price you got")
    c.add_argument("--close-fair", type=float, required=True, help="Sharp no-vig closing probability")
    c.set_defaults(func=cmd_clv)

    k = sub.add_parser("kalshi", help="Prediction-market break-even after fees")
    k.add_argument("--contracts", type=int, required=True)
    k.add_argument("--price", type=float, required=True, help="Contract price in dollars, e.g. 0.47")
    k.set_defaults(func=cmd_kalshi)

    s = sub.add_parser("sim", help="Monte Carlo a bankroll plan")
    s.add_argument("--p", type=float, required=True)
    s.add_argument("--odds", required=True)
    s.add_argument("--fraction", type=float, required=True)
    s.add_argument("--bets", type=int, default=500)
    s.add_argument("--sims", type=int, default=20_000)
    s.set_defaults(func=cmd_sim)

    lg = sub.add_parser("log", help="Summarize a bet log CSV")
    lg.add_argument("path")
    lg.set_defaults(func=cmd_log)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
