"""Deterministic identity correlation engine based on normalized email."""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence

if __package__ in (None, ""):
    PROJECT_ROOT = Path(__file__).resolve().parents[1]
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))

from models.identity import UnifiedIdentity
from services.data_loader import (  # type: ignore[import-not-found]
    load_ad_users,
    load_aws_users,
    load_all_datasets,
    load_azure_users,
    load_login_events,
    load_okta_users,
    load_offboarding_records,
    load_salesforce_users,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "unified_identities.json"

PLATFORM_ALIASES = {
    "active directory": "ad",
    "ad": "ad",
    "azure ad": "azure",
    "azure": "azure",
    "aws iam": "aws",
    "aws": "aws",
    "okta": "okta",
    "salesforce": "salesforce",
}

LAST_RESULT: List[UnifiedIdentity] = []


def load_all_platforms() -> Dict[str, List[dict]]:
    """Load all supported platform datasets as plain dictionaries."""
    datasets = load_all_datasets()
    return {
        "ad": [record.__dict__ for record in datasets["ad_users"]],
        "azure": [record.__dict__ for record in datasets["azure_users"]],
        "aws": [record.__dict__ for record in datasets["aws_users"]],
        "okta": [record.__dict__ for record in datasets["okta_users"]],
        "salesforce": [record.__dict__ for record in datasets["salesforce_users"]],
    }


def normalize_email(email: str) -> str:
    return email.lower().strip()


def normalize_platform(platform: str) -> str:
    return PLATFORM_ALIASES.get(platform.lower().strip(), platform.lower().strip())


def _record_email(record: Mapping[str, str]) -> str:
    email = record.get("email", "")
    return normalize_email(email)


def build_unified_identity(person_id: str, grouped_records: Sequence[Mapping[str, Any]]) -> UnifiedIdentity:
    if not grouped_records:
        raise ValueError("grouped_records must not be empty")

    ordered_records = list(grouped_records)
    primary = ordered_records[0]
    accounts: Dict[str, Dict[str, Any]] = {}

    for record in ordered_records:
        platform_key = normalize_platform(record.get("platform", ""))
        accounts[platform_key] = {
            "status": record.get("status", ""),
            "role": record.get("role", ""),
            "last_login": record.get("last_login", ""),
            "account_type": record.get("account_type", ""),
            "owner_email": record.get("owner_email", ""),
            "mfa_enabled": record.get("mfa_enabled", False),
            "risk_context": record.get("risk_context", None),
        }

    return UnifiedIdentity(
        person_id=person_id,
        name=primary.get("name", ""),
        email=_record_email(primary),
        accounts=accounts,
    )


def correlate_identities(
    platform_records: Mapping[str, Sequence[Mapping[str, str]]] | None = None,
) -> List[UnifiedIdentity]:
    source = platform_records or load_all_platforms()
    grouped: MutableMapping[str, List[Mapping[str, str]]] = defaultdict(list)

    for records in source.values():
        for record in records:
            email = _record_email(record)
            if not email:
                continue
            normalized = dict(record)
            normalized["email"] = email
            grouped[email].append(normalized)

    unified: List[UnifiedIdentity] = []
    for index, email in enumerate(sorted(grouped), start=1):
        unified.append(build_unified_identity(f"PID{index:03d}", grouped[email]))

    global LAST_RESULT
    LAST_RESULT = unified
    return unified


def get_total_people(unified_identities: Sequence[UnifiedIdentity] | None = None) -> int:
    identities = unified_identities if unified_identities is not None else LAST_RESULT
    return len(identities)


def get_total_accounts(platform_records: Mapping[str, Sequence[Mapping[str, str]]] | None = None) -> int:
    source = platform_records or load_all_platforms()
    return sum(len(records) for records in source.values())


def get_platform_distribution(
    platform_records: Mapping[str, Sequence[Mapping[str, str]]] | None = None,
) -> Dict[str, int]:
    source = platform_records or load_all_platforms()
    return {platform: len(records) for platform, records in source.items()}


def save_unified_identities(
    unified_identities: Sequence[UnifiedIdentity],
    output_path: Path | str = OUTPUT_FILE,
) -> Path:
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = [identity.to_dict() for identity in unified_identities]
    destination.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return destination


def generate_correlation_report(
    unified_identities: Sequence[UnifiedIdentity],
    platform_records: Mapping[str, Sequence[Mapping[str, str]]] | None = None,
) -> str:
    source = platform_records or load_all_platforms()
    total_accounts = get_total_accounts(source)
    unique_people = get_total_people(unified_identities)
    distribution = get_platform_distribution(source)

    lines = [
        "========== CORRELATION REPORT ==========",
        f"Total Accounts: {total_accounts}",
        f"Unique People: {unique_people}",
        "",
        f"AD Accounts: {distribution.get('ad', 0)}",
        f"Azure Accounts: {distribution.get('azure', 0)}",
        f"AWS Accounts: {distribution.get('aws', 0)}",
        f"Okta Accounts: {distribution.get('okta', 0)}",
        f"Salesforce Accounts: {distribution.get('salesforce', 0)}",
        "",
        f"Unified Identities Created: {unique_people}",
        "========================================",
    ]
    report = "\n".join(lines)
    print(report)
    return report


def main() -> int:
    platforms = load_all_platforms()
    unified_identities = correlate_identities(platforms)
    save_unified_identities(unified_identities, OUTPUT_FILE)
    generate_correlation_report(unified_identities, platforms)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
