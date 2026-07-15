import pandas as pd

# Load the file — replace the filename below with your actual file name if different
df = pd.read_csv(
    "BTCUSDT-aggTrades-2026-07-10.csv",
    names=["trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
           "timestamp", "is_buyer_maker", "is_best_match"]
)

# Show basic info
print("Number of rows:", len(df))
print("\nFirst 5 rows:")
print(df.head())