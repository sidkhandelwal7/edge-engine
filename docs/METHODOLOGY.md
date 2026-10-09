# Methodology

A short tour of the math in `src/edge_engine`, with the reasoning behind each choice.

## 1. Start from the sharp market, not from opinion

Sportsbooks are not all equal. Low-margin, high-limit books (Pinnacle is the standard reference) and
liquid prediction markets (Kalshi) do the price discovery. Retail books like DraftKings copy them and
add margin. So the fair probability of an outcome is estimated by taking the sharp market and removing
its margin. Personal opinion only moves that number when there is specific information the market has
not priced yet, and the adjustment has to be written down.

## 2. Removing the vig (`devig.py`)

A two-way market at -110 / -110 has implied probabilities of 52.38% each, summing to 104.76%. That
extra 4.76% is the book's margin. Different assumptions about how it was spread give different
fair numbers:

| Method | Assumption | Best for |
|---|---|---|
| Multiplicative | Margin scales with each outcome | Near even two-way markets |
| Additive | Equal margin per outcome | Rarely; breaks on longshots |
| Power | Solve sum(q^k) = 1 | Lopsided markets, favorite-longshot bias |
| Shin | Book protects against insiders | Multi-way outrights like golf and futures |
| Worst case | All margin on your side | Conservative sanity check |

When the methods disagree by more than 1.5 points, the bet is sized off the most conservative one.

## 3. Edge, EV, and the decision rule (`ev.py`)

- **Edge** = fair probability minus the break-even probability of your price.
- **EV per dollar** = fair probability times decimal odds, minus one.
- **Thresholds** scale with how noisy the market is: 2% for main lines, 3.5% for player props, 4% for
  alternate lines, 5% for futures.
- **Don't bet past** solves for the worst price at which the edge still clears the threshold, so the
  decision survives the price moving while you are placing the bet.

## 4. Sizing (`ev.py`, `analytics.py`)

Full Kelly maximizes long-run growth but is brutally volatile and assumes your probability is exactly
right. The framework uses quarter Kelly with a hard cap per bet and a daily exposure cap.
`simulate_bankroll` shows why: even a genuine 55% bettor at -110 has a meaningful chance of being down
after 500 bets and a typical max drawdown around 30%.

## 5. Promotions (`promos.py`)

Retail books hand out positive EV through promotions, and these turned out to be the most reliable
source of edge in practice.

- **Profit boosts** multiply winnings, not the stake: d' = 1 + (d - 1)(1 + b). A +175 price with a 100%
  boost becomes +350. Against a sharp fair probability of 35.7%, that is roughly +60% EV.
- **Bonus bets** do not return the stake, so their value per dollar is p(d - 1). That makes plus-money
  prices in the +200 to +500 range the efficient way to convert them to cash, typically 70 to 80 cents
  on the dollar.
- **Prediction-market fees** are modeled explicitly so contract prices can be compared to sportsbook
  no-vig prices on equal footing.

## 6. Correlated parlays (`parlay.py`)

Same-game parlays are not priced as independent events, because the legs are correlated (a team
winning and its total going over tend to happen together). The engine prices them with a Gaussian
copula: each leg gets a latent normal variable whose cutoff matches that leg's fair probability, the
latent variables are correlated, and a Monte Carlo counts how often every leg hits. That keeps every
leg's individual probability exact while capturing the dependence between them. Comparing the
independent product to the book's displayed price also reveals how much correlation the book priced in.

## 7. Grading the process (`analytics.py`)

Win/loss records are nearly useless at small samples. A true 55% bettor at -110 needs roughly 1,500 bets
before the record is statistically convincing. Closing line value (did your price beat the sharp
closing price?) converges much faster, so it is the primary grade. `record_zscore` and `roi_tstat` exist
mostly to show how little a short record proves.

## 8. Shrinkage

Early-season stats are mostly noise. `shrink` blends an observed rate with a prior using a
stabilization sample size, so a hot shooting week moves the estimate a little and a full season of
strikeout data moves it a lot.
