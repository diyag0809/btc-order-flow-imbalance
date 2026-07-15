import pandas as pd

bucket = pd.read_csv("buckets.csv", parse_dates=["time"], index_col="time")

# The price move over the NEXT bucket (10 seconds later)
# shift(-1) pulls the future price back to line up with today's row
bucket["future_price"] = bucket["price"].shift(-1)
bucket["future_return"] = (bucket["future_price"] - bucket["price"]) / bucket["price"]

# Drop the last row (it has no "future" to compare to)
bucket = bucket.dropna(subset=["future_return"])

# THE KEY QUESTION: does imbalance correlate with future_return?
correlation = bucket["imbalance"].corr(bucket["future_return"])
print("Correlation between imbalance and next-window return:", correlation)

# A more intuitive check: split into "high imbalance" (buy-heavy) vs
# "low imbalance" (sell-heavy) and compare average future returns
bucket["signal_group"] = pd.cut(
    bucket["imbalance"],
    bins=[-1.01, -0.3, 0.3, 1.01],
    labels=["sell-heavy", "neutral", "buy-heavy"]
)

print("\nAverage next-window return by group:")
print(bucket.groupby("signal_group", observed=True)["future_return"].mean())

print("\nHow many buckets fall in each group:")
print(bucket["signal_group"].value_counts())

bucket.to_csv("buckets_with_signal.csv")