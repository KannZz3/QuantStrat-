from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import ModelConfig
from .utils import mean_existing, safe_quantile, today_utc_date


class UnifiedBTCPricingModelV12:
    """基于 validated features 的 BTC 动态下沿估值模型。"""

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg

    def bdk_anchor(self, p_current: float, hr_current: float, aa_current: float, hr_stress: float, aa_stress: float) -> float:
        """Bhambhwani/BDK 链上基本面压力锚。"""
        if any(pd.isna(x) or x <= 0 for x in [p_current, hr_current, aa_current, hr_stress, aa_stress]):
            return np.nan
        return float(
            p_current
            * (hr_stress / hr_current) ** self.cfg.beta_hashrate
            * (aa_stress / aa_current) ** self.cfg.beta_network
        )

    def compute_biais_score(self, df: pd.DataFrame, validation_report: dict) -> pd.Series:
        """
        Biais 启发式均衡折价层。
        注意：该层不是 Biais 原论文 Euler 方程的直接校准。
        active addresses 不在此使用，避免和 BDK network size 重复。
        """
        components = validation_report["module_pass"]["biais_components"]

        scores = []
        weights = []

        # Transaction benefit：只用 transaction count + transfer volume，禁止 active addresses 重复进入。
        if components["transaction_benefit_pass"]:
            benefit = mean_existing(df, ["z_validated_transaction_count_7d", "z_validated_transfer_volume_usd_7d"])
            scores.append(benefit)
            weights.append(float(self.cfg.biais_weights.get("transaction_benefit", 0.40)))

        # Transaction cost：fee 越高越差，但必须结合 transfer volume 判断。
        # 低手续费 + 低转账量不能被误解为强利好；高手续费 + 高转账量也不一定完全利空。
        if components["transaction_cost_pass"]:
            cost = -df["z_validated_avg_fee_usd_7d"]
            if components.get("transaction_benefit_pass") and "z_validated_transfer_volume_usd_7d" in df.columns:
                cost_combined = 0.75 * cost + 0.25 * df["z_validated_transfer_volume_usd_7d"]
                cost = cost_combined.fillna(cost)
            scores.append(cost)
            weights.append(float(self.cfg.biais_weights.get("transaction_cost", 0.20)))

        # Market access：ETF flow 通过交叉验证才允许进入。
        if components["market_access_pass"]:
            access = df["z_validated_etf_flow_usd_7d"]
            scores.append(access)
            weights.append(float(self.cfg.biais_weights.get("market_access", 0.20)))

        # Crash risk：价格通过即可计算 realized vol + drawdown。
        if components["crash_risk_pass"]:
            crash = -mean_existing(df, ["z_validated_realized_vol_30d", "z_validated_drawdown_90d"])
            scores.append(crash)
            weights.append(float(self.cfg.biais_weights.get("crash_risk", 0.20)))

        if not scores:
            return pd.Series(np.nan, index=df.index)

        weighted_sum = pd.Series(0.0, index=df.index)
        weight_sum_series = pd.Series(0.0, index=df.index)
        for s, w in zip(scores, weights):
            mask = s.notna()
            weighted_sum.loc[mask] += s.loc[mask] * w
            weight_sum_series.loc[mask] += w
        
        return weighted_sum / weight_sum_series.replace(0, np.nan)

    def _discount_from_score(self, score: Optional[float], module_pass: bool, thresholds) -> Optional[float]:
        if not module_pass or score is None or pd.isna(score):
            return None
        for min_score, discount in thresholds:
            if score >= min_score:
                return float(discount)
        return None

    def biais_discount_from_score(self, score: Optional[float], module_pass: bool) -> Optional[float]:
        """Biais score 转折价；模块未通过则返回 None，不参与模型。"""
        return self._discount_from_score(score, module_pass, self.cfg.biais_discount_thresholds)

    def compute_liu_score(self, df: pd.DataFrame, validation_report: dict) -> pd.Series:
        """
        Liu-Tsyvinski 启发式收益状态折价层。
        注意：不是原论文预测回归系数的直接复刻。
        active addresses 不在此使用；activity growth 用 transaction_count 或 transfer_volume 的 validated proxy。
        """
        components = validation_report["module_pass"]["liu_components"]
        scores = []
        weights = []

        if components["momentum_pass"]:
            momentum = mean_existing(df, ["z_validated_ret_7d", "z_validated_ret_14d", "z_validated_ret_28d"])
            scores.append(momentum)
            weights.append(float(self.cfg.liu_weights.get("momentum", 0.40)))

        if components["ordinary_attention_pass"]:
            scores.append(df["validated_attention_z"])
            weights.append(float(self.cfg.liu_weights.get("ordinary_attention", 0.25)))

        if components["negative_attention_pass"]:
            scores.append(-df["validated_negative_attention_z"])
            weights.append(float(self.cfg.liu_weights.get("negative_attention", 0.20)))

        if components["activity_growth_pass"]:
            scores.append(df["z_validated_activity_growth"])
            weights.append(float(self.cfg.liu_weights.get("activity_growth", 0.15)))

        if not scores:
            return pd.Series(np.nan, index=df.index)

        weighted_sum = pd.Series(0.0, index=df.index)
        weight_sum_series = pd.Series(0.0, index=df.index)
        for s, w in zip(scores, weights):
            mask = s.notna()
            weighted_sum.loc[mask] += s.loc[mask] * w
            weight_sum_series.loc[mask] += w
        
        return weighted_sum / weight_sum_series.replace(0, np.nan)

    def liu_discount_from_score(self, score: Optional[float], module_pass: bool) -> Optional[float]:
        """Liu score 转折价；模块未通过则返回 None，不参与模型。"""
        return self._discount_from_score(score, module_pass, self.cfg.liu_discount_thresholds)

    @staticmethod
    def _confidence_level(model_status: str, data_quality: Optional[float], min_core_obs: int) -> dict:
        quality = float(data_quality) if data_quality is not None and pd.notna(data_quality) else 0.0
        if model_status == "Full Model" and quality >= 0.85 and min_core_obs >= 90:
            level = "high"
            desc = "完整模块通过，核心样本充足。"
        elif model_status in ["Core Model", "Reduced Model"] and quality >= 0.70 and min_core_obs >= 60:
            level = "medium"
            desc = "核心锚有效，但部分扩展模块缺失或样本有限。"
        elif model_status == "BDK Only" and quality >= 0.55:
            level = "low"
            desc = "仅 BDK 链上锚进入严格估值，折价层未通过。"
        else:
            level = "none"
            desc = "严格估值条件不足，只能作为诊断。"
        return {
            "level": level,
            "description_cn": desc,
            "validated_data_quality_score": quality,
            "min_core_validated_obs": int(min_core_obs),
        }

    @staticmethod
    def _make_downgrade_table(validation_report: dict, excluded_modules: List[dict]) -> List[dict]:
        rows: List[dict] = []
        for item in validation_report.get("excluded_variables", []):
            rows.append({
                "type": "variable",
                "name": item.get("variable"),
                "reason": item.get("reason"),
            })
        for item in excluded_modules:
            rows.append({
                "type": "module",
                "name": item.get("module"),
                "reason": item.get("reason"),
                "components": item.get("components"),
            })
        for rec in validation_report.get("data_source_health", {}).get("records", []):
            if rec.get("status") in ["failed", "empty", "skipped"]:
                rows.append({
                    "type": "source",
                    "name": rec.get("source"),
                    "reason": rec.get("reason"),
                    "status": rec.get("status"),
                    "rows": rec.get("rows"),
                    "latest_date": rec.get("latest_date"),
                })
        return rows

    def _discount_sensitivity_rows(
        self,
        bdk_anchor_price: float,
        biais_score: Optional[float],
        liu_score: Optional[float],
        biais_module_pass: bool,
        liu_module_pass: bool,
    ) -> List[dict]:
        if pd.isna(bdk_anchor_price):
            return []
        rows: List[dict] = []
        for biais_shock in self.cfg.sensitivity_score_shocks:
            for liu_shock in self.cfg.sensitivity_score_shocks:
                shifted_biais_score = None if biais_score is None or pd.isna(biais_score) else float(biais_score + biais_shock)
                shifted_liu_score = None if liu_score is None or pd.isna(liu_score) else float(liu_score + liu_shock)
                b_disc = self.biais_discount_from_score(shifted_biais_score, biais_module_pass)
                l_disc = self.liu_discount_from_score(shifted_liu_score, liu_module_pass)
                combined = 1.0
                if b_disc is not None:
                    combined *= b_disc
                if l_disc is not None:
                    combined *= l_disc
                rows.append({
                    "biais_score_shock": float(biais_shock),
                    "liu_score_shock": float(liu_shock),
                    "biais_discount": b_disc,
                    "liu_discount": l_disc,
                    "combined_discount": combined,
                    "core_lower_point": float(bdk_anchor_price * combined),
                })
        return rows

    def price(self, df: pd.DataFrame, validation_report: dict) -> Tuple[pd.DataFrame, dict]:
        out = df.copy().sort_values("date").reset_index(drop=True)
        module = validation_report["module_pass"]

        # latest_date 必须是核心 validated 三变量同时有效，且核心输入主要来自真实观测而非插值/ffill。
        core_cols = ["validated_btc_price", "validated_hashrate_7d", "validated_active_addresses_7d"]
        core_observed_cols = [
            "validated_btc_price_observed_ok",
            "validated_hashrate_observed_ok",
            "validated_active_addresses_observed_ok",
        ]
        for c in core_observed_cols:
            if c not in out.columns:
                out[c] = False
        core_candidate = out.dropna(subset=core_cols)
        available_core = core_candidate[core_candidate[core_observed_cols].all(axis=1)]
        if available_core.empty:
            latest_idx = out["date"].last_valid_index()
            latest = out.loc[latest_idx]
            summary_base = {
                "run_time_utc": datetime.now(timezone.utc).isoformat(),
                "model_name": "BTC Unified Multi-Dimensional Pricing Model",
                "model_version": "v1.3",
                "papers": [
                    "Bhambhwani, Delikouras, and Korniotis (2019) - on-chain fundamentals",
                    "Biais et al. (2023) - equilibrium Bitcoin pricing",
                    "Liu and Tsyvinski (2021) - risks and returns of cryptocurrency",
                ],
                "important_model_boundary_cn": (
                    "Biais 与 Liu-Tsyvinski 模块在本代码中是基于论文机制的启发式折价层，"
                    "不是原论文参数的直接估计。未通过交叉验证的数据不参与严格定价。"
                ),
                "active_addresses_usage_cn": "active addresses 只在 BDK 链上基本面锚中使用，避免 network factor 重复计数。",
                "latest_date": str(latest["date"]),
                "latest_validated_core_date": None,
                "latest_validated_core_staleness_days": None,
                "max_allowed_core_stale_days": self.cfg.max_core_stale_days,
                "validation_report": validation_report,
                "excluded_variables": validation_report.get("excluded_variables", []),
                "validated_observation_counts": validation_report.get("validated_observation_counts", {}),
                "excluded_modules": [],
            }
            summary = dict(summary_base)
            summary.update({
                "strict_model_status": "No Strict Valuation",
                "main_conclusion_cn": "核心 BDK validated 数据无法在同一日期同时满足交叉验证与真实观测要求，严格模型不输出 BTC 下沿估值。",
                "confidence_level": self._confidence_level(
                    "No Strict Valuation",
                    validation_report.get("validated_data_quality_score"),
                    0,
                ),
                "downgrade_table": self._make_downgrade_table(validation_report, []),
                "scenarios": [],
            })
            return out, summary

        latest_idx = int(available_core.index.max())
        latest = out.loc[latest_idx]

        summary_base = {
            "run_time_utc": datetime.now(timezone.utc).isoformat(),
            "model_name": "BTC Unified Multi-Dimensional Pricing Model",
            "model_version": "v1.3",
            "papers": [
                "Bhambhwani, Delikouras, and Korniotis (2019) - on-chain fundamentals",
                "Biais et al. (2023) - equilibrium Bitcoin pricing",
                "Liu and Tsyvinski (2021) - risks and returns of cryptocurrency",
            ],
            "important_model_boundary_cn": (
                "Biais 与 Liu-Tsyvinski 模块在本代码中是基于论文机制的启发式折价层，"
                "不是原论文参数的直接估计。未通过交叉验证的数据不参与严格定价。"
            ),
            "active_addresses_usage_cn": "active addresses 只在 BDK 链上基本面锚中使用，避免 network factor 重复计数。",
            "latest_date": str(latest["date"]),
            "latest_validated_core_date": str(latest["date"]),
            "latest_validated_core_staleness_days": int((today_utc_date() - latest["date"]).days),
            "max_allowed_core_stale_days": self.cfg.max_core_stale_days,
            "latest_core_observed_status": {
                "price_observed_ok": bool(latest.get("validated_btc_price_observed_ok", False)),
                "hashrate_observed_ok": bool(latest.get("validated_hashrate_observed_ok", False)),
                "active_addresses_observed_ok": bool(latest.get("validated_active_addresses_observed_ok", False)),
            },
            "validation_report": validation_report,
            "excluded_variables": validation_report.get("excluded_variables", []),
            "validated_observation_counts": validation_report.get("validated_observation_counts", {}),
            "excluded_modules": [],
        }

        core_staleness_days = int((today_utc_date() - latest["date"]).days)
        early_counts = validation_report.get("validated_observation_counts", {})
        early_min_core_obs = int(min([
            early_counts.get("validated_btc_price", 0),
            early_counts.get("validated_hashrate_7d", 0),
            early_counts.get("validated_active_addresses_7d", 0),
        ]))
        if core_staleness_days > self.cfg.max_core_stale_days:
            summary = dict(summary_base)
            summary.update({
                "strict_model_status": "No Strict Valuation",
                "main_conclusion_cn": (
                    f"最近一个核心 validated 数据同时有效的日期为 {latest['date']}，"
                    f"距今天已滞后 {core_staleness_days} 天，超过允许阈值 {self.cfg.max_core_stale_days} 天。"
                    "因此严格模型不输出当前 BTC 下沿估值，只保留最近有效数据诊断。"
                ),
                "confidence_level": self._confidence_level(
                    "No Strict Valuation",
                    validation_report.get("validated_data_quality_score"),
                    early_min_core_obs,
                ),
                "downgrade_table": self._make_downgrade_table(validation_report, []),
                "scenarios": [],
            })
            return out, summary

        if not module["bdk_pass"]:
            bdk_excluded_modules = [{"module": "BDK", "reason": "Core BDK on-chain anchor failed strict validation or observed-input requirement."}]
            summary = dict(summary_base)
            summary.update({
                "strict_model_status": "No Strict Valuation",
                "excluded_modules": bdk_excluded_modules,
                "main_conclusion_cn": "核心 BDK 链上锚未通过交叉验证或真实观测要求，严格模型不输出 BTC 下沿估值。",
                "confidence_level": self._confidence_level(
                    "No Strict Valuation",
                    validation_report.get("validated_data_quality_score"),
                    early_min_core_obs,
                ),
                "downgrade_table": self._make_downgrade_table(validation_report, bdk_excluded_modules),
                "scenarios": [],
            })
            return out, summary

        # ----------------------------------------------------
        # 5.1 Biais / Liu 分数与折价，只在模块通过且 latest 有分数时进入。
        # ----------------------------------------------------
        out["biais_score"] = self.compute_biais_score(out, validation_report)
        out["liu_score"] = self.compute_liu_score(out, validation_report)

        latest_biais_score = out.at[latest_idx, "biais_score"] if "biais_score" in out.columns else np.nan
        latest_liu_score = out.at[latest_idx, "liu_score"] if "liu_score" in out.columns else np.nan

        biais_discount = self.biais_discount_from_score(latest_biais_score, module["biais_module_pass"])
        liu_discount = self.liu_discount_from_score(latest_liu_score, module["liu_module_pass"])

        # 记录模块剔除原因，让模型降级原因透明。
        excluded_modules: List[dict] = []
        if biais_discount is None:
            if not module.get("biais_module_pass"):
                excluded_modules.append({
                    "module": "Biais",
                    "reason": "Biais strict layer excluded because transaction benefit or required Biais components failed validation.",
                    "components": module.get("biais_components", {}),
                })
            elif pd.isna(latest_biais_score):
                excluded_modules.append({
                    "module": "Biais",
                    "reason": "Biais validation passed but latest_biais_score is NaN, usually due to insufficient latest validated z-score observations.",
                })
        if liu_discount is None:
            if not module.get("liu_module_pass"):
                excluded_modules.append({
                    "module": "Liu-Tsyvinski",
                    "reason": "Liu strict layer excluded because momentum plus at least one attention dimension did not pass validation.",
                    "components": module.get("liu_components", {}),
                })
            elif pd.isna(latest_liu_score):
                excluded_modules.append({
                    "module": "Liu-Tsyvinski",
                    "reason": "Liu validation passed but latest_liu_score is NaN, usually due to insufficient latest validated z-score observations.",
                })

        # 严格模型只乘实际可用且通过的模块。
        included_modules = ["BDK"]
        combined_discount = 1.0
        if biais_discount is not None:
            combined_discount *= biais_discount
            included_modules.append("Biais")
        if liu_discount is not None:
            combined_discount *= liu_discount
            included_modules.append("Liu-Tsyvinski")

        # model_status 和区间宽度根据实际 included_modules 重算，避免状态虚高。
        if included_modules == ["BDK", "Biais", "Liu-Tsyvinski"]:
            if module.get("biais_full_pass") and module.get("liu_full_pass"):
                actual_model_status = "Full Model"
                band_width = 0.05
            else:
                actual_model_status = "Core Model"
                band_width = 0.10
        elif included_modules in (["BDK", "Biais"], ["BDK", "Liu-Tsyvinski"]):
            actual_model_status = "Reduced Model"
            band_width = 0.15
        else:
            actual_model_status = "BDK Only"
            band_width = 0.18

        # validated 样本数越少，区间越宽。
        counts = validation_report.get("validated_observation_counts", {})
        core_count_values = [
            counts.get("validated_btc_price", 0),
            counts.get("validated_hashrate_7d", 0),
            counts.get("validated_active_addresses_7d", 0),
        ]
        min_core_validated_obs = int(min(core_count_values)) if core_count_values else 0
        sample_width_addon = 0.0
        if min_core_validated_obs < 60:
            sample_width_addon = 0.05
        elif min_core_validated_obs < 90:
            sample_width_addon = 0.03
        band_width_base = band_width
        band_width = min(band_width + sample_width_addon, 0.30)

        # ----------------------------------------------------
        # 5.2 压力情景：只用 validated hashrate / active addresses，且 stress 不得高于当前值。
        # ----------------------------------------------------
        p_current = float(latest["validated_btc_price"])
        hr_current = float(latest["validated_hashrate_7d"])
        aa_current = float(latest["validated_active_addresses_7d"])
        # 只使用通过交叉验证的重叠窗口样本计算分位数。
        hr_series = out.loc[:latest_idx, "validated_hashrate_7d"].dropna()
        aa_series = out.loc[:latest_idx, "validated_active_addresses_7d"].dropna()

        def downside_stress(series: pd.Series, q: float, current: float, cap_mult: float) -> float:
            raw = safe_quantile(series, q, current * cap_mult)
            return float(min(raw, current * cap_mult))

        scenarios = {
            "base_pressure": {
                "desc_cn": "基础压力：validated hashrate 与 active addresses 回落到最近验证样本 30% 分位，且不高于当前值的 98%",
                "hr_stress": downside_stress(hr_series, 0.30, hr_current, 0.98),
                "aa_stress": downside_stress(aa_series, 0.30, aa_current, 0.98),
            },
            "core_lower_bound": {
                "desc_cn": "核心下沿：validated hashrate 与 active addresses 回落到最近验证样本 15% 分位，且不高于当前值的 95%",
                "hr_stress": downside_stress(hr_series, 0.15, hr_current, 0.95),
                "aa_stress": downside_stress(aa_series, 0.15, aa_current, 0.95),
            },
            "severe_lower_bound": {
                "desc_cn": "严重压力：validated hashrate 与 active addresses 回落到最近验证样本 5% 分位，且不高于当前值的 90%",
                "hr_stress": downside_stress(hr_series, 0.05, hr_current, 0.90),
                "aa_stress": downside_stress(aa_series, 0.05, aa_current, 0.90),
            },
            "extreme_tail": {
                "desc_cn": "极端尾部：validated 5% 分位基础上进一步下压，且不高于当前值的 85%",
                "hr_stress": min(safe_quantile(hr_series, 0.05, hr_current * 0.85) * 0.90, hr_current * 0.85),
                "aa_stress": min(safe_quantile(aa_series, 0.05, aa_current * 0.85) * 0.90, aa_current * 0.85),
            },
        }

        scenario_rows = []
        for name, s in scenarios.items():
            bdk = self.bdk_anchor(p_current, hr_current, aa_current, s["hr_stress"], s["aa_stress"])
            strict_point = bdk * combined_discount if not pd.isna(bdk) else np.nan
            lower = strict_point * (1 - band_width) if not pd.isna(strict_point) else np.nan
            upper = strict_point * (1 + band_width) if not pd.isna(strict_point) else np.nan
            scenario_rows.append({
                "scenario": name,
                "desc_cn": s["desc_cn"],
                "hashrate_stress_ehs": s["hr_stress"],
                "active_addresses_stress": s["aa_stress"],
                "bdk_anchor_price": bdk,
                "biais_discount": biais_discount,
                "liu_discount": liu_discount,
                "combined_discount": combined_discount,
                "included_modules": "+".join(included_modules),
                "strict_lower_point": strict_point,
                "strict_lower_band_low": lower,
                "strict_lower_band_high": upper,
                "band_width": band_width,
                "band_width_base": band_width_base,
                "sample_width_addon": sample_width_addon,
                "min_core_validated_obs": min_core_validated_obs,
            })
        scenario_df = pd.DataFrame(scenario_rows)
        core_rows = scenario_df[scenario_df["scenario"] == "core_lower_bound"]
        core_bdk_anchor = float(core_rows.iloc[0]["bdk_anchor_price"]) if not core_rows.empty else np.nan
        sensitivity_rows = self._discount_sensitivity_rows(
            core_bdk_anchor,
            latest_biais_score if pd.notna(latest_biais_score) else None,
            latest_liu_score if pd.notna(latest_liu_score) else None,
            bool(module["biais_module_pass"]),
            bool(module["liu_module_pass"]),
        )

        summary = dict(summary_base)
        summary.update({
            "strict_model_status": actual_model_status,
            "validation_model_status_pre_score": module.get("model_status"),
            "included_modules": included_modules,
            "excluded_modules": excluded_modules,
            "band_width_base": band_width_base,
            "sample_width_addon": sample_width_addon,
            "min_core_validated_obs": min_core_validated_obs,
            "btc_price_current": p_current,
            "hashrate_current_ehs_7d_validated": hr_current,
            "active_addresses_current_7d_validated": aa_current,
            "biais_score_latest": float(latest_biais_score) if pd.notna(latest_biais_score) else None,
            "liu_score_latest": float(latest_liu_score) if pd.notna(latest_liu_score) else None,
            "biais_discount_latest": biais_discount,
            "liu_discount_latest": liu_discount,
            "combined_discount_latest": combined_discount,
            "discount_model_config": {
                "biais_weights": dict(self.cfg.biais_weights),
                "liu_weights": dict(self.cfg.liu_weights),
                "biais_discount_thresholds": [list(x) for x in self.cfg.biais_discount_thresholds],
                "liu_discount_thresholds": [list(x) for x in self.cfg.liu_discount_thresholds],
                "sensitivity_score_shocks": list(self.cfg.sensitivity_score_shocks),
            },
            "discount_sensitivity_core_lower_bound": sensitivity_rows,
            "confidence_level": self._confidence_level(
                actual_model_status,
                validation_report.get("validated_data_quality_score"),
                min_core_validated_obs,
            ),
            "downgrade_table": self._make_downgrade_table(validation_report, excluded_modules),
            "validated_data_quality_score": validation_report.get("validated_data_quality_score"),
            "validated_observation_counts": validation_report.get("validated_observation_counts", {}),
            "excluded_variables": validation_report.get("excluded_variables", []),
            "scenarios": scenario_rows,
            "main_conclusion_cn": self._make_conclusion_cn(scenario_df, actual_model_status, included_modules),
        })
        return out, summary

    @staticmethod
    def _make_conclusion_cn(scenario_df: pd.DataFrame, model_status: str, included_modules: List[str]) -> str:
        def fmt(x):
            if pd.isna(x):
                return "NA"
            return f"{x:,.0f}"
        core = scenario_df[scenario_df["scenario"] == "core_lower_bound"]
        severe = scenario_df[scenario_df["scenario"] == "severe_lower_bound"]
        if core.empty:
            return "数据不足，无法生成核心下沿结论。"
        c = core.iloc[0]
        text = (
            f"当前严格模型状态为 {model_status}，实际进入模型的模块为 {' + '.join(included_modules)}。"
            f"核心 BTC 下沿区间为 {fmt(c['strict_lower_band_low'])}–{fmt(c['strict_lower_band_high'])} 美元。"
        )
        if not severe.empty:
            s = severe.iloc[0]
            text += f" 若进入更强链上压力，风险下沿扩展至 {fmt(s['strict_lower_band_low'])}–{fmt(s['strict_lower_band_high'])} 美元。"
        return text
