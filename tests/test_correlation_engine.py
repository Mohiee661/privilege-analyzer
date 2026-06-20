from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.correlation_engine import (  # noqa: E402
    build_unified_identity,
    correlate_identities,
    generate_correlation_report,
    get_platform_distribution,
    get_total_accounts,
    get_total_people,
    normalize_email,
    save_unified_identities,
)


def make_record(email: str, platform: str, status: str = "active", role: str = "Employee", name: str = "John Smith"):
    return {
        "user_id": f"{platform[:2].upper()}-001",
        "name": name,
        "email": email,
        "department": "Engineering",
        "status": status,
        "platform": platform,
        "role": role,
        "last_login": "2026-06-01T10:00:00",
        "account_type": "human",
        "owner_email": email,
        "mfa_enabled": True,
        "risk_context": None,
    }


def test_same_email_across_platforms_becomes_one_person():
    platform_records = {
        "ad": [make_record("john.smith@company.com", "Active Directory")],
        "aws": [make_record("john.smith@company.com", "AWS IAM")],
        "okta": [make_record("john.smith@company.com", "Okta")],
    }

    unified = correlate_identities(platform_records)

    assert len(unified) == 1
    assert unified[0].email == "john.smith@company.com"
    assert set(unified[0].accounts) == {"ad", "aws", "okta"}


def test_different_emails_remain_separate():
    platform_records = {
        "ad": [make_record("john.smith@company.com", "Active Directory")],
        "aws": [make_record("jane.smith@company.com", "AWS IAM")],
        "okta": [make_record("mark.jones@company.com", "Okta")],
    }

    unified = correlate_identities(platform_records)

    assert len(unified) == 3


def test_case_insensitive_matching():
    platform_records = {
        "ad": [make_record("John.Smith@company.com", "Active Directory")],
        "aws": [make_record("john.smith@company.com", "AWS IAM")],
    }

    unified = correlate_identities(platform_records)

    assert len(unified) == 1
    assert normalize_email("John.Smith@company.com") == "john.smith@company.com"


def test_export_file_generation(tmp_path):
    platform_records = {
        "ad": [make_record("john.smith@company.com", "Active Directory")],
    }
    unified = correlate_identities(platform_records)
    output_path = tmp_path / "output" / "unified_identities.json"

    written = save_unified_identities(unified, output_path)

    assert written.exists()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload
    assert payload[0]["person_id"] == "PID001"


def test_statistics_and_report_generation(tmp_path, capsys):
    platform_records = {
        "ad": [make_record("john.smith@company.com", "Active Directory")],
        "aws": [make_record("john.smith@company.com", "AWS IAM")],
        "okta": [make_record("jane.smith@company.com", "Okta")],
    }
    unified = correlate_identities(platform_records)

    assert get_total_people(unified) == 2
    assert get_total_accounts(platform_records) == 3
    assert get_platform_distribution(platform_records) == {"ad": 1, "aws": 1, "okta": 1}

    report = generate_correlation_report(unified, platform_records)
    captured = capsys.readouterr().out

    assert "CORRELATION REPORT" in captured
    assert "Unique People: 2" in report

    output_path = tmp_path / "output" / "unified_identities.json"
    save_unified_identities(unified, output_path)
    assert output_path.exists()


def test_build_unified_identity_preserves_additional_account_fields():
    azure_record = make_record("john.smith@company.com", "Azure AD")
    azure_record["account_type"] = "human"
    azure_record["owner_email"] = "john.smith@company.com"
    azure_record["mfa_enabled"] = True
    azure_record["risk_context"] = "standard"

    aws_record = make_record("john.smith@company.com", "AWS IAM")
    aws_record["account_type"] = "service_account"
    aws_record["owner_email"] = "owner@company.com"
    aws_record["mfa_enabled"] = False
    aws_record["risk_context"] = "sensitive"

    unified = build_unified_identity("PID001", [azure_record, aws_record])

    azure_account = unified.accounts["azure"]
    aws_account = unified.accounts["aws"]

    assert azure_account["account_type"] == "human"
    assert azure_account["owner_email"] == "john.smith@company.com"
    assert azure_account["mfa_enabled"] is True
    assert azure_account["risk_context"] == "standard"
    assert aws_account["account_type"] == "service_account"
    assert aws_account["owner_email"] == "owner@company.com"
    assert aws_account["mfa_enabled"] is False
    assert aws_account["risk_context"] == "sensitive"


def test_unrelated_platform_admin_does_not_leak_into_other_accounts():
    platform_records = {
        "azure": [make_record("alice@company.com", "Azure AD", role="Employee")],
        "aws": [make_record("alice@company.com", "AWS IAM", role="Administrator")],
    }

    unified = correlate_identities(platform_records)

    assert len(unified) == 1
    account = unified[0].accounts["azure"]
    assert account["role"] == "Employee"
    assert account["status"] == "active"
    assert account["account_type"] == "human"
