import pandas as pd
import requests
import zipfile
import io
from scipy import stats

# Spread across the last month, mix of weekdays/weekends, not just consecutive days
DATES = [
    "2026-06-15", "2026-06-19", "2026-06-22", "2026-06-26",
    "2026-06-29", "2026-07-03", "2026-07-06", "2026-07-10",
    "2026-07-12", "2026-07-13"
]

def download_day(date_str):
    """Downloads one day's aggTrades file from Binance if we don't already have it."""
    filename = f"BTCUSDT-aggTrades-{date_str}.csv"
    try:
        # Check if already downloaded
        pd.read_csv(filename, nrows=1)
        print(f"{date_str}: already have it, skipping download")
        return filename
    except FileNotFoundError:
        pass

    url = f"https://data.binance.vision/data/spot/daily/aggTrades/BTCUSDT/BTCUSDT-aggTrades-{date_str}.zip"
    print(f"{date_str}: downloading...")
    r = requests.get(url)
    if r.status_code != 200:
        print(f"{date_str}: FAILED to download (status {r.status_code})")
        return None

    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall(".")
    # The extracted file might already be named correctly, or need renaming
    extracted_name = z.namelist()[0]
    if extracted_name != filename:
        import os
        os.rename(extracted_name, filename)
    print(f"{date_str}: downloaded and extracted")
    return filename


def process_day(filename, date_str, horizon=5):
    """Runs the same cleaning + imbalance + test pipeline as before, on one day."""
    df = pd.read_csv(
        filename,
        names=["trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
               "timestamp", "is_buyer_maker", "is_best_match"]
    )
    df["time"] = pd.to_datetime(df["timestamp"], unit="us")
    df["side"] = df["is_buyer_maker"].map({True: "sell", False: "buy"})
    df = df.set_index("time")

    df["buy_volume"] = df["quantity"].where(df["side"] == "buy", 0)
    df["sell_volume"] = df["quantity"].where(df["side"] == "sell", 0)

    bucket = df.resample("1s").agg(
        buy_volume=("buy_volume", "sum"),
        sell_volume=("sell_volume", "sum"),
        price=("price", "last"),
        n_trades=("price", "count")
    )

    full_range = pd.date_range(bucket.index.min(), bucket.index.max(), freq="1s")
    bucket = bucket.reindex(full_range)
    bucket["price"] = bucket["price"].ffill()
    bucket["buy_volume"] = bucket["buy_volume"].fillna(0)
    bucket["sell_volume"] = bucket["sell_volume"].fillna(0)

    total_volume = bucket["buy_volume"] + bucket["sell_volume"]
    bucket["imbalance"] = (bucket["buy_volume"] - bucket["sell_volume"]) / total_volume

    bucket["future_price"] = bucket["price"].shift(-horizon)
    bucket["future_return"] = (bucket["future_price"] - bucket["price"]) / bucket["price"]
    bucket = bucket.dropna(subset=["imbalance", "future_return"])

    corr, p_value = stats.pearsonr(bucket["imbalance"], bucket["future_return"])
    avg_buy = bucket[bucket["imbalance"] > 0.3]["future_return"].mean()
    avg_sell = bucket[bucket["imbalance"] < -0.3]["future_return"].mean()

    return {
        "date": date_str,
        "n_buckets": len(bucket),
        "correlation": corr,
        "p_value": p_value,
        "avg_return_buy_heavy": avg_buy,
        "avg_return_sell_heavy": avg_sell,
        "edge_vs_cost": (avg_buy - avg_sell) / 0.002
    }


results = []
for date_str in DATES:
    filename = download_day(date_str)
    if filename is None:
        continue
    result = process_day(filename, date_str, horizon=5)
    results.append(result)
    print(f"  -> correlation: {result['correlation']:.4f}, edge_vs_cost: {result['edge_vs_cost']:.4f}")

results_df = pd.DataFrame(results)
pd.set_option("display.float_format", lambda x: f"{x:.6f}")
print("\n=== Results across all days ===")
print(results_df)

print("\n=== Summary stats across days ===")
print("Average correlation:", results_df["correlation"].mean())
print("Std dev of correlation:", results_df["correlation"].std())
print("Average edge_vs_cost:", results_df["edge_vs_cost"].mean())
print("Days where edge_vs_cost > 1 (i.e. tradeable):", (results_df["edge_vs_cost"] > 1).sum())

results_df.to_csv("multi_day_results.csv", index=False)
print("\nSaved multi_day_results.csv")