from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.scoring_engine import (  # noqa: E402
    build_risk_profiles,
    calculate_identity_score,
    calculate_risk_level,
    generate_risk_distribution,
    get_average_risk_score,
    print_top_risks,
    rank_identities,
    save_risk_profiles,
)


def make_identity(person_id: str, name: str = "John Smith", email: str = "john.smith@company.com") -> dict:
    return {
        "person_id": person_id,
        "name": name,
        "email": email,
        "accounts": {},
    }


def make_finding(person_id: str, risk_type: str) -> dict:
    return {
        "finding_id": "F001",
        "person_id": person_id,
        "name": "John Smith",
        "email": "john.smith@company.com",
        "risk_type": risk_type,
        "severity": "HIGH",
        "description": risk_type,
        "evidence": {},
    }


def test_offboarding_gap_score_is_40():
    score = calculate_identity_score([make_finding("PID001", "OFFBOARDING_GAP")])
    assert score == 40


def test_combined_score_is_70():
    score = calculate_identity_score(
        [
            make_finding("PID001", "OFFBOARDING_GAP"),
            make_finding("PID001", "MULTI_PLATFORM_ADMIN"),
        ]
    )
    assert score == 70


def test_score_caps_at_100():
    score = calculate_identity_score(
        [
            make_finding("PID001", "OFFBOARDING_GAP"),
            make_finding("PID001", "MULTI_PLATFORM_ADMIN"),
            make_finding("PID001", "SUSPENDED_ACCOUNT_MISMATCH"),
            make_finding("PID001", "EXCESSIVE_PLATFORM_EXPOSURE"),
        ]
    )
    assert score == 100


def test_risk_level_for_95_is_critical():
    assert calculate_risk_level(95) == "CRITICAL"


def test_ranking_order_highest_score_first():
    identities = [
        make_identity("PID001", "Alice", "alice@company.com"),
        make_identity("PID002", "Bob", "bob@company.com"),
        make_identity("PID003", "Carol", "carol@company.com"),
    ]
    findings = [
        make_finding("PID001", "EXCESSIVE_PLATFORM_EXPOSURE"),
        make_finding("PID002", "OFFBOARDING_GAP"),
        make_finding("PID002", "MULTI_PLATFORM_ADMIN"),
        make_finding("PID003", "OFFBOARDING_GAP"),
    ]

    profiles = build_risk_profiles(identities, findings)
    ranked = rank_identities(profiles)

    assert ranked[0].person_id == "PID002"
    assert ranked[0].score == 70


def test_distribution_average_and_export(tmp_path, capsys):
    identities = [
        make_identity("PID001", "Alice", "alice@company.com"),
        make_identity("PID002", "Bob", "bob@company.com"),
    ]
    findings = [
        make_finding("PID001", "OFFBOARDING_GAP"),
        make_finding("PID002", "EXCESSIVE_PLATFORM_EXPOSURE"),
    ]
    profiles = build_risk_profiles(identities, findings)
    ranked = rank_identities(profiles)

    assert generate_risk_distribution(ranked) == {
        "critical": 0,
        "high": 0,
        "medium": 1,
        "low": 1,
        "none": 0,
    }
    assert get_average_risk_score(ranked) == 27.5

    output_path = tmp_path / "output" / "risk_profiles.json"
    written = save_risk_profiles(ranked, output_path)
    assert written.exists()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload[0]["person_id"] == "PID001"

    report = print_top_risks(ranked, limit=2)
    captured = capsys.readouterr().out
    assert "TOP RISKS" in captured
    assert "Alice" in report or "Bob" in report
