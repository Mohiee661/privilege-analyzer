from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reports.executive_report_generator import (  # noqa: E402
    generate_executive_report,
    get_showcase_incidents,
    get_top_incidents,
    load_demo_scenarios,
    save_exports,
)


def test_demo_scenarios_load_correctly():
    scenarios = load_demo_scenarios()
    assert len(scenarios) >= 10
    assert any(item["title"] == "Ghost Employee" for item in scenarios)


def test_top_incidents_generated():
    incidents = get_top_incidents(limit=5)
    assert len(incidents) == 5
    assert incidents[0]["risk_score"] >= incidents[-1]["risk_score"]


def test_showcase_incidents_have_expected_fields():
    incidents = get_showcase_incidents(limit=3)
    for incident in incidents:
        assert "title" in incident
        assert "accounts" in incident
        assert "timeline" in incident


def test_executive_report_generation_and_exports():
    report = generate_executive_report()

    assert "summary" in report
    assert "top_risks" in report
    assert "risk_distribution" in report
    assert "recommended_priorities" in report

    executive_json = ROOT / "output" / "executive_report.json"
    executive_pdf = ROOT / "output" / "executive_report.pdf"
    exported_pdf = ROOT / "exports" / "pdf" / "executive_report.pdf"
    csv_risk_profiles = ROOT / "exports" / "csv" / "risk_profiles.csv"
    csv_findings = ROOT / "exports" / "csv" / "findings.csv"
    csv_ai_reports = ROOT / "exports" / "csv" / "ai_reports.csv"

    assert executive_json.exists()
    assert executive_pdf.exists()
    assert exported_pdf.exists()
    assert csv_risk_profiles.exists()
    assert csv_findings.exists()
    assert csv_ai_reports.exists()

    assert executive_pdf.read_bytes().startswith(b"%PDF")
    assert exported_pdf.read_bytes().startswith(b"%PDF")


def test_export_files_contain_rows():
    report = generate_executive_report()
    save_exports(
        report["top_risks"],
        [
            {
                "finding_id": "F001",
                "person_id": "PID001",
                "name": "John Smith",
                "email": "john.smith@company.com",
                "risk_type": "OFFBOARDING_GAP",
                "severity": "HIGH",
                "description": "Example",
                "evidence": {},
            }
        ],
        [
            {
                "person_id": "PID001",
                "risk_score": 95,
                "risk_level": "CRITICAL",
                "summary": "Example",
                "security_impact": "Example",
                "recommended_actions": ["A", "B"],
            }
        ],
    )
    assert (ROOT / "exports" / "csv" / "risk_profiles.csv").exists()
