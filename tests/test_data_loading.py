from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.data_loader import (  # noqa: E402
    load_ad_users,
    load_all_datasets,
    load_aws_users,
    load_azure_users,
    load_login_events,
    load_okta_users,
    load_offboarding_records,
    load_salesforce_users,
)


DATA_DIR = ROOT / "data"


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_all_files_exist():
    expected_files = {
        "ad_users.json",
        "azure_users.json",
        "aws_users.json",
        "okta_users.json",
        "salesforce_users.json",
        "login_events.json",
        "offboarding_records.json",
    }
    actual_files = {path.name for path in DATA_DIR.glob("*.json")}
    assert expected_files.issubset(actual_files)


def test_json_is_well_formed():
    for path in DATA_DIR.glob("*.json"):
        payload = read_json(path)
        assert isinstance(payload, list)


def test_user_datasets_load_successfully():
    datasets = {
        "ad": load_ad_users(),
        "azure": load_azure_users(),
        "aws": load_aws_users(),
        "okta": load_okta_users(),
        "salesforce": load_salesforce_users(),
    }
    for name, records in datasets.items():
        assert len(records) == 60, name
        for record in records:
            assert record.user_id
            assert record.name
            assert record.email
            assert record.department
            assert record.status in {"active", "disabled", "suspended"}
            assert record.platform
            assert record.role
            assert record.last_login


def test_event_and_offboarding_datasets_load_successfully():
    events = load_login_events()
    offboarding = load_offboarding_records()

    assert len(events) == 750
    assert len(offboarding) == 75

    for event in events:
        assert event.event_id
        assert event.email
        assert event.platform
        assert event.timestamp
        assert event.event_type == "login"

    for record in offboarding:
        assert record.record_id
        assert record.email
        assert record.termination_date
        assert record.reason


def test_load_all_datasets_smoke():
    datasets = load_all_datasets()
    assert set(datasets) == {
        "ad_users",
        "azure_users",
        "aws_users",
        "okta_users",
        "salesforce_users",
        "login_events",
        "offboarding_records",
    }
