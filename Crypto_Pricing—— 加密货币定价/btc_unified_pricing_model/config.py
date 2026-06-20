from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass
class ModelConfig:
    """模型核心参数。"""
    days: int = 180
    output_dir: str = "./btc_pricing_output_v1_3"
    manual_etf_csv: Optional[str] = None
    manual_google_trends_csv: Optional[str] = None
    # 审计缓存只写不读，避免旧缓存影响 strict validation。
    cache_dir: str = "./btc_model_cache"

    # Bhambhwani et al. 中 BTC 的长期 log-log 弹性；用于复刻与压力测试。
    beta_hashrate: float = 1.298
    beta_network: float = 1.802

    # 平滑窗口
    smooth_window: int = 7
    long_window: int = 30

    # z-score 窗口
    z_window: int = 180
    z_min_periods: int = 60

    # HTTP 请求配置
    request_timeout: int = 30
    sleep_seconds: float = 0.25
    user_agent: str = "btc-unified-pricing-model-v1.3 research-use"
    max_request_retries: int = 3
    non_retryable_status_codes: Tuple[int, ...] = (400, 401, 403, 404, 451)
    cryptocompare_api_key: Optional[str] = None

    # Google Trends 可选；默认关闭以降低非官方接口风险。
    use_pytrends: bool = False

    # 核心 validated 数据最大允许滞后天数。
    max_core_stale_days: int = 2

    # crash risk 固定使用 90 天回撤窗口。
    drawdown_window: int = 90

    # 严格交叉验证阈值
    price_max_gap: float = 0.015
    hashrate_min_corr: float = 0.85
    hashrate_max_gap: float = 0.15
    active_min_corr: float = 0.75
    active_max_percentile_gap: float = 0.25
    tx_count_min_corr: float = 0.90
    tx_count_max_gap: float = 0.15
    transfer_min_corr: float = 0.50
    transfer_max_percentile_gap: float = 0.25
    fee_min_corr: float = 0.70
    fee_max_percentile_gap: float = 0.30
    attention_min_corr: float = 0.50

    # Liu attention 验证：比较标准化后的 attention shock。
    attention_validation_min_overlap: int = 90
    attention_validation_window: int = 90
    attention_lead_lag_days: int = 3
    attention_min_same_day_spearman: float = 0.05
    attention_min_best_lag_spearman: float = 0.30
    attention_min_shock_overlap_rate: float = 0.25
    attention_min_recent_direction_agreement: float = 0.50
    attention_recent_window_days: int = 30
    attention_top_quantile: float = 0.80

    # GDELT 抓取参数；缓存只写不读。
    gdelt_min_request_interval_seconds: float = 10.0
    gdelt_backoff_seconds: Tuple[int, ...] = (30, 60, 120)
    gdelt_chunk_days: int = 90
    gdelt_cache_max_stale_days: int = 1
    gdelt_read_fresh_cache: bool = True
    skip_gdelt: bool = False
    skip_etf: bool = False
    fast_mode: bool = False
    parallel_fetch: bool = True
    fetch_max_workers: int = 6

    # 价格共识：不再使用“第一个通过的 pair”，而是在所有自动源中选择最佳 pair。
    price_validation_window: int = 30
    price_min_sources: int = 2

    # Biais / Liu 启发式折价层参数；输出会同步给出敏感性分析。
    enable_research_fallbacks: bool = True
    research_min_observations: int = 30
    allow_liu_momentum_only: bool = True
    biais_weights: Dict[str, float] = field(default_factory=lambda: {
        "transaction_benefit": 0.40,
        "transaction_cost": 0.20,
        "market_access": 0.20,
        "crash_risk": 0.20,
    })
    liu_weights: Dict[str, float] = field(default_factory=lambda: {
        "momentum": 0.40,
        "ordinary_attention": 0.25,
        "negative_attention": 0.20,
        "activity_growth": 0.15,
    })
    biais_discount_thresholds: Tuple[Tuple[float, float], ...] = (
        (0.50, 1.00),
        (-0.50, 0.92),
        (-1.00, 0.85),
        (-1e99, 0.75),
    )
    liu_discount_thresholds: Tuple[Tuple[float, float], ...] = (
        (0.50, 1.00),
        (-0.50, 0.95),
        (-1.00, 0.90),
        (-1e99, 0.82),
    )
    sensitivity_score_shocks: Tuple[float, ...] = (-0.50, 0.0, 0.50)
