"""Generate deterministic synthetic identity datasets for phase 1."""

from __future__ import annotations

import json
import random
import sys
from datetime import datetime, timedelta
from itertools import product
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

SEED = 20260619
USER_RECORDS_PER_PLATFORM = 60
PLATFORMS = [
    "Active Directory",
    "Azure AD",
    "AWS IAM",
    "Okta",
    "Salesforce",
]
DEPARTMENTS = [
    "Engineering",
    "Security",
    "IT",
    "Finance",
    "HR",
    "Operations",
    "Sales",
]
STATUS_SEQUENCE = ["active"] * 48 + ["disabled"] * 6 + ["suspended"] * 6
LOGIN_EVENT_COUNT = 750
OFFBOARDING_COUNT = 75

FIRST_NAMES = [
    "John",
    "Jane",
    "Michael",
    "Sarah",
    "David",
    "Emily",
    "Robert",
    "Priya",
    "Daniel",
    "Olivia",
    "James",
    "Ava",
    "William",
    "Sophia",
    "Ethan",
    "Mia",
    "Noah",
    "Isabella",
    "Lucas",
    "Amelia",
]

LAST_NAMES = [
    "Smith",
    "Johnson",
    "Williams",
    "Brown",
    "Jones",
    "Miller",
    "Davis",
    "Wilson",
    "Anderson",
    "Taylor",
    "Thomas",
    "Moore",
    "Jackson",
    "Martin",
    "Lee",
    "Perez",
    "Thompson",
    "White",
    "Harris",
    "Clark",
    "Lewis",
    "Robinson",
    "Walker",
    "Hall",
]

ROLE_BY_DEPARTMENT = {
    "Engineering": ["Developer", "Administrator", "Employee", "Manager"],
    "Security": ["Security Analyst", "Administrator", "Manager", "Employee"],
    "IT": ["Support Engineer", "Administrator", "Employee", "Manager"],
    "Finance": ["Employee", "Manager", "Contractor"],
    "HR": ["Employee", "Manager", "Contractor"],
    "Operations": ["Employee", "Support Engineer", "Manager", "Contractor"],
    "Sales": ["Employee", "Manager", "Contractor"],
}

OFFBOARDING_REASONS = [
    "Contract Ended",
    "Voluntary Resignation",
    "Termination",
    "Role Reassignment",
    "Retirement",
    "Inactivity Review",
]


def slugify(value: str) -> str:
    return value.lower().replace(" ", ".").replace("-", ".")


def build_base_people(count: int = 180) -> List[dict]:
    people: List[dict] = []
    rng = random.Random(SEED)
    seen = set()
    for first, last in product(FIRST_NAMES, LAST_NAMES):
        name = f"{first} {last}"
        if name in seen:
            continue
        seen.add(name)
        department = rng.choice(DEPARTMENTS)
        role = rng.choice(ROLE_BY_DEPARTMENT[department])
        people.append(
            {
                "name": name,
                "email": f"{slugify(first)}.{slugify(last)}@company.com",
                "department": department,
                "role": role,
            }
        )
        if len(people) >= count:
            break
    return people


def random_login_time(rng: random.Random) -> str:
    base = datetime(2026, 6, 19, 18, 0, 0)
    delta = timedelta(
        days=rng.randint(0, 120),
        hours=rng.randint(0, 23),
        minutes=rng.randint(0, 59),
        seconds=rng.randint(0, 59),
    )
    return (base - delta).replace(microsecond=0).isoformat()


def random_termination_date(rng: random.Random) -> str:
    base = datetime(2026, 6, 19)
    delta = timedelta(days=rng.randint(1, 240))
    return (base - delta).date().isoformat()


def create_user_records() -> Dict[str, List[dict]]:
    rng = random.Random(SEED)
    base_people = build_base_people()
    core_people = base_people[:30]
    platform_people = {
        platform: base_people[30 + (index * 30) : 30 + (index * 30) + 30]
        for index, platform in enumerate(PLATFORMS)
    }

    records_by_platform: Dict[str, List[dict]] = {}
    user_counter = 1

    for platform in PLATFORMS:
        statuses = STATUS_SEQUENCE[:]
        rng.shuffle(statuses)
        selected_people = core_people + platform_people[platform]
        rng.shuffle(selected_people)

        platform_records: List[dict] = []
        for person, status in zip(selected_people, statuses):
            platform_records.append(
                {
                    "user_id": f"USR{user_counter:03d}",
                    "name": person["name"],
                    "email": person["email"],
                    "department": person["department"],
                    "status": status,
                    "platform": platform,
                    "role": person["role"],
                    "last_login": random_login_time(rng),
                }
            )
            user_counter += 1

        records_by_platform[platform] = platform_records

    return records_by_platform


def create_login_events(user_records: List[dict]) -> List[dict]:
    rng = random.Random(SEED + 1)
    events: List[dict] = []
    for index in range(1, LOGIN_EVENT_COUNT + 1):
        source = rng.choice(user_records)
        events.append(
            {
                "event_id": f"EVT{index:03d}",
                "email": source["email"],
                "platform": source["platform"],
                "timestamp": random_login_time(rng),
                "event_type": "login",
            }
        )
    return events


def create_offboarding_records(base_people: List[dict]) -> List[dict]:
    rng = random.Random(SEED + 2)
    selected_people = rng.sample(base_people, OFFBOARDING_COUNT)
    reasons = OFFBOARDING_REASONS[:]
    records: List[dict] = []
    for index, person in enumerate(selected_people, start=1):
        records.append(
            {
                "record_id": f"OFF{index:03d}",
                "email": person["email"],
                "termination_date": random_termination_date(rng),
                "reason": reasons[(index - 1) % len(reasons)],
            }
        )
    return records


def write_json(path: Path, payload: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    base_people = build_base_people()
    user_records_by_platform = create_user_records()

    write_json(DATA_DIR / "ad_users.json", user_records_by_platform["Active Directory"])
    write_json(DATA_DIR / "azure_users.json", user_records_by_platform["Azure AD"])
    write_json(DATA_DIR / "aws_users.json", user_records_by_platform["AWS IAM"])
    write_json(DATA_DIR / "okta_users.json", user_records_by_platform["Okta"])
    write_json(DATA_DIR / "salesforce_users.json", user_records_by_platform["Salesforce"])

    all_user_records = [record for records in user_records_by_platform.values() for record in records]
    write_json(DATA_DIR / "login_events.json", create_login_events(all_user_records))
    write_json(DATA_DIR / "offboarding_records.json", create_offboarding_records(base_people))

    print(f"Generated synthetic identity data in {DATA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
