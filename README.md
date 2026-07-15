# Order Flow Imbalance and Short-Horizon Price Prediction in BTC/USDT

## Overview

This project tests whether short-horizon order flow imbalance, a measure of how
much buying pressure versus selling pressure is happening in real time, can
predict which way BTC/USDT price moves over the next 1 to 120 seconds. It also
tests whether any predictive power found is actually large enough to trade on
once realistic costs are included.

**Summary:** The imbalance signal is statistically significant and consistent
across ten separately sampled trading days (mean correlation 0.098, standard
deviation 0.013, p < 0.001 on every day). But the size of the effect is small,
between roughly 0.6% and 2.4% of a conservative round-trip trading cost on every
day tested. The effect is real. It is not tradeable as-is.

## Motivation

I built this as a follow-up to two earlier signal projects, one testing CFTC
positioning data at weekly horizons and one testing equity momentum at daily
horizons. Both projects taught me the same lesson: a signal that looks real on
paper can fall apart once you check it properly. I wanted to apply that same
process (check for statistical significance, then check for economic viability
after costs, then check it holds up on more than one day) to the opposite end of
the frequency spectrum, where trades happen every fraction of a second and false
signals are easy to manufacture by accident.

## Data

- **Source:** Binance public historical trade data (data.binance.vision),
  aggTrades endpoint, BTC/USDT spot market
- **What's in it:** individual trades, each with price, quantity, a timestamp
  accurate to the microsecond, and a flag showing whether the buyer or seller
  initiated the trade
- **Sample:** 10 non-consecutive days between 15 June and 13 July 2026, mixing
  weekdays and weekends so the sample isn't clustered around one type of day
- **Size:** roughly 750,000 to 870,000 trades per day, grouped into about
  75,000 to 80,500 one-second buckets per day once empty seconds are handled

## Method

### 1. Cleaning and labeling trades

Binance's is_buyer_maker flag is backwards from how it sounds: when it's True,
the seller was actually the one initiating the trade, so I flipped it into a
clear buy/sell label. Timestamps were read at microsecond precision (an early
version of this script assumed millisecond precision and produced dates in the
year 58491, which is how I caught the mistake).

### 2. Building the imbalance signal

Trades were grouped into one-second windows. In each window, I summed buy volume
and sell volume separately and calculated:
Imbalance(t) = (BuyVolume(t) - SellVolume(t)) / (BuyVolume(t) + SellVolume(t))
This gives a number between -1 (all selling) and +1 (all buying) for that
second. Roughly 6-7% of one-second windows had no trades at all, so I filled
those gaps by carrying the last known price forward and treating volume as zero,
otherwise "5 seconds later" wouldn't reliably mean 5 real seconds later.

### 3. Measuring the forward return

For a given horizon h (in seconds):
Return(t, h) = (Price(t + h) - Price(t)) / Price(t)
I tested this at 1, 2, 5, 10, 30, 60, and 120 second horizons.

### 4. Checking statistical significance

I ran a Pearson correlation between Imbalance(t) and Return(t, h) at each
horizon, along with the p-value, to check whether any relationship was likely to
be real rather than random noise.

### 5. Checking economic significance

I split each day into buy-heavy windows (imbalance above 0.3) and sell-heavy
windows (imbalance below -0.3), then compared the average forward return between
the two groups against a round-trip trading cost of 0.20% (a reasonable retail
spot fee assumption):
EdgeRatio(h) = [Avg Return, buy-heavy - Avg Return, sell-heavy] / 0.002
An EdgeRatio at or above 1.0 would mean the average edge is big enough to cover
trading costs. Below 1.0 means the signal is real but too small to act on
profitably.

### 6. Checking it wasn't a one-off day

I reran the entire pipeline on ten separate days instead of trusting the result
from a single day, since markets can behave very differently day to day.

## Results

### Horizon sweep (10 July 2026)

| Horizon | Correlation | p-value | Edge / Cost |
|---|---|---|---|
| 1s   | 0.078 | < 0.001 | 0.004 |
| 2s   | 0.080 | < 0.001 | 0.006 |
| 5s   | 0.082 | < 0.001 | 0.011 |
| 10s  | 0.072 | < 0.001 | 0.014 |
| 30s  | 0.045 | < 0.001 | 0.016 |
| 60s  | 0.033 | < 0.001 | 0.016 |
| 120s | 0.025 | < 0.001 | 0.016 |

The correlation is strongest around 5 seconds and fades from there. The edge
relative to cost keeps creeping up slightly out to 120 seconds, since price
tends to drift further given more time even as the relationship gets noisier.
At no point does the edge get close to covering costs.

### Across 10 days (5 second horizon)

| Date | Correlation | Edge / Cost |
|---|---|---|
| 2026-06-15 | 0.109 | 0.015 |
| 2026-06-19 | 0.106 | 0.014 |
| 2026-06-22 | 0.106 | 0.017 |
| 2026-06-26 | 0.096 | 0.024 |
| 2026-06-29 | 0.099 | 0.021 |
| 2026-07-03 | 0.115 | 0.014 |
| 2026-07-06 | 0.093 | 0.017 |
| 2026-07-10 | 0.082 | 0.011 |
| 2026-07-12 | 0.072 | 0.006 |
| 2026-07-13 | 0.100 | 0.015 |
| **Mean** | **0.098** | **0.015** |
| **Std dev** | **0.013** | — |

Every single day came back statistically significant (p < 0.001), and the
correlation barely moved day to day. So 10 July wasn't an outlier, it was
actually on the low end of a pretty stable pattern. None of the ten days got
anywhere near an EdgeRatio of 1.0.

## What this actually means

There's a real difference between a signal being statistically significant and
a signal being worth trading on, and this project is a clean example of that gap.
Order flow imbalance genuinely predicts short-term price direction here. It's
consistent, it shows up every single day tested, and the p-values leave basically
no room for it being chance. But the size of that edge is roughly 50 to 150 times
smaller than what it costs to actually act on it.

That kind of gap usually only closes for firms with much lower execution costs,
much lower latency, or the ability to stack many small edges like this one
together across instruments, which is a different scale of infrastructure than
what this project used.

## Limitations and what I'd try next

- **Only tested on BTC/USDT spot.** Futures markets have lower fees, and equities
  or commodities (closer to what most trading desks actually trade) might behave
  differently.
- **No order book data.** This only uses executed trades, not resting buy/sell
  orders sitting in the book. Book depth is often a stronger signal than trade
  flow alone, but wasn't available for free at this level of detail.
- **Deliberately avoided ML models for now.** A tree-based model might squeeze
  out a bit more signal, but running one on just ten days risks fitting noise
  rather than finding something real, which defeats the point of this project.
  If I extend this, I'd want a lot more days first.
- **One fixed cost assumption.** Lower fees (futures, market maker rebates)
  would shrink the gap a bit but wouldn't close it. A 50-150x gap doesn't
  disappear because of a slightly better fee tier.

## Related work

Same approach, different speeds:
- **Commodity Positioning Signals** — CFTC futures data, weekly/monthly horizon
- **Momentum Strategy Backtester** — S&P 500 equities, daily horizon

## Repository structure

```
01_load_data.py            initial load and row count check
02_clean_data.py           timestamp fix, buy/sell labeling
03_imbalance.py            first pass, 10-second buckets
04_test_signal.py          correlation + grouped return test
05_significance_costs.py   p-value test, cost comparison
06_shorter_horizon.py      1s/2s/5s comparison
07_full_horizon_sweep.py   gap-fixed 1s-120s sweep
08_multi_day.py            auto-download + 10-day robustness check
horizon_sweep_results.csv  output of 07
multi_day_results.csv      output of 08
requirements.txt
README.md
```

Raw trade CSVs aren't included (too large, and not really mine to redistribute).
`08_multi_day.py` downloads them automatically on first run.

## How to run

```bash
pip install -r requirements.txt
python3 08_multi_day.py
```

Steps 01 through 07 can also be run individually against any single downloaded
day.

## Requirements
pandas

scipy

requests
