import pandas as pd
from scipy import stats

df = pd.read_csv("cleaned_trades.csv", parse_dates=["time"])
df = df.set_index("time")

df["buy_volume"] = df["quantity"].where(df["side"] == "buy", 0)
df["sell_volume"] = df["quantity"].where(df["side"] == "sell", 0)

# 1-second buckets instead of 10-second
bucket = df.resample("1s").agg(
    buy_volume=("buy_volume", "sum"),
    sell_volume=("sell_volume", "sum"),
    price=("price", "last"),
    n_trades=("price", "count")
)

bucket = bucket[bucket["n_trades"] > 0]

bucket["imbalance"] = (bucket["buy_volume"] - bucket["sell_volume"]) / \
                       (bucket["buy_volume"] + bucket["sell_volume"])

print("Total 1-second buckets with trades:", len(bucket))

# Test a few different horizons: 1 second ahead, 2 seconds ahead
for horizon in [1, 2, 5]:
    b = bucket.copy()
    b["future_price"] = b["price"].shift(-horizon)
    b["future_return"] = (b["future_price"] - b["price"]) / b["price"]
    b = b.dropna(subset=["future_return"])

    corr, p_value = stats.pearsonr(b["imbalance"], b["future_return"])

    avg_buy = b[b["imbalance"] > 0.3]["future_return"].mean()
    avg_sell = b[b["imbalance"] < -0.3]["future_return"].mean()

    print(f"\n--- Horizon: {horizon} second(s) ahead ---")
    print(f"Correlation: {corr:.4f}, P-value: {p_value:.6f}")
    print(f"Avg return after buy-heavy (>0.3): {avg_buy:.6f}")
    print(f"Avg return after sell-heavy (<-0.3): {avg_sell:.6f}")