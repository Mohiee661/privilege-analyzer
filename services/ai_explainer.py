"""Groq-backed AI security copilot for identity risk explanations."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

if __package__ in (None, ""):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from models.ai_report import AIReport
from services.correlation_engine import OUTPUT_FILE as UNIFIED_IDENTITIES_FILE
from services.groq_client import call_chat_completion, load_groq_client
from services.scoring_engine import RISK_PROFILES_FILE
from services.risk_engine import RISK_FINDINGS_FILE


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
AI_REPORTS_FILE = OUTPUT_DIR / "ai_reports.json"
PROMPT_FILE = PROJECT_ROOT / "prompts" / "risk_explanation.txt"

DEFAULT_TOP_N = 25
DEFAULT_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"
CACHE_FILE = OUTPUT_DIR / "ai_report_cache.json"


def load_json_list(path: Path | str, label: str) -> List[dict]:
    source = Path(path)
    if not source.exists():
        print(f"[ai_explainer] Missing {label}: {source}", file=sys.stderr)
        return []
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[ai_explainer] Invalid JSON in {source}: {exc}", file=sys.stderr)
        return []
    except OSError as exc:
        print(f"[ai_explainer] Could not read {source}: {exc}", file=sys.stderr)
        return []
    if not isinstance(payload, list):
        print(f"[ai_explainer] Expected an array in {source}", file=sys.stderr)
        return []
    return [item for item in payload if isinstance(item, dict)]


def build_prompt(identity: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]) -> str:
    template = PROMPT_FILE.read_text(encoding="utf-8")
    identity_json = json.dumps(identity, indent=2, sort_keys=True)
    findings_json = json.dumps(list(findings), indent=2, sort_keys=True)
    return template.format(
        identity_json=identity_json,
        findings_json=findings_json,
        score=identity.get("score", 0),
        risk_level=identity.get("risk_level", "NONE"),
    )


def _normalize_actions(actions: Any) -> List[str]:
    if isinstance(actions, list):
        return [str(action) for action in actions if str(action).strip()]
    if isinstance(actions, str) and actions.strip():
        return [actions.strip()]
    return []


def _normalize_finding(finding: Mapping[str, Any]) -> dict:
    return {
        "finding_id": str(finding.get("finding_id", "")),
        "person_id": str(finding.get("person_id", "")),
        "risk_type": str(finding.get("risk_type", "")),
        "severity": str(finding.get("severity", "")),
        "description": str(finding.get("description", "")),
        "evidence": finding.get("evidence", {}),
    }


def _fallback_report(identity: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]) -> AIReport:
    risk_types = [str(f.get("risk_type", "")) for f in findings if f.get("risk_type")]
    summary_parts: List[str] = []
    if "OFFBOARDING_GAP" in risk_types:
        summary_parts.append("The identity has active access after offboarding in at least one system.")
    if "MULTI_PLATFORM_ADMIN" in risk_types:
        summary_parts.append("The identity retains administrative access across multiple platforms.")
    if "STALE_ACTIVE_ACCOUNT" in risk_types:
        summary_parts.append("An active account has not been used recently.")
    if "SUSPENDED_ACCOUNT_MISMATCH" in risk_types:
        summary_parts.append("Account status is inconsistent across systems.")
    if "EXCESSIVE_PLATFORM_EXPOSURE" in risk_types:
        summary_parts.append("The identity spans many systems, increasing exposure.")
    if not summary_parts:
        summary_parts.append("No notable risk patterns were found.")

    recommended_actions = [
        "Review the linked findings and confirm current business need.",
        "Revoke or reduce access where it is no longer required.",
        "Validate recent activity and ownership for the identity.",
    ]
    if "OFFBOARDING_GAP" in risk_types:
        recommended_actions[0] = "Disable remaining active accounts and complete offboarding."

    return AIReport(
        person_id=str(identity.get("person_id", "")),
        risk_score=int(identity.get("score", 0) or 0),
        risk_level=str(identity.get("risk_level", "NONE")),
        summary=" ".join(summary_parts),
        security_impact=(
            "Ignoring this identity could leave unnecessary access in place and increase the chance of misuse."
        ),
        recommended_actions=recommended_actions[:3],
    )


def _extract_json_payload(text: str) -> dict:
    try:
        payload = json.loads(text)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        payload = json.loads(match.group(0))
        if isinstance(payload, dict):
            return payload
    raise ValueError("Model response did not contain valid JSON")


def _parse_ai_response(identity: Mapping[str, Any], raw_text: str) -> AIReport:
    payload = _extract_json_payload(raw_text)
    summary = str(payload.get("summary", "")).strip()
    security_impact = str(payload.get("security_impact", "")).strip()
    recommended_actions = _normalize_actions(payload.get("recommended_actions", []))
    if not summary or not security_impact or not recommended_actions:
        raise ValueError("AI response missing required fields")

    return AIReport(
        person_id=str(identity.get("person_id", "")),
        risk_score=int(identity.get("score", 0) or 0),
        risk_level=str(identity.get("risk_level", "NONE")),
        summary=summary,
        security_impact=security_impact,
        recommended_actions=recommended_actions,
    )


def _load_cache(path: Path = CACHE_FILE) -> Dict[str, dict]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _save_cache(cache: Mapping[str, dict], path: Path = CACHE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _cache_key(identity: Mapping[str, Any], findings: Sequence[Mapping[str, Any]]) -> str:
    normalized_findings = sorted(
        (_normalize_finding(finding) for finding in findings),
        key=lambda item: json.dumps(item, sort_keys=True),
    )
    canonical = json.dumps(
        {
            "person_id": identity.get("person_id", ""),
            "score": identity.get("score", 0),
            "risk_level": identity.get("risk_level", ""),
            "findings": normalized_findings,
        },
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_ai_report(
    identity: Mapping[str, Any],
    findings: Sequence[Mapping[str, Any]],
    client=None,
    model: str = DEFAULT_MODEL,
    cache: Mapping[str, dict] | None = None,
) -> AIReport:
    report_cache = cache if isinstance(cache, dict) else dict(cache or {})
    cache_key = _cache_key(identity, findings)
    cached = report_cache.get(cache_key)
    if cached:
        return AIReport(
            person_id=str(cached.get("person_id", identity.get("person_id", ""))),
            risk_score=int(cached.get("risk_score", identity.get("score", 0)) or 0),
            risk_level=str(cached.get("risk_level", identity.get("risk_level", "NONE"))),
            summary=str(cached.get("summary", "")),
            security_impact=str(cached.get("security_impact", "")),
            recommended_actions=list(cached.get("recommended_actions", [])),
        )

    if client is None:
        client = load_groq_client()

    prompt = build_prompt(identity, findings)
    if client is None:
        return _fallback_report(identity, findings)

    try:
        raw_text = call_chat_completion(client, prompt, (model, FALLBACK_MODEL))
        report = _parse_ai_response(identity, raw_text)
    except Exception as exc:
        print(f"[ai_explainer] Groq generation failed for {identity.get('person_id', '')}: {exc}", file=sys.stderr)
        report = _fallback_report(identity, findings)

    report_cache[cache_key] = report.to_dict()
    _save_cache(report_cache)
    return report


def _findings_for_person(findings: Sequence[Mapping[str, Any]], person_id: str) -> List[Mapping[str, Any]]:
    return [finding for finding in findings if str(finding.get("person_id", "")) == person_id]


def generate_reports_for_all_profiles(
    limit: int = DEFAULT_TOP_N,
    client=None,
    model: str = DEFAULT_MODEL,
) -> List[AIReport]:
    risk_profiles = load_json_list(RISK_PROFILES_FILE, "risk profiles")
    findings = load_json_list(RISK_FINDINGS_FILE, "risk findings")

    ranked_profiles = sorted(
        risk_profiles,
        key=lambda profile: (-int(profile.get("score", 0) or 0), str(profile.get("name", "")).lower()),
    )
    selected_profiles = [profile for profile in ranked_profiles if int(profile.get("score", 0) or 0) > 0][:limit]

    cache = _load_cache()
    resolved_client = client if client is not None else load_groq_client()
    reports: List[AIReport] = []
    for profile in selected_profiles:
        person_findings = _findings_for_person(findings, str(profile.get("person_id", "")))
        try:
            report = generate_ai_report(profile, person_findings, client=resolved_client, model=model, cache=cache)
        except Exception as exc:
            print(f"[ai_explainer] Skipping {profile.get('person_id', '')}: {exc}", file=sys.stderr)
            continue
        reports.append(report)
        cache[_cache_key(profile, person_findings)] = report.to_dict()

    _save_cache(cache)
    return reports


def save_ai_reports(reports: Sequence[AIReport], output_path: Path | str = AI_REPORTS_FILE) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = [report.to_dict() for report in reports]
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def load_ai_reports(output_path: Path | str = AI_REPORTS_FILE) -> List[AIReport]:
    records = load_json_list(output_path, "AI reports")
    reports: List[AIReport] = []
    for record in records:
        if "person_id" not in record:
            continue
        reports.append(
            AIReport(
                person_id=str(record.get("person_id", "")),
                risk_score=int(record.get("risk_score", 0) or 0),
                risk_level=str(record.get("risk_level", "NONE")),
                summary=str(record.get("summary", "")),
                security_impact=str(record.get("security_impact", "")),
                recommended_actions=list(record.get("recommended_actions", [])),
            )
        )
    return reports


def upsert_ai_report(report: AIReport, output_path: Path | str = AI_REPORTS_FILE) -> Path:
    existing = load_ai_reports(output_path)
    retained = [item for item in existing if item.person_id != report.person_id]
    retained.append(report)
    return save_ai_reports(retained, output_path)


def generate_ai_report_for_person(
    person_id: str,
    client=None,
    model: str = DEFAULT_MODEL,
) -> AIReport | None:
    risk_profiles = load_json_list(RISK_PROFILES_FILE, "risk profiles")
    findings = load_json_list(RISK_FINDINGS_FILE, "risk findings")
    profile = next((item for item in risk_profiles if str(item.get("person_id", "")) == person_id), None)
    if profile is None:
        return None
    person_findings = _findings_for_person(findings, person_id)
    cache = _load_cache()
    report = generate_ai_report(profile, person_findings, client=client, model=model, cache=cache)
    cache[_cache_key(profile, person_findings)] = report.to_dict()
    _save_cache(cache)
    upsert_ai_report(report, AI_REPORTS_FILE)
    return report


def _print_report_preview(report: AIReport) -> None:
    print("========== AI SECURITY REPORT ==========")
    print()
    print(report.person_id)
    print()
    print(f"Score: {report.risk_score}")
    print()
    print(f"Level: {report.risk_level}")
    print()
    print("Summary:")
    print(report.summary)
    print()
    print("Recommended Actions:")
    for action in report.recommended_actions:
        print(f"- {action}")
    print()
    print("========================================")


def main() -> int:
    reports = generate_reports_for_all_profiles(limit=DEFAULT_TOP_N)
    save_ai_reports(reports, AI_REPORTS_FILE)
    if reports:
        _print_report_preview(reports[0])
    else:
        print("[ai_explainer] No AI reports were generated.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
