from __future__ import annotations

import math
from datetime import timedelta
from typing import Dict

import numpy as np
import pandas as pd

from .config import ModelConfig
from .utils import mean_existing, rolling_zscore, today_utc_date, winsorize_series


class DataProcessor:
    """把原始数据清洗为日频 master table。"""

    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg

    def build_date_frame(self) -> pd.DataFrame:
        end = today_utc_date()
        start = end - timedelta(days=self.cfg.days - 1)
        return pd.DataFrame({"date": pd.date_range(start=start, end=end, freq="D").date})

    def merge_all(self, data: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        master = self.build_date_frame()
        for _, df in data.items():
            if df is None or df.empty or "date" not in df.columns:
                continue
            tmp = df.copy()
            tmp["date"] = pd.to_datetime(tmp["date"]).dt.date
            master = master.merge(tmp, on="date", how="left")
        return master.sort_values("date").reset_index(drop=True)

    def clean_and_engineer(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy().sort_values("date").reset_index(drop=True)
        for c in out.columns:
            if c != "date":
                out[c] = pd.to_numeric(out[c], errors="coerce")

        # ----------------------------------------------------
        # 3.1 价格：主源 CoinGecko，验证源 CoinCap / Binance；不做无限前值填充。
        # ----------------------------------------------------
        if "btc_price_coingecko" not in out:
            out["btc_price_coingecko"] = np.nan
        if "btc_price_coincap" not in out:
            out["btc_price_coincap"] = np.nan
        if "btc_price_binance" not in out:
            out["btc_price_binance"] = np.nan
        if "btc_price_coinbase" not in out:
            out["btc_price_coinbase"] = np.nan
        if "btc_price_kraken" not in out:
            out["btc_price_kraken"] = np.nan
        if "btc_price_yahoo" not in out:
            out["btc_price_yahoo"] = np.nan
        if "btc_price_cryptocompare" not in out:
            out["btc_price_cryptocompare"] = np.nan
        if "btc_volume_coingecko" not in out:
            out["btc_volume_coingecko"] = np.nan

        # 保留真实观测标记；核心输入不能主要来自填补值。
        for c in ["btc_price_coingecko", "btc_price_coincap", "btc_price_binance", "btc_price_coinbase", "btc_price_kraken", "btc_price_yahoo", "btc_price_cryptocompare", "btc_volume_coingecko"]:
            out[f"{c}_observed_flag"] = out[c].notna().astype(int)

        # 价格最多 ffill 1 天。
        out["btc_price_coingecko"] = out["btc_price_coingecko"].ffill(limit=1)
        out["btc_price_coincap"] = out["btc_price_coincap"].ffill(limit=1)
        out["btc_price_binance"] = out["btc_price_binance"].ffill(limit=1)
        out["btc_price_coinbase"] = out["btc_price_coinbase"].ffill(limit=1)
        out["btc_price_kraken"] = out["btc_price_kraken"].ffill(limit=1)
        out["btc_price_yahoo"] = out["btc_price_yahoo"].ffill(limit=1)
        out["btc_price_cryptocompare"] = out["btc_price_cryptocompare"].ffill(limit=1)
        out["btc_volume_coingecko"] = out["btc_volume_coingecko"].ffill(limit=1)

        # ----------------------------------------------------
        # 3.2 Hashrate / Active / Tx / Fee：只做短缺插值，最终是否进模型由 CrossValidator 决定。
        # ----------------------------------------------------
        required_feature_cols = [
            "hashrate_ehs_blockchain", "hashrate_ehs_coinmetrics",
            "active_addresses_blockchain", "active_addresses_coinmetrics",
            "transaction_count_blockchain", "transaction_count_coinmetrics",
            "transfer_volume_usd_blockchain", "transfer_volume_usd_coinmetrics", "transfer_volume_btc_blockchain",
            "avg_fee_usd_blockchain", "avg_fee_usd_coinmetrics",
            "total_fee_usd_blockchain", "total_fee_btc_blockchain", "total_fee_usd_coinmetrics",
            "transfer_volume_usd_blockchair", "avg_fee_usd_blockchair", "total_fee_usd_blockchair", "transaction_count_blockchair", "avg_fee_usd_mempool_proxy",
            "etf_net_flow_usd_farside", "etf_net_flow_usd_manual",
            "wiki_views_bitcoin", "wiki_views_cryptocurrency_bubble", "wiki_views_bitcoin_scalability_problem",
            "gdelt_news_count", "gdelt_negative_news_count",
            "gt_bitcoin", "gt_bitcoin_price", "gt_bitcoin_crash", "gt_bitcoin_hack", "gt_bitcoin_regulation",
        ]
        missing_feature_cols = {c: pd.Series(np.nan, index=out.index) for c in required_feature_cols if c not in out.columns}
        if missing_feature_cols:
            out = pd.concat([out, pd.DataFrame(missing_feature_cols, index=out.index)], axis=1)

        # 仅链上连续数据允许短缺插值；ETF/attention 不插值。
        continuous_cols = [
            "hashrate_ehs_blockchain", "hashrate_ehs_coinmetrics",
            "active_addresses_blockchain", "active_addresses_coinmetrics",
            "transaction_count_blockchain", "transaction_count_coinmetrics",
            "transfer_volume_usd_blockchain", "transfer_volume_usd_coinmetrics", "transfer_volume_btc_blockchain",
            "avg_fee_usd_blockchain", "avg_fee_usd_coinmetrics",
            "total_fee_usd_blockchain", "total_fee_btc_blockchain", "total_fee_usd_coinmetrics",
            "transfer_volume_usd_blockchair", "avg_fee_usd_blockchair", "total_fee_usd_blockchair", "transaction_count_blockchair", "avg_fee_usd_mempool_proxy",
        ]
        # 先记录真实观测标记，再做短缺插值。
        continuous_aux_cols = {}
        for c in continuous_cols:
            observed_flag = out[c].notna().astype(int)
            out[c] = out[c].interpolate(limit=2).ffill(limit=2)
            imputed_flag = ((out[c].notna()) & (observed_flag == 0)).astype(int)
            continuous_aux_cols[f"{c}_observed_flag"] = observed_flag
            continuous_aux_cols[f"{c}_imputed_flag"] = imputed_flag
        if continuous_aux_cols:
            out = pd.concat([out, pd.DataFrame(continuous_aux_cols, index=out.index)], axis=1)
            out = out.copy()

        # ----------------------------------------------------
        # 3.2b Biais 层严格区分 independent validation 与 same-source derived consistency。
        # - independent strict source：Blockchain vs Coin Metrics / 其他独立自动源。
        # - Blockchain USD vs Blockchain BTC × price 只算 derived consistency，不再让 Biais strict layer 通过。
        # ----------------------------------------------------
        derived_features = {}

        tx_count_safe = out["transaction_count_blockchain"].replace(0, np.nan)
        tx_count_cm_safe = out["transaction_count_coinmetrics"].replace(0, np.nan)
        price_for_derived = out["btc_price_primary" if "btc_price_primary" in out.columns else "btc_price_coingecko"]

        # 同源派生一致性仅作诊断，不作为 strict source。
        derived_features["transfer_volume_usd_blockchain_derived"] = out["transfer_volume_btc_blockchain"] * price_for_derived
        derived_features["avg_fee_usd_blockchain_from_total_usd"] = out["total_fee_usd_blockchain"] / tx_count_safe
        derived_features["avg_fee_usd_blockchain_from_total_btc"] = out["total_fee_btc_blockchain"] * price_for_derived / tx_count_safe
        derived_features["avg_fee_usd_blockchain_primary"] = out["avg_fee_usd_blockchain"].combine_first(derived_features["avg_fee_usd_blockchain_from_total_usd"])

        # 独立 strict 候选源：Coin Metrics / Blockchair / mempool.space。
        tx_count_blockchair_safe = out["transaction_count_blockchair"].replace(0, np.nan)
        derived_features["transfer_volume_usd_independent"] = out["transfer_volume_usd_coinmetrics"].combine_first(out["transfer_volume_usd_blockchair"])
        derived_features["avg_fee_usd_coinmetrics_from_total_usd"] = out["total_fee_usd_coinmetrics"] / tx_count_cm_safe
        derived_features["avg_fee_usd_blockchair_from_total_usd"] = out["total_fee_usd_blockchair"] / tx_count_blockchair_safe
        derived_features["avg_fee_usd_independent"] = (
            out["avg_fee_usd_coinmetrics"]
            .combine_first(derived_features["avg_fee_usd_coinmetrics_from_total_usd"])
            .combine_first(out["avg_fee_usd_blockchair"])
            .combine_first(derived_features["avg_fee_usd_blockchair_from_total_usd"])
            .combine_first(out["avg_fee_usd_mempool_proxy"])
        )

        out = pd.concat([out, pd.DataFrame(derived_features, index=out.index)], axis=1)

        # 派生字段必须由真实观测组合而来。
        derived_obs = {}
        price_obs = out.get("btc_price_coingecko_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        tx_obs = out.get("transaction_count_blockchain_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        tx_cm_obs = out.get("transaction_count_coinmetrics_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        tv_btc_obs = out.get("transfer_volume_btc_blockchain_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        fee_usd_obs = out.get("total_fee_usd_blockchain_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        fee_btc_obs = out.get("total_fee_btc_blockchain_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        avg_fee_direct_obs = out.get("avg_fee_usd_blockchain_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        avg_fee_cm_obs = out.get("avg_fee_usd_coinmetrics_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        tv_cm_obs = out.get("transfer_volume_usd_coinmetrics_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        fee_cm_total_obs = out.get("total_fee_usd_coinmetrics_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        tv_blockchair_obs = out.get("transfer_volume_usd_blockchair_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        avg_fee_blockchair_obs = out.get("avg_fee_usd_blockchair_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        fee_blockchair_total_obs = out.get("total_fee_usd_blockchair_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        tx_blockchair_obs = out.get("transaction_count_blockchair_observed_flag", pd.Series(0, index=out.index)).fillna(0)
        fee_mempool_obs = out.get("avg_fee_usd_mempool_proxy_observed_flag", pd.Series(0, index=out.index)).fillna(0)

        derived_obs["transfer_volume_usd_blockchain_derived_observed_flag"] = ((tv_btc_obs >= 1) & (price_obs >= 1)).astype(int)
        derived_obs["avg_fee_usd_blockchain_from_total_usd_observed_flag"] = ((fee_usd_obs >= 1) & (tx_obs >= 1)).astype(int)
        derived_obs["avg_fee_usd_blockchain_from_total_btc_observed_flag"] = ((fee_btc_obs >= 1) & (price_obs >= 1) & (tx_obs >= 1)).astype(int)
        derived_obs["avg_fee_usd_blockchain_primary_observed_flag"] = ((avg_fee_direct_obs >= 1) | ((fee_usd_obs >= 1) & (tx_obs >= 1))).astype(int)
        derived_obs["transfer_volume_usd_independent_observed_flag"] = ((tv_cm_obs >= 1) | (tv_blockchair_obs >= 1)).astype(int)
        derived_obs["avg_fee_usd_coinmetrics_from_total_usd_observed_flag"] = ((fee_cm_total_obs >= 1) & (tx_cm_obs >= 1)).astype(int)
        derived_obs["avg_fee_usd_blockchair_from_total_usd_observed_flag"] = ((fee_blockchair_total_obs >= 1) & (tx_blockchair_obs >= 1)).astype(int)
        derived_obs["avg_fee_usd_independent_observed_flag"] = (
            (avg_fee_cm_obs >= 1)
            | ((fee_cm_total_obs >= 1) & (tx_cm_obs >= 1))
            | (avg_fee_blockchair_obs >= 1)
            | ((fee_blockchair_total_obs >= 1) & (tx_blockchair_obs >= 1))
            | (fee_mempool_obs >= 1)
        ).astype(int)
        out = pd.concat([out, pd.DataFrame(derived_obs, index=out.index)], axis=1)
        out = out.copy()

        # ----------------------------------------------------
        # 3.3 7D/30D 平滑
        # ----------------------------------------------------
        smooth_cols = [
            "btc_price_coingecko", "btc_price_coincap", "btc_price_binance", "btc_price_coinbase", "btc_price_kraken", "btc_price_yahoo", "btc_price_cryptocompare", "btc_volume_coingecko",
            "hashrate_ehs_blockchain", "hashrate_ehs_coinmetrics",
            "active_addresses_blockchain", "active_addresses_coinmetrics",
            "transaction_count_blockchain", "transaction_count_coinmetrics",
            "transfer_volume_usd_blockchain", "transfer_volume_usd_coinmetrics", "transfer_volume_btc_blockchain", "transfer_volume_usd_blockchain_derived", "transfer_volume_usd_independent", "transfer_volume_usd_blockchair",
            "avg_fee_usd_blockchain", "avg_fee_usd_coinmetrics", "avg_fee_usd_blockchain_primary", "avg_fee_usd_independent", "avg_fee_usd_blockchair", "avg_fee_usd_mempool_proxy",
            "total_fee_usd_blockchain", "total_fee_btc_blockchain", "total_fee_usd_coinmetrics", "total_fee_usd_blockchair", "transaction_count_blockchair",
            "avg_fee_usd_blockchain_from_total_usd", "avg_fee_usd_blockchain_from_total_btc", "avg_fee_usd_blockchair_from_total_usd",
            "etf_net_flow_usd_farside", "etf_net_flow_usd_manual",
            "wiki_views_bitcoin", "wiki_views_cryptocurrency_bubble", "wiki_views_bitcoin_scalability_problem",
            "gdelt_news_count", "gdelt_negative_news_count",
            "gt_bitcoin", "gt_bitcoin_price", "gt_bitcoin_crash", "gt_bitcoin_hack", "gt_bitcoin_regulation",
        ]
        smooth_features = {}
        for c in smooth_cols:
            smooth_features[f"{c}_7d"] = out[c].rolling(self.cfg.smooth_window, min_periods=3).mean()
            smooth_features[f"{c}_30d"] = out[c].rolling(self.cfg.long_window, min_periods=10).mean()
            # 同步计算真实观测数量。
            obs_col = f"{c}_observed_flag"
            if obs_col in out.columns:
                smooth_features[f"{c}_observed_count_7d"] = out[obs_col].rolling(self.cfg.smooth_window, min_periods=1).sum()
                smooth_features[f"{c}_observed_count_30d"] = out[obs_col].rolling(self.cfg.long_window, min_periods=1).sum()
        if smooth_features:
            out = pd.concat([out, pd.DataFrame(smooth_features, index=out.index)], axis=1)
            out = out.copy()

        # ----------------------------------------------------
        # 3.4 收益、动量、波动率、回撤
        # ----------------------------------------------------
        out["btc_price_primary"] = out["btc_price_coingecko"]
        out["log_price"] = np.log(out["btc_price_primary"])
        out["ret_1d"] = out["log_price"].diff(1)
        out["ret_7d"] = out["log_price"].diff(7)
        out["ret_14d"] = out["log_price"].diff(14)
        out["ret_28d"] = out["log_price"].diff(28)
        out["realized_vol_30d"] = out["ret_1d"].rolling(30, min_periods=15).std() * math.sqrt(365)
        # 90D drawdown 固定为 min(90, days)。
        drawdown_window = min(self.cfg.drawdown_window, self.cfg.days)
        out["rolling_90d_high"] = out["btc_price_primary"].rolling(drawdown_window, min_periods=20).max()
        out["drawdown_from_90d_high"] = 1.0 - out["btc_price_primary"] / out["rolling_90d_high"]

        # ----------------------------------------------------
        # 3.5 Attention shock：注意只作为 raw feature，能否入模型由 CrossValidator 决定。
        # ----------------------------------------------------
        out["wiki_negative_views"] = out[["wiki_views_cryptocurrency_bubble", "wiki_views_bitcoin_scalability_problem"]].sum(axis=1, min_count=1)
        out["wiki_attention_shock"] = out["wiki_views_bitcoin"] - out["wiki_views_bitcoin"].rolling(28, min_periods=14).mean()
        out["wiki_negative_ratio"] = out["wiki_negative_views"] / out["wiki_views_bitcoin"].replace(0, np.nan)

        out["google_attention_raw"] = out[["gt_bitcoin", "gt_bitcoin_price"]].mean(axis=1, skipna=True)
        out["google_attention_shock"] = out["google_attention_raw"] - out["google_attention_raw"].rolling(28, min_periods=14).mean()
        out["google_negative_raw"] = out[["gt_bitcoin_crash", "gt_bitcoin_hack", "gt_bitcoin_regulation"]].mean(axis=1, skipna=True)
        out["google_negative_ratio"] = out["google_negative_raw"] / out["gt_bitcoin"].replace(0, np.nan)

        # GDELT attention proxy 是否入模由 Wiki 交叉验证决定。
        out["gdelt_attention_shock"] = out["gdelt_news_count"] - out["gdelt_news_count"].rolling(28, min_periods=14).mean()
        out["gdelt_negative_ratio"] = out["gdelt_negative_news_count"] / out["gdelt_news_count"].replace(0, np.nan)

        # Liu attention 统一为 log/ratio → 7D rolling → z-score。
        out["wiki_attention_log"] = np.log1p(out["wiki_views_bitcoin"].clip(lower=0))
        out["gdelt_attention_log"] = np.log1p(out["gdelt_news_count"].clip(lower=0))
        out["google_attention_log"] = np.log1p(out["google_attention_raw"].clip(lower=0))

        out["wiki_attention_7d"] = out["wiki_attention_log"].rolling(7, min_periods=5).mean()
        out["gdelt_attention_7d"] = out["gdelt_attention_log"].rolling(7, min_periods=5).mean()
        out["google_attention_7d"] = out["google_attention_log"].rolling(7, min_periods=5).mean()

        out["wiki_negative_ratio_7d"] = out["wiki_negative_ratio"].rolling(7, min_periods=5).mean()
        out["gdelt_negative_ratio_7d"] = out["gdelt_negative_ratio"].rolling(7, min_periods=5).mean()
        out["google_negative_ratio_7d"] = out["google_negative_ratio"].rolling(7, min_periods=5).mean()

        # ----------------------------------------------------
        # 3.6 极端值处理：只处理波动型 proxy，不处理原始核心链上值。
        # ----------------------------------------------------
        for c in [
            "wiki_attention_shock", "google_attention_shock", "gdelt_attention_shock",
            "wiki_attention_7d", "google_attention_7d", "gdelt_attention_7d",
            "wiki_negative_ratio", "google_negative_ratio", "gdelt_negative_ratio",
            "wiki_negative_ratio_7d", "google_negative_ratio_7d", "gdelt_negative_ratio_7d",
        ]:
            out[c] = winsorize_series(out[c])

        # ----------------------------------------------------
        # 3.7 z-score：raw z-score，不等于 validated feature。
        # ----------------------------------------------------
        z_cols = [
            "transaction_count_blockchain_7d", "transaction_count_coinmetrics_7d",
            "transfer_volume_usd_blockchain_7d", "transfer_volume_usd_coinmetrics_7d", "transfer_volume_usd_blockchain_derived_7d", "transfer_volume_usd_independent_7d",
            "avg_fee_usd_blockchain_7d", "avg_fee_usd_coinmetrics_7d", "avg_fee_usd_blockchain_primary_7d", "avg_fee_usd_independent_7d",
            "btc_volume_coingecko_7d",
            "etf_net_flow_usd_farside_7d", "etf_net_flow_usd_manual_7d",
            "wiki_attention_shock", "google_attention_shock", "gdelt_attention_shock",
            "wiki_attention_7d", "google_attention_7d", "gdelt_attention_7d",
            "wiki_negative_ratio", "google_negative_ratio", "gdelt_negative_ratio",
            "wiki_negative_ratio_7d", "google_negative_ratio_7d", "gdelt_negative_ratio_7d",
            "ret_7d", "ret_14d", "ret_28d",
            "realized_vol_30d", "drawdown_from_90d_high",
        ]
        z_features = {}
        for c in z_cols:
            if c in out.columns:
                z_features[f"z_{c}"] = rolling_zscore(out[c], self.cfg.z_window, self.cfg.z_min_periods)
        if z_features:
            out = pd.concat([out, pd.DataFrame(z_features, index=out.index)], axis=1)
            out = out.copy()

        return out
