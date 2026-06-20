"""Cross-platform identity risk detection engine."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

if __package__ in (None, ""):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from models.finding import Finding
from services.correlation_engine import OUTPUT_FILE as UNIFIED_IDENTITIES_FILE
from services.data_loader import load_api_tokens, load_privilege_events
from services.privilege_graph import effective_privilege


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
RISK_FINDINGS_FILE = OUTPUT_DIR / "risk_findings.json"

ADMIN_ROLES = {
    "administrator",
    "global administrator",
    "admin",
    "super admin",
    "security administrator",
}
LOW_PRIVILEGE_ROLES = {
    "employee",
    "standard user",
    "support engineer",
    "read only",
    "contractor",
    "developer",
}

ACTIVE_STATUSES = {"active"}
DISABLED_STATUSES = {"disabled"}
SUSPENDED_STATUSES = {"suspended"}
STALE_DAYS_THRESHOLD = 180

LAST_FINDINGS: List[Finding] = []


def load_unified_identities(path: Path | str = UNIFIED_IDENTITIES_FILE) -> List[dict]:
    source = Path(path)
    if not source.exists():
        print(f"[risk_engine] Missing unified identity file: {source}", file=sys.stderr)
        return []

    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[risk_engine] Invalid JSON in {source}: {exc}", file=sys.stderr)
        return []
    except OSError as exc:
        print(f"[risk_engine] Could not read {source}: {exc}", file=sys.stderr)
        return []

    if not isinstance(payload, list):
        print(f"[risk_engine] Expected an array in {source}", file=sys.stderr)
        return []

    return [item for item in payload if isinstance(item, dict)]


def _normalize_account_status(value: str) -> str:
    return value.lower().strip()


def _parse_last_login(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def _normalize_role(value: str) -> str:
    return value.lower().strip()


def _is_admin_role(value: str) -> bool:
    return _normalize_role(value) in ADMIN_ROLES


def _is_low_privilege_role(value: str) -> bool:
    normalized = _normalize_role(value)
    return bool(normalized) and not _is_admin_role(normalized)


def _new_finding(
    counter: int,
    unified: Mapping[str, Any],
    risk_type: str,
    severity: str,
    description: str,
    evidence: Dict[str, Any],
) -> Finding:
    return Finding(
        finding_id=f"F{counter:03d}",
        person_id=str(unified.get("person_id", "")),
        name=str(unified.get("name", "")),
        email=str(unified.get("email", "")),
        risk_type=risk_type,
        severity=severity,
        description=description,
        evidence=evidence,
    )


def detect_offboarding_gaps(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1
    for unified in unified_identities:
        accounts = unified.get("accounts", {}) or {}
        statuses = {
            platform: _normalize_account_status(str(data.get("status", "")))
            for platform, data in accounts.items()
            if isinstance(data, Mapping)
        }
        disabled = [platform for platform, status in statuses.items() if status in DISABLED_STATUSES]
        active = [platform for platform, status in statuses.items() if status in ACTIVE_STATUSES]
        if disabled and active:
            description = f"User disabled in {', '.join(sorted(disabled))} but active in {', '.join(sorted(active))}"
            findings.append(
                _new_finding(
                    counter,
                    unified,
                    "OFFBOARDING_GAP",
                    "HIGH",
                    description,
                    statuses,
                )
            )
            counter += 1
    return findings


def detect_multi_platform_admins(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1
    for unified in unified_identities:
        accounts = unified.get("accounts", {}) or {}
        admin_accounts = {
            platform: data.get("role", "")
            for platform, data in accounts.items()
            if isinstance(data, Mapping) and str(data.get("role", "")).strip().lower() in ADMIN_ROLES
        }
        if len(admin_accounts) >= 2:
            description = f"Admin privileges detected across {len(admin_accounts)} platforms"
            findings.append(
                _new_finding(
                    counter,
                    unified,
                    "MULTI_PLATFORM_ADMIN",
                    "HIGH",
                    description,
                    admin_accounts,
                )
            )
            counter += 1
    return findings


def detect_stale_accounts(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1
    now = datetime.now(timezone.utc)

    for unified in unified_identities:
        accounts = unified.get("accounts", {}) or {}
        for platform, data in accounts.items():
            if not isinstance(data, Mapping):
                continue
            status = _normalize_account_status(str(data.get("status", "")))
            if status != "active":
                continue
            last_login = _parse_last_login(str(data.get("last_login", "")))
            if last_login is None:
                continue
            age_days = (now - last_login).days
            if age_days > STALE_DAYS_THRESHOLD:
                evidence = {
                    "platform": platform,
                    "last_login": last_login.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                    "days_since_last_login": age_days,
                }
                findings.append(
                    _new_finding(
                        counter,
                        unified,
                        "STALE_ACTIVE_ACCOUNT",
                        "MEDIUM",
                        f"Active account unused for {age_days} days on {platform}",
                        evidence,
                    )
                )
                counter += 1
    return findings


def detect_suspended_mismatches(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1
    for unified in unified_identities:
        accounts = unified.get("accounts", {}) or {}
        statuses = {
            platform: _normalize_account_status(str(data.get("status", "")))
            for platform, data in accounts.items()
            if isinstance(data, Mapping)
        }
        suspended = [platform for platform, status in statuses.items() if status in SUSPENDED_STATUSES]
        active = [platform for platform, status in statuses.items() if status in ACTIVE_STATUSES]
        if suspended and active:
            description = f"User suspended in {', '.join(sorted(suspended))} but active elsewhere"
            findings.append(
                _new_finding(
                    counter,
                    unified,
                    "SUSPENDED_ACCOUNT_MISMATCH",
                    "HIGH",
                    description,
                    statuses,
                )
            )
            counter += 1
    return findings


def detect_platform_exposure(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1
    for unified in unified_identities:
        accounts = unified.get("accounts", {}) or {}
        platforms = sorted([platform for platform, data in accounts.items() if isinstance(data, Mapping)])
        if len(platforms) >= 4:
            description = f"Identity present in {len(platforms)} platforms"
            findings.append(
                _new_finding(
                    counter,
                    unified,
                    "EXCESSIVE_PLATFORM_EXPOSURE",
                    "MEDIUM",
                    description,
                    {"platforms": platforms},
                )
            )
            counter += 1
    return findings


def detect_nested_group_privilege(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1

    for unified in unified_identities:
        email = str(unified.get("email", ""))
        accounts = unified.get("accounts", {}) or {}
        stated_roles = [
            str(data.get("role", ""))
            for data in accounts.values()
            if isinstance(data, Mapping) and _is_low_privilege_role(str(data.get("role", "")))
        ]
        if not stated_roles:
            continue

        effective_roles = effective_privilege(email)
        admin_roles = sorted(role for role in effective_roles if _is_admin_role(role))
        if not admin_roles:
            continue

        evidence = {
            "stated_roles": sorted(set(stated_roles)),
            "effective_privilege": effective_roles,
            "admin_equivalent_roles": admin_roles,
        }
        findings.append(
            _new_finding(
                counter,
                unified,
                "HIDDEN_PRIVILEGE_VIA_GROUP_NESTING",
                "HIGH",
                "Low-privilege account gains admin-equivalent access through nested groups",
                evidence,
            )
        )
        counter += 1

    return findings


def detect_privilege_spikes(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1
    events = load_privilege_events()
    events_by_email: Dict[str, List[Any]] = {}

    for event in events:
        if not event.approved_by:
            events_by_email.setdefault(event.email.lower().strip(), []).append(event)

    identity_lookup = {
        str(identity.get("email", "")).lower().strip(): identity
        for identity in unified_identities
    }

    for email, records in events_by_email.items():
        timestamps = sorted(
            (
                _parse_timestamp(record.timestamp),
                record,
            )
            for record in records
            if _parse_timestamp(record.timestamp) is not None
        )
        if len(timestamps) < 3:
            continue

        window_start = 0
        for window_end, (current_timestamp, _) in enumerate(timestamps):
            while (
                window_start < window_end
                and (current_timestamp - timestamps[window_start][0]).days > 7
            ):
                window_start += 1
            if window_end - window_start + 1 >= 3:
                identity = identity_lookup.get(email)
                if identity is None:
                    break
                evidence_records = [record.event_id for _, record in timestamps[window_start : window_end + 1]]
                findings.append(
                    _new_finding(
                        counter,
                        identity,
                        "UNAPPROVED_PRIVILEGE_SPIKE",
                        "HIGH",
                        "Three or more unapproved privilege changes occurred within seven days",
                        {
                            "email": email,
                            "event_ids": evidence_records,
                            "window_start": timestamps[window_start][0].isoformat(),
                            "window_end": current_timestamp.isoformat(),
                        },
                    )
                )
                counter += 1
                break

    return findings


def detect_token_abuse(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    counter = 1
    now = date.today()
    tokens = load_api_tokens()
    identity_lookup = {
        str(identity.get("email", "")).lower().strip(): identity
        for identity in unified_identities
    }

    for token in tokens:
        stale = False
        misuse = False

        last_rotated = _parse_date(token.last_rotated)
        if last_rotated is not None and (now - last_rotated).days > 365:
            stale = True

        if _normalize_role(token.scope) == "read-only" and bool(token.observed_write_call):
            misuse = True

        if not (stale or misuse):
            continue

        identity = identity_lookup.get(token.owner_email.lower().strip())
        if identity is None:
            continue

        severity = "HIGH" if misuse else "MEDIUM"
        reasons = []
        if stale:
            reasons.append("stale_rotation")
        if misuse:
            reasons.append("misused_write_scope")

        findings.append(
            _new_finding(
                counter,
                identity,
                "STALE_OR_MISUSED_TOKEN",
                severity,
                "API token is stale or used beyond its declared scope",
                {
                    "token_id": token.token_id,
                    "scope": token.scope,
                    "status": token.status,
                    "reasons": reasons,
                    "last_rotated": token.last_rotated,
                    "observed_write_call": token.observed_write_call,
                },
            )
        )
        counter += 1

    return findings


def run_all_detectors(unified_identities: Sequence[Mapping[str, Any]]) -> List[Finding]:
    findings: List[Finding] = []
    detectors = [
        detect_offboarding_gaps,
        detect_multi_platform_admins,
        detect_stale_accounts,
        detect_suspended_mismatches,
        detect_platform_exposure,
        detect_nested_group_privilege,
        detect_privilege_spikes,
        detect_token_abuse,
    ]

    for detector in detectors:
        findings.extend(detector(unified_identities))

    for index, finding in enumerate(findings, start=1):
        finding.finding_id = f"F{index:03d}"

    global LAST_FINDINGS
    LAST_FINDINGS = findings
    return findings


def save_findings(findings: Sequence[Finding], output_path: Path | str = RISK_FINDINGS_FILE) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = [finding.to_dict() for finding in findings]
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def generate_risk_report(findings: Sequence[Finding], unified_identities: Sequence[Mapping[str, Any]]) -> str:
    counts = Counter(finding.risk_type for finding in findings)
    lines = [
        "========== RISK REPORT ==========",
        "",
        f"Unified Identities: {len(unified_identities)}",
        "",
        f"OFFBOARDING_GAP: {counts.get('OFFBOARDING_GAP', 0)}",
        "",
        f"MULTI_PLATFORM_ADMIN: {counts.get('MULTI_PLATFORM_ADMIN', 0)}",
        "",
        f"STALE_ACTIVE_ACCOUNT: {counts.get('STALE_ACTIVE_ACCOUNT', 0)}",
        "",
        f"SUSPENDED_ACCOUNT_MISMATCH: {counts.get('SUSPENDED_ACCOUNT_MISMATCH', 0)}",
        "",
        f"EXCESSIVE_PLATFORM_EXPOSURE: {counts.get('EXCESSIVE_PLATFORM_EXPOSURE', 0)}",
        "",
        f"HIDDEN_PRIVILEGE_VIA_GROUP_NESTING: {counts.get('HIDDEN_PRIVILEGE_VIA_GROUP_NESTING', 0)}",
        "",
        f"UNAPPROVED_PRIVILEGE_SPIKE: {counts.get('UNAPPROVED_PRIVILEGE_SPIKE', 0)}",
        "",
        f"STALE_OR_MISUSED_TOKEN: {counts.get('STALE_OR_MISUSED_TOKEN', 0)}",
        "",
        f"TOTAL FINDINGS: {len(findings)}",
        "",
        "=================================",
    ]
    report = "\n".join(lines)
    print(report)
    return report


def main() -> int:
    unified_identities = load_unified_identities()
    findings = run_all_detectors(unified_identities)
    save_findings(findings, RISK_FINDINGS_FILE)
    generate_risk_report(findings, unified_identities)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
