from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.evaluate_accuracy import compute_accuracy_metrics, load_ground_truth_labels, load_risk_profiles


def test_real_data_accuracy_metrics_exceed_minimum_thresholds():
    metrics = compute_accuracy_metrics(
        load_ground_truth_labels(),
        load_risk_profiles(),
    )

    assert metrics.precision > 0.7
    assert metrics.recall > 0.7
