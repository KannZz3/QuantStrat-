from __future__ import annotations

import argparse
from typing import Any, Dict

from .config import ModelConfig
from .config_loader import load_model_config
from .pipeline import run_pipeline


def _put(overrides: Dict[str, Any], key: str, value: Any) -> None:
    if value is not None:
        overrides[key] = value


def parse_args() -> ModelConfig:
    defaults = ModelConfig()
    parser = argparse.ArgumentParser(description="BTC unified multi-module downside pricing model v1.3")
    parser.add_argument("--config", type=str, default=None, help="Optional JSON/YAML config file for ModelConfig fields")
    parser.add_argument("--days", type=int, default=None, help="Recent data window; minimum is derived from validation settings")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory")
    parser.add_argument("--use-pytrends", action="store_true", default=None, help="Try pytrends for Google Trends")
    parser.add_argument("--manual-etf-csv", type=str, default=None, help="Diagnostic-only manual ETF flow CSV")
    parser.add_argument("--manual-google-trends-csv", type=str, default=None, help="Diagnostic-only manual Google Trends CSV")
    parser.add_argument("--skip-gdelt", action="store_true", default=None, help="Skip GDELT news attention sources")
    parser.add_argument("--skip-etf", action="store_true", default=None, help="Skip Farside/manual ETF flow sources")
    parser.add_argument("--fast", action="store_true", default=None, help="Fast diagnostic mode: skip GDELT/ETF and reduce timeout/retries")
    parser.add_argument("--no-gdelt-cache", action="store_true", default=None, help="Do not read fresh GDELT cache")
    parser.add_argument("--cryptocompare-api-key", type=str, default=None, help="Optional CryptoCompare API key")
    parser.add_argument("--request-timeout", type=int, default=None, help="HTTP request timeout in seconds")
    parser.add_argument("--source-timeout", type=int, default=None, help="Alias for --request-timeout with higher priority")
    parser.add_argument("--max-request-retries", type=int, default=None, help="Maximum HTTP retries")
    parser.add_argument("--no-parallel-fetch", action="store_true", default=None, help="Disable grouped concurrent fetching")
    parser.add_argument("--fetch-max-workers", type=int, default=None, help="Maximum concurrent fetch workers")
    args = parser.parse_args()

    overrides: Dict[str, Any] = {}
    _put(overrides, "days", args.days)
    _put(overrides, "output_dir", args.output_dir)
    _put(overrides, "manual_etf_csv", args.manual_etf_csv)
    _put(overrides, "manual_google_trends_csv", args.manual_google_trends_csv)
    _put(overrides, "cryptocompare_api_key", args.cryptocompare_api_key)
    _put(overrides, "request_timeout", args.source_timeout if args.source_timeout is not None else args.request_timeout)
    _put(overrides, "max_request_retries", args.max_request_retries)
    _put(overrides, "fetch_max_workers", args.fetch_max_workers)

    for cli_key, cfg_key in [
        ("use_pytrends", "use_pytrends"),
        ("skip_gdelt", "skip_gdelt"),
        ("skip_etf", "skip_etf"),
        ("fast", "fast_mode"),
    ]:
        if getattr(args, cli_key) is True:
            overrides[cfg_key] = True
    if args.no_gdelt_cache is True:
        overrides["gdelt_read_fresh_cache"] = False
    if args.no_parallel_fetch is True:
        overrides["parallel_fetch"] = False

    cfg = load_model_config(args.config, overrides)
    if cfg.fast_mode:
        cfg.request_timeout = min(cfg.request_timeout, 8)
        cfg.max_request_retries = min(cfg.max_request_retries, 1)
        cfg.sleep_seconds = min(cfg.sleep_seconds, 0.05)
        cfg.skip_gdelt = True
        cfg.skip_etf = True
    return cfg


def main() -> None:
    config = parse_args()
    run_pipeline(config)
