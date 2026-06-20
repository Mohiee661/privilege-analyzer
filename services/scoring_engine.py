"""Risk scoring and prioritization engine."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Sequence

if __package__ in (None, ""):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from models.risk_profile import RiskProfile
from services.correlation_engine import OUTPUT_FILE as UNIFIED_IDENTITIES_FILE
from services.risk_engine import RISK_FINDINGS_FILE


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
RISK_PROFILES_FILE = OUTPUT_DIR / "risk_profiles.json"

FINDING_SCORES = {
    "OFFBOARDING_GAP": 40,
    "MULTI_PLATFORM_ADMIN": 30,
    "STALE_ACTIVE_ACCOUNT": 20,
    "SUSPENDED_ACCOUNT_MISMATCH": 25,
    "EXCESSIVE_PLATFORM_EXPOSURE": 15,
    "HIDDEN_PRIVILEGE_VIA_GROUP_NESTING": 35,
    "UNAPPROVED_PRIVILEGE_SPIKE": 30,
    "STALE_OR_MISUSED_TOKEN": 20,
}


def load_unified_identities(path: Path | str = UNIFIED_IDENTITIES_FILE) -> List[dict]:
    source = Path(path)
    if not source.exists():
        print(f"[scoring_engine] Missing unified identities file: {source}", file=sys.stderr)
        return []
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[scoring_engine] Invalid JSON in {source}: {exc}", file=sys.stderr)
        return []
    if not isinstance(payload, list):
        print(f"[scoring_engine] Expected an array in {source}", file=sys.stderr)
        return []
    return [item for item in payload if isinstance(item, dict)]


def load_risk_findings(path: Path | str = RISK_FINDINGS_FILE) -> List[dict]:
    source = Path(path)
    if not source.exists():
        print(f"[scoring_engine] Missing risk findings file: {source}", file=sys.stderr)
        return []
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[scoring_engine] Invalid JSON in {source}: {exc}", file=sys.stderr)
        return []
    if not isinstance(payload, list):
        print(f"[scoring_engine] Expected an array in {source}", file=sys.stderr)
        return []
    return [item for item in payload if isinstance(item, dict)]


def calculate_identity_score(findings: Sequence[Mapping[str, object]]) -> int:
    total = 0
    for finding in findings:
        risk_type = str(finding.get("risk_type", ""))
        total += FINDING_SCORES.get(risk_type, 0)
    return min(100, total)


def calculate_risk_level(score: int) -> str:
    if score >= 90:
        return "CRITICAL"
    if score >= 70:
        return "HIGH"
    if score >= 40:
        return "MEDIUM"
    if score >= 1:
        return "LOW"
    return "NONE"


def build_risk_profiles(
    unified_identities: Sequence[Mapping[str, object]],
    findings: Sequence[Mapping[str, object]],
) -> List[RiskProfile]:
    findings_by_person: Dict[str, List[Mapping[str, object]]] = {}
    for finding in findings:
        person_id = str(finding.get("person_id", ""))
        findings_by_person.setdefault(person_id, []).append(finding)

    profiles: List[RiskProfile] = []
    for identity in unified_identities:
        person_id = str(identity.get("person_id", ""))
        person_findings = findings_by_person.get(person_id, [])
        score = calculate_identity_score(person_findings)
        profile = RiskProfile(
            person_id=person_id,
            name=str(identity.get("name", "")),
            email=str(identity.get("email", "")),
            score=score,
            risk_level=calculate_risk_level(score),
            findings=sorted({str(f.get("risk_type", "")) for f in person_findings if f.get("risk_type")}),
        )
        profiles.append(profile)
    return profiles


def rank_identities(risk_profiles: Sequence[RiskProfile]) -> List[RiskProfile]:
    return sorted(risk_profiles, key=lambda profile: (-profile.score, profile.name.lower(), profile.person_id))


def generate_risk_distribution(risk_profiles: Sequence[RiskProfile]) -> Dict[str, int]:
    counts = Counter(profile.risk_level.lower() for profile in risk_profiles)
    return {
        "critical": counts.get("critical", 0),
        "high": counts.get("high", 0),
        "medium": counts.get("medium", 0),
        "low": counts.get("low", 0),
        "none": counts.get("none", 0),
    }


def get_average_risk_score(risk_profiles: Sequence[RiskProfile]) -> float:
    if not risk_profiles:
        return 0.0
    return round(sum(profile.score for profile in risk_profiles) / len(risk_profiles), 1)


def get_top_risks(risk_profiles: Sequence[RiskProfile], limit: int = 5) -> List[RiskProfile]:
    return rank_identities(risk_profiles)[:limit]


def save_risk_profiles(
    risk_profiles: Sequence[RiskProfile],
    output_path: Path | str = RISK_PROFILES_FILE,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = [profile.to_dict() for profile in risk_profiles]
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def print_top_risks(risk_profiles: Sequence[RiskProfile], limit: int = 5) -> str:
    top_profiles = get_top_risks(risk_profiles, limit=limit)
    lines = [
        "========== TOP RISKS ==========",
        "",
    ]
    for index, profile in enumerate(top_profiles, start=1):
        lines.append(f"{index}. {profile.name:<16} {profile.score:>3}   {profile.risk_level}")
        lines.append("")
    lines.append("===============================")
    report = "\n".join(lines)
    print(report)
    return report


def print_analytics(risk_profiles: Sequence[RiskProfile]) -> str:
    distribution = generate_risk_distribution(risk_profiles)
    lines = [
        "========== RISK ANALYTICS ==========",
        "",
        f"Identities Analyzed: {len(risk_profiles)}",
        "",
        f"Critical: {distribution['critical']}",
        "",
        f"High: {distribution['high']}",
        "",
        f"Medium: {distribution['medium']}",
        "",
        f"Low: {distribution['low']}",
        "",
        f"Average Score: {get_average_risk_score(risk_profiles)}",
        "",
        "====================================",
    ]
    report = "\n".join(lines)
    print(report)
    return report


def main() -> int:
    unified_identities = load_unified_identities()
    findings = load_risk_findings()
    risk_profiles = build_risk_profiles(unified_identities, findings)
    ranked_profiles = rank_identities(risk_profiles)
    save_risk_profiles(ranked_profiles, RISK_PROFILES_FILE)
    print_top_risks(ranked_profiles)
    print_analytics(ranked_profiles)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
