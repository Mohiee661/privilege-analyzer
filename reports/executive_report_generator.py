"""Executive report generation, exports, and demo scenario utilities."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

if __package__ in (None, ""):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from services.correlation_engine import OUTPUT_FILE as UNIFIED_IDENTITIES_FILE
from services.data_loader import (
    load_ad_users,
    load_aws_users,
    load_azure_users,
    load_okta_users,
    load_salesforce_users,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
EXPORTS_DIR = PROJECT_ROOT / "exports"
CSV_DIR = EXPORTS_DIR / "csv"
PDF_DIR = EXPORTS_DIR / "pdf"
DEMO_SCENARIOS_FILE = DATA_DIR / "demo_scenarios.json"
EXECUTIVE_JSON_FILE = OUTPUT_DIR / "executive_report.json"
EXECUTIVE_PDF_FILE = OUTPUT_DIR / "executive_report.pdf"
PDF_EXPORT_FILE = PDF_DIR / "executive_report.pdf"
CSV_RISK_PROFILES_FILE = CSV_DIR / "risk_profiles.csv"
CSV_FINDINGS_FILE = CSV_DIR / "findings.csv"
CSV_AI_REPORTS_FILE = CSV_DIR / "ai_reports.csv"


def _load_json_list(path: Path) -> List[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def load_unified_identities() -> List[dict]:
    return _load_json_list(UNIFIED_IDENTITIES_FILE)


def load_risk_profiles() -> List[dict]:
    return _load_json_list(OUTPUT_DIR / "risk_profiles.json")


def load_findings() -> List[dict]:
    return _load_json_list(OUTPUT_DIR / "risk_findings.json")


def load_ai_reports() -> List[dict]:
    return _load_json_list(OUTPUT_DIR / "ai_reports.json")


def load_demo_scenarios() -> List[dict]:
    return _load_json_list(DEMO_SCENARIOS_FILE)


def get_showcase_incidents(limit: int = 10) -> List[dict]:
    scenarios = sorted(
        load_demo_scenarios(),
        key=lambda item: (-int(item.get("risk_score", 0) or 0), str(item.get("title", ""))),
    )
    return scenarios[:limit]


def get_top_incidents(limit: int = 10) -> List[dict]:
    return get_showcase_incidents(limit=limit)


def build_security_timeline(identity: Mapping[str, Any], findings: Sequence[Mapping[str, Any]] | None = None) -> List[dict]:
    timeline: List[dict] = []
    for platform, account in (identity.get("accounts", {}) or {}).items():
        if not isinstance(account, Mapping):
            continue
        last_login = account.get("last_login")
        if last_login:
            date_value = str(last_login)[:10]
            timeline.append({"date": date_value, "event": f"{platform.upper()} login recorded"})
        status = str(account.get("status", "")).lower()
        if status == "disabled":
            timeline.append({"date": "2026-03-01", "event": f"{platform.upper()} account disabled"})
        elif status == "suspended":
            timeline.append({"date": "2026-03-15", "event": f"{platform.upper()} account suspended"})

    for finding in findings or []:
        risk_type = str(finding.get("risk_type", ""))
        if risk_type == "OFFBOARDING_GAP":
            timeline.append({"date": "2026-04-12", "event": "Offboarding gap detected"})
        elif risk_type == "STALE_ACTIVE_ACCOUNT":
            timeline.append({"date": "2026-05-28", "event": "Stale active account flagged"})

    unique = {(item["date"], item["event"]): item for item in timeline if item.get("date") and item.get("event")}
    return sorted(unique.values(), key=lambda item: (item["date"], item["event"]))


def _build_email_to_department_map() -> Dict[str, str]:
    directory: Dict[str, str] = {}
    for loader in (load_ad_users, load_azure_users, load_aws_users, load_okta_users, load_salesforce_users):
        for record in loader():
            email = str(record.email).lower().strip()
            if email and email not in directory and record.department:
                directory[email] = record.department
    return directory


def get_platform_risk_breakdown() -> Dict[str, int]:
    unified_identities = load_unified_identities()
    findings_by_person = Counter(str(finding.get("person_id", "")) for finding in load_findings())
    breakdown: Counter[str] = Counter()
    for identity in unified_identities:
        if findings_by_person.get(str(identity.get("person_id", "")), 0) <= 0:
            continue
        for platform in (identity.get("accounts", {}) or {}).keys():
            breakdown[str(platform)] += 1
    return dict(sorted(breakdown.items()))


def get_risk_trends() -> List[dict]:
    scenarios = load_demo_scenarios()
    monthly = Counter()
    for scenario in scenarios:
        for entry in scenario.get("timeline", []):
            date_value = str(entry.get("date", ""))
            if len(date_value) >= 7:
                monthly[date_value[:7]] += 1
    return [{"month": month, "events": count} for month, count in sorted(monthly.items())]


def get_top_departments_at_risk(limit: int = 5) -> List[dict]:
    email_to_department = _build_email_to_department_map()
    unified_identities = load_unified_identities()
    risky_person_ids = {str(finding.get("person_id", "")) for finding in load_findings()}
    counts: Counter[str] = Counter()
    for identity in unified_identities:
        if str(identity.get("person_id", "")) not in risky_person_ids:
            continue
        department = email_to_department.get(str(identity.get("email", "")).lower().strip(), "Unknown")
        counts[department] += 1
    return [{"department": department, "risky_identities": count} for department, count in counts.most_common(limit)]


def _most_common_finding(findings: Sequence[Mapping[str, Any]]) -> str:
    counts = Counter(str(finding.get("risk_type", "")) for finding in findings)
    if not counts:
        return "None"
    return counts.most_common(1)[0][0]


def _recommended_priorities(findings: Sequence[Mapping[str, Any]]) -> List[str]:
    counts = Counter(str(finding.get("risk_type", "")) for finding in findings)
    priorities = []
    mapping = [
        ("OFFBOARDING_GAP", "Review offboarding processes"),
        ("MULTI_PLATFORM_ADMIN", "Audit administrative accounts"),
        ("STALE_ACTIVE_ACCOUNT", "Remove stale privileged identities"),
        ("SUSPENDED_ACCOUNT_MISMATCH", "Verify suspended account synchronization"),
        ("EXCESSIVE_PLATFORM_EXPOSURE", "Reduce excessive platform exposure"),
    ]
    mapping.sort(key=lambda item: (-counts.get(item[0], 0), item[0]))
    for _, label in mapping:
        priorities.append(label)
    return priorities


def _top_risks(risk_profiles: Sequence[Mapping[str, Any]], limit: int = 5) -> List[dict]:
    ranked = sorted(
        risk_profiles,
        key=lambda profile: (-int(profile.get("score", 0) or 0), str(profile.get("name", "")).lower()),
    )
    return [
        {
            "person_id": str(profile.get("person_id", "")),
            "name": str(profile.get("name", "")),
            "email": str(profile.get("email", "")),
            "score": int(profile.get("score", 0) or 0),
            "risk_level": str(profile.get("risk_level", "")),
            "findings": list(profile.get("findings", [])),
        }
        for profile in ranked[:limit]
    ]


def _risk_distribution(risk_profiles: Sequence[Mapping[str, Any]]) -> Dict[str, int]:
    counts = Counter(str(profile.get("risk_level", "")).lower() for profile in risk_profiles)
    return {
        "critical": counts.get("critical", 0),
        "high": counts.get("high", 0),
        "medium": counts.get("medium", 0),
        "low": counts.get("low", 0),
        "none": counts.get("none", 0),
    }


def _average_score(risk_profiles: Sequence[Mapping[str, Any]]) -> float:
    if not risk_profiles:
        return 0.0
    return round(sum(int(profile.get("score", 0) or 0) for profile in risk_profiles) / len(risk_profiles), 1)


def _summary_text(summary: Mapping[str, Any]) -> str:
    lines = [
        f"{summary['total_identities']} identities analyzed",
        "",
        f"{summary['critical_risks']} critical risks identified",
        "",
        f"{summary['offboarding_gaps']} offboarding gaps detected",
        "",
        f"Most common issue: {summary['most_common_finding'].replace('_', ' ').title()}",
    ]
    return "\n".join(lines)


def _table_from_dicts(rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> List[List[str]]:
    table = [list(columns)]
    for row in rows:
        table.append([str(row.get(column, "")) for column in columns])
    return table


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]], columns: Sequence[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})
    return path


def save_exports(risk_profiles: Sequence[Mapping[str, Any]], findings: Sequence[Mapping[str, Any]], ai_reports: Sequence[Mapping[str, Any]]) -> Dict[str, Path]:
    _write_csv(
        CSV_RISK_PROFILES_FILE,
        [
            {
                "person_id": item.get("person_id", ""),
                "name": item.get("name", ""),
                "email": item.get("email", ""),
                "score": item.get("score", 0),
                "risk_level": item.get("risk_level", ""),
                "findings": "; ".join(item.get("findings", [])),
            }
            for item in risk_profiles
        ],
        ["person_id", "name", "email", "score", "risk_level", "findings"],
    )
    _write_csv(
        CSV_FINDINGS_FILE,
        [
            {
                "finding_id": item.get("finding_id", ""),
                "person_id": item.get("person_id", ""),
                "name": item.get("name", ""),
                "email": item.get("email", ""),
                "risk_type": item.get("risk_type", ""),
                "severity": item.get("severity", ""),
                "description": item.get("description", ""),
                "evidence": json.dumps(item.get("evidence", {}), sort_keys=True),
            }
            for item in findings
        ],
        ["finding_id", "person_id", "name", "email", "risk_type", "severity", "description", "evidence"],
    )
    _write_csv(
        CSV_AI_REPORTS_FILE,
        [
            {
                "person_id": item.get("person_id", ""),
                "risk_score": item.get("risk_score", 0),
                "risk_level": item.get("risk_level", ""),
                "summary": item.get("summary", ""),
                "security_impact": item.get("security_impact", ""),
                "recommended_actions": "; ".join(item.get("recommended_actions", [])),
            }
            for item in ai_reports
        ],
        ["person_id", "risk_score", "risk_level", "summary", "security_impact", "recommended_actions"],
    )
    return {
        "risk_profiles_csv": CSV_RISK_PROFILES_FILE,
        "findings_csv": CSV_FINDINGS_FILE,
        "ai_reports_csv": CSV_AI_REPORTS_FILE,
    }


def save_executive_report(report: Mapping[str, Any], json_path: Path = EXECUTIVE_JSON_FILE) -> Path:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return json_path


def save_pdf_report(report: Mapping[str, Any], pdf_path: Path = EXECUTIVE_PDF_FILE) -> Path:
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(str(pdf_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story: List[Any] = []

    story.append(Paragraph("Executive Report", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(_summary_text(report["summary"]).replace("\n", "<br/>"), styles["BodyText"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Top Risks", styles["Heading2"]))
    top_risks = report.get("top_risks", [])[:5]
    risk_rows = [["Name", "Score", "Level"]]
    for item in top_risks:
        risk_rows.append([item["name"], str(item["score"]), item["risk_level"]])
    table = Table(risk_rows, colWidths=[250, 70, 80])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))

    story.append(Paragraph("Recommendations", styles["Heading2"]))
    for recommendation in report.get("recommended_priorities", []):
        story.append(Paragraph(f"- {recommendation}", styles["BodyText"]))

    document.build(story)
    if pdf_path != PDF_EXPORT_FILE:
        PDF_EXPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        PDF_EXPORT_FILE.write_bytes(pdf_path.read_bytes())
    return pdf_path


def _build_summary(risk_profiles: Sequence[Mapping[str, Any]], findings: Sequence[Mapping[str, Any]], unified_identities: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    risk_distribution = _risk_distribution(risk_profiles)
    summary = {
        "total_identities": len(unified_identities),
        "critical_risks": risk_distribution["critical"],
        "high_risks": risk_distribution["high"],
        "average_risk_score": _average_score(risk_profiles),
        "most_common_finding": _most_common_finding(findings),
        "offboarding_gaps": sum(1 for finding in findings if finding.get("risk_type") == "OFFBOARDING_GAP"),
    }
    return summary


def generate_executive_report() -> Dict[str, Any]:
    unified_identities = load_unified_identities()
    risk_profiles = load_risk_profiles()
    findings = load_findings()
    ai_reports = load_ai_reports()
    demo_scenarios = load_demo_scenarios()

    summary = _build_summary(risk_profiles, findings, unified_identities)
    report = {
        "summary": summary,
        "top_risks": _top_risks(risk_profiles),
        "risk_distribution": _risk_distribution(risk_profiles),
        "recommended_priorities": _recommended_priorities(findings),
        "showcase_incidents": get_showcase_incidents(),
        "platform_risk_breakdown": get_platform_risk_breakdown(),
        "risk_trends": get_risk_trends(),
        "top_departments_at_risk": get_top_departments_at_risk(),
        "demo_scenarios": demo_scenarios,
        "security_timelines": {
            str(item.get("person_id", "")): build_security_timeline(item, [finding for finding in findings if str(finding.get("person_id", "")) == str(item.get("person_id", ""))])
            for item in get_top_incidents(limit=10)
        },
        "ai_reports_count": len(ai_reports),
    }
    save_executive_report(report, EXECUTIVE_JSON_FILE)
    save_exports(risk_profiles, findings, ai_reports)
    save_pdf_report(report, EXECUTIVE_PDF_FILE)
    return report


def print_executive_preview(report: Mapping[str, Any]) -> None:
    summary = report["summary"]
    print("========== EXECUTIVE REPORT ==========")
    print()
    print(f"{summary['total_identities']} identities analyzed")
    print()
    print(f"{summary['critical_risks']} critical risks identified")
    print()
    print(f"{summary['offboarding_gaps']} offboarding gaps detected")
    print()
    print("Most common issue:")
    print(str(summary["most_common_finding"]).replace("_", " ").title())
    print()
    print("Priority Recommendations:")
    for index, item in enumerate(report.get("recommended_priorities", [])[:5], start=1):
        print(f"{index}. {item}")
    print()
    print("======================================")


def main() -> int:
    report = generate_executive_report()
    print_executive_preview(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
