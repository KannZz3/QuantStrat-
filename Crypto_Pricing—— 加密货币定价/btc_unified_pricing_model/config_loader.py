from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path
from typing import Any, Dict, Optional

from .config import ModelConfig


def _load_mapping(path: str) -> Dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    suffix = p.suffix.lower()
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in [".yaml", ".yml"]:
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RuntimeError("YAML config requires PyYAML; use JSON or install pyyaml.") from e
        data = yaml.safe_load(text)
    else:
        raise ValueError("Config file must be .json, .yaml, or .yml")
    if not isinstance(data, dict):
        raise ValueError("Config file root must be an object/mapping.")
    return data


def _coerce_config_value(name: str, value: Any) -> Any:
    tuple_fields = {
        "non_retryable_status_codes",
        "gdelt_backoff_seconds",
        "biais_discount_thresholds",
        "liu_discount_thresholds",
        "sensitivity_score_shocks",
    }
    if name in tuple_fields and isinstance(value, list):
        if name in {"biais_discount_thresholds", "liu_discount_thresholds"}:
            return tuple(tuple(x) for x in value)
        return tuple(value)
    return value


def load_model_config(path: Optional[str], overrides: Optional[Dict[str, Any]] = None) -> ModelConfig:
    allowed = {f.name for f in fields(ModelConfig)}
    data: Dict[str, Any] = {}
    if path:
        raw = _load_mapping(path)
        unknown = sorted(set(raw) - allowed)
        if unknown:
            raise ValueError(f"Unknown ModelConfig keys in config file: {unknown}")
        data.update({k: _coerce_config_value(k, v) for k, v in raw.items()})
    if overrides:
        data.update({k: _coerce_config_value(k, v) for k, v in overrides.items() if v is not None})
    return ModelConfig(**data)
