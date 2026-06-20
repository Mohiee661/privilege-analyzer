from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.risk_engine import (  # noqa: E402
    detect_multi_platform_admins,
    detect_offboarding_gaps,
    detect_platform_exposure,
    detect_stale_accounts,
    detect_suspended_mismatches,
    generate_risk_report,
    run_all_detectors,
    save_findings,
)


def make_unified_identity(person_id: str, email: str, accounts: dict, name: str = "John Smith") -> dict:
    return {
        "person_id": person_id,
        "name": name,
        "email": email,
        "accounts": accounts,
    }


def test_offboarding_gap_detection():
    identities = [
        make_unified_identity(
            "PID001",
            "john.smith@company.com",
            {
                "ad": {"status": "disabled", "role": "Employee", "last_login": "2026-01-01T10:00:00"},
                "aws": {"status": "active", "role": "Developer", "last_login": "2026-06-01T10:00:00"},
                "okta": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]

    findings = detect_offboarding_gaps(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "OFFBOARDING_GAP"


def test_multi_platform_admin_detection():
    identities = [
        make_unified_identity(
            "PID001",
            "jane.smith@company.com",
            {
                "aws": {"status": "active", "role": "Administrator", "last_login": "2026-06-01T10:00:00"},
                "azure": {"status": "active", "role": "Global Administrator", "last_login": "2026-06-01T10:00:00"},
                "okta": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]

    findings = detect_multi_platform_admins(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "MULTI_PLATFORM_ADMIN"
    assert set(findings[0].evidence) == {"aws", "azure"}


def test_stale_active_account_detection():
    identities = [
        make_unified_identity(
            "PID001",
            "mark.jones@company.com",
            {
                "okta": {"status": "active", "role": "Employee", "last_login": "2025-01-01T10:00:00"},
            },
        )
    ]

    findings = detect_stale_accounts(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "STALE_ACTIVE_ACCOUNT"
    assert findings[0].evidence["platform"] == "okta"


def test_suspended_account_mismatch_detection():
    identities = [
        make_unified_identity(
            "PID001",
            "sarah.wilson@company.com",
            {
                "azure": {"status": "suspended", "role": "Employee", "last_login": "2026-05-01T10:00:00"},
                "aws": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]

    findings = detect_suspended_mismatches(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "SUSPENDED_ACCOUNT_MISMATCH"


def test_platform_exposure_detection():
    identities = [
        make_unified_identity(
            "PID001",
            "olivia.brown@company.com",
            {
                "ad": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
                "azure": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
                "aws": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
                "okta": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]

    findings = detect_platform_exposure(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "EXCESSIVE_PLATFORM_EXPOSURE"


def test_save_findings_and_report(tmp_path, capsys):
    identities = [
        make_unified_identity(
            "PID001",
            "john.smith@company.com",
            {
                "ad": {"status": "disabled", "role": "Employee", "last_login": "2026-01-01T10:00:00"},
                "aws": {"status": "active", "role": "Administrator", "last_login": "2026-06-01T10:00:00"},
                "azure": {"status": "active", "role": "Global Administrator", "last_login": "2026-06-01T10:00:00"},
                "okta": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]
    findings = run_all_detectors(identities)
    output_path = tmp_path / "output" / "risk_findings.json"

    written = save_findings(findings, output_path)
    assert written.exists()

    payload = json.loads(written.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload

    report = generate_risk_report(findings, identities)
    captured = capsys.readouterr().out
    assert "RISK REPORT" in captured
    assert "TOTAL FINDINGS" in report
