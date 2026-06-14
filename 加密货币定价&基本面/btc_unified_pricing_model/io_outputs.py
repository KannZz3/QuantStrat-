from __future__ import annotations

import json
import os
from typing import Dict

import pandas as pd

from .utils import ensure_dir


def save_raw_data(data: Dict[str, pd.DataFrame], output_dir: str) -> None:
    raw_dir = os.path.join(output_dir, "raw")
    ensure_dir(raw_dir)
    for name, df in data.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            df.to_csv(os.path.join(raw_dir, f"{name}.csv"), index=False)

def save_outputs(master: pd.DataFrame, summary: dict, output_dir: str) -> None:
    ensure_dir(output_dir)
    processed_dir = os.path.join(output_dir, "processed")
    ensure_dir(processed_dir)

    master_path = os.path.join(processed_dir, "btc_daily_master_v1_3.csv")
    summary_path = os.path.join(output_dir, "btc_pricing_summary_v1_3.json")
    latest_path = os.path.join(output_dir, "btc_pricing_latest_table_v1_3.csv")
    validation_path = os.path.join(output_dir, "btc_validation_report_v1_3.json")
    source_health_path = os.path.join(output_dir, "btc_data_source_health_v1_3.json")
    source_coverage_path = os.path.join(output_dir, "btc_source_coverage_v1_3.csv")
    downgrade_table_path = os.path.join(output_dir, "btc_downgrade_table_v1_3.csv")
    sensitivity_path = os.path.join(output_dir, "btc_discount_sensitivity_v1_3.csv")

    master.to_csv(master_path, index=False)
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, default=str)
    with open(validation_path, "w", encoding="utf-8") as f:
        json.dump(summary.get("validation_report", {}), f, ensure_ascii=False, indent=2, default=str)
    with open(source_health_path, "w", encoding="utf-8") as f:
        json.dump(summary.get("validation_report", {}).get("data_source_health", {}), f, ensure_ascii=False, indent=2, default=str)
    pd.DataFrame(summary.get("scenarios", [])).to_csv(latest_path, index=False)
    pd.DataFrame(summary.get("validation_report", {}).get("data_source_health", {}).get("records", [])).to_csv(source_coverage_path, index=False)
    pd.DataFrame(summary.get("downgrade_table", [])).to_csv(downgrade_table_path, index=False)
    pd.DataFrame(summary.get("discount_sensitivity_core_lower_bound", [])).to_csv(sensitivity_path, index=False)

    print(f"[OK] master table saved: {master_path}")
    print(f"[OK] summary json saved: {summary_path}")
    print(f"[OK] validation report saved: {validation_path}")
    print(f"[OK] data source health saved: {source_health_path}")
    print(f"[OK] source coverage saved: {source_coverage_path}")
    print(f"[OK] downgrade table saved: {downgrade_table_path}")
    print(f"[OK] discount sensitivity saved: {sensitivity_path}")
    print(f"[OK] latest scenario table saved: {latest_path}")

def print_summary(summary: dict) -> None:
    print("\n" + "=" * 88)
    print("BTC 统一多模块动态下沿估值模型 v1.3")
    print("=" * 88)
    print(f"最新日期: {summary.get('latest_date')}")
    print(f"模型状态: {summary.get('strict_model_status')}")
    print(f"进入模型模块: {' + '.join(summary.get('included_modules', [])) if summary.get('included_modules') else 'None'}")
    confidence = summary.get("confidence_level", {})
    if confidence:
        print(f"置信层级: {confidence.get('level')} | {confidence.get('description_cn')}")
    if summary.get("downgrade_table"):
        print(f"降级/剔除项数量: {len(summary.get('downgrade_table', []))}")

    if summary.get("strict_model_status") == "No Strict Valuation":
        print("\n结论：")
        print(summary.get("main_conclusion_cn"))
        print("\n验证报告摘要：")
        print(json.dumps(summary.get("validation_report", {}).get("module_pass", {}), ensure_ascii=False, indent=2))
        print("\nvalidated observations:")
        print(json.dumps(summary.get("validated_observation_counts", {}), ensure_ascii=False, indent=2))
        print("\n剔除变量：")
        print(json.dumps(summary.get("excluded_variables", []), ensure_ascii=False, indent=2))
        print("\n剔除模块：")
        print(json.dumps(summary.get("excluded_modules", []), ensure_ascii=False, indent=2))
        print("=" * 88 + "\n")
        return

    print(f"当前 BTC 价格: {summary.get('btc_price_current'):,.2f} USD")
    print(f"Validated Hashrate 7D: {summary.get('hashrate_current_ehs_7d_validated'):,.2f} EH/s")
    print(f"Validated Active Addresses 7D: {summary.get('active_addresses_current_7d_validated'):,.0f}")
    print(f"Biais 折价: {summary.get('biais_discount_latest')}")
    print(f"Liu-Tsyvinski 折价: {summary.get('liu_discount_latest')}")
    print(f"综合折价: {summary.get('combined_discount_latest')}")
    print(f"validated data quality: {summary.get('validated_data_quality_score')}")
    print(f"core staleness days: {summary.get('latest_validated_core_staleness_days')}")
    print("validated observations:", json.dumps(summary.get("validated_observation_counts", {}), ensure_ascii=False))
    print("excluded variables:", json.dumps(summary.get("excluded_variables", []), ensure_ascii=False))
    print("excluded modules:", json.dumps(summary.get("excluded_modules", []), ensure_ascii=False))
    print(f"band width base/addon: {summary.get('band_width_base')} / {summary.get('sample_width_addon')}")

    print("\n情景结果：")
    for s in summary.get("scenarios", []):
        print(
            f"- {s['scenario']} | {s['desc_cn']} | "
            f"点位 {s['strict_lower_point']:,.0f} | "
            f"区间 {s['strict_lower_band_low']:,.0f}–{s['strict_lower_band_high']:,.0f} USD | "
            f"模块 {s['included_modules']}"
        )
    print("\n结论：")
    print(summary.get("main_conclusion_cn"))
    print("\n边界说明：")
    print(summary.get("important_model_boundary_cn"))
    print(summary.get("active_addresses_usage_cn"))
    print("=" * 88 + "\n")
