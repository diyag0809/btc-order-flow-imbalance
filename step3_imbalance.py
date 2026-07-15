import pandas as pd

df = pd.read_csv("cleaned_trades.csv", parse_dates=["time"])

# Set time as the index so we can group by time windows
df = df.set_index("time")

# Split buy volume and sell volume into separate columns
# so we can sum them separately per time bucket
df["buy_volume"] = df["quantity"].where(df["side"] == "buy", 0)
df["sell_volume"] = df["quantity"].where(df["side"] == "sell", 0)

# Group into 10-second buckets
bucket = df.resample("10s").agg(
    buy_volume=("buy_volume", "sum"),
    sell_volume=("sell_volume", "sum"),
    price=("price", "last"),   # last traded price in that bucket
    n_trades=("price", "count")
)

# Drop empty buckets (no trades at all in that 10s window)
bucket = bucket[bucket["n_trades"] > 0]

# The imbalance signal: (buys - sells) / (buys + sells)
# Ranges from -1 (all selling) to +1 (all buying)
bucket["imbalance"] = (bucket["buy_volume"] - bucket["sell_volume"]) / \
                       (bucket["buy_volume"] + bucket["sell_volume"])

print(bucket.head(15))
print("\nTotal buckets:", len(bucket))

bucket.to_csv("buckets.csv")
print("Saved buckets.csv")