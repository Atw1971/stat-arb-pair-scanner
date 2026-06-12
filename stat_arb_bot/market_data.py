from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import pandas as pd


@dataclass(frozen=True)
class SymbolSpec:
    symbol: str
    provider_symbol: str


DEFAULT_SYMBOLS = {
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "AUDUSD": "AUDUSD=X",
    "NZDUSD": "NZDUSD=X",
    "USDJPY": "JPY=X",
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
}


def parse_symbol_list(raw: str) -> list[SymbolSpec]:
    specs: list[SymbolSpec] = []
    for item in raw.replace("\n", ",").split(","):
        token = item.strip()
        if not token:
            continue
        if "=" in token:
            symbol, provider_symbol = token.split("=", 1)
            specs.append(SymbolSpec(symbol.strip().upper(), provider_symbol.strip()))
        else:
            normalized = token.upper().replace("/", "")
            specs.append(SymbolSpec(normalized, DEFAULT_SYMBOLS.get(normalized, token.strip())))
    return specs


def fetch_yahoo_prices(
    specs: list[SymbolSpec],
    period: str = "1y",
    interval: str = "1d",
    output_dir: str | Path | None = None,
    retries: int = 2,
    retry_sleep: float = 1.0,
) -> pd.DataFrame:
    import yfinance as yf

    frames: list[pd.Series] = []
    failures: list[str] = []
    saved_dir = Path(output_dir) if output_dir else None
    if saved_dir:
        saved_dir.mkdir(parents=True, exist_ok=True)

    for spec in specs:
        try:
            close = _fetch_yahoo_chart_close(spec.provider_symbol, period, interval).rename(spec.symbol)
            if close.empty:
                failures.append(f"{spec.symbol} ({spec.provider_symbol}): empty chart response")
                continue
            frames.append(close)
        except Exception as exc:
            failures.append(f"{spec.symbol} ({spec.provider_symbol}) chart API: {exc}")

    if frames:
        combined = pd.concat(frames, axis=1).sort_index().ffill().dropna(how="all")
        if saved_dir:
            for symbol in combined.columns:
                out = combined[symbol].dropna().reset_index()
                out.columns = ["timestamp", "close"]
                out.to_csv(saved_dir / f"{symbol}.csv", index=False)
        return combined

    frames = []
    tickers = [spec.provider_symbol for spec in specs]
    symbols_by_ticker = {spec.provider_symbol: spec.symbol for spec in specs}
    batch_error = ""
    for attempt in range(retries + 1):
        try:
            batch = yf.download(
                tickers,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False,
                threads=False,
                group_by="column",
            )
            batch_frames = _extract_batch_close(batch, symbols_by_ticker)
            if batch_frames:
                frames.extend(batch_frames)
                break
            batch_error = "empty batch response"
        except Exception as exc:
            batch_error = str(exc)
        if attempt < retries:
            time.sleep(retry_sleep * (attempt + 1))

    if frames:
        combined = pd.concat(frames, axis=1).sort_index().ffill().dropna(how="all")
        if saved_dir:
            for symbol in combined.columns:
                out = combined[symbol].dropna().reset_index()
                out.columns = ["timestamp", "close"]
                out.to_csv(saved_dir / f"{symbol}.csv", index=False)
        return combined

    failures.append(f"batch request: {batch_error or 'empty response'}")

    for spec in specs:
        df = pd.DataFrame()
        last_error = ""
        for attempt in range(retries + 1):
            try:
                df = yf.download(
                    spec.provider_symbol,
                    period=period,
                    interval=interval,
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )
                if not df.empty:
                    break
                last_error = "empty response"
            except Exception as exc:
                last_error = str(exc)
            if attempt < retries:
                time.sleep(retry_sleep * (attempt + 1))

        if df.empty:
            failures.append(f"{spec.symbol} ({spec.provider_symbol}): {last_error or 'empty response'}")
            continue

        close = _extract_close(df).dropna().rename(spec.symbol)
        if close.empty:
            failures.append(f"{spec.symbol} ({spec.provider_symbol}): missing close")
            continue
        close.index = pd.to_datetime(close.index, utc=True)
        frames.append(close)

        if saved_dir:
            out = close.reset_index()
            out.columns = ["timestamp", "close"]
            out.to_csv(saved_dir / f"{spec.symbol}.csv", index=False)

    if not frames:
        detail = "; ".join(failures[:8])
        raise ValueError(
            "No price data returned from Yahoo Finance. "
            "This is often a Yahoo rate limit or unsupported interval. "
            f"Failed symbols: {detail}"
        )

    return pd.concat(frames, axis=1).sort_index().ffill().dropna(how="all")


def _fetch_yahoo_chart_close(provider_symbol: str, period: str, interval: str) -> pd.Series:
    import requests

    response = requests.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{provider_symbol}",
        params={"range": period, "interval": interval},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=12,
    )
    response.raise_for_status()
    payload = response.json()
    chart = payload.get("chart", {})
    error = chart.get("error")
    if error:
        raise ValueError(error.get("description") or str(error))

    results = chart.get("result") or []
    if not results:
        return pd.Series(dtype=float)
    result = results[0]
    timestamps = result.get("timestamp") or []
    quote = ((result.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    if not timestamps or not closes:
        return pd.Series(dtype=float)

    series = pd.Series(closes, index=pd.to_datetime(timestamps, unit="s", utc=True), dtype="float64")
    return series.dropna()


def _extract_batch_close(df: pd.DataFrame, symbols_by_ticker: dict[str, str]) -> list[pd.Series]:
    if df.empty:
        return []

    frames: list[pd.Series] = []
    if isinstance(df.columns, pd.MultiIndex):
        level_0 = list(df.columns.get_level_values(0))
        level_1 = list(df.columns.get_level_values(1))

        if "Close" in level_0:
            close_df = df["Close"]
        elif "Adj Close" in level_0:
            close_df = df["Adj Close"]
        elif "Close" in level_1:
            close_df = df.xs("Close", level=1, axis=1)
        elif "Adj Close" in level_1:
            close_df = df.xs("Adj Close", level=1, axis=1)
        else:
            return []

        if isinstance(close_df, pd.Series):
            close_df = close_df.to_frame()

        for ticker, symbol in symbols_by_ticker.items():
            if ticker not in close_df.columns:
                continue
            close = close_df[ticker].dropna().rename(symbol)
            if close.empty:
                continue
            close.index = pd.to_datetime(close.index, utc=True)
            frames.append(close)
        return frames

    if "Close" in df.columns or "Adj Close" in df.columns:
        close = _extract_close(df).dropna()
        if len(symbols_by_ticker) == 1 and not close.empty:
            symbol = next(iter(symbols_by_ticker.values()))
            close.index = pd.to_datetime(close.index, utc=True)
            return [close.rename(symbol)]

    return []


def _extract_close(df: pd.DataFrame) -> pd.Series:
    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.get_level_values(0):
            close = df["Close"]
        elif "Adj Close" in df.columns.get_level_values(0):
            close = df["Adj Close"]
        else:
            raise ValueError("Yahoo response does not include Close prices")
        if isinstance(close, pd.DataFrame):
            return close.iloc[:, 0]
        return close

    if "Close" in df.columns:
        return df["Close"]
    if "Adj Close" in df.columns:
        return df["Adj Close"]
    raise ValueError("Yahoo response does not include Close prices")
