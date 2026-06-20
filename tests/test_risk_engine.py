from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.risk_engine import (  # noqa: E402
    _generate_remediation_steps,
    consolidate_findings,
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


def test_nested_group_privilege_requires_same_platform_scope(monkeypatch):
    identities = [
        make_unified_identity(
            "PID001",
            "alice@company.com",
            {
                "azure": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
                "aws": {"status": "active", "role": "Administrator", "last_login": "2026-06-01T10:00:00"},
            },
        ),
        make_unified_identity(
            "PID002",
            "bob@company.com",
            {
                "azure": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
                "aws": {"status": "active", "role": "Employee", "last_login": "2026-06-01T10:00:00"},
            },
        ),
    ]

    def fake_effective_privilege(email, platform=None):
        if email == "alice@company.com" and platform == "azure":
            return ["Employee"]
        if email == "alice@company.com" and platform == "aws":
            return ["Administrator"]
        if email == "bob@company.com" and platform == "azure":
            return ["Employee", "Global Administrator"]
        if email == "bob@company.com" and platform == "aws":
            return ["Employee", "Administrator"]
        return []

    monkeypatch.setattr("services.risk_engine.effective_privilege", fake_effective_privilege)

    findings = detect_nested_group_privilege(identities)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.risk_type == "HIDDEN_PRIVILEGE_VIA_GROUP_NESTING"
    assert finding.person_id == "PID002"
    assert finding.evidence["platforms"] == ["aws", "azure"]
    assert set(finding.evidence["details"]) == {"aws", "azure"}
    assert finding.evidence["details"]["azure"]["platform"] == "azure"
    assert finding.evidence["details"]["aws"]["platform"] == "aws"


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


def test_consolidation_reduces_alert_count():
    """Test that consolidation reduces alert count by at least 35% using production data."""
    # Load actual production data to test consolidation
    from services.risk_engine import load_unified_identities, LAST_FINDINGS
    
    # Load unified identities
    unified_identities = load_unified_identities()
    
    # Run detectors to get findings
    findings = run_all_detectors(unified_identities)
    raw_count = len(findings)
    
    # Consolidate findings
    incidents = consolidate_findings(findings, unified_identities)
    incident_count = len(incidents)
    
    reduction_percentage = ((raw_count - incident_count) / raw_count) * 100
    
    print(f"\nRaw findings: {raw_count}")
    print(f"Consolidated incidents: {incident_count}")
    print(f"Reduction: {reduction_percentage:.2f}%")
    
    # Assert at least 35% reduction
    assert reduction_percentage >= 35, f"Consolidation only achieved {reduction_percentage:.2f}% reduction, below 35% target"


def test_remediation_steps_include_specific_platforms():
    """Test that remediation steps reference specific platforms from evidence."""
    # Test OFFBOARDING_GAP
    evidence = {"ad": "disabled", "aws": "active", "azure": "active"}
    steps = _generate_remediation_steps("OFFBOARDING_GAP", evidence)
    assert len(steps) > 0
    step_text = " ".join(steps)
    assert "Active Directory" in step_text or "AWS" in step_text or "Azure" in step_text

    # Test MULTI_PLATFORM_ADMIN
    evidence = {"aws": "Administrator", "azure": "Global Administrator"}
    steps = _generate_remediation_steps("MULTI_PLATFORM_ADMIN", evidence)
    assert len(steps) > 0
    step_text = " ".join(steps)
    assert "AWS" in step_text or "Azure" in step_text

    # Test STALE_ACTIVE_ACCOUNT
    evidence = {"platform": "okta", "days_since_last_login": 90}
    steps = _generate_remediation_steps("STALE_ACTIVE_ACCOUNT", evidence)
    assert len(steps) > 0
    step_text = " ".join(steps)
    assert "Okta" in step_text
    assert "90" in step_text

    # Test EXCESSIVE_PLATFORM_EXPOSURE
    evidence = {"platforms": ["ad", "aws", "azure", "okta"]}
    steps = _generate_remediation_steps("EXCESSIVE_PLATFORM_EXPOSURE", evidence)
    assert len(steps) > 0
    step_text = " ".join(steps)
    assert "Active Directory" in step_text or "AWS" in step_text or "Azure" in step_text or "Okta" in step_text

    # Test HIDDEN_PRIVILEGE_VIA_GROUP_NESTING
    evidence = {
        "details": {
            "aws": {
                "stated_role": "Developer",
                "admin_equivalent_roles": ["Administrator"],
            }
        }
    }
    steps = _generate_remediation_steps("HIDDEN_PRIVILEGE_VIA_GROUP_NESTING", evidence)
    assert len(steps) > 0
    step_text = " ".join(steps)
    assert "AWS" in step_text
    assert "Administrator" in step_text

    # Test STALE_OR_MISUSED_TOKEN
    evidence = {
        "token_id": "TOK001",
        "scope": "aws",
        "last_rotated": "2024-01-01",
        "reasons": ["stale_rotation"],
    }
    steps = _generate_remediation_steps("STALE_OR_MISUSED_TOKEN", evidence)
    assert len(steps) > 0
    step_text = " ".join(steps)
    assert "TOK001" in step_text
    assert "AWS" in step_text
