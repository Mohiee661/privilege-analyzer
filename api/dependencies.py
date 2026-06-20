"""Runtime data access helpers for the API."""

from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"


@lru_cache(maxsize=1)
def get_runtime_data() -> Dict[str, list[dict]]:
    def load(name: str) -> list[dict]:
        path = OUTPUT_DIR / name
        if not path.exists():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []

    unified_identities = load("unified_identities.json")
    findings = load("risk_findings.json")
    risk_profiles = load("risk_profiles.json")
    ai_reports = load("ai_reports.json")

    return {
        "unified_identities": unified_identities,
        "findings": findings,
        "risk_profiles": risk_profiles,
        "ai_reports": ai_reports,
    }
