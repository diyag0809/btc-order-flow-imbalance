import pandas as pd
from scipy import stats

bucket = pd.read_csv("buckets_with_signal.csv", parse_dates=["time"], index_col="time")

# Statistical significance test: is the correlation likely to be real, or noise?
corr, p_value = stats.pearsonr(bucket["imbalance"], bucket["future_return"])
print(f"Correlation: {corr:.4f}")
print(f"P-value: {p_value:.6f}")
print("(p < 0.05 usually means 'probably not random chance')")

# Now the realism check: does it survive trading costs?
# Binance spot trading fee is roughly 0.1% (0.001) per trade round-trip is ~0.002
ROUND_TRIP_COST = 0.002  # 0.2% total, a reasonable conservative assumption

avg_return_buy_heavy = bucket[bucket["signal_group"] == "buy-heavy"]["future_return"].mean()
avg_return_sell_heavy = bucket[bucket["signal_group"] == "sell-heavy"]["future_return"].mean()

print(f"\nAvg return after buy-heavy signal: {avg_return_buy_heavy:.6f}")
print(f"Avg return after sell-heavy signal: {avg_return_sell_heavy:.6f}")
print(f"Round-trip trading cost assumed: {ROUND_TRIP_COST:.6f}")

print(f"\nDoes buy-heavy edge survive costs? {'YES' if avg_return_buy_heavy > ROUND_TRIP_COST else 'NO'}")
print(f"Does sell-heavy edge survive costs? {'YES' if abs(avg_return_sell_heavy) > ROUND_TRIP_COST else 'NO'}")