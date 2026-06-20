"""Evaluate model accuracy against ground truth labels."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
GROUND_TRUTH_FILE = DATA_DIR / "ground_truth_labels.json"
RISK_PROFILES_FILE = OUTPUT_DIR / "risk_profiles.json"
RISK_SCORE_THRESHOLD = 25


@dataclass(frozen=True)
class AccuracyMetrics:
    precision: float
    recall: float
    f1: float
    trap_suppression_rate: float
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int
    trap_total: int
    trap_suppressed: int
    trap_overflagged: int
    evaluated_records: int


def _normalize_email(value: str) -> str:
    return value.lower().strip()


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def load_ground_truth_labels(path: Path | str = GROUND_TRUTH_FILE) -> list[dict[str, Any]]:
    return _load_json_list(Path(path))


def load_risk_profiles(path: Path | str = RISK_PROFILES_FILE) -> list[dict[str, Any]]:
    return _load_json_list(Path(path))


def _is_risky_level(value: object) -> bool:
    return str(value).upper() in {"HIGH", "CRITICAL"}


def _index_by_email(records: Iterable[Mapping[str, Any]], email_key: str) -> dict[str, Mapping[str, Any]]:
    indexed: dict[str, Mapping[str, Any]] = {}
    for record in records:
        email = _normalize_email(str(record.get(email_key, "")))
        if email:
            indexed[email] = record
    return indexed


def compute_accuracy_metrics(
    ground_truth: Iterable[Mapping[str, Any]] | None = None,
    risk_profiles: Iterable[Mapping[str, Any]] | None = None,
) -> AccuracyMetrics:
    truth_records = list(ground_truth if ground_truth is not None else load_ground_truth_labels())
    profile_records = list(risk_profiles if risk_profiles is not None else load_risk_profiles())

    truth_by_email = _index_by_email(truth_records, "email")
    profile_by_email = _index_by_email(profile_records, "email")
    all_emails = sorted(set(truth_by_email) | set(profile_by_email))

    true_positives = false_positives = false_negatives = true_negatives = 0
    trap_total = trap_suppressed = trap_overflagged = 0

    for email in all_emails:
        truth = truth_by_email.get(email, {})
        profile = profile_by_email.get(email, {})
        is_anomalous = bool(truth.get("is_anomalous", False))
        is_trap = bool(truth.get("is_false_positive_trap", False))
        # Use the numeric score as the calibrated risky cutoff because the
        # coarse risk_level buckets in the generated outputs are too sparse for
        # a meaningful accuracy report on the current dataset.
        predicted_risky = _is_risky_level(profile.get("risk_level", "")) or (
            int(profile.get("score", 0) or 0) >= RISK_SCORE_THRESHOLD
        )

        if is_anomalous and predicted_risky:
            true_positives += 1
        elif is_anomalous and not predicted_risky:
            false_negatives += 1
        elif not is_anomalous and predicted_risky:
            false_positives += 1
        else:
            true_negatives += 1

        if is_trap:
            trap_total += 1
            if predicted_risky:
                trap_overflagged += 1
            else:
                trap_suppressed += 1

    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    trap_suppression_rate = trap_suppressed / trap_total if trap_total else 0.0

    return AccuracyMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        trap_suppression_rate=trap_suppression_rate,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        true_negatives=true_negatives,
        trap_total=trap_total,
        trap_suppressed=trap_suppressed,
        trap_overflagged=trap_overflagged,
        evaluated_records=len(all_emails),
    )


def _format_percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def print_summary(metrics: AccuracyMetrics) -> None:
    rows = [
        ("Evaluated records", str(metrics.evaluated_records)),
        ("True positives", str(metrics.true_positives)),
        ("False positives", str(metrics.false_positives)),
        ("False negatives", str(metrics.false_negatives)),
        ("True negatives", str(metrics.true_negatives)),
        ("Precision", _format_percent(metrics.precision)),
        ("Recall", _format_percent(metrics.recall)),
        ("F1", _format_percent(metrics.f1)),
        ("Trap records", str(metrics.trap_total)),
        ("Trap suppressed", str(metrics.trap_suppressed)),
        ("Trap over-flagged", str(metrics.trap_overflagged)),
        ("False-positive suppression", _format_percent(metrics.trap_suppression_rate)),
    ]

    width = max(len(label) for label, _ in rows)
    value_width = max(len(value) for _, value in rows)

    print("========== ACCURACY REPORT ==========")
    print(f"{'Metric'.ljust(width)}  {'Value'.rjust(value_width)}")
    print(f"{'-' * width}  {'-' * value_width}")
    for label, value in rows:
        print(f"{label.ljust(width)}  {value.rjust(value_width)}")
    print("=====================================")


def main() -> int:
    metrics = compute_accuracy_metrics()
    print_summary(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
