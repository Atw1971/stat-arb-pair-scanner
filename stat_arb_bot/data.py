from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_price_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "timestamp" not in df.columns:
        raise ValueError(f"{path} must include a timestamp column")
    if "close" not in df.columns:
        raise ValueError(f"{path} must include a close column")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    df = df.dropna(subset=["timestamp", "close"]).sort_values("timestamp")
    df = df.drop_duplicates(subset=["timestamp"], keep="last")
    df = df.set_index("timestamp")
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df.dropna(subset=["close"])


def load_price_matrix(data_dir: str | Path) -> pd.DataFrame:
    data_path = Path(data_dir)
    frames: list[pd.Series] = []

    for csv_path in sorted(data_path.glob("*.csv")):
        symbol = csv_path.stem.upper()
        df = load_price_csv(csv_path)
        frames.append(df["close"].rename(symbol))

    if not frames:
        raise ValueError(f"No CSV files found in {data_path}")

    prices = pd.concat(frames, axis=1).sort_index()
    return prices.ffill().dropna(how="all")


def load_pair(data_dir: str | Path, symbol_a: str, symbol_b: str) -> pd.DataFrame:
    prices = load_price_matrix(data_dir)
    columns = [symbol_a.upper(), symbol_b.upper()]
    missing = [symbol for symbol in columns if symbol not in prices.columns]
    if missing:
        raise ValueError(f"Missing price files for: {', '.join(missing)}")
    return prices[columns].dropna()
