from __future__ import annotations

import os
import re
import time
from datetime import datetime, timezone
from io import StringIO
from typing import Any, List, Optional

import numpy as np
import pandas as pd
import requests


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def safe_get_json(
    url: str,
    params: Optional[dict] = None,
    headers: Optional[dict] = None,
    timeout: int = 30,
    max_retries: int = 3,
    sleep_seconds: float = 0.5,
    non_retryable_status_codes: tuple = (400, 401, 403, 404, 451),
    session: Optional[requests.Session] = None,
) -> dict:
    """带重试的 JSON GET。"""
    last_err = None
    client = session or requests
    for i in range(max_retries):
        try:
            r = client.get(url, params=params, headers=headers, timeout=timeout)
            if r.status_code in non_retryable_status_codes:
                r.raise_for_status()
            r.raise_for_status()
            return r.json()
        except requests.HTTPError as e:
            last_err = e
            status = getattr(e.response, "status_code", None)
            if status in non_retryable_status_codes:
                break
            time.sleep(sleep_seconds * (i + 1))
        except Exception as e:
            last_err = e
            time.sleep(sleep_seconds * (i + 1))
    raise RuntimeError(f"GET JSON failed: {url}, params={params}, error={last_err}")


def _looks_like_html_challenge(html: str) -> bool:
    lower = html.lower()
    challenge_markers = [
        "just a moment",
        "enable javascript and cookies",
        "challenge-platform",
        "__cf_chl",
        "cf-chl",
        "cloudflare",
    ]
    return any(marker in lower for marker in challenge_markers)


def safe_read_html(
    url: str,
    timeout: int = 30,
    max_retries: int = 3,
    non_retryable_status_codes: tuple = (400, 401, 403, 404, 451),
    session: Optional[requests.Session] = None,
) -> List[pd.DataFrame]:
    """安全读取网页表格；用于 ETF flow 这类没有稳定免费 API 的数据。"""
    last_err = None
    headers = {"User-Agent": "btc-unified-pricing-model-v1.3 research-use"}
    client = session or requests
    for i in range(max_retries):
        try:
            r = client.get(url, headers=headers, timeout=timeout)
            if r.status_code in non_retryable_status_codes:
                r.raise_for_status()
            r.raise_for_status()
            html = r.text
            if _looks_like_html_challenge(html):
                raise RuntimeError("HTML challenge / Cloudflare page detected; table cannot be read without a browser session.")
            return pd.read_html(StringIO(html))
        except requests.HTTPError as e:
            last_err = e
            status = getattr(e.response, "status_code", None)
            if status in non_retryable_status_codes:
                break
        except Exception as e:
            last_err = e
            time.sleep(0.5 * (i + 1))
    raise RuntimeError(f"read_html failed: {url}, error={last_err}")

def today_utc_date() -> datetime.date:
    return datetime.now(timezone.utc).date()

def to_date_from_ms(ms: int) -> datetime.date:
    return pd.to_datetime(ms, unit="ms", utc=True).date()

def to_date_from_seconds(sec: int) -> datetime.date:
    return pd.to_datetime(sec, unit="s", utc=True).date()

def winsorize_series(s: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    if s.dropna().empty:
        return s
    lo, hi = s.quantile(lower), s.quantile(upper)
    return s.clip(lo, hi)

def rolling_zscore(s: pd.Series, window: int = 90, min_periods: int = 30) -> pd.Series:
    mu = s.rolling(window, min_periods=min_periods).mean()
    sd = s.rolling(window, min_periods=min_periods).std()
    return ((s - mu) / sd.replace(0, np.nan)).replace([np.inf, -np.inf], np.nan)

def latest_nonnull(series: pd.Series, fallback: Optional[float] = None) -> Optional[float]:
    x = series.dropna()
    if x.empty:
        return fallback
    return float(x.iloc[-1])

def safe_quantile(series: pd.Series, q: float, fallback: float) -> float:
    x = series.dropna()
    if x.empty:
        return fallback
    return float(x.quantile(q))

def percentile_rank(series: pd.Series, value: float) -> float:
    x = series.dropna()
    if x.empty or pd.isna(value):
        return np.nan
    return float((x <= value).mean())

def mean_existing(df: pd.DataFrame, cols: List[str]) -> pd.Series:
    use_cols = [c for c in cols if c in df.columns]
    if not use_cols:
        return pd.Series(np.nan, index=df.index)
    return df[use_cols].mean(axis=1, skipna=True)

def infer_hashrate_to_ehs(s: pd.Series) -> pd.Series:
    """
    自动推断 hashrate 单位并统一为 EH/s。

    常见情况：
        - Blockchain.com hash-rate: TH/s，当前 BTC 约 900,000,000 TH/s，除以 1e6 得 EH/s。
        - Coin Metrics HashRate 可能是 H/s，当前 BTC 约 9e20 H/s，除以 1e18 得 EH/s。
        - 个别数据源可能直接是 EH/s。
    """
    x = pd.to_numeric(s, errors="coerce")
    med = x.dropna().median()
    if pd.isna(med):
        return x
    if med > 1e17:      # H/s
        return x / 1e18
    if med > 1e6:       # TH/s
        return x / 1e6
    if med > 10:        # 已经很可能是 EH/s
        return x
    return x

def parse_money_to_usd(x: Any, default_multiplier: Optional[float] = None) -> Optional[float]:
    """
    解析金额字段，尽量避免 ETF 单位误读。

    参数：
        default_multiplier:
            如果表头明确显示 US$m / USDm，可传 1_000_000。
            如果表头明确显示 US$bn / USDb，可传 1_000_000_000。
            如果无法确认，且数值没有 m/b 后缀，则返回 NaN，避免把 100.9 错当成 100.9 美元。
    """
    if pd.isna(x):
        return np.nan
    s = str(x).strip().replace(",", "")
    if s in ["", "-", "—", "nan", "None"]:
        return np.nan

    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    if s.startswith("-"):
        neg = True
        s = s[1:]

    # 先处理货币前缀，避免 US$100.9m 被误读。
    s = (
        s.replace("US$", "")
         .replace("USD", "")
         .replace("US", "")
         .replace("$", "")
         .strip()
    )
    lower = s.lower().strip()

    multiplier = default_multiplier
    # 显式单位优先。
    if lower.endswith("bn"):
        multiplier = 1_000_000_000.0
        lower = lower[:-2]
    elif lower.endswith("b"):
        multiplier = 1_000_000_000.0
        lower = lower[:-1]
    elif lower.endswith("mn"):
        multiplier = 1_000_000.0
        lower = lower[:-2]
    elif lower.endswith("m"):
        multiplier = 1_000_000.0
        lower = lower[:-1]

    # 无显式或默认单位时不入模。
    if multiplier is None:
        return np.nan

    try:
        val = float(lower) * multiplier
        return -val if neg else val
    except Exception:
        return np.nan
