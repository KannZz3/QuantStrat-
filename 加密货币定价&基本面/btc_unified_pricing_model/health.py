from __future__ import annotations

import time
from threading import Lock
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class SourceHealthRecord:
    source: str
    status: str
    rows: int = 0
    latest_date: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    reason: Optional[str] = None
    issues: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "status": self.status,
            "rows": self.rows,
            "latest_date": self.latest_date,
            "elapsed_seconds": self.elapsed_seconds,
            "reason": self.reason,
            "issues": self.issues,
            "columns": self.columns,
        }


class SourceHealthTracker:
    """Collect per-source fetch health in a JSON-friendly form."""

    def __init__(self) -> None:
        self._records: Dict[str, SourceHealthRecord] = {}
        self._issues: Dict[str, List[str]] = {}
        self._lock = Lock()

    def issue(self, source: str, message: str) -> None:
        with self._lock:
            self._issues.setdefault(source, []).append(str(message))

    def record(
        self,
        source: str,
        df: Optional[pd.DataFrame],
        *,
        elapsed_seconds: Optional[float] = None,
        reason: Optional[str] = None,
        status: Optional[str] = None,
    ) -> None:
        rows = int(len(df)) if isinstance(df, pd.DataFrame) else 0
        columns = list(df.columns) if isinstance(df, pd.DataFrame) else []
        latest_date = None
        if isinstance(df, pd.DataFrame) and "date" in df.columns and not df.empty:
            dates = pd.to_datetime(df["date"], errors="coerce").dropna()
            if not dates.empty:
                latest_date = str(dates.max().date())

        with self._lock:
            issues = self._issues.pop(source, [])
        final_status = status
        if final_status is None:
            final_status = "ok" if rows > 0 else "empty"
        if issues and final_status == "ok":
            final_status = "ok_with_warnings"
        if issues and final_status == "empty":
            final_status = "failed"
        if reason is None and issues:
            reason = " | ".join(issues)
        elif reason is None and rows == 0:
            reason = "empty result"

        with self._lock:
            self._records[source] = SourceHealthRecord(
                source=source,
                status=final_status,
                rows=rows,
                latest_date=latest_date,
                elapsed_seconds=round(float(elapsed_seconds), 3) if elapsed_seconds is not None else None,
                reason=reason,
                issues=issues,
                columns=columns,
            )

    def as_dict(self) -> Dict[str, Any]:
        with self._lock:
            records = [r.to_dict() for r in self._records.values()]
        return {
            "records": records,
            "summary": {
                "ok": sum(1 for r in records if r["status"] == "ok"),
                "ok_with_warnings": sum(1 for r in records if r["status"] == "ok_with_warnings"),
                "empty": sum(1 for r in records if r["status"] == "empty"),
                "failed": sum(1 for r in records if r["status"] == "failed"),
                "skipped": sum(1 for r in records if r["status"] == "skipped"),
            },
        }

    @staticmethod
    def now() -> float:
        return time.time()
