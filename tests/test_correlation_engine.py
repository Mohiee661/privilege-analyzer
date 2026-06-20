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
