# How the Agent Loop Works

The core idea: treat an LLM agent like a junior analyst on a trading desk. It gets a written
policy, real tools, hard limits on what it is allowed to claim, and a post-mortem process that
turns every mistake into a new rule. The model does the legwork. The system decides what counts
as a valid answer.

## The loop

```
intake -> [Agent] -> research -> [Tools] -> pricing -> [edge_engine] -> decision
          bankroll,   sharp odds,             de-vig, EV,               BET / LEAN / PASS
          promos,     prediction markets,     Kelly, boosts,            thresholds, steelman,
          screenshots injury news, rules      copula SGP, CLV           don't-bet-past price

decision -> bet log (CSV) -> settlement + closing line -> post-mortem grade -> new rule in the spec
```

1. **Intake.** Every session starts with a jurisdiction and date check, then a single intake block:
   bankroll, open exposure, available promos, and slip screenshots.
2. **Research with provenance.** The agent pulls sharp reference prices (Pinnacle, Kalshi mids),
   retail prices, injury reports, and house rules. Every number carries a source and an ET timestamp.
   Anything it cannot verify is labeled `UNVERIFIED` and is banned from calculations.
3. **Pricing through code, never vibes.** Every probability and dollar figure goes through the
   functions in `src/edge_engine`. The agent is not allowed to do arithmetic in its head.
4. **Decision gates.** A bet only clears if its edge beats a market-specific threshold, survives a
   steelman of the other side, and passes a "too good to be true" check that forces a news re-search
   whenever the price beats the sharp market by more than 5 points.
5. **Logging.** Every placed bet becomes a structured CSV row with the fair probability, method,
   edge, stake, and a "don't bet past" price.
6. **Settlement and grading.** Results are pulled from league data feeds, closing prices are
   captured where possible, and each bet gets a process grade that is independent of whether it won.
7. **Rule updates.** Mistakes found in grading become new lines in the spec, so the next session
   cannot repeat them.

## Guardrails that make an LLM trustworthy with money

| Failure mode | Guardrail |
|---|---|
| Hallucinated odds or injuries | R1 search first, R3 `UNVERIFIED` tag, R2 staleness windows |
| Arithmetic mistakes | R4 every calculation in code with printed inputs and outputs |
| Misreading the actual slip | R5 screenshots are ground truth; parlay payout vs leg product checked |
| Overconfidence | R6 anchor to the sharp market; deviations need a written reason |
| Rationalizing a bet | R11 steelman plus pre-mortem; PASS if the other side is stronger |
| Results-oriented thinking | R14 grade by closing line value and decision quality |
| Tilt and chasing | R15 calls it out once and recommends stopping |

## Mistakes the loop caught, and what changed

These are real entries from the first week of the log. Including them is the point: a system that
documents its own failures is one you can actually improve.

- **Promo terms misread (grade D).** The agent read a "$0 of $10" progress tracker as cumulative and
  recommended splitting a qualifying bet into two $5 bets. The terms required each bet to be at least
  $10. Both bets were cashed out before settling, and the correct single $10 qualifier was placed
  minutes later, which unlocked the bonus. New rule: parse full promo terms, not the progress UI.
- **Boost stripped by a voided leg.** A tennis parlay with a 30% profit boost had one leg void after a
  retirement. The book settled the remaining leg as a single and removed the boost entirely. New
  pre-bet check: confirm void and retirement handling on boosted parlays.
- **Off-plan bet found in reconciliation.** A boosted MLB alt total was placed outside the session plan
  and never logged. Reconciling the log against the sportsbook's activity screen surfaced it. It still
  beat the closing line by about 2%, but it was flagged as off-plan.
- **Bonus bet placed as a parlay instead of the priced single.** It won, but two legs were never priced
  against the sharp market, so it was graded on process (B-) rather than on the result.
- **Injury check skipped.** A WNBA boost was placed in the morning instead of after the evening injury
  window. The price already reflected the uncertainty, so EV was fine, but the option to switch sides on
  news was lost.

## Why this is interesting beyond betting

Sports markets are a clean sandbox for agentic decision systems: prices are public, outcomes resolve
in hours, and there is a hard, objective benchmark (the sharp closing line) for whether a decision was
good. The same pattern applies to any workflow where an AI agent has to research, price, decide, and
be held accountable: credit decisions, procurement, trading desk support, or consulting analysis.
