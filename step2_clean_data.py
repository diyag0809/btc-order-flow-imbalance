import pandas as pd

# Load the same way as before
df = pd.read_csv(
    "BTCUSDT-aggTrades-2026-07-10.csv",
    names=["trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
           "timestamp", "is_buyer_maker", "is_best_match"]
)

# Keep only the columns we actually need
df = df[["price", "quantity", "timestamp", "is_buyer_maker"]]

# Convert timestamp from a giant number into a real datetime
# Binance timestamps are in milliseconds, so we tell pandas that with unit="ms"
df["time"] = pd.to_datetime(df["timestamp"], unit="us")

# Flip the confusing flag into something readable:
# is_buyer_maker = True  -> this was a SELL (seller was the aggressor)
# is_buyer_maker = False -> this was a BUY  (buyer was the aggressor)
df["side"] = df["is_buyer_maker"].map({True: "sell", False: "buy"})

# Drop the columns we no longer need
df = df[["time", "price", "quantity", "side"]]

print(df.head(10))
print("\nHow many buys vs sells overall:")
print(df["side"].value_counts())

# Save this cleaned version so we don't have to redo this step every time
df.to_csv("cleaned_trades.csv", index=False)
print("\nSaved cleaned_trades.csv")