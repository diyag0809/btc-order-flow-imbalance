import pandas as pd
from scipy import stats

df = pd.read_csv("cleaned_trades.csv", parse_dates=["time"])
df = df.set_index("time")

df["buy_volume"] = df["quantity"].where(df["side"] == "buy", 0)
df["sell_volume"] = df["quantity"].where(df["side"] == "sell", 0)

bucket = df.resample("1s").agg(
    buy_volume=("buy_volume", "sum"),
    sell_volume=("sell_volume", "sum"),
    price=("price", "last"),
    n_trades=("price", "count")
)

# IMPORTANT FIX: reindex to a complete, gap-free 1-second grid covering the
# whole day. This guarantees "shift by N rows" really means "N seconds ahead."
full_range = pd.date_range(bucket.index.min(), bucket.index.max(), freq="1s")
bucket = bucket.reindex(full_range)

# For seconds with no trades: no volume happened, and price didn't move,
# so carry the last known price forward.
bucket["price"] = bucket["price"].ffill()
bucket["buy_volume"] = bucket["buy_volume"].fillna(0)
bucket["sell_volume"] = bucket["sell_volume"].fillna(0)
bucket["n_trades"] = bucket["n_trades"].fillna(0)

# Imbalance is undefined when there was no volume at all in that second
total_volume = bucket["buy_volume"] + bucket["sell_volume"]
bucket["imbalance"] = (bucket["buy_volume"] - bucket["sell_volume"]) / total_volume
# rows with zero volume become NaN here — that's correct, we'll drop them per-horizon

print("Total seconds in the day (grid):", len(bucket))
print("Seconds with at least one trade:", (bucket["n_trades"] > 0).sum())

ROUND_TRIP_COST = 0.002
results = []

for horizon in [1, 2, 5, 10, 30, 60, 120]:
    b = bucket.copy()
    b["future_price"] = b["price"].shift(-horizon)
    b["future_return"] = (b["future_price"] - b["price"]) / b["price"]
    b = b.dropna(subset=["imbalance", "future_return"])

    corr, p_value = stats.pearsonr(b["imbalance"], b["future_return"])
    avg_buy = b[b["imbalance"] > 0.3]["future_return"].mean()
    avg_sell = b[b["imbalance"] < -0.3]["future_return"].mean()
    edge = avg_buy - avg_sell  # total spread between the two groups

    results.append({
        "horizon_sec": horizon,
        "correlation": corr,
        "p_value": p_value,
        "avg_return_buy_heavy": avg_buy,
        "avg_return_sell_heavy": avg_sell,
        "edge_vs_cost": edge / ROUND_TRIP_COST
    })

results_df = pd.DataFrame(results)
pd.set_option("display.float_format", lambda x: f"{x:.6f}")
print("\n=== Horizon sweep results ===")
print(results_df)

results_df.to_csv("horizon_sweep_results.csv", index=False)
print("\nSaved horizon_sweep_results.csv")