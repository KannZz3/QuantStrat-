from __future__ import annotations

from typing import Tuple

import pandas as pd

from .config import ModelConfig
from .fetchers import DataFetcher
from .processor import DataProcessor
from .validator import CrossValidator
from .pricing import UnifiedBTCPricingModelV12
from .io_outputs import print_summary, save_outputs, save_raw_data
from .utils import ensure_dir


def run_pipeline(cfg: ModelConfig) -> Tuple[pd.DataFrame, dict]:
    # 默认使用 180 天窗口；最小窗口必须同时满足 z-score 与 attention strict validation。
    min_required_days = max(60, int(cfg.z_min_periods), int(cfg.attention_validation_min_overlap))
    if cfg.days < min_required_days:
        raise ValueError(
            "Strict BTC pricing model requires at least "
            f"{min_required_days} days of data with current validation settings "
            f"(z_min_periods={cfg.z_min_periods}, attention_validation_min_overlap={cfg.attention_validation_min_overlap})."
        )
    ensure_dir(cfg.output_dir)

    # Step 1：抓取数据
    fetcher = DataFetcher(cfg)
    raw_data = fetcher.fetch_all()
    data_source_health = fetcher.get_source_health()
    save_raw_data(raw_data, cfg.output_dir)

    # Step 2：清洗与特征工程
    processor = DataProcessor(cfg)
    merged = processor.merge_all(raw_data)
    master = processor.clean_and_engineer(merged)

    # Step 3：严格交叉验证，只生成 validated features
    validator = CrossValidator(cfg)
    validated_master, validation_report = validator.validate_all(master)
    validation_report["data_source_health"] = data_source_health

    # Step 4：只用 validated features 进入定价模型
    model = UnifiedBTCPricingModelV12(cfg)
    priced_master, summary = model.price(validated_master, validation_report)

    # Step 5：保存结果
    save_outputs(priced_master, summary, cfg.output_dir)
    print_summary(summary)
    return priced_master, summary
