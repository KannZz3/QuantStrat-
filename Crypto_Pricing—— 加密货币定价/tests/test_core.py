from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from btc_unified_pricing_model.config import ModelConfig
from btc_unified_pricing_model.pricing import UnifiedBTCPricingModelV12
from btc_unified_pricing_model.utils import infer_hashrate_to_ehs, parse_money_to_usd
from btc_unified_pricing_model.utils import today_utc_date
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

    def test_attention_research_fallback_marks_tier(self) -> None:
        cfg = ModelConfig(days=60, research_min_observations=30, attention_validation_window=40)
        validator = CrossValidator(cfg)
        dates = pd.date_range("2026-01-01", periods=45, freq="D").date
        df = pd.DataFrame({
            "date": dates,
            "z_wiki_attention_7d": np.linspace(-1.0, 1.0, 45),
            "z_wiki_negative_ratio_7d": np.linspace(1.0, -1.0, 45),
        })
        att_res, att_series, neg_res, neg_series = validator.validate_attention(df)
        self.assertTrue(att_res["pass"])
        self.assertFalse(att_res["strict_pass"])
        self.assertEqual(att_res["validation_tier"], "research")
        self.assertGreaterEqual(int(att_series.notna().sum()), 30)
        self.assertTrue(neg_res["pass"])
        self.assertEqual(neg_res["validation_tier"], "research")
        self.assertGreaterEqual(int(neg_series.notna().sum()), 30)


class PricingTests(unittest.TestCase):
    def test_liu_momentum_only_enters_discount_layer(self) -> None:
        cfg = ModelConfig(days=100, max_core_stale_days=9999)
        model = UnifiedBTCPricingModelV12(cfg)
        dates = pd.date_range(end=today_utc_date(), periods=100, freq="D").date
        df = pd.DataFrame({
            "date": dates,
            "validated_btc_price": np.linspace(50_000, 60_000, 100),
            "validated_hashrate_7d": np.linspace(700, 900, 100),
            "validated_active_addresses_7d": np.linspace(350_000, 450_000, 100),
            "validated_btc_price_observed_ok": True,
            "validated_hashrate_observed_ok": True,
            "validated_active_addresses_observed_ok": True,
            "z_validated_ret_7d": np.linspace(-0.2, -0.8, 100),
            "z_validated_ret_14d": np.linspace(-0.2, -0.7, 100),
            "z_validated_ret_28d": np.linspace(-0.1, -0.6, 100),
        })
        validation_report = {
            "module_pass": {
                "bdk_pass": True,
                "biais_module_pass": False,
                "biais_full_pass": False,
                "liu_module_pass": True,
                "liu_full_pass": False,
                "liu_attention_enhanced": False,
                "liu_momentum_only": True,
                "biais_components": {
                    "transaction_benefit_pass": False,
                    "transaction_cost_pass": False,
                    "market_access_pass": False,
                    "crash_risk_pass": False,
                },
                "liu_components": {
                    "momentum_pass": True,
                    "ordinary_attention_pass": False,
                    "ordinary_attention_tier": "excluded",
                    "negative_attention_pass": False,
                    "negative_attention_tier": "excluded",
                    "activity_growth_pass": False,
                },
            },
            "validated_observation_counts": {
                "validated_btc_price": 100,
                "validated_hashrate_7d": 100,
                "validated_active_addresses_7d": 100,
            },
            "validated_data_quality_score": 0.7,
            "excluded_variables": [],
            "data_source_health": {"records": []},
        }
        _, summary = model.price(df, validation_report)
        self.assertEqual(summary["strict_model_status"], "Reduced Model")
        self.assertEqual(summary["included_modules"], ["BDK", "Liu-Tsyvinski"])
        self.assertIsNotNone(summary["liu_discount_latest"])
        self.assertLess(summary["combined_discount_latest"], 1.0)
        self.assertEqual(len(summary["three_paper_framework_rows"]), 4)


if __name__ == "__main__":
    unittest.main()
