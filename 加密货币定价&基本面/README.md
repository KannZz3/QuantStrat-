BTC Unified Pricing Model v1.3
==============================

This is a modularized upgrade of `btc_unified_pricing_model_v1_2.py`.

Core changes in v1.3
--------------------

- Split the former single 3,000+ line script into modules:
  `config`, `utils`, `fetchers`, `processor`, `validator`, `pricing`, `io_outputs`, `pipeline`, `cli`.
- Added structured data-source health tracking and saved it as:
  `btc_data_source_health_v1_3.json` and `btc_source_coverage_v1_3.csv`.
- Reworked public-source reliability:
  `requests.Session`, configurable retry count, non-retryable status codes, optional CryptoCompare API key.
- Fixed HTML table reading:
  uses `StringIO(html)` and detects Cloudflare / JavaScript challenge pages explicitly.
- Reworked GDELT:
  fresh cache can be read, stale cache is ignored, 429 backoff is tracked in source health, `--skip-gdelt` is available.
- Unified minimum validation window:
  `days` must satisfy `max(60, z_min_periods, attention_validation_min_overlap)`.
- Reworked price validation:
  all automatic price-source pairs are scored; the best pair is reported; validated price uses the median of all eligible consensus sources.
- Parameterized Biais/Liu heuristic weights and discount thresholds in `ModelConfig`, with JSON/YAML config-file support.
- Added discount sensitivity output for the core-lower-bound scenario.
- Added confidence level and downgrade table outputs.
- Added fast/skip modes and grouped concurrent fetching.
- Added unit tests for parsing, hashrate unit inference, and validator behavior.

Run
---

```bash
python btc_unified_pricing_model_v1_3.py --days 180 --output-dir ./btc_pricing_output_v1_3
```

Fast diagnostic run:

```bash
python btc_unified_pricing_model_v1_3.py --days 90 --fast --output-dir ./btc_pricing_output_fast
```

With config file:

```bash
python btc_unified_pricing_model_v1_3.py --config config.example.json
```

Useful flags
------------

- `--skip-gdelt`: skip GDELT news attention requests.
- `--skip-etf`: skip ETF flow sources.
- `--fast`: skip GDELT/ETF, reduce timeout/retry counts.
- `--source-timeout N`: alias for request timeout.
- `--no-parallel-fetch`: disable grouped concurrent fetches.
- `--fetch-max-workers N`: tune concurrent fetch workers.
- `--cryptocompare-api-key KEY`: optional CryptoCompare API key.

Outputs
-------

- `processed/btc_daily_master_v1_3.csv`
- `btc_pricing_summary_v1_3.json`
- `btc_validation_report_v1_3.json`
- `btc_pricing_latest_table_v1_3.csv`
- `btc_data_source_health_v1_3.json`
- `btc_source_coverage_v1_3.csv`
- `btc_downgrade_table_v1_3.csv`
- `btc_discount_sensitivity_v1_3.csv`

Tests
-----

```bash
python -m unittest discover tests
```

Boundary
--------

Biais and Liu-Tsyvinski layers remain heuristic discount layers inspired by paper mechanisms. They are not direct econometric calibrations of the original papers. Only cross-validated variables enter strict valuation.
