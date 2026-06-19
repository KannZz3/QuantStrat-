from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import requests

from .config import ModelConfig
from .health import SourceHealthTracker
from .utils import (
    ensure_dir, infer_hashrate_to_ehs, parse_money_to_usd, safe_get_json, safe_read_html,
    today_utc_date, to_date_from_ms, to_date_from_seconds,
)


class DataFetcher:
    """自动抓取免费公开数据。"""

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg
        self.headers = {"User-Agent": cfg.user_agent}
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.health = SourceHealthTracker()
        # GDELT 全局限速状态。
        self._last_gdelt_request_ts = 0.0

    def get_source_health(self) -> Dict[str, Any]:
        return self.health.as_dict()

    def _warn(self, source: str, message: str) -> None:
        self.health.issue(source, message)
        print(f"[WARN] {message}")

    def _safe_get_json(self, url: str, params: Optional[dict] = None, max_retries: Optional[int] = None) -> dict:
        return safe_get_json(
            url,
            params=params,
            headers=self.headers,
            timeout=self.cfg.request_timeout,
            max_retries=max_retries or self.cfg.max_request_retries,
            sleep_seconds=self.cfg.sleep_seconds,
            non_retryable_status_codes=self.cfg.non_retryable_status_codes,
            session=self.session,
        )

    def _record_fetch_health(self, source: str, df: pd.DataFrame, started_at: float, reason: Optional[str] = None) -> None:
        self.health.record(source, df, elapsed_seconds=time.time() - started_at, reason=reason)

    def _fetch_one(self, key: str, label: str, fn) -> Tuple[str, pd.DataFrame]:
        print(f"[INFO] {label}")
        started_at = time.time()
        try:
            df = fn()
            if df is None:
                df = pd.DataFrame(columns=["date"])
            self._record_fetch_health(key, df, started_at)
        except Exception as e:
            self._warn(key, f"{label} failed with unhandled error: {e}")
            df = pd.DataFrame(columns=["date"])
            self.health.record(key, df, elapsed_seconds=time.time() - started_at, reason=str(e), status="failed")
        return key, df

    def _fetch_group(self, tasks: List[Tuple[str, str, Any]]) -> Dict[str, pd.DataFrame]:
        if not tasks:
            return {}
        if not self.cfg.parallel_fetch or len(tasks) == 1:
            out: Dict[str, pd.DataFrame] = {}
            for key, label, fn in tasks:
                k, df = self._fetch_one(key, label, fn)
                out[k] = df
                time.sleep(self.cfg.sleep_seconds)
            return out

        out: Dict[str, pd.DataFrame] = {}
        max_workers = max(1, min(int(self.cfg.fetch_max_workers), len(tasks)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_map = {
                executor.submit(self._fetch_one, key, label, fn): key
                for key, label, fn in tasks
            }
            for future in as_completed(future_map):
                key, df = future.result()
                out[key] = df
        return out

    # --------------------------------------------------------
    # 2.1 BTC 价格主源：CoinGecko
    # --------------------------------------------------------
    def fetch_coingecko_price(self) -> pd.DataFrame:
        """
        BTC 价格主源：CoinGecko。

        主价格源失败时不直接中断流程，而是返回空表；
        后续由价格交叉验证决定是否输出 strict valuation。
        """
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {"vs_currency": "usd", "days": str(self.cfg.days), "interval": "daily"}
        try:
            js = self._safe_get_json(url, params=params)
            price = pd.DataFrame(js.get("prices", []), columns=["timestamp_ms", "btc_price_coingecko"])
            mcap = pd.DataFrame(js.get("market_caps", []), columns=["timestamp_ms", "btc_market_cap"])
            vol = pd.DataFrame(js.get("total_volumes", []), columns=["timestamp_ms", "btc_volume_coingecko"])
            if price.empty:
                return pd.DataFrame(columns=["date", "btc_price_coingecko", "btc_market_cap", "btc_volume_coingecko"])
            df = price.merge(mcap, on="timestamp_ms", how="outer").merge(vol, on="timestamp_ms", how="outer")
            df["date"] = df["timestamp_ms"].apply(to_date_from_ms)
            return df.drop(columns=["timestamp_ms"]).drop_duplicates("date").sort_values("date")
        except Exception as e:
            self._warn("price_coingecko", f"CoinGecko price fetch failed: {e}")
            return pd.DataFrame(columns=["date", "btc_price_coingecko", "btc_market_cap", "btc_volume_coingecko"])

    # --------------------------------------------------------
    # 2.2 BTC 价格验证源：CoinCap 免费 API
    # --------------------------------------------------------
    def fetch_coincap_price(self) -> pd.DataFrame:
        """CoinCap 免费历史价格，用于价格交叉验证。"""
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 2)
        start_ms = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int(datetime(end.year, end.month, end.day, tzinfo=timezone.utc).timestamp() * 1000)
        url = "https://api.coincap.io/v2/assets/bitcoin/history"
        params = {"interval": "d1", "start": start_ms, "end": end_ms}
        try:
            js = self._safe_get_json(url, params=params)
        except Exception as e:
            self._warn("price_coincap", f"CoinCap price fetch failed: {e}")
            return pd.DataFrame(columns=["date", "btc_price_coincap"])
        raw = pd.DataFrame(js.get("data", []))
        if raw.empty:
            return pd.DataFrame(columns=["date", "btc_price_coincap"])
        raw["date"] = pd.to_datetime(raw["time"], unit="ms", utc=True).dt.date
        raw["btc_price_coincap"] = pd.to_numeric(raw["priceUsd"], errors="coerce")
        return raw[["date", "btc_price_coincap"]].drop_duplicates("date").sort_values("date")

    # --------------------------------------------------------
    # 2.3 BTC 价格第二验证源：Binance public klines
    # --------------------------------------------------------
    def fetch_binance_price(self) -> pd.DataFrame:
        """
        Binance 公共 Kline 日线，作为 CoinCap 失败时的价格验证源。
        注意：使用 BTCUSDT 近似 BTC/USD，主要用于和 CoinGecko 做价格交叉验证。
        """
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 2)
        start_ms = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp() * 1000)
        end_ms = int((datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)).timestamp() * 1000)
        url = "https://api.binance.com/api/v3/klines"
        params = {"symbol": "BTCUSDT", "interval": "1d", "startTime": start_ms, "endTime": end_ms, "limit": 1000}
        try:
            js = self._safe_get_json(url, params=params)
        except Exception as e:
            self._warn("price_binance", f"Binance price fetch failed: {e}")
            return pd.DataFrame(columns=["date", "btc_price_binance"])
        rows = []
        for row in js:
            try:
                rows.append({
                    "date": pd.to_datetime(int(row[0]), unit="ms", utc=True).date(),
                    "btc_price_binance": float(row[4]),  # close price
                })
            except Exception:
                continue
        return pd.DataFrame(rows).drop_duplicates("date").sort_values("date") if rows else pd.DataFrame(columns=["date", "btc_price_binance"])


    # --------------------------------------------------------
    # 2.4 BTC 价格备用验证源：Coinbase Exchange candles
    # --------------------------------------------------------
    def fetch_coinbase_price(self) -> pd.DataFrame:
        """
        Coinbase Exchange 公共 BTC-USD 日线，作为价格交叉验证备用源。
        返回 close price。若 API 不可用，返回空表，不中断 pipeline。
        """
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 2)
        url = "https://api.exchange.coinbase.com/products/BTC-USD/candles"
        params = {
            "granularity": 86400,
            "start": datetime(start.year, start.month, start.day, tzinfo=timezone.utc).isoformat(),
            "end": (datetime(end.year, end.month, end.day, tzinfo=timezone.utc) + timedelta(days=1)).isoformat(),
        }
        try:
            js = self._safe_get_json(url, params=params)
        except Exception as e:
            self._warn("price_coinbase", f"Coinbase price fetch failed: {e}")
            return pd.DataFrame(columns=["date", "btc_price_coinbase"])
        rows = []
        for row in js if isinstance(js, list) else []:
            try:
                # Coinbase candles: [time, low, high, open, close, volume]
                rows.append({
                    "date": pd.to_datetime(int(row[0]), unit="s", utc=True).date(),
                    "btc_price_coinbase": float(row[4]),
                })
            except Exception:
                continue
        return pd.DataFrame(rows).drop_duplicates("date").sort_values("date") if rows else pd.DataFrame(columns=["date", "btc_price_coinbase"])

    # --------------------------------------------------------
    # 2.5 BTC 价格备用验证源：Kraken OHLC
    # --------------------------------------------------------
    def fetch_kraken_price(self) -> pd.DataFrame:
        """
        Kraken 公共 BTC/USD 日线，作为价格交叉验证备用源。
        返回 close price。若 API 不可用，返回空表，不中断 pipeline。
        """
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 2)
        since = int(datetime(start.year, start.month, start.day, tzinfo=timezone.utc).timestamp())
        url = "https://api.kraken.com/0/public/OHLC"
        params = {"pair": "XBTUSD", "interval": 1440, "since": since}
        try:
            js = self._safe_get_json(url, params=params)
        except Exception as e:
            self._warn("price_kraken", f"Kraken price fetch failed: {e}")
            return pd.DataFrame(columns=["date", "btc_price_kraken"])
        if js.get("error"):
            self._warn("price_kraken", f"Kraken price fetch returned error: {js.get('error')}")
            return pd.DataFrame(columns=["date", "btc_price_kraken"])
        result = js.get("result", {})
        rows = []
        for key, values in result.items():
            if key == "last":
                continue
            for row in values:
                try:
                    # Kraken OHLC: [time, open, high, low, close, vwap, volume, count]
                    rows.append({
                        "date": pd.to_datetime(int(row[0]), unit="s", utc=True).date(),
                        "btc_price_kraken": float(row[4]),
                    })
                except Exception:
                    continue
        return pd.DataFrame(rows).drop_duplicates("date").sort_values("date") if rows else pd.DataFrame(columns=["date", "btc_price_kraken"])


    # --------------------------------------------------------
    # 2.6 BTC 价格备用验证源：Yahoo Finance chart API
    # --------------------------------------------------------
    def fetch_yahoo_price(self) -> pd.DataFrame:
        """
        Yahoo Finance BTC-USD 日线，作为全自动价格交叉验证源。
        不需要手工输入，不需要 API key；失败时返回空表，不中断 pipeline。
        """
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"
        params = {"range": f"{self.cfg.days + 5}d", "interval": "1d"}
        try:
            js = self._safe_get_json(url, params=params)
            result = js.get("chart", {}).get("result", [])
            if not result:
                return pd.DataFrame(columns=["date", "btc_price_yahoo"])
            r0 = result[0]
            ts = r0.get("timestamp", [])
            quote = r0.get("indicators", {}).get("quote", [{}])[0]
            close = quote.get("close", [])
            rows = []
            for t, c in zip(ts, close):
                if c is None:
                    continue
                rows.append({
                    "date": pd.to_datetime(int(t), unit="s", utc=True).date(),
                    "btc_price_yahoo": float(c),
                })
            return pd.DataFrame(rows).drop_duplicates("date").sort_values("date") if rows else pd.DataFrame(columns=["date", "btc_price_yahoo"])
        except Exception as e:
            self._warn("price_yahoo", f"Yahoo Finance price fetch failed: {e}")
            return pd.DataFrame(columns=["date", "btc_price_yahoo"])

    # --------------------------------------------------------
    # 2.6b BTC 价格备用验证源：CryptoCompare histoday
    # --------------------------------------------------------
    def fetch_cryptocompare_price(self) -> pd.DataFrame:
        """
        CryptoCompare BTC/USD histoday 日线，作为全自动价格交叉验证源。
        不需要手工输入；免费接口可能限流，失败时返回空表。
        """
        url = "https://min-api.cryptocompare.com/data/v2/histoday"
        params = {"fsym": "BTC", "tsym": "USD", "limit": int(self.cfg.days + 5)}
        api_key = self.cfg.cryptocompare_api_key or os.environ.get("CRYPTOCOMPARE_API_KEY")
        if api_key:
            params["api_key"] = api_key
        try:
            js = self._safe_get_json(url, params=params)
            raw = pd.DataFrame(js.get("Data", {}).get("Data", []))
            if raw.empty:
                return pd.DataFrame(columns=["date", "btc_price_cryptocompare"])
            raw["date"] = pd.to_datetime(raw["time"], unit="s", utc=True).dt.date
            raw["btc_price_cryptocompare"] = pd.to_numeric(raw["close"], errors="coerce")
            return raw[["date", "btc_price_cryptocompare"]].drop_duplicates("date").sort_values("date")
        except Exception as e:
            self._warn("price_cryptocompare", f"CryptoCompare price fetch failed: {e}")
            return pd.DataFrame(columns=["date", "btc_price_cryptocompare"])

    # --------------------------------------------------------
    # 2.7 Blockchain.com charts
    # --------------------------------------------------------
    def fetch_blockchain_chart(self, chart_name: str, value_name: str) -> pd.DataFrame:
        url = f"https://api.blockchain.info/charts/{chart_name}"
        params = {"timespan": f"{self.cfg.days}days", "format": "json"}
        js = self._safe_get_json(url, params=params)
        df = pd.DataFrame(js.get("values", []))
        if df.empty:
            return pd.DataFrame(columns=["date", value_name])
        df["date"] = df["x"].apply(to_date_from_seconds)
        df[value_name] = pd.to_numeric(df["y"], errors="coerce")
        return df[["date", value_name]].drop_duplicates("date").sort_values("date")

    def fetch_blockchain_onchain(self) -> pd.DataFrame:
        charts = [
            ("hash-rate", "hashrate_raw_blockchain"),
            ("n-unique-addresses", "active_addresses_blockchain"),
            ("n-transactions", "transaction_count_blockchain"),
            ("estimated-transaction-volume-usd", "transfer_volume_usd_blockchain"),
            # Biais transaction benefit 主口径；BTC 口径仅作同源诊断。
            ("estimated-transaction-volume", "transfer_volume_btc_blockchain"),
            # 平均手续费 best-effort；总手续费可用于构造备用口径。
            ("fees-usd-per-transaction", "avg_fee_usd_blockchain"),
            ("transaction-fees-usd", "total_fee_usd_blockchain"),
            ("transaction-fees", "total_fee_btc_blockchain"),
        ]
        out = None
        for chart, name in charts:
            try:
                df = self.fetch_blockchain_chart(chart, name)
                time.sleep(self.cfg.sleep_seconds)
            except Exception as e:
                self._warn("blockchain_onchain", f"Blockchain chart failed: {chart}: {e}")
                df = pd.DataFrame(columns=["date", name])
            out = df if out is None else out.merge(df, on="date", how="outer")
        if out is None:
            return pd.DataFrame(columns=["date"])
        if "hashrate_raw_blockchain" in out.columns:
            out["hashrate_ehs_blockchain"] = infer_hashrate_to_ehs(out["hashrate_raw_blockchain"])
        return out.sort_values("date")

    # --------------------------------------------------------
    # 2.9 Coin Metrics Community API：链上交叉验证源
    # --------------------------------------------------------
    def fetch_coinmetrics_metrics(self) -> pd.DataFrame:
        """逐项抓取 Coin Metrics；单项失败不终止流程。"""
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 5)
        metric_map = {
            "HashRate": "hashrate_raw_coinmetrics",
            "AdrActCnt": "active_addresses_coinmetrics",
            "TxCnt": "transaction_count_coinmetrics",
            "TxTfrValAdjUSD": "transfer_volume_usd_coinmetrics",
            "FeeMeanUSD": "avg_fee_usd_coinmetrics",
            "FeeTotUSD": "total_fee_usd_coinmetrics",
        }
        url = "https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
        out = None
        for metric, dst in metric_map.items():
            params = {
                "assets": "btc",
                "metrics": metric,
                "frequency": "1d",
                "start_time": str(start),
                "end_time": str(end),
            }
            try:
                js = self._safe_get_json(url, params=params)
                raw = pd.DataFrame(js.get("data", []))
            except Exception as e:
                self._warn("coinmetrics", f"Coin Metrics metric fetch failed: {metric}: {e}")
                continue
            if raw.empty or metric not in raw.columns:
                self._warn("coinmetrics", f"Coin Metrics metric unavailable or empty: {metric}")
                continue
            raw["date"] = pd.to_datetime(raw["time"], utc=True).dt.date
            raw[dst] = pd.to_numeric(raw[metric], errors="coerce")
            tmp = raw[["date", dst]].drop_duplicates("date").sort_values("date")
            out = tmp if out is None else out.merge(tmp, on="date", how="outer")
            time.sleep(self.cfg.sleep_seconds)
        if out is None:
            return pd.DataFrame(columns=["date"])
        if "hashrate_raw_coinmetrics" in out.columns:
            out["hashrate_ehs_coinmetrics"] = infer_hashrate_to_ehs(out["hashrate_raw_coinmetrics"])
        return out.sort_values("date")

    # --------------------------------------------------------
    # 2.10 Blockchair charts：Biais 独立自动验证候选源
    # --------------------------------------------------------
    @staticmethod
    def _parse_flexible_chart_json(js: Any, value_col: str) -> pd.DataFrame:
        """宽松解析 chart JSON，兼容 list / dict / nested data / date-value map。"""
        rows = []

        def add_row(d, v):
            try:
                dd = DataFetcher._parse_gdelt_date(d)
                vv = pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]
                if dd is not None and pd.notna(vv):
                    rows.append({"date": dd, value_col: float(vv)})
            except Exception:
                pass

        def walk(obj):
            if isinstance(obj, dict):
                # 常见：{"YYYY-MM-DD": value}
                date_like_keys = 0
                for k, v in obj.items():
                    if DataFetcher._parse_gdelt_date(k) is not None and not isinstance(v, (dict, list)):
                        add_row(k, v)
                        date_like_keys += 1
                if date_like_keys:
                    return

                d = None
                v = None
                for dk in ["date", "time", "timestamp", "x", "Date", "datetime"]:
                    if dk in obj:
                        d = obj.get(dk)
                        break
                for vk in ["value", "y", "count", "volume", "amount", "fee", "fees", "avg", "average", "Value"]:
                    if vk in obj:
                        v = obj.get(vk)
                        break
                if d is not None and v is not None:
                    add_row(d, v)
                    return
                for v2 in obj.values():
                    if isinstance(v2, (dict, list)):
                        walk(v2)
            elif isinstance(obj, list):
                # 常见：[[date, value], ...]
                if len(obj) >= 2 and not isinstance(obj[0], (dict, list)):
                    add_row(obj[0], obj[1])
                else:
                    for it in obj:
                        walk(it)

        walk(js)
        if not rows:
            return pd.DataFrame(columns=["date", value_col])
        return pd.DataFrame(rows).groupby("date", as_index=False)[value_col].mean().sort_values("date")

    @staticmethod
    def _parse_flexible_chart_text(text: str, value_col: str) -> pd.DataFrame:
        """宽松解析 TSV/CSV/chart text；HTML 页面会返回空表。"""
        if not isinstance(text, str) or "<html" in text.lower() or "<!doctype" in text.lower():
            return pd.DataFrame(columns=["date", value_col])
        for sep in ["\t", ",", ";"]:
            try:
                df = pd.read_csv(StringIO(text), sep=sep, comment="#")
            except Exception:
                continue
            if df is None or df.empty or len(df.columns) < 2:
                continue
            date_col = None
            for c in df.columns:
                cc = str(c).lower()
                if "date" in cc or "time" in cc:
                    date_col = c
                    break
            if date_col is None:
                date_col = df.columns[0]
            num_cols = [c for c in df.columns if c != date_col and pd.to_numeric(df[c], errors="coerce").notna().sum() > 0]
            if not num_cols:
                continue
            value_src = num_cols[-1]
            out = pd.DataFrame({
                "date": df[date_col].apply(DataFetcher._parse_gdelt_date),
                value_col: pd.to_numeric(df[value_src], errors="coerce"),
            }).dropna(subset=["date"])
            if not out.empty:
                return out.groupby("date", as_index=False)[value_col].mean().sort_values("date")
        return pd.DataFrame(columns=["date", value_col])

    def fetch_blockchair_chart(self, chart_slug: str, value_col: str) -> pd.DataFrame:
        """
        Blockchair chart 自动源。
        说明：Blockchair 可能受限或变更格式；本函数只作 best-effort。
        若失败，返回空表，不中断 pipeline。
        """
        candidates = [
            (f"https://api.blockchair.com/bitcoin/charts/{chart_slug}", {"format": "json"}, "json"),
            (f"https://api.blockchair.com/bitcoin/charts/{chart_slug}", None, "json"),
            (f"https://blockchair.com/bitcoin/charts/{chart_slug}.tsv", None, "text"),
            (f"https://blockchair.com/bitcoin/charts/{chart_slug}", {"format": "tsv"}, "text"),
            (f"https://blockchair.com/bitcoin/charts/{chart_slug}", {"download": "tsv"}, "text"),
        ]
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 5)
        last_err = None
        for url, params, mode in candidates:
            try:
                r = self.session.get(url, params=params, headers=self.headers, timeout=self.cfg.request_timeout)
                if r.status_code in self.cfg.non_retryable_status_codes:
                    r.raise_for_status()
                r.raise_for_status()
                if mode == "json":
                    try:
                        df = self._parse_flexible_chart_json(r.json(), value_col)
                    except Exception:
                        df = self._parse_flexible_chart_text(r.text, value_col)
                else:
                    df = self._parse_flexible_chart_text(r.text, value_col)
                if not df.empty:
                    df = df[(df["date"] >= start) & (df["date"] <= end)].copy()
                    if not df.empty:
                        return df[["date", value_col]].drop_duplicates("date").sort_values("date")
            except Exception as e:
                last_err = e
                continue
        if last_err is not None:
            self._warn("blockchair_biais", f"Blockchair chart fetch failed: {chart_slug}: {last_err}")
        return pd.DataFrame(columns=["date", value_col])

    def fetch_blockchair_biais_sources(self) -> pd.DataFrame:
        """Blockchair 独立候选源，用于 Biais transfer volume / fee validation。"""
        chart_map = [
            ("transaction-volume-usd", "transfer_volume_usd_blockchair"),
            ("average-transaction-fee-usd", "avg_fee_usd_blockchair"),
            # Blockchair total fees / tx count 可作为相对 Blockchain.com 的独立 fee 候选。
            ("total-transaction-fees-usd", "total_fee_usd_blockchair"),
            ("transaction-count", "transaction_count_blockchair"),
        ]
        out = None
        for slug, col in chart_map:
            df = self.fetch_blockchair_chart(slug, col)
            time.sleep(self.cfg.sleep_seconds)
            out = df if out is None else out.merge(df, on="date", how="outer")
        return out.sort_values("date") if out is not None else pd.DataFrame(columns=["date"])

    # --------------------------------------------------------
    # 2.11 mempool.space historical fee proxy：Biais fee 独立候选源
    # --------------------------------------------------------
    def _parse_mempool_series_json(self, js: Any, value_col: str) -> pd.DataFrame:
        """宽松解析 mempool.space historical mining/fee series。"""
        rows = []

        def add(d, v):
            try:
                if isinstance(d, (int, float)) and d > 10_000_000_000:
                    dd = pd.to_datetime(int(d), unit="ms", utc=True).date()
                elif isinstance(d, (int, float)) and d > 1_000_000_000:
                    dd = pd.to_datetime(int(d), unit="s", utc=True).date()
                else:
                    dd = DataFetcher._parse_gdelt_date(d)
                vv = pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]
                if dd is not None and pd.notna(vv):
                    rows.append({"date": dd, value_col: float(vv)})
            except Exception:
                pass

        def walk(obj):
            if isinstance(obj, list):
                if len(obj) >= 2 and not isinstance(obj[0], (dict, list)):
                    add(obj[0], obj[1])
                else:
                    for it in obj:
                        walk(it)
            elif isinstance(obj, dict):
                d = None
                v = None
                for dk in ["date", "time", "timestamp", "x"]:
                    if dk in obj:
                        d = obj.get(dk)
                        break
                # 常见候选字段：avgFees / fees / totalFees / value / y
                for vk in ["avgFees", "averageFees", "fees", "totalFees", "total_fees", "value", "y"]:
                    if vk in obj:
                        v = obj.get(vk)
                        break
                if d is not None and v is not None:
                    add(d, v)
                    return
                for v2 in obj.values():
                    if isinstance(v2, (dict, list)):
                        walk(v2)

        walk(js)
        if not rows:
            return pd.DataFrame(columns=["date", value_col])
        return pd.DataFrame(rows).groupby("date", as_index=False)[value_col].mean().sort_values("date")

    def fetch_mempool_historical_fee_proxy(self) -> pd.DataFrame:
        """
        mempool.space historical fee proxy。
        仅用于 fee validation 的独立候选源，不用于 transfer volume。
        """
        periods = ["6m", "3m", "1m"]
        url_template = "https://mempool.space/api/v1/mining/blocks/fees/{period}"
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 5)
        last_err = None
        for period in periods:
            try:
                js = self._safe_get_json(url_template.format(period=period), max_retries=2)
                df = self._parse_mempool_series_json(js, "avg_fee_usd_mempool_proxy")
                if not df.empty:
                    df = df[(df["date"] >= start) & (df["date"] <= end)].copy()
                    if not df.empty:
                        return df[["date", "avg_fee_usd_mempool_proxy"]].drop_duplicates("date").sort_values("date")
            except Exception as e:
                last_err = e
                continue
        if last_err is not None:
            self._warn("mempool_fee_history", f"mempool historical fee proxy fetch failed: {last_err}")
        return pd.DataFrame(columns=["date", "avg_fee_usd_mempool_proxy"])

    # --------------------------------------------------------
    # 2.12 mempool.space 当前手续费：只作 latest sanity check
    # --------------------------------------------------------
    def fetch_mempool_current_fee(self) -> pd.DataFrame:
        url = "https://mempool.space/api/v1/fees/recommended"
        try:
            js = self._safe_get_json(url)
        except Exception as e:
            self._warn("mempool_fee_current", f"mempool fee fetch failed: {e}")
            return pd.DataFrame(columns=["date"])
        row = {
            "date": today_utc_date(),
            "fee_fastest_sat_vb_mempool": js.get("fastestFee"),
            "fee_halfhour_sat_vb_mempool": js.get("halfHourFee"),
            "fee_hour_sat_vb_mempool": js.get("hourFee"),
            "fee_economy_sat_vb_mempool": js.get("economyFee"),
            "fee_minimum_sat_vb_mempool": js.get("minimumFee"),
        }
        return pd.DataFrame([row])

    # --------------------------------------------------------
    # 2.13 Wikipedia Pageviews：attention 辅助源
    # --------------------------------------------------------
    def fetch_wikipedia_pageviews(self, article: str) -> pd.DataFrame:
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 2)
        start_str = start.strftime("%Y%m%d") + "00"
        end_str = end.strftime("%Y%m%d") + "00"
        article_enc = article.replace(" ", "_")
        url = (
            "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
            f"en.wikipedia/all-access/user/{article_enc}/daily/{start_str}/{end_str}"
        )
        try:
            js = self._safe_get_json(url)
        except Exception as e:
            self._warn("wikipedia", f"Wikipedia pageviews failed for {article}: {e}")
            return pd.DataFrame(columns=["date", f"wiki_views_{article_enc.lower()}"])
        df = pd.DataFrame(js.get("items", []))
        if df.empty:
            return pd.DataFrame(columns=["date", f"wiki_views_{article_enc.lower()}"])
        df["date"] = pd.to_datetime(df["timestamp"].str[:8], format="%Y%m%d").dt.date
        col = f"wiki_views_{article_enc.lower()}"
        df[col] = pd.to_numeric(df["views"], errors="coerce")
        return df[["date", col]].drop_duplicates("date").sort_values("date")

    def fetch_attention_wikipedia(self) -> pd.DataFrame:
        articles = ["Bitcoin", "Cryptocurrency bubble", "Bitcoin scalability problem"]
        out = None
        for a in articles:
            df = self.fetch_wikipedia_pageviews(a)
            time.sleep(self.cfg.sleep_seconds)
            out = df if out is None else out.merge(df, on="date", how="outer")
        return out if out is not None else pd.DataFrame(columns=["date"])


    # --------------------------------------------------------
    # 2.14 GDELT DOC API：自动 attention / negative attention 新闻量源
    # --------------------------------------------------------
    @staticmethod
    def _parse_gdelt_date(x) -> Optional[datetime.date]:
        """尽量兼容 GDELT timeline 返回的多种日期格式。"""
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return None
        try:
            s = str(x).strip()
            # 常见：YYYYMMDDHHMMSS / YYYYMMDD
            digits = re.sub(r"\D", "", s)
            if len(digits) >= 8:
                return pd.to_datetime(digits[:8], format="%Y%m%d", errors="coerce").date()
            dt = pd.to_datetime(s, utc=True, errors="coerce")
            if pd.isna(dt):
                return None
            return dt.date()
        except Exception:
            return None

    @staticmethod
    def _parse_gdelt_timeline_json(js: dict, value_col: str) -> pd.DataFrame:
        """
        解析 GDELT DOC timelinevolraw JSON。
        GDELT 返回结构可能随 mode/format 有差异，因此这里做宽松兼容：
            - {"timeline": [{"data": [{"date": ..., "value": ...}, ...]}]}
            - {"timeline": [{"data": [[date, value], ...]}]}
            - {"data": [{...}]}
        """
        rows = []

        def add_point(point):
            d = None
            v = None
            if isinstance(point, dict):
                for dk in ["date", "datetime", "time", "timestamp", "Date"]:
                    if dk in point:
                        d = DataFetcher._parse_gdelt_date(point.get(dk))
                        break
                for vk in ["value", "count", "articles", "Article Count", "Volume Intensity", "Value"]:
                    if vk in point:
                        v = point.get(vk)
                        break
                if v is None:
                    # 兜底：找第一个可转 numeric 的非日期字段。
                    for k, val in point.items():
                        if k.lower() in ["date", "datetime", "time", "timestamp"]:
                            continue
                        vv = pd.to_numeric(pd.Series([val]), errors="coerce").iloc[0]
                        if pd.notna(vv):
                            v = vv
                            break
            elif isinstance(point, (list, tuple)) and len(point) >= 2:
                d = DataFetcher._parse_gdelt_date(point[0])
                v = point[1]
            if d is not None:
                vv = pd.to_numeric(pd.Series([v]), errors="coerce").iloc[0]
                if pd.notna(vv):
                    rows.append({"date": d, value_col: float(vv)})

        containers = []
        if isinstance(js, dict):
            for key in ["timeline", "data", "results"]:
                if key in js:
                    val = js.get(key)
                    if isinstance(val, list):
                        containers.extend(val)
                    elif isinstance(val, dict):
                        containers.append(val)
        elif isinstance(js, list):
            containers = js

        for item in containers:
            if isinstance(item, dict) and isinstance(item.get("data"), list):
                for pnt in item.get("data", []):
                    add_point(pnt)
            elif isinstance(item, dict) and isinstance(item.get("timeline"), list):
                for pnt in item.get("timeline", []):
                    add_point(pnt)
            else:
                add_point(item)

        if not rows:
            return pd.DataFrame(columns=["date", value_col])
        return pd.DataFrame(rows).groupby("date", as_index=False)[value_col].sum().sort_values("date")

    @staticmethod
    def _parse_gdelt_timeline_csv(text: str, value_col: str) -> pd.DataFrame:
        """JSON 解析失败时的 CSV 兜底解析。"""
        try:
            df = pd.read_csv(StringIO(text))
        except Exception:
            return pd.DataFrame(columns=["date", value_col])
        if df.empty:
            return pd.DataFrame(columns=["date", value_col])
        cols = list(df.columns)
        date_col = None
        for c in cols:
            if "date" in str(c).lower() or "time" in str(c).lower():
                date_col = c
                break
        if date_col is None:
            date_col = cols[0]
        value_col_src = None
        for c in cols:
            cl = str(c).lower()
            if c == date_col:
                continue
            if any(k in cl for k in ["value", "count", "volume", "article"]):
                value_col_src = c
                break
        if value_col_src is None:
            numeric_cols = [c for c in cols if c != date_col and pd.to_numeric(df[c], errors="coerce").notna().sum() > 0]
            if not numeric_cols:
                return pd.DataFrame(columns=["date", value_col])
            value_col_src = numeric_cols[-1]
        out = pd.DataFrame({
            "date": df[date_col].apply(DataFetcher._parse_gdelt_date),
            value_col: pd.to_numeric(df[value_col_src], errors="coerce"),
        }).dropna(subset=["date"])
        if out.empty:
            return pd.DataFrame(columns=["date", value_col])
        return out.groupby("date", as_index=False)[value_col].sum().sort_values("date")

    def _gdelt_cache_path(self, value_col: str) -> str:
        """GDELT 自动抓取结果缓存路径；仅新鲜缓存可作为本轮输入。"""
        cache_dir = os.path.join(getattr(self.cfg, "cache_dir", "./btc_model_cache"), "gdelt_cache")
        ensure_dir(cache_dir)
        safe_col = re.sub(r"[^A-Za-z0-9_\-]+", "_", value_col)
        return os.path.join(cache_dir, f"{safe_col}_{self.cfg.days}d.csv")

    def _read_fresh_gdelt_cache(self, value_col: str, start: datetime.date, end: datetime.date) -> pd.DataFrame:
        if not getattr(self.cfg, "gdelt_read_fresh_cache", True):
            return pd.DataFrame(columns=["date", value_col])
        path = self._gdelt_cache_path(value_col)
        if not os.path.exists(path):
            return pd.DataFrame(columns=["date", value_col])
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path), tz=timezone.utc).date()
            stale_days = (today_utc_date() - mtime).days
            if stale_days > int(getattr(self.cfg, "gdelt_cache_max_stale_days", 1)):
                return pd.DataFrame(columns=["date", value_col])
            df = pd.read_csv(path)
            if "date" not in df.columns or value_col not in df.columns:
                return pd.DataFrame(columns=["date", value_col])
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
            df[value_col] = pd.to_numeric(df[value_col], errors="coerce")
            df = df[(df["date"] >= start) & (df["date"] <= end)].dropna(subset=["date"])
            if df.empty:
                return pd.DataFrame(columns=["date", value_col])
            self._warn("gdelt_attention", f"GDELT used fresh cache for {value_col}: {path}")
            return self._complete_gdelt_daily_frame(df, value_col, start, end)
        except Exception as e:
            self._warn("gdelt_attention", f"GDELT cache read failed for {value_col}: {e}")
            return pd.DataFrame(columns=["date", value_col])

    def _save_gdelt_cache(self, df: pd.DataFrame, value_col: str) -> None:
        """保存本轮 GDELT 自动抓取结果；后续仅在新鲜窗口内可读。"""
        if df is None or df.empty or "date" not in df.columns or value_col not in df.columns:
            return
        try:
            path = self._gdelt_cache_path(value_col)
            tmp = df[["date", value_col]].drop_duplicates("date").sort_values("date")
            tmp.to_csv(path, index=False)
            print(f"[OK] GDELT cache saved for {value_col}: {path}")
        except Exception as e:
            self._warn("gdelt_attention", f"GDELT cache save failed for {value_col}: {e}")

    def _gdelt_wait_rate_limit(self) -> None:
        """GDELT 全局限速，降低 Too Many Requests 概率。"""
        interval = float(getattr(self.cfg, "gdelt_min_request_interval_seconds", 10.0))
        elapsed = time.time() - self._last_gdelt_request_ts
        if self._last_gdelt_request_ts > 0 and elapsed < interval:
            time.sleep(interval - elapsed)

    def _gdelt_request(self, url: str, params: dict, fmt: str) -> requests.Response:
        """
        GDELT 请求函数。
        - 遇到 429 时先退避，不立即 CSV fallback；
        - 遵守 Retry-After；若没有则使用指数退避；
        - 所有 GDELT 请求共享全局限速。
        """
        request_params = dict(params)
        request_params["format"] = fmt
        backoffs = list(getattr(self.cfg, "gdelt_backoff_seconds", (30, 60, 120)))
        max_attempts = len(backoffs) + 1
        last_err = None
        for attempt in range(max_attempts):
            self._gdelt_wait_rate_limit()
            try:
                r = self.session.get(url, params=request_params, headers=self.headers, timeout=self.cfg.request_timeout)
                self._last_gdelt_request_ts = time.time()
                if r.status_code == 429:
                    retry_after = r.headers.get("Retry-After")
                    if retry_after is not None:
                        try:
                            wait_s = int(float(retry_after))
                        except Exception:
                            wait_s = backoffs[min(attempt, len(backoffs) - 1)] if backoffs else 60
                    else:
                        wait_s = backoffs[min(attempt, len(backoffs) - 1)] if backoffs else 60
                    if attempt < max_attempts - 1:
                        self._warn("gdelt_attention", f"GDELT 429 for format={fmt}; backoff {wait_s}s before retry {attempt + 2}/{max_attempts}.")
                        time.sleep(wait_s)
                        continue
                    raise RuntimeError("GDELT rate limited after retries")
                if r.status_code in self.cfg.non_retryable_status_codes:
                    r.raise_for_status()
                r.raise_for_status()
                return r
            except Exception as e:
                last_err = e
                # 非 429 错误不做长时间退避，交给上层决定是否 CSV fallback。
                if "GDELT rate limited" in str(e):
                    raise
                if attempt < max_attempts - 1 and isinstance(e, requests.exceptions.RequestException):
                    wait_s = min(5 * (attempt + 1), 15)
                    time.sleep(wait_s)
                    continue
                raise RuntimeError(str(last_err))
        raise RuntimeError(str(last_err))

    def _fetch_gdelt_range(self, query: str, value_col: str, start: datetime.date, end: datetime.date) -> Tuple[pd.DataFrame, bool, str]:
        """
        抓取单个 GDELT 时间区间。
        返回：(df, rate_limited, reason)。
        只有非 429 的 JSON 失败才尝试 CSV fallback；429 先退避，退避后仍失败则直接停止。
        """
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        params = {
            "query": query,
            "mode": "timelinevolraw",
            "startdatetime": start.strftime("%Y%m%d000000"),
            "enddatetime": end.strftime("%Y%m%d235959"),
        }
        # 1) JSON 优先。
        try:
            r = self._gdelt_request(url, params, fmt="json")
            js = r.json()
            df = self._parse_gdelt_timeline_json(js, value_col)
            if not df.empty:
                return df, False, "json_pass"
            json_reason = "json_empty"
        except Exception as e:
            if "rate limited" in str(e).lower() or "429" in str(e):
                return pd.DataFrame(columns=["date", value_col]), True, str(e)
            json_reason = str(e)

        # 2) 只有非 429 情况下才 CSV fallback，避免 429 时请求数翻倍。
        try:
            r = self._gdelt_request(url, params, fmt="csv")
            df = self._parse_gdelt_timeline_csv(r.text, value_col)
            if not df.empty:
                return df, False, "csv_pass"
            return pd.DataFrame(columns=["date", value_col]), False, f"json={json_reason}; csv_empty"
        except Exception as e2:
            if "rate limited" in str(e2).lower() or "429" in str(e2):
                return pd.DataFrame(columns=["date", value_col]), True, str(e2)
            return pd.DataFrame(columns=["date", value_col]), False, f"json={json_reason}; csv={e2}"

    def _complete_gdelt_daily_frame(self, df: pd.DataFrame, value_col: str, start: datetime.date, end: datetime.date) -> pd.DataFrame:
        """把 GDELT 返回序列补齐到日频。未返回日期视为新闻量 0；整段失败则上层返回空表。"""
        if df is None or df.empty:
            return pd.DataFrame(columns=["date", value_col])
        out = df.groupby("date", as_index=False)[value_col].sum().sort_values("date")
        dates = pd.date_range(start=start, end=end, freq="D").date
        full = pd.DataFrame({"date": dates})
        full = full.merge(out, on="date", how="left")
        full[value_col] = full[value_col].fillna(0.0)
        return full[["date", value_col]]

    def fetch_gdelt_timeline(self, query: str, value_col: str) -> pd.DataFrame:
        """
        稳定版 GDELT DOC 2.0 timelinevolraw 抓取。
        优化点：
            1. 先读本地新鲜缓存；
            2. 优先一次性抓完整窗口；
            3. 完整窗口失败后才按 90 天分段，最多少量请求；
            4. 全局限速 + 429 指数退避；
            5. 429 时不立即 CSV fallback，避免请求数翻倍。
        """
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days + 2)

        cached = self._read_fresh_gdelt_cache(value_col, start, end)
        if not cached.empty:
            return cached

        # 优先尝试完整窗口。
        full_df, rate_limited, reason = self._fetch_gdelt_range(query, value_col, start, end)
        if rate_limited:
            self._warn("gdelt_attention", f"GDELT rate limited for {value_col} full-window request; stop GDELT fetch. reason={reason}")
            return pd.DataFrame(columns=["date", value_col])
        if not full_df.empty:
            out = self._complete_gdelt_daily_frame(full_df, value_col, start, end)
            self._save_gdelt_cache(out, value_col)
            return out
        self._warn("gdelt_attention", f"GDELT full-window fetch returned empty/failed for {value_col}; fallback to {self.cfg.gdelt_chunk_days}d chunks. reason={reason}")

        # 完整窗口失败后再按 90 天分段。
        rows = []
        cur = start
        chunk_days = int(getattr(self.cfg, "gdelt_chunk_days", 90))
        while cur <= end:
            chunk_end = min(cur + timedelta(days=chunk_days - 1), end)
            chunk_df, rate_limited, reason = self._fetch_gdelt_range(query, value_col, cur, chunk_end)
            if rate_limited:
                self._warn("gdelt_attention", f"GDELT rate limited for {value_col} chunk {cur} to {chunk_end}; stop further chunk requests. reason={reason}")
                # 分段中途限流时不返回部分结果。
                return pd.DataFrame(columns=["date", value_col])
            if not chunk_df.empty:
                rows.append(chunk_df)
            else:
                self._warn("gdelt_attention", f"GDELT chunk empty/failed for {value_col} {cur} to {chunk_end}: {reason}")
            cur = chunk_end + timedelta(days=1)

        if not rows:
            return pd.DataFrame(columns=["date", value_col])
        out = pd.concat(rows, ignore_index=True)
        out = self._complete_gdelt_daily_frame(out, value_col, start, end)
        self._save_gdelt_cache(out, value_col)
        return out

    def fetch_attention_gdelt(self) -> pd.DataFrame:
        """
        GDELT 自动 attention 源。
            ordinary attention = Bitcoin 新闻量；
            negative attention = Bitcoin + crash/hack/regulation/scam/fraud 等负面新闻量。
        """
        ordinary_query = 'Bitcoin'
        negative_query = 'Bitcoin (crash OR hack OR hacked OR regulation OR ban OR banned OR scam OR fraud OR lawsuit OR "money laundering")'
        ordinary = self.fetch_gdelt_timeline(ordinary_query, "gdelt_news_count")
        if ordinary.empty:
            # ordinary 是 negative ratio 分母；不可用时跳过 negative。
            self._warn("gdelt_attention", "GDELT ordinary attention unavailable; skip negative GDELT request for this run.")
            return pd.DataFrame(columns=["date", "gdelt_news_count", "gdelt_negative_news_count"])
        time.sleep(self.cfg.sleep_seconds)
        negative = self.fetch_gdelt_timeline(negative_query, "gdelt_negative_news_count")
        out = ordinary
        out = out.merge(negative, on="date", how="outer") if not negative.empty else out
        return out.drop_duplicates("date").sort_values("date")

    # --------------------------------------------------------
    # 2.15 Google Trends：可选源，原论文更接近该类数据
    # --------------------------------------------------------
    def fetch_google_trends_optional(self) -> pd.DataFrame:
        if not self.cfg.use_pytrends:
            return pd.DataFrame(columns=["date"])
        try:
            from pytrends.request import TrendReq  # type: ignore
        except Exception:
            self._warn("google_trends", "pytrends not installed; skip Google Trends.")
            return pd.DataFrame(columns=["date"])
        try:
            end = today_utc_date()
            start = end - timedelta(days=self.cfg.days)
            timeframe = f"{start} {end}"
            kw_list = ["Bitcoin", "Bitcoin price", "Bitcoin crash", "Bitcoin hack", "Bitcoin regulation"]
            pytrends = TrendReq(hl="en-US", tz=0)
            pytrends.build_payload(kw_list, cat=0, timeframe=timeframe, geo="", gprop="")
            data = pytrends.interest_over_time().reset_index()
            if data.empty:
                return pd.DataFrame(columns=["date"])
            data["date"] = pd.to_datetime(data["date"]).dt.date
            rename = {
                "Bitcoin": "gt_bitcoin",
                "Bitcoin price": "gt_bitcoin_price",
                "Bitcoin crash": "gt_bitcoin_crash",
                "Bitcoin hack": "gt_bitcoin_hack",
                "Bitcoin regulation": "gt_bitcoin_regulation",
            }
            data = data.rename(columns=rename)
            keep = ["date"] + [v for v in rename.values() if v in data.columns]
            return data[keep].drop_duplicates("date").sort_values("date")
        except Exception as e:
            self._warn("google_trends", f"Google Trends fetch failed: {e}")
            return pd.DataFrame(columns=["date"])

    def fetch_manual_google_trends(self) -> pd.DataFrame:
        """
        可选手工 Google Trends CSV；仅作为 diagnostic，不进入 strict Liu validation。
        建议字段：date, gt_bitcoin, gt_bitcoin_price, gt_bitcoin_crash, gt_bitcoin_hack, gt_bitcoin_regulation
        """
        path = self.cfg.manual_google_trends_csv
        if not path or not os.path.exists(path):
            return pd.DataFrame(columns=["date"])
        try:
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"]).dt.date
            return df.drop_duplicates("date").sort_values("date")
        except Exception as e:
            self._warn("google_trends_manual", f"manual Google Trends CSV failed: {e}")
            return pd.DataFrame(columns=["date"])

    # --------------------------------------------------------
    # 2.16 ETF flow：自动 best-effort + manual diagnostic；manual 不得进入 strict
    # --------------------------------------------------------
    def fetch_etf_flows_farside_optional(self) -> pd.DataFrame:
        """
        尝试抓取 Farside BTC ETF flow。
        关键修正：
            - 尝试根据表头识别单位 US$m / US$bn。
            - 如果单位无法确认，裸数字不解析，避免把 100.9 US$m 错成 100.9 USD。
            - Farside 单源只作为 raw source；manual 只作 diagnostic，不能作为 strict validator。
        """
        url = "https://farside.co.uk/btc/"
        try:
            tables = safe_read_html(
                url,
                timeout=self.cfg.request_timeout,
                max_retries=self.cfg.max_request_retries,
                non_retryable_status_codes=self.cfg.non_retryable_status_codes,
                session=self.session,
            )
        except Exception as e:
            self._warn("etf_farside", f"Farside ETF flow auto fetch failed: {e}")
            return pd.DataFrame(columns=["date", "etf_net_flow_usd_farside"])

        for t in tables:
            df = t.copy()
            df.columns = [str(c).strip() for c in df.columns]
            if df.empty:
                continue
            # 尝试识别日期列和 total 列。
            date_col = None
            total_col = None
            for c in df.columns:
                cl = c.lower()
                if date_col is None and ("date" in cl or cl in ["day"]):
                    date_col = c
                if "total" in cl or "net" in cl:
                    total_col = c
            if date_col is None:
                date_col = df.columns[0]
            if total_col is None:
                # Farside 常见最后一列为 Total。
                total_col = df.columns[-1]

            header_text = " ".join([str(c).lower() for c in df.columns])
            default_multiplier = None
            if re.search(r"us\$?\s*m|usd\s*m|\$m|\(m\)", header_text):
                default_multiplier = 1_000_000.0
            elif re.search(r"us\$?\s*b|usd\s*b|\$b|\(b\)", header_text):
                default_multiplier = 1_000_000_000.0

            try:
                out = df[[date_col, total_col]].copy()
                out.columns = ["date", "etf_net_flow_raw"]
                out["date"] = pd.to_datetime(out["date"], errors="coerce").dt.date
                out["etf_net_flow_usd_farside"] = out["etf_net_flow_raw"].apply(
                    lambda x: parse_money_to_usd(x, default_multiplier=default_multiplier)
                )
                out = out.dropna(subset=["date"])
                if out["etf_net_flow_usd_farside"].notna().sum() >= 5:
                    return out[["date", "etf_net_flow_usd_farside"]].drop_duplicates("date").sort_values("date")
            except Exception:
                continue

        return pd.DataFrame(columns=["date", "etf_net_flow_usd_farside"])

    def fetch_manual_etf_flows(self) -> pd.DataFrame:
        """
        可选手工 ETF flow CSV；仅作为 diagnostic，不进入 strict ETF / market-access validation。

        支持字段：
            1. date, etf_net_flow_usd_manual
               表示已经是美元口径。
            2. date, etf_net_flow_usdm_manual
               表示单位是 USD million / US$m，会自动乘以 1,000,000。
            3. 兼容字段：total_net_flow_usd, etf_net_flow_usd, net_flow_usd。

        这样可以避免用户从 Farside / SoSoValue 复制 US$m 裸数字后，
        被误读成普通美元。
        """
        path = self.cfg.manual_etf_csv
        if not path or not os.path.exists(path):
            return pd.DataFrame(columns=["date", "etf_net_flow_usd_manual"])
        try:
            df = pd.read_csv(path)
            df["date"] = pd.to_datetime(df["date"]).dt.date

            if "etf_net_flow_usd_manual" in df.columns:
                df["etf_net_flow_usd_manual"] = pd.to_numeric(df["etf_net_flow_usd_manual"], errors="coerce")
            elif "etf_net_flow_usdm_manual" in df.columns:
                df["etf_net_flow_usd_manual"] = pd.to_numeric(df["etf_net_flow_usdm_manual"], errors="coerce") * 1_000_000.0
            else:
                # 兼容已经明确写明 USD 的字段；这些字段默认视为美元，不做额外单位换算。
                for alt in ["total_net_flow_usd", "etf_net_flow_usd", "net_flow_usd"]:
                    if alt in df.columns:
                        df["etf_net_flow_usd_manual"] = pd.to_numeric(df[alt], errors="coerce")
                        break

            if "etf_net_flow_usd_manual" not in df.columns:
                self._warn("etf_manual", "manual ETF CSV has no supported flow column; expected etf_net_flow_usd_manual or etf_net_flow_usdm_manual.")
                return pd.DataFrame(columns=["date", "etf_net_flow_usd_manual"])

            return df[["date", "etf_net_flow_usd_manual"]].drop_duplicates("date").sort_values("date")
        except Exception as e:
            self._warn("etf_manual", f"manual ETF CSV failed: {e}")
            return pd.DataFrame(columns=["date", "etf_net_flow_usd_manual"])

    # --------------------------------------------------------
    # 2.17 一键抓取全部数据
    # --------------------------------------------------------
    def fetch_all(self) -> Dict[str, pd.DataFrame]:
        data: Dict[str, pd.DataFrame] = {}
        price_tasks = [
            ("price_coingecko", "Fetch CoinGecko price...", self.fetch_coingecko_price),
            ("price_coincap", "Fetch CoinCap price for validation...", self.fetch_coincap_price),
            ("price_binance", "Fetch Binance BTCUSDT price as fallback validation source...", self.fetch_binance_price),
            ("price_coinbase", "Fetch Coinbase BTC-USD price as fallback validation source...", self.fetch_coinbase_price),
            ("price_kraken", "Fetch Kraken XBT/USD price as fallback validation source...", self.fetch_kraken_price),
            ("price_yahoo", "Fetch Yahoo Finance BTC-USD price as fallback validation source...", self.fetch_yahoo_price),
            ("price_cryptocompare", "Fetch CryptoCompare BTC/USD price as fallback validation source...", self.fetch_cryptocompare_price),
        ]
        data.update(self._fetch_group(price_tasks))

        onchain_tasks = [
            ("blockchain_onchain", "Fetch Blockchain.com on-chain charts...", self.fetch_blockchain_onchain),
            ("coinmetrics", "Fetch Coin Metrics community metrics for validation...", self.fetch_coinmetrics_metrics),
            ("blockchair_biais", "Fetch Blockchair Biais independent sources...", self.fetch_blockchair_biais_sources),
            ("mempool_fee_history", "Fetch mempool.space historical fee proxy...", self.fetch_mempool_historical_fee_proxy),
            ("mempool_fee_current", "Fetch mempool.space current fee...", self.fetch_mempool_current_fee),
        ]
        data.update(self._fetch_group(onchain_tasks))

        attention_tasks = [
            ("wikipedia", "Fetch Wikipedia pageviews...", self.fetch_attention_wikipedia),
            ("google_trends", "Fetch Google Trends optional...", self.fetch_google_trends_optional),
        ]
        if not self.cfg.skip_gdelt:
            attention_tasks.append(("gdelt_attention", "Fetch GDELT news attention proxies...", self.fetch_attention_gdelt))
        data.update(self._fetch_group(attention_tasks))

        if self.cfg.skip_gdelt:
            print("[INFO] Skip GDELT news attention proxies by config.")
            data["gdelt_attention"] = pd.DataFrame(columns=["date", "gdelt_news_count", "gdelt_negative_news_count"])
            self.health.record("gdelt_attention", data["gdelt_attention"], elapsed_seconds=0.0, reason="skip_gdelt=True", status="skipped")

        key, manual_gt = self._fetch_one("google_trends_manual", "Load manual Google Trends CSV optional diagnostic...", self.fetch_manual_google_trends)
        if not manual_gt.empty:
            # manual Google Trends 仅作诊断，不参与 strict Liu validation。
            print("[INFO] Manual Google Trends CSV found; keep as diagnostic only, not strict source.")
            manual_gt = manual_gt.rename(columns={c: f"manual_{c}" for c in manual_gt.columns if c != "date"})
            data["google_trends_manual_diagnostic"] = manual_gt

        if self.cfg.skip_etf:
            print("[INFO] Skip ETF flow sources by config.")
            data["etf_farside"] = pd.DataFrame(columns=["date", "etf_net_flow_usd_farside"])
            data["etf_manual"] = pd.DataFrame(columns=["date", "etf_net_flow_usd_manual"])
            self.health.record("etf_farside", data["etf_farside"], elapsed_seconds=0.0, reason="skip_etf=True", status="skipped")
            self.health.record("etf_manual", data["etf_manual"], elapsed_seconds=0.0, reason="skip_etf=True", status="skipped")
        else:
            etf_tasks = [
                ("etf_farside", "Fetch Farside ETF flows optional...", self.fetch_etf_flows_farside_optional),
                ("etf_manual", "Load manual ETF flows optional...", self.fetch_manual_etf_flows),
            ]
            data.update(self._fetch_group(etf_tasks))

        return data
