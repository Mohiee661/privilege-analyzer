"""Dataset loading and validation helpers for synthetic identity data."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Type, TypeVar

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    name: str
    email: str
    department: str
    status: str
    platform: str
    role: str
    last_login: str


@dataclass(frozen=True)
class LoginEvent:
    event_id: str
    email: str
    platform: str
    timestamp: str
    event_type: str


@dataclass(frozen=True)
class OffboardingRecord:
    record_id: str
    email: str
    termination_date: str
    reason: str


T = TypeVar("T")


USER_FIELDS: Sequence[str] = (
    "user_id",
    "name",
    "email",
    "department",
    "status",
    "platform",
    "role",
    "last_login",
)

LOGIN_EVENT_FIELDS: Sequence[str] = (
    "event_id",
    "email",
    "platform",
    "timestamp",
    "event_type",
)

OFFBOARDING_FIELDS: Sequence[str] = (
    "record_id",
    "email",
    "termination_date",
    "reason",
)


def _load_json_list(path: Path) -> List[dict]:
    if not path.exists():
        print(f"[data_loader] Missing file: {path}", file=sys.stderr)
        return []

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[data_loader] Invalid JSON in {path}: {exc}", file=sys.stderr)
        return []
    except OSError as exc:
        print(f"[data_loader] Could not read {path}: {exc}", file=sys.stderr)
        return []

    if not isinstance(raw, list):
        print(f"[data_loader] Expected a JSON array in {path}", file=sys.stderr)
        return []

    records: List[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            print(
                f"[data_loader] Skipping non-object record at index {index} in {path}",
                file=sys.stderr,
            )
            continue
        records.append(item)
    return records


def _validate_and_convert(
    records: Iterable[dict],
    required_fields: Sequence[str],
    model: Type[T],
    source_name: str,
) -> List[T]:
    validated: List[T] = []
    for index, record in enumerate(records):
        missing = [field for field in required_fields if field not in record]
        if missing:
            print(
                f"[data_loader] {source_name} record {index} missing fields: {', '.join(missing)}",
                file=sys.stderr,
            )
            continue

        try:
            validated.append(model(**{field: record[field] for field in required_fields}))
        except TypeError as exc:
            print(
                f"[data_loader] {source_name} record {index} could not be loaded: {exc}",
                file=sys.stderr,
            )
    return validated


def _load_dataset(filename: str, required_fields: Sequence[str], model: Type[T]) -> List[T]:
    path = DATA_DIR / filename
    records = _load_json_list(path)
    return _validate_and_convert(records, required_fields, model, filename)


def load_ad_users() -> List[UserRecord]:
    return _load_dataset("ad_users.json", USER_FIELDS, UserRecord)


def load_azure_users() -> List[UserRecord]:
    return _load_dataset("azure_users.json", USER_FIELDS, UserRecord)


def load_aws_users() -> List[UserRecord]:
    return _load_dataset("aws_users.json", USER_FIELDS, UserRecord)


def load_okta_users() -> List[UserRecord]:
    return _load_dataset("okta_users.json", USER_FIELDS, UserRecord)


def load_salesforce_users() -> List[UserRecord]:
    return _load_dataset("salesforce_users.json", USER_FIELDS, UserRecord)


def load_login_events() -> List[LoginEvent]:
    return _load_dataset("login_events.json", LOGIN_EVENT_FIELDS, LoginEvent)


def load_offboarding_records() -> List[OffboardingRecord]:
    return _load_dataset("offboarding_records.json", OFFBOARDING_FIELDS, OffboardingRecord)


def load_all_datasets() -> Dict[str, List[object]]:
    return {
        "ad_users": load_ad_users(),
        "azure_users": load_azure_users(),
        "aws_users": load_aws_users(),
        "okta_users": load_okta_users(),
        "salesforce_users": load_salesforce_users(),
        "login_events": load_login_events(),
        "offboarding_records": load_offboarding_records(),
    }
