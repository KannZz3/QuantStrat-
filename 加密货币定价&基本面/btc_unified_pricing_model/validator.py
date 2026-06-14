from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import ModelConfig
from .utils import percentile_rank, rolling_zscore


class CrossValidator:
    """
    严格交叉验证：
        - 通过验证的数据生成 validated_* 字段；
        - 未通过验证的数据只保留为 raw / diagnostic，不允许进入最终定价。
    """

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg

    @staticmethod
    def _observed_mask_for_col(df: pd.DataFrame, col: str) -> pd.Series:
        """
        交叉验证窗口本身也排除主要来自插值 / ffill 的观测。

        规则：
            - 原始价格列：如果存在 *_observed_flag，则只允许真实观测日参与验证。
            - 7D 平滑链上列：如果存在对应 *_observed_count_7d，则要求 7D 窗口内至少 5 天真实观测。
            - 30D 平滑列：如果存在对应 *_observed_count_30d，则要求 30D 窗口内至少 20 天真实观测。
            - 没有 observed 信息的列，保持原逻辑，不额外过滤。
        """
        idx = df.index
        if col in df.columns and f"{col}_observed_flag" in df.columns:
            return df[f"{col}_observed_flag"].fillna(0).astype(float) >= 1

        if col.endswith("_7d"):
            base = col[:-3]
            obs_count_col = f"{base}_observed_count_7d"
            if obs_count_col in df.columns:
                return df[obs_count_col].fillna(0).astype(float) >= 5

        if col.endswith("_30d"):
            base = col[:-4]
            obs_count_col = f"{base}_observed_count_30d"
            if obs_count_col in df.columns:
                return df[obs_count_col].fillna(0).astype(float) >= 20

        return pd.Series(True, index=idx)

    def validate_pair_level(
        self,
        df: pd.DataFrame,
        primary_col: str,
        secondary_col: str,
        min_corr: float,
        max_gap: float,
        window: int = 30,
        require_direction: bool = True,
    ) -> Tuple[dict, pd.Series]:
        result = {
            "primary": primary_col,
            "secondary": secondary_col,
            "pass": False,
            "corr": None,
            "latest_gap": None,
            "direction_match_7d": None,
            "reason": "",
            "overlap_obs_total": 0,
            "raw_overlap_obs_total": 0,
            "overlap_obs_window": 0,
            "validated_obs": 0,
        }
        if primary_col not in df.columns or secondary_col not in df.columns:
            result["reason"] = "missing source column"
            return result, pd.Series(np.nan, index=df.index)

        raw_overlap_mask = df[[primary_col, secondary_col]].notna().all(axis=1)
        observed_mask = self._observed_mask_for_col(df, primary_col) & self._observed_mask_for_col(df, secondary_col)
        overlap_mask_all = raw_overlap_mask & observed_mask
        result["raw_overlap_obs_total"] = int(raw_overlap_mask.sum())
        overlap_all = df.loc[overlap_mask_all, [primary_col, secondary_col]].dropna()
        result["overlap_obs_total"] = int(len(overlap_all))
        tmp = overlap_all.tail(window)
        result["overlap_obs_window"] = int(len(tmp))
        if len(tmp) < max(10, window // 2):
            result["reason"] = "insufficient overlapping observations"
            return result, pd.Series(np.nan, index=df.index)
        corr = tmp[primary_col].corr(tmp[secondary_col])
        result["corr"] = float(corr) if pd.notna(corr) else None
        latest_primary = tmp[primary_col].iloc[-1]
        latest_secondary = tmp[secondary_col].iloc[-1]
        if latest_primary == 0 or pd.isna(latest_primary):
            result["reason"] = "invalid primary latest value"
            return result, pd.Series(np.nan, index=df.index)
        gap = abs(latest_primary - latest_secondary) / abs(latest_primary)
        result["latest_gap"] = float(gap)
        direction_match = True
        if len(tmp) >= 8:
            dx = tmp[primary_col].iloc[-1] - tmp[primary_col].iloc[-8]
            dy = tmp[secondary_col].iloc[-1] - tmp[secondary_col].iloc[-8]
            direction_match = bool(np.sign(dx) == np.sign(dy))
        result["direction_match_7d"] = direction_match
        if corr >= min_corr and gap <= max_gap and (direction_match or not require_direction):
            result["pass"] = True
            result["reason"] = "level validation pass"
            validated = pd.Series(np.nan, index=df.index, dtype="float64")
            # validated series 仅保留双源重叠且观测质量合格的日期。
            validated.loc[overlap_mask_all] = df.loc[overlap_mask_all, primary_col]
            result["validated_obs"] = int(validated.notna().sum())
            return result, validated
        result["reason"] = "level validation failed"
        return result, pd.Series(np.nan, index=df.index)

    def validate_pair_percentile(
        self,
        df: pd.DataFrame,
        primary_col: str,
        secondary_col: str,
        min_corr: float,
        max_percentile_gap: float,
        window: int = 90,
    ) -> Tuple[dict, pd.Series]:
        result = {
            "primary": primary_col,
            "secondary": secondary_col,
            "pass": False,
            "corr": None,
            "primary_percentile": None,
            "secondary_percentile": None,
            "percentile_gap": None,
            "direction_match_7d": None,
            "reason": "",
            "overlap_obs_total": 0,
            "raw_overlap_obs_total": 0,
            "overlap_obs_window": 0,
            "validated_obs": 0,
        }
        if primary_col not in df.columns or secondary_col not in df.columns:
            result["reason"] = "missing source column"
            return result, pd.Series(np.nan, index=df.index)

        raw_overlap_mask = df[[primary_col, secondary_col]].notna().all(axis=1)
        observed_mask = self._observed_mask_for_col(df, primary_col) & self._observed_mask_for_col(df, secondary_col)
        overlap_mask_all = raw_overlap_mask & observed_mask
        result["raw_overlap_obs_total"] = int(raw_overlap_mask.sum())
        overlap_all = df.loc[overlap_mask_all, [primary_col, secondary_col]].dropna()
        result["overlap_obs_total"] = int(len(overlap_all))
        tmp = overlap_all.tail(window)
        result["overlap_obs_window"] = int(len(tmp))
        if len(tmp) < 30:
            result["reason"] = "insufficient overlapping observations"
            return result, pd.Series(np.nan, index=df.index)
        corr = tmp[primary_col].corr(tmp[secondary_col])
        p_pct = percentile_rank(tmp[primary_col], tmp[primary_col].iloc[-1])
        s_pct = percentile_rank(tmp[secondary_col], tmp[secondary_col].iloc[-1])
        pct_gap = abs(p_pct - s_pct)
        direction_match = True
        if len(tmp) >= 8:
            dx = tmp[primary_col].iloc[-1] - tmp[primary_col].iloc[-8]
            dy = tmp[secondary_col].iloc[-1] - tmp[secondary_col].iloc[-8]
            direction_match = bool(np.sign(dx) == np.sign(dy))
        result.update({
            "corr": float(corr) if pd.notna(corr) else None,
            "primary_percentile": float(p_pct),
            "secondary_percentile": float(s_pct),
            "percentile_gap": float(pct_gap),
            "direction_match_7d": direction_match,
        })
        if corr >= min_corr and pct_gap <= max_percentile_gap and direction_match:
            result["pass"] = True
            result["reason"] = "percentile-state validation pass"
            validated = pd.Series(np.nan, index=df.index, dtype="float64")
            # validated series 仅保留双源重叠且观测质量合格的日期。
            validated.loc[overlap_mask_all] = df.loc[overlap_mask_all, primary_col]
            result["validated_obs"] = int(validated.notna().sum())
            return result, validated
        result["reason"] = "percentile-state validation failed"
        return result, pd.Series(np.nan, index=df.index)

    def validate_pair_zscore_direction(
        self,
        df: pd.DataFrame,
        primary_col: str,
        secondary_col: str,
        min_corr: float,
        window: int = 30,
        require_direction: bool = True,
    ) -> Tuple[dict, pd.Series]:
        """
        专用于 attention / negative attention 这类 z-score 序列的双源验证。

        与 validate_pair_level 的区别：
            - 不检查 level gap；
            - 不把 latest value = 0 视为无效，因为 z-score 接近 0 是正常状态；
            - 只检查双源重叠样本、相关性和最近方向一致性；
            - validated series 只保留双源同时非空的日期。
        """
        result = {
            "primary": primary_col,
            "secondary": secondary_col,
            "pass": False,
            "corr": None,
            "direction_match_7d": None,
            "reason": "",
            "overlap_obs_total": 0,
            "overlap_obs_window": 0,
            "validated_obs": 0,
        }
        if primary_col not in df.columns or secondary_col not in df.columns:
            result["reason"] = "missing z-score source column"
            return result, pd.Series(np.nan, index=df.index)

        overlap_mask = df[[primary_col, secondary_col]].notna().all(axis=1)
        overlap_all = df.loc[overlap_mask, [primary_col, secondary_col]].dropna()
        result["overlap_obs_total"] = int(len(overlap_all))
        tmp = overlap_all.tail(window)
        result["overlap_obs_window"] = int(len(tmp))
        if len(tmp) < max(10, window // 2):
            result["reason"] = "insufficient overlapping z-score observations"
            return result, pd.Series(np.nan, index=df.index)

        corr = tmp[primary_col].corr(tmp[secondary_col])
        result["corr"] = float(corr) if pd.notna(corr) else None

        direction_match = True
        if len(tmp) >= 8:
            dx = tmp[primary_col].iloc[-1] - tmp[primary_col].iloc[-8]
            dy = tmp[secondary_col].iloc[-1] - tmp[secondary_col].iloc[-8]
            direction_match = bool(np.sign(dx) == np.sign(dy))
        result["direction_match_7d"] = direction_match

        if corr is not None and pd.notna(corr) and corr >= min_corr and (direction_match or not require_direction):
            result["pass"] = True
            result["reason"] = "z-score corr/direction validation pass"
            validated = pd.Series(np.nan, index=df.index, dtype="float64")
            validated.loc[overlap_mask] = df.loc[overlap_mask, primary_col]
            result["validated_obs"] = int(validated.notna().sum())
            return result, validated

        result["reason"] = "z-score corr/direction validation failed"
        return result, pd.Series(np.nan, index=df.index)

    def _attention_best_lag_corr(self, tmp: pd.DataFrame, primary_col: str, secondary_col: str, max_lag: int) -> Tuple[Optional[int], Optional[float], Dict[str, Optional[float]]]:
        """在 [-max_lag, +max_lag] 内寻找 Spearman 最佳 lead/lag 相关性。"""
        lag_corrs: Dict[str, Optional[float]] = {}
        best_lag: Optional[int] = None
        best_corr: Optional[float] = None
        for lag in range(-max_lag, max_lag + 1):
            aligned = pd.DataFrame({
                "primary": tmp[primary_col],
                "secondary": tmp[secondary_col].shift(lag),
            }).dropna()
            if len(aligned) < max(20, int(0.5 * len(tmp))):
                corr = np.nan
            else:
                corr = aligned["primary"].corr(aligned["secondary"], method="spearman")
            lag_corrs[str(lag)] = float(corr) if pd.notna(corr) else None
            if pd.notna(corr) and (best_corr is None or corr > best_corr):
                best_corr = float(corr)
                best_lag = int(lag)
        return best_lag, best_corr, lag_corrs

    def _attention_shock_overlap_rate(
        self,
        tmp: pd.DataFrame,
        primary_col: str,
        secondary_col: str,
        max_lag: int,
        top_quantile: float,
    ) -> Tuple[Optional[float], int, int]:
        """验证 top attention shock 是否在 ±max_lag 天内互相确认。"""
        if "date" not in tmp.columns:
            return None, 0, 0
        work = tmp[["date", primary_col, secondary_col]].dropna().copy()
        if work.empty:
            return None, 0, 0
        work["date"] = pd.to_datetime(work["date"]).dt.date
        p_thr = work[primary_col].quantile(top_quantile)
        s_thr = work[secondary_col].quantile(top_quantile)
        # 注意：这里验证的是正向 attention shock；z-score 全部低于 0 时，不应强行制造 shock。
        p_events = sorted(work.loc[work[primary_col] >= max(p_thr, 0.0), "date"].dropna().unique())
        s_events = sorted(work.loc[work[secondary_col] >= max(s_thr, 0.0), "date"].dropna().unique())
        if not p_events or not s_events:
            return None, len(p_events), len(s_events)

        def _match_rate(src, dst):
            matched = 0
            for d in src:
                if any(abs((pd.Timestamp(d) - pd.Timestamp(e)).days) <= max_lag for e in dst):
                    matched += 1
            return matched / len(src) if src else np.nan

        p_to_s = _match_rate(p_events, s_events)
        s_to_p = _match_rate(s_events, p_events)
        rate = min(p_to_s, s_to_p)
        return float(rate) if pd.notna(rate) else None, len(p_events), len(s_events)

    def _attention_recent_direction_agreement(
        self,
        tmp: pd.DataFrame,
        primary_col: str,
        secondary_col: str,
        best_lag: int,
        recent_window: int,
    ) -> Tuple[Optional[float], int]:
        """最近窗口内 7D change 的方向一致率，防止最近状态明显冲突。"""
        work = pd.DataFrame({
            "primary": tmp[primary_col],
            "secondary": tmp[secondary_col].shift(best_lag),
        }).dropna().tail(recent_window)
        if len(work) < max(10, recent_window // 2):
            return None, int(len(work))
        d = pd.DataFrame({
            "dp": work["primary"].diff(7),
            "ds": work["secondary"].diff(7),
        }).dropna()
        d = d[(d["dp"].abs() > 1e-12) | (d["ds"].abs() > 1e-12)]
        if len(d) < 8:
            return None, int(len(d))
        agree = (np.sign(d["dp"]) == np.sign(d["ds"])).mean()
        return float(agree), int(len(d))

    def validate_pair_attention_strict(
        self,
        df: pd.DataFrame,
        primary_col: str,
        secondary_col: str,
        label: str,
    ) -> Tuple[dict, pd.Series]:
        """
        Liu attention 严格验证。

        输入应为 rolling z-score 后的 attention state。通过条件包括样本重叠、
        same-day / lead-lag Spearman、shock overlap 与 recent direction agreement。
        验证失败则不生成 validated attention 特征。
        """
        result = {
            "primary": primary_col,
            "secondary": secondary_col,
            "label": label,
            "pass": False,
            "reason": "",
            "validation_method": "rolling_zscore_lead_lag_shock_overlap",
            "overlap_obs_total": 0,
            "overlap_obs_window": 0,
            "same_day_spearman_corr": None,
            "best_lag": None,
            "best_lag_spearman_corr": None,
            "lag_corrs": {},
            "top_shock_overlap_rate": None,
            "primary_top_shock_count": 0,
            "secondary_top_shock_count": 0,
            "recent_direction_agreement": None,
            "recent_direction_obs": 0,
            "thresholds": {
                "min_overlap": self.cfg.attention_validation_min_overlap,
                "window": self.cfg.attention_validation_window,
                "max_lag_days": self.cfg.attention_lead_lag_days,
                "min_same_day_spearman": self.cfg.attention_min_same_day_spearman,
                "min_best_lag_spearman": self.cfg.attention_min_best_lag_spearman,
                "min_shock_overlap_rate": self.cfg.attention_min_shock_overlap_rate,
                "min_recent_direction_agreement": self.cfg.attention_min_recent_direction_agreement,
                "top_quantile": self.cfg.attention_top_quantile,
            },
            "validated_obs": 0,
        }
        if primary_col not in df.columns or secondary_col not in df.columns:
            result["reason"] = "missing rolling z-score attention source column"
            return result, pd.Series(np.nan, index=df.index, dtype="float64")

        keep_cols = ["date", primary_col, secondary_col] if "date" in df.columns else [primary_col, secondary_col]
        overlap_mask = df[[primary_col, secondary_col]].notna().all(axis=1)
        overlap_all = df.loc[overlap_mask, keep_cols].dropna().copy()
        result["overlap_obs_total"] = int(len(overlap_all))
        if len(overlap_all) < self.cfg.attention_validation_min_overlap:
            result["reason"] = "insufficient overlapping rolling attention observations"
            return result, pd.Series(np.nan, index=df.index, dtype="float64")

        window = min(int(self.cfg.attention_validation_window), len(overlap_all))
        tmp = overlap_all.tail(window).copy()
        result["overlap_obs_window"] = int(len(tmp))
        if tmp[primary_col].std(skipna=True) <= 1e-8 or tmp[secondary_col].std(skipna=True) <= 1e-8:
            result["reason"] = "attention source nearly constant in validation window"
            return result, pd.Series(np.nan, index=df.index, dtype="float64")

        same_corr = tmp[primary_col].corr(tmp[secondary_col], method="spearman")
        result["same_day_spearman_corr"] = float(same_corr) if pd.notna(same_corr) else None

        best_lag, best_corr, lag_corrs = self._attention_best_lag_corr(
            tmp, primary_col, secondary_col, int(self.cfg.attention_lead_lag_days)
        )
        result["best_lag"] = best_lag
        result["best_lag_spearman_corr"] = best_corr
        result["lag_corrs"] = lag_corrs

        shock_rate, p_shocks, s_shocks = self._attention_shock_overlap_rate(
            tmp, primary_col, secondary_col, int(self.cfg.attention_lead_lag_days), float(self.cfg.attention_top_quantile)
        )
        result["top_shock_overlap_rate"] = shock_rate
        result["primary_top_shock_count"] = int(p_shocks)
        result["secondary_top_shock_count"] = int(s_shocks)

        if best_lag is None:
            recent_agree, recent_n = None, 0
        else:
            recent_agree, recent_n = self._attention_recent_direction_agreement(
                tmp, primary_col, secondary_col, int(best_lag), int(self.cfg.attention_recent_window_days)
            )
        result["recent_direction_agreement"] = recent_agree
        result["recent_direction_obs"] = int(recent_n)

        failures = []
        if same_corr is None or pd.isna(same_corr) or same_corr < self.cfg.attention_min_same_day_spearman:
            failures.append("same_day_spearman_below_threshold")
        if best_corr is None or pd.isna(best_corr) or best_corr < self.cfg.attention_min_best_lag_spearman:
            failures.append("best_lag_spearman_below_threshold")
        if shock_rate is None or pd.isna(shock_rate) or shock_rate < self.cfg.attention_min_shock_overlap_rate:
            failures.append("top_shock_overlap_below_threshold")
        if recent_agree is None or pd.isna(recent_agree) or recent_agree < self.cfg.attention_min_recent_direction_agreement:
            failures.append("recent_direction_agreement_below_threshold")

        if failures:
            result["reason"] = "strict attention validation failed: " + ", ".join(failures)
            return result, pd.Series(np.nan, index=df.index, dtype="float64")

        validated = pd.Series(np.nan, index=df.index, dtype="float64")
        validated.loc[overlap_mask] = df.loc[overlap_mask, primary_col]
        result["pass"] = True
        result["reason"] = "strict attention validation pass"
        result["validated_obs"] = int(validated.notna().sum())
        return result, validated


    def validate_price(self, df: pd.DataFrame) -> Tuple[dict, pd.Series]:
        """
        BTC 价格自动多源共识验证。

        不允许 manual price。价格必须来自自动抓取的免费公开源。
        逻辑：在 CoinGecko / CoinCap / Coinbase / Kraken / Yahoo / CryptoCompare / Binance 中，
        遍历所有自动来源 pair，按 overlap/corr/gap/direction 评分选择最佳 pair。
        返回的 validated price 使用所有通过共识源的逐日中位数，避免候选顺序主导。
        """
        candidates = [
            "btc_price_coingecko",
            "btc_price_coinbase",
            "btc_price_kraken",
            "btc_price_yahoo",
            "btc_price_cryptocompare",
            "btc_price_binance",
            "btc_price_coincap",
        ]
        candidates = [c for c in candidates if c in df.columns]
        best_fail: Optional[dict] = None
        best_fail_score: Tuple[int, float, float] = (-1, -1e99, -1e99)
        passed_pairs: List[dict] = []

        for i, primary in enumerate(candidates):
            for secondary in candidates[i + 1:]:
                result, _ = self.validate_pair_level(
                    df,
                    primary,
                    secondary,
                    min_corr=0.95,
                    max_gap=self.cfg.price_max_gap,
                    window=int(self.cfg.price_validation_window),
                    require_direction=True,
                )
                result["primary_candidate_used"] = primary
                result["secondary_candidate_used"] = secondary
                result["price_validation_mode"] = "automatic_multi_source_scored_consensus"

                overlap = int(result.get("overlap_obs_total", 0) or 0)
                corr = float(result.get("corr") if result.get("corr") is not None else -1e99)
                gap = float(result.get("latest_gap") if result.get("latest_gap") is not None else 1e99)
                score = (overlap, corr, -gap)
                result["price_pair_score"] = {
                    "overlap_obs_total": overlap,
                    "corr": result.get("corr"),
                    "negative_latest_gap": -gap if gap < 1e99 else None,
                }
                if score > best_fail_score:
                    best_fail = result
                    best_fail_score = score

                if result.get("pass"):
                    passed_pairs.append(result)

        if passed_pairs:
            passed_pairs = sorted(
                passed_pairs,
                key=lambda r: (
                    int(r.get("overlap_obs_total", 0) or 0),
                    float(r.get("corr") if r.get("corr") is not None else -1e99),
                    -float(r.get("latest_gap") if r.get("latest_gap") is not None else 1e99),
                ),
                reverse=True,
            )
            best = dict(passed_pairs[0])
            eligible_sources = sorted({
                src
                for r in passed_pairs
                for src in [r.get("primary_candidate_used"), r.get("secondary_candidate_used")]
                if src
            })

            observed_price = pd.DataFrame(index=df.index)
            for c in eligible_sources:
                observed_price[c] = df[c].where(self._observed_mask_for_col(df, c))

            valid_count = observed_price.notna().sum(axis=1)
            enough_sources = valid_count >= max(2, int(self.cfg.price_min_sources))
            validated = pd.Series(np.nan, index=df.index, dtype="float64")
            validated.loc[enough_sources] = observed_price.loc[enough_sources].median(axis=1)

            best["pass"] = True
            best["reason"] = (
                "automatic multi-source price validation pass: "
                f"best pair {best.get('primary_candidate_used')} vs {best.get('secondary_candidate_used')}; "
                f"median over eligible sources {eligible_sources}"
            )
            best["eligible_price_sources"] = eligible_sources
            best["passed_pair_count"] = len(passed_pairs)
            best["passed_pairs"] = [
                {
                    "primary": r.get("primary_candidate_used"),
                    "secondary": r.get("secondary_candidate_used"),
                    "corr": r.get("corr"),
                    "latest_gap": r.get("latest_gap"),
                    "overlap_obs_total": r.get("overlap_obs_total"),
                    "overlap_obs_window": r.get("overlap_obs_window"),
                }
                for r in passed_pairs
            ]
            best["validated_obs"] = int(validated.notna().sum())
            return best, validated

        if best_fail is None:
            best_fail = {
                "pass": False,
                "reason": "no automatic price source available",
                "price_validation_mode": "automatic_multi_source_scored_consensus",
                "primary_candidate_used": None,
                "secondary_candidate_used": None,
            }
        else:
            best_fail["reason"] = "no automatic price source pair passed validation"
        return best_fail, pd.Series(np.nan, index=df.index, dtype="float64")

    def validate_attention(self, df: pd.DataFrame) -> Tuple[dict, pd.Series, dict, pd.Series]:
        """
        Liu attention validation 严格重构。

        核心变化：
            - 不再用 raw daily shock 的简单 30D corr/direction 作为硬门槛；
            - 使用 log/ratio → 7D rolling → rolling z-score 后的 attention state；
            - 必须通过 overlap、same-day Spearman、lead-lag Spearman、top shock overlap、recent direction audit；
            - Google + Wiki 优先，GDELT + Wiki 备用；
            - 单源 Google/GDELT/Wiki 均不得进入 strict Liu。
        """
        attention_attempts = [
            ("google_wiki", "z_google_attention_7d", "z_wiki_attention_7d"),
            ("gdelt_wiki", "z_gdelt_attention_7d", "z_wiki_attention_7d"),
        ]
        att_result = None
        att_series = pd.Series(np.nan, index=df.index, dtype="float64")
        att_failures = []
        for mode, primary, secondary in attention_attempts:
            res, ser = self.validate_pair_attention_strict(df, primary, secondary, label=f"ordinary_attention:{mode}")
            res["attention_validation_mode"] = mode
            att_failures.append({
                "mode": mode,
                "reason": res.get("reason"),
                "overlap_obs_total": res.get("overlap_obs_total"),
                "same_day_spearman_corr": res.get("same_day_spearman_corr"),
                "best_lag": res.get("best_lag"),
                "best_lag_spearman_corr": res.get("best_lag_spearman_corr"),
                "top_shock_overlap_rate": res.get("top_shock_overlap_rate"),
                "recent_direction_agreement": res.get("recent_direction_agreement"),
            })
            if res.get("pass"):
                res["reason"] = f"ordinary attention strict validation pass by {mode}"
                att_result = res
                att_series = ser
                break
        if att_result is None:
            att_result = {
                "primary": "google_or_gdelt_attention",
                "secondary": "z_wiki_attention_7d",
                "pass": False,
                "reason": "ordinary attention strict validation failed: neither Google+Wiki nor GDELT+Wiki passed",
                "attention_validation_mode": "none",
                "validation_method": "rolling_zscore_lead_lag_shock_overlap",
                "attempts": att_failures,
                "validated_obs": 0,
            }

        negative_attempts = [
            ("google_wiki", "z_google_negative_ratio_7d", "z_wiki_negative_ratio_7d"),
            ("gdelt_wiki", "z_gdelt_negative_ratio_7d", "z_wiki_negative_ratio_7d"),
        ]
        neg_result = None
        neg_series = pd.Series(np.nan, index=df.index, dtype="float64")
        neg_failures = []
        for mode, primary, secondary in negative_attempts:
            res, ser = self.validate_pair_attention_strict(df, primary, secondary, label=f"negative_attention:{mode}")
            res["negative_attention_validation_mode"] = mode
            neg_failures.append({
                "mode": mode,
                "reason": res.get("reason"),
                "overlap_obs_total": res.get("overlap_obs_total"),
                "same_day_spearman_corr": res.get("same_day_spearman_corr"),
                "best_lag": res.get("best_lag"),
                "best_lag_spearman_corr": res.get("best_lag_spearman_corr"),
                "top_shock_overlap_rate": res.get("top_shock_overlap_rate"),
                "recent_direction_agreement": res.get("recent_direction_agreement"),
            })
            if res.get("pass"):
                res["reason"] = f"negative attention strict validation pass by {mode}"
                neg_result = res
                neg_series = ser
                break
        if neg_result is None:
            neg_result = {
                "primary": "google_or_gdelt_negative",
                "secondary": "z_wiki_negative_ratio_7d",
                "pass": False,
                "reason": "negative attention strict validation failed: neither Google+Wiki nor GDELT+Wiki passed",
                "negative_attention_validation_mode": "none",
                "validation_method": "rolling_zscore_lead_lag_shock_overlap",
                "attempts": neg_failures,
                "validated_obs": 0,
            }

        return att_result, att_series, neg_result, neg_series

    def validate_etf_cumulative_flow(self, df: pd.DataFrame) -> Tuple[dict, pd.Series]:
        """
        ETF flow strict policy:
            - manual ETF CSV is diagnostic only and cannot validate an automatic source.
            - Farside single source is not enough for strict market-access validation.
            - Until a second independent automatic ETF flow source is added, ETF flow is excluded from strict model.
        """
        primary_col = "etf_net_flow_usd_farside"
        manual_col = "etf_net_flow_usd_manual"
        result = {
            "primary": primary_col,
            "secondary": None,
            "pass": False,
            "reason": "ETF flow excluded from strict validation: manual ETF CSV is diagnostic only and no independent automatic second source is configured.",
            "strict_source_independence": "independent_automatic_source_required",
            "manual_source_policy": "manual ETF data may be loaded for diagnostics but cannot generate validated_etf_flow_usd_7d",
            "farside_obs": int(df[primary_col].notna().sum()) if primary_col in df.columns else 0,
            "manual_obs": int(df[manual_col].notna().sum()) if manual_col in df.columns else 0,
            "validated_obs": 0,
        }
        return result, pd.Series(np.nan, index=df.index, dtype="float64")

    def validate_all(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        out = df.copy()
        report: Dict[str, Any] = {
            "strict_validation_policy": "Only cross-validated variables enter the pricing model.",
            "variables": {},
            "excluded_variables": [],
        }

        # ----------------------------------------------------
        # 4.1 价格验证：未通过则不能输出严格估值。
        # ----------------------------------------------------
        price_res, out["validated_btc_price"] = self.validate_price(out)
        report["variables"]["btc_price"] = price_res
        if not price_res["pass"]:
            report["excluded_variables"].append({"variable": "btc_price", "reason": price_res["reason"]})

        # ----------------------------------------------------
        # 4.2 Hashrate：level + correlation 验证。
        # ----------------------------------------------------
        hr_res, out["validated_hashrate_7d"] = self.validate_pair_level(
            out,
            "hashrate_ehs_blockchain_7d",
            "hashrate_ehs_coinmetrics_7d",
            min_corr=self.cfg.hashrate_min_corr,
            max_gap=self.cfg.hashrate_max_gap,
            window=30,
            require_direction=True,
        )
        report["variables"]["hashrate"] = hr_res
        if not hr_res["pass"]:
            report["excluded_variables"].append({"variable": "hashrate", "reason": hr_res["reason"]})

        # ----------------------------------------------------
        # 4.3 Active addresses：只用于 BDK，且用分位状态验证。
        # ----------------------------------------------------
        aa_res, out["validated_active_addresses_7d"] = self.validate_pair_percentile(
            out,
            "active_addresses_blockchain_7d",
            "active_addresses_coinmetrics_7d",
            min_corr=self.cfg.active_min_corr,
            max_percentile_gap=self.cfg.active_max_percentile_gap,
            window=min(90, self.cfg.days),
        )
        report["variables"]["active_addresses"] = aa_res
        if not aa_res["pass"]:
            report["excluded_variables"].append({"variable": "active_addresses", "reason": aa_res["reason"]})

        # ----------------------------------------------------
        # 4.3b 核心 validated 输入的真实观测检查。
        # 清洗可插值；当前 strict 输入必须主要来自真实观测。
        # ----------------------------------------------------
        price_primary = price_res.get("primary_candidate_used")
        price_secondary = price_res.get("secondary_candidate_used")
        if price_primary:
            price_primary_obs = out.get(f"{price_primary}_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        else:
            price_primary_obs = pd.Series(0, index=out.index)
        if price_secondary:
            price_secondary_obs = out.get(f"{price_secondary}_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        else:
            price_secondary_obs = pd.Series(0, index=out.index)
        out["validated_btc_price_observed_ok"] = (
            out["validated_btc_price"].notna() &
            (price_primary_obs >= 1) &
            (price_secondary_obs >= 1)
        )

        out["validated_hashrate_observed_ok"] = (
            out["validated_hashrate_7d"].notna() &
            (out.get("hashrate_ehs_blockchain_observed_count_7d", pd.Series(0, index=out.index)).fillna(0) >= 5) &
            (out.get("hashrate_ehs_coinmetrics_observed_count_7d", pd.Series(0, index=out.index)).fillna(0) >= 5)
        )
        out["validated_active_addresses_observed_ok"] = (
            out["validated_active_addresses_7d"].notna() &
            (out.get("active_addresses_blockchain_observed_count_7d", pd.Series(0, index=out.index)).fillna(0) >= 5) &
            (out.get("active_addresses_coinmetrics_observed_count_7d", pd.Series(0, index=out.index)).fillna(0) >= 5)
        )
        report["core_observed_policy"] = "latest strict core requires observed price sources on the same day and at least 5/7 real observations in both hashrate and active-address 7D windows."

        # ----------------------------------------------------
        # 4.4 Transaction count：进入 Biais transaction benefit。
        # ----------------------------------------------------
        tx_res, out["validated_transaction_count_7d"] = self.validate_pair_level(
            out,
            "transaction_count_blockchain_7d",
            "transaction_count_coinmetrics_7d",
            min_corr=self.cfg.tx_count_min_corr,
            max_gap=self.cfg.tx_count_max_gap,
            window=30,
            require_direction=True,
        )
        report["variables"]["transaction_count"] = tx_res
        if not tx_res["pass"]:
            report["excluded_variables"].append({"variable": "transaction_count", "reason": tx_res["reason"]})

        # ----------------------------------------------------
        # 4.5 Transfer volume：口径差异大，用分位状态验证。
        # strict Biais 只允许独立来源验证；同源派生仅作诊断。
        # ----------------------------------------------------
        tv_res, out["validated_transfer_volume_usd_7d"] = self.validate_pair_percentile(
            out,
            "transfer_volume_usd_blockchain_7d",
            "transfer_volume_usd_independent_7d",
            min_corr=self.cfg.transfer_min_corr,
            max_percentile_gap=self.cfg.transfer_max_percentile_gap,
            window=min(90, self.cfg.days),
        )
        tv_res["validation_source_note"] = "strict independent validation: Blockchain transfer-volume USD vs Coin Metrics transfer-volume USD. Same-source derived Blockchain BTC × price is diagnostic only."
        tv_res["strict_source_independence"] = "independent_cross_source_required"
        report["variables"]["transfer_volume"] = tv_res
        if not tv_res["pass"]:
            report["excluded_variables"].append({"variable": "transfer_volume", "reason": tv_res["reason"]})

        tv_diag_res, _ = self.validate_pair_percentile(
            out,
            "transfer_volume_usd_blockchain_7d",
            "transfer_volume_usd_blockchain_derived_7d",
            min_corr=self.cfg.transfer_min_corr,
            max_percentile_gap=self.cfg.transfer_max_percentile_gap,
            window=min(90, self.cfg.days),
        )
        tv_diag_res["strict_eligible"] = False
        tv_diag_res["validation_source_note"] = "same-source derived consistency only: Blockchain USD transfer volume vs Blockchain BTC transfer volume × automatic BTC price. Not allowed to pass strict Biais."
        report["variables"]["transfer_volume_derived_consistency"] = tv_diag_res

        # ----------------------------------------------------
        # 4.6 Fee：平均手续费验证。
        # strict Biais 只允许 Blockchain fee proxy vs independent automatic fee proxy。
        # Blockchain total-fee-USD vs total-fee-BTC × price 只作为 diagnostic consistency。
        # ----------------------------------------------------
        fee_res, out["validated_avg_fee_usd_7d"] = self.validate_pair_percentile(
            out,
            "avg_fee_usd_blockchain_primary_7d",
            "avg_fee_usd_independent_7d",
            min_corr=self.cfg.fee_min_corr,
            max_percentile_gap=self.cfg.fee_max_percentile_gap,
            window=min(90, self.cfg.days),
        )
        fee_res["validation_source_note"] = "strict independent validation: Blockchain average-fee proxy vs Coin Metrics average-fee proxy. Same-source Blockchain BTC/USD fee consistency is diagnostic only."
        fee_res["strict_source_independence"] = "independent_cross_source_required"
        report["variables"]["transaction_fee"] = fee_res
        if not fee_res["pass"]:
            report["excluded_variables"].append({"variable": "transaction_fee", "reason": fee_res["reason"]})

        fee_diag_res, _ = self.validate_pair_percentile(
            out,
            "avg_fee_usd_blockchain_primary_7d",
            "avg_fee_usd_blockchain_from_total_btc_7d",
            min_corr=self.cfg.fee_min_corr,
            max_percentile_gap=self.cfg.fee_max_percentile_gap,
            window=min(90, self.cfg.days),
        )
        fee_diag_res["strict_eligible"] = False
        fee_diag_res["validation_source_note"] = "same-source derived consistency only: Blockchain fee USD proxy vs Blockchain fee BTC × automatic BTC price / tx-count. Not allowed to pass strict Biais."
        report["variables"]["transaction_fee_derived_consistency"] = fee_diag_res

        # ----------------------------------------------------
        # 4.7 ETF flow：manual source 不得进入 strict model；当前无第二个独立自动源，因此 ETF 只作 diagnostic。
        # ----------------------------------------------------
        etf_res, out["validated_etf_flow_usd_7d"] = self.validate_etf_cumulative_flow(out)
        report["variables"]["etf_flow"] = etf_res
        if not etf_res["pass"]:
            report["excluded_variables"].append({"variable": "etf_flow", "reason": etf_res["reason"]})

        # ----------------------------------------------------
        # 4.8 Attention：Google + Wikipedia 双源一致才入 Liu。
        # ----------------------------------------------------
        att_res, out["validated_attention_z"], neg_res, out["validated_negative_attention_z"] = self.validate_attention(out)
        report["variables"]["ordinary_attention"] = att_res
        report["variables"]["negative_attention"] = neg_res
        if not att_res["pass"]:
            report["excluded_variables"].append({"variable": "ordinary_attention", "reason": att_res["reason"]})
        if not neg_res["pass"]:
            report["excluded_variables"].append({"variable": "negative_attention", "reason": neg_res["reason"]})

        # ----------------------------------------------------
        # 4.9 基于 validated 数据构造可入模 z-score。
        # ----------------------------------------------------
        validated_to_z = [
            "validated_transaction_count_7d",
            "validated_transfer_volume_usd_7d",
            "validated_avg_fee_usd_7d",
            "validated_etf_flow_usd_7d",
        ]
        for c in validated_to_z:
            out[f"z_{c}"] = rolling_zscore(out[c], self.cfg.z_window, self.cfg.z_min_periods)

        # 价格通过后，动量可通过；否则动量不进入模型。
        if price_res["pass"]:
            out["validated_ret_7d"] = np.log(out["validated_btc_price"]).diff(7)
            out["validated_ret_14d"] = np.log(out["validated_btc_price"]).diff(14)
            out["validated_ret_28d"] = np.log(out["validated_btc_price"]).diff(28)
            out["z_validated_ret_7d"] = rolling_zscore(out["validated_ret_7d"], self.cfg.z_window, self.cfg.z_min_periods)
            out["z_validated_ret_14d"] = rolling_zscore(out["validated_ret_14d"], self.cfg.z_window, self.cfg.z_min_periods)
            out["z_validated_ret_28d"] = rolling_zscore(out["validated_ret_28d"], self.cfg.z_window, self.cfg.z_min_periods)
            out["validated_realized_vol_30d"] = np.log(out["validated_btc_price"]).diff(1).rolling(30, min_periods=15).std() * math.sqrt(365)
            # validated drawdown_90d 固定为 90D 口径，避免整体样本窗口改变 crash risk 定义。
            drawdown_window = min(self.cfg.drawdown_window, self.cfg.days)
            out["validated_drawdown_90d"] = 1.0 - out["validated_btc_price"] / out["validated_btc_price"].rolling(drawdown_window, min_periods=20).max()
            out["z_validated_realized_vol_30d"] = rolling_zscore(out["validated_realized_vol_30d"], self.cfg.z_window, self.cfg.z_min_periods)
            out["z_validated_drawdown_90d"] = rolling_zscore(out["validated_drawdown_90d"], self.cfg.z_window, self.cfg.z_min_periods)
            momentum_pass = True
        else:
            momentum_pass = False

        # network/activity growth：不使用 active addresses，避免与 BDK 重复。
        # 这里仅用 transaction_count 或 transfer_volume 的增长作为“市场/网络活动状态”代理。
        if tx_res["pass"]:
            out["validated_activity_growth"] = out["validated_transaction_count_7d"].pct_change(7)
            out["z_validated_activity_growth"] = rolling_zscore(out["validated_activity_growth"], self.cfg.z_window, self.cfg.z_min_periods)
            activity_growth_pass = True
        elif tv_res["pass"]:
            out["validated_activity_growth"] = out["validated_transfer_volume_usd_7d"].pct_change(7)
            out["z_validated_activity_growth"] = rolling_zscore(out["validated_activity_growth"], self.cfg.z_window, self.cfg.z_min_periods)
            activity_growth_pass = True
        else:
            out["validated_activity_growth"] = np.nan
            out["z_validated_activity_growth"] = np.nan
            activity_growth_pass = False

        # ----------------------------------------------------
        # 4.10 模块通过情况
        # ----------------------------------------------------
        bdk_pass = bool(price_res["pass"] and hr_res["pass"] and aa_res["pass"])

        transaction_benefit_pass = bool(tx_res["pass"] and tv_res["pass"])
        transaction_cost_pass = bool(fee_res["pass"])
        market_access_pass = bool(etf_res["pass"])
        crash_risk_pass = bool(price_res["pass"])
        biais_pass_count = sum([transaction_benefit_pass, transaction_cost_pass, market_access_pass, crash_risk_pass])
        # Biais 的核心是交易便利收益。没有 transaction benefit，不允许 Biais 进入 strict 模型。
        biais_module_pass = bool(transaction_benefit_pass and (transaction_cost_pass or market_access_pass or crash_risk_pass))
        biais_full_pass = bool(transaction_benefit_pass and transaction_cost_pass and crash_risk_pass)

        ordinary_attention_pass = bool(att_res["pass"])
        negative_attention_pass = bool(neg_res["pass"])
        liu_pass_count = sum([momentum_pass, ordinary_attention_pass, negative_attention_pass, activity_growth_pass])
        # Liu 严格折价层必须有 momentum + 至少一个 attention 维度；
        # momentum + activity growth 只能作为 diagnostic，不进入 strict Liu discount。
        liu_module_pass = bool(momentum_pass and (ordinary_attention_pass or negative_attention_pass))
        liu_full_pass = bool(momentum_pass and ordinary_attention_pass and negative_attention_pass)
        liu_momentum_activity_diagnostic = bool(momentum_pass and activity_growth_pass and not liu_module_pass)

        if not bdk_pass:
            model_status = "No Strict Valuation"
        elif biais_full_pass and liu_full_pass:
            model_status = "Full Model"
        elif biais_module_pass and liu_module_pass:
            model_status = "Core Model"
        elif biais_module_pass or liu_module_pass:
            model_status = "Reduced Model"
        else:
            model_status = "BDK Only"

        # ----------------------------------------------------
        # 4.11 每个 validated 变量的有效样本数。
        # ----------------------------------------------------
        validated_count_cols = [
            "validated_btc_price",
            "validated_hashrate_7d",
            "validated_active_addresses_7d",
            "validated_transaction_count_7d",
            "validated_transfer_volume_usd_7d",
            "validated_avg_fee_usd_7d",
            "validated_etf_flow_usd_7d",
            "validated_attention_z",
            "validated_negative_attention_z",
            "validated_ret_7d",
            "validated_activity_growth",
        ]
        report["validated_observation_counts"] = {
            c: int(out[c].notna().sum()) for c in validated_count_cols if c in out.columns
        }
        report["core_observed_ok_counts"] = {
            c: int(out[c].fillna(False).astype(bool).sum())
            for c in [
                "validated_btc_price_observed_ok",
                "validated_hashrate_observed_ok",
                "validated_active_addresses_observed_ok",
            ]
            if c in out.columns
        }

        report["module_pass"] = {
            "bdk_pass": bdk_pass,
            "biais_pass_count": biais_pass_count,
            "biais_module_pass": biais_module_pass,
            "biais_full_pass": biais_full_pass,
            "biais_components": {
                "transaction_benefit_pass": transaction_benefit_pass,
                "transaction_cost_pass": transaction_cost_pass,
                "market_access_pass": market_access_pass,
                "crash_risk_pass": crash_risk_pass,
            },
            "liu_pass_count": liu_pass_count,
            "liu_module_pass": liu_module_pass,
            "liu_full_pass": liu_full_pass,
            "liu_momentum_activity_diagnostic": liu_momentum_activity_diagnostic,
            "liu_components": {
                "momentum_pass": momentum_pass,
                "ordinary_attention_pass": ordinary_attention_pass,
                "negative_attention_pass": negative_attention_pass,
                "activity_growth_pass": activity_growth_pass,
            },
            "model_status": model_status,
        }

        # 数据质量：通过变量越多，分数越高。
        total_core = 3  # price, hashrate, active addresses
        passed_core = sum([price_res["pass"], hr_res["pass"], aa_res["pass"]])
        total_optional = 8
        passed_optional = sum([tx_res["pass"], tv_res["pass"], fee_res["pass"], etf_res["pass"], att_res["pass"], neg_res["pass"], momentum_pass, activity_growth_pass])
        report["validated_data_quality_score"] = round(0.65 * passed_core / total_core + 0.35 * passed_optional / total_optional, 4)
        out["validated_data_quality_score"] = report["validated_data_quality_score"]

        return out, report
