# edge-engine

[![tests](https://github.com/sidkhandelwal7/edge-engine/actions/workflows/tests.yml/badge.svg)](https://github.com/sidkhandelwal7/edge-engine/actions/workflows/tests.yml)

**Can an AI agent, held to the standards of a real trading desk, find mispriced bets that a sportsbook is literally handing out?**

That question took over my October. I'm a Finance student who has always been more interested in *why* a price is what it is than in who wins the game. So instead of picking teams, I built a system that treats sportsbooks like a market: an LLM agent that does the research, a Python pricing engine that does the math, and a strict rulebook that decides what the agent is and isn't allowed to say. Then I ran it with real money, logged every decision, and graded every bet on process instead of outcome.

This repo is the engine, the agent's full operating spec, and an honest look at what happened.

## The idea in one paragraph

Sportsbooks don't set prices in a vacuum. A handful of sharp, low-margin markets (Pinnacle, and prediction markets like Kalshi) do the real price discovery, and retail books like DraftKings copy those prices and add their margin on top. That means you can estimate the "true" probability of almost any outcome by taking the sharp price and stripping out its margin. Once you have that, every retail price, profit boost, and bonus bet becomes a math problem: is what they're offering worth more than what the outcome is actually worth? Most of the time the answer is no, and the system says PASS. Sometimes, especially with promotions, the answer is a very clear yes.

## What's inside

```
edge-engine/
├── src/edge_engine/
│   ├── odds.py        American, decimal, and probability conversions
│   ├── devig.py       5 methods for removing bookmaker margin (incl. Shin and power)
│   ├── ev.py          edge, EV, fractional Kelly, thresholds, "don't bet past" price
│   ├── promos.py      profit boosts, bonus bet conversion, prediction market fees
│   ├── parlay.py      correlated same-game parlay pricing with a Gaussian copula
│   ├── analytics.py   closing line value, skill tests, shrinkage, bankroll Monte Carlo
│   ├── betlog.py      log parsing and performance summary
│   └── cli.py         price any bet from the terminal in one line
├── agent/
│   └── analyst_system_prompt.md   the full rulebook the AI agent runs under
├── docs/
│   ├── AGENTIC_WORKFLOW.md        how the agent loop works and what it got wrong
│   └── METHODOLOGY.md             the math, explained
├── examples/sample_log.csv        the first week of real decisions, anonymized
└── tests/                         50 tests, many pinned to real logged bets
```

## The agentic part (the part I'm proudest of)

The interesting problem wasn't the math. The math is well known. The interesting problem was: **how do you get an AI agent to make real money decisions without hallucinating, getting overconfident, or talking itself into bad bets?**

My answer was to stop thinking of it as a chatbot and start thinking of it as a new analyst on a desk. New analysts get a written policy, real tools, a checklist, and a manager who reviews their work. So the agent gets:

- **A 15 rule operating spec** ([read it here](agent/analyst_system_prompt.md)). Search before answering. Timestamp every price. If you can't verify something, label it `UNVERIFIED` and you're not allowed to use it in a calculation. Never do arithmetic in your head.
- **Tools.** Live web search, sharp sportsbook and prediction market prices, injury reports, league data feeds for settlement, and my own slip screenshots, which are treated as ground truth for what I actually got.
- **This codebase as its calculator.** Every probability and dollar figure the agent reports has to come out of code, with inputs printed so I can audit it.
- **Hard decision gates.** A bet has to clear a minimum edge that scales with how noisy the market is, survive a written steelman of the other side, and pass a "too good to be true" check that forces a fresh news search whenever a price looks suspiciously generous.
- **A manager.** After every bet settles, it gets a process grade from A to F that is completely independent of whether it won. Every mistake becomes a new rule in the spec so the next session can't repeat it.

That last loop is what made this feel like engineering instead of gambling. Some of my favorite entries in the log are the agent's own mistakes, like the time it misread a promo's terms (a "$0 of $10" progress bar read as cumulative when each bet needed to be $10 on its own). That decision got a D, the rule got rewritten, and the correct single $10 qualifier went in seven minutes later and unlocked the bonus. [The full list of what broke and what changed is here.](docs/AGENTIC_WORKFLOW.md)

The library itself was also built agentically: I designed the system and the rules, and worked with an AI coding agent to implement, test, and verify each module against numbers from real bets.

## Try it

```bash
git clone https://github.com/sidkhandelwal7/edge-engine.git
cd edge-engine
pip install -e ".[dev]"
pytest -q
```

Price a real bet from the log. Hiroshima Carp at +175 on DraftKings with a 100% profit boost, against Pinnacle's sharp market of +167 / -191, adjusted for the chance of a tie in Japanese baseball:

```
$ edge-engine price --mine +175 --sharp +167 -191 --side 0 --tie-factor 0.982 --boost 1.0

Sharp market     +167 / -191  (side 0)
  multiplicative 36.33%
  power          35.70%
  shin           35.91%
  additive       35.91%
  worst_case     34.36%
  method spread  1.97%
Fair prob used   35.68%  (fair odds +180)
Your price       +175 boosted 100% -> +350  (break-even 22.22%)
Edge             13.45%  vs main threshold 2.00%
EV per $100      $60.55
Full Kelly       17.30%
Stake            $2.00
Don't bet past   +197 (effective price)
Decision         BET
FLAG             TOO_GOOD_TO_BE_TRUE: re-check injuries, lineups, weather and palpable-error risk
```

That bet lost 2 to 1. It was still one of the best decisions in the log, and the system graded it that way.

Other commands:

```bash
edge-engine bonus --odds +350 --fair 0.2137 --face 10     # what is a $10 bonus bet worth here?
edge-engine clv --odds +143 --close-fair 0.4199           # did I beat the closing line?
edge-engine kalshi --contracts 100 --price 0.47           # prediction market break-even after fees
edge-engine sim --p 0.55 --odds -110 --fraction 0.02      # what does variance actually look like?
edge-engine log examples/sample_log.csv                   # summarize a bet log
```

## What actually happened

I want to be upfront here, because honesty about results is the whole philosophy of the project.

After the first week of live use (12 decisions, flat sizing in small units):

| | |
|---|---|
| Cash bets | 11, risking 19.5 units |
| Cash result | +4.5 units |
| Bonus bets | 1, converted at 525% of face |
| Process grades | 3 A-, 1 B+, 4 B, 2 B-, 2 D |
| Average modeled edge | about 3.9% |

**Twelve bets prove nothing.** A genuinely skilled bettor needs something like 1,500 bets before a win rate is statistically convincing, and the engine includes the tests to show exactly that. The real takeaways from week one were about the system, not the scoreboard:

1. **Promotions are where the edge lives.** Every bet that cleared the bar in week one involved a profit boost, a bonus bet, or a promo qualifier, where the book is effectively paying for engagement. Raw pricing errors on main lines are rare and small.
2. **The agent is only as good as its guardrails.** Every serious mistake traced back to something the rules didn't cover yet, and every one became a rule.
3. **Capturing the closing price is the hardest part operationally**, and it's the most important metric. That's the top item on the roadmap.

## Why I built it this way

A few principles I stuck to the whole time:

- **The price is the pick.** A great team at a bad price is a bad bet.
- **PASS is a position.** A day with zero bets is a good day if nothing cleared the bar.
- **Grade the decision, not the result.** Good bets lose all the time and bad bets win all the time.
- **Anchor to the market.** The model never gets to overrule the sharpest price available without a specific, written reason.

These are the same ideas behind good investing and good risk management, which is exactly why this project pulled me in. Sports markets just give you feedback in hours instead of years.

## Roadmap

- Automated closing line capture at game time so every bet gets a CLV grade
- A scheduled agent that scans the day's promotions and boosts and ranks them by EV before I wake up
- Player prop projection models (Poisson and negative binomial for counts, skewed distributions for yardage)
- A dashboard for CLV distribution, drawdown, and exposure by market type

## Responsible use

Built and used in Pennsylvania, where sports betting is legal for adults 21 and over and prediction markets are available to 18 and over. This is a research and engineering project, not betting advice. Staking rules here are deliberately conservative: small fixed units, a hard daily exposure cap, and a rule against ever raising stakes to win back a loss. If gambling stops being fun, 1-800-GAMBLER is free and confidential.

## License

MIT
