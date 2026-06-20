from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.risk_engine import (  # noqa: E402
    detect_nested_group_privilege,
    detect_privilege_spikes,
    detect_token_abuse,
    detect_multi_platform_admins,
    detect_offboarding_gaps,
    detect_platform_exposure,
    detect_stale_accounts,
    detect_suspended_mismatches,
    generate_risk_report,
    run_all_detectors,
    save_findings,
)
from services.data_loader import ApiToken, PrivilegeEvent  # noqa: E402


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


def test_nested_group_privilege_detection(monkeypatch):
    identities = [
        make_unified_identity(
            "PID001",
            "alice@company.com",
            {
                "azure": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]
    monkeypatch.setattr(
        "services.risk_engine.effective_privilege",
        lambda email: ["Employee", "Global Administrator"],
    )

    findings = detect_nested_group_privilege(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "HIDDEN_PRIVILEGE_VIA_GROUP_NESTING"


def test_privilege_spike_detection(monkeypatch):
    identities = [
        make_unified_identity(
            "PID001",
            "alice@company.com",
            {
                "azure": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]
    events = [
        PrivilegeEvent("PEV001", "alice@company.com", "Azure AD", "role_granted", "Employee", "Developer", "2026-06-01T00:00:00", None),
        PrivilegeEvent("PEV002", "alice@company.com", "Azure AD", "role_granted", "Developer", "Security Analyst", "2026-06-03T00:00:00", None),
        PrivilegeEvent("PEV003", "alice@company.com", "Azure AD", "role_granted", "Security Analyst", "Global Administrator", "2026-06-05T00:00:00", None),
    ]
    monkeypatch.setattr("services.risk_engine.load_privilege_events", lambda: events)

    findings = detect_privilege_spikes(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "UNAPPROVED_PRIVILEGE_SPIKE"


def test_token_abuse_detection(monkeypatch):
    identities = [
        make_unified_identity(
            "PID001",
            "alice@company.com",
            {
                "azure": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        )
    ]
    tokens = [
        ApiToken(
            "TOK001",
            "alice@company.com",
            "Azure AD",
            "read-only",
            "2024-01-01",
            "2024-01-01",
            "2026-06-01T00:00:00",
            True,
            "active",
        )
    ]
    monkeypatch.setattr("services.risk_engine.load_api_tokens", lambda: tokens)

    findings = detect_token_abuse(identities)

    assert len(findings) == 1
    assert findings[0].risk_type == "STALE_OR_MISUSED_TOKEN"
    assert findings[0].severity == "HIGH"


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
