from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from btc_unified_pricing_model.config import ModelConfig
from btc_unified_pricing_model.utils import infer_hashrate_to_ehs, parse_money_to_usd
from btc_unified_pricing_model.validator import CrossValidator


class UtilityTests(unittest.TestCase):
    def test_parse_money_requires_known_multiplier(self) -> None:
        self.assertTrue(np.isnan(parse_money_to_usd("100.9")))
        self.assertEqual(parse_money_to_usd("100.9", default_multiplier=1_000_000), 100_900_000)
        self.assertEqual(parse_money_to_usd("(1.2bn)"), -1_200_000_000)
        self.assertEqual(parse_money_to_usd("-3.5m"), -3_500_000)

    def test_infer_hashrate_to_ehs(self) -> None:
        hs = pd.Series([8.5e20, 9.0e20, 9.5e20])
        ths = pd.Series([850_000_000, 900_000_000, 950_000_000])
        ehs = pd.Series([850, 900, 950])
        self.assertAlmostEqual(float(infer_hashrate_to_ehs(hs).median()), 900.0)
        self.assertAlmostEqual(float(infer_hashrate_to_ehs(ths).median()), 900.0)
        self.assertAlmostEqual(float(infer_hashrate_to_ehs(ehs).median()), 900.0)


class ValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cfg = ModelConfig(days=120, price_validation_window=30)
        self.validator = CrossValidator(self.cfg)

    def test_validate_pair_level_passes_correlated_series(self) -> None:
        x = pd.Series(range(1, 41), dtype="float64")
        df = pd.DataFrame({"a": x, "b": x * 1.005})
        result, validated = self.validator.validate_pair_level(
            df,
            "a",
            "b",
            min_corr=0.99,
            max_gap=0.01,
            window=30,
            require_direction=True,
        )
        self.assertTrue(result["pass"])
        self.assertEqual(int(validated.notna().sum()), 40)

    def test_validate_price_uses_multi_source_median(self) -> None:
        dates = pd.date_range("2026-01-01", periods=40, freq="D").date
        base = pd.Series(np.linspace(100, 140, 40))
        df = pd.DataFrame({
            "date": dates,
            "btc_price_coingecko": base,
            "btc_price_coinbase": base * 1.001,
            "btc_price_kraken": base * 0.999,
            "btc_price_binance": base * 1.20,
        })
        for c in [col for col in df.columns if col.startswith("btc_price_")]:
            df[f"{c}_observed_flag"] = 1
        result, validated = self.validator.validate_price(df)
        self.assertTrue(result["pass"])
        self.assertGreaterEqual(result["passed_pair_count"], 3)
        self.assertIn("btc_price_coingecko", result["eligible_price_sources"])
        self.assertAlmostEqual(float(validated.dropna().iloc[-1]), float(base.iloc[-1]), places=4)


if __name__ == "__main__":
    unittest.main()
