from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import services.privilege_graph as privilege_graph  # noqa: E402
from services.data_loader import GroupMembership  # noqa: E402


def test_effective_privilege_walks_ancestors(monkeypatch):
    memberships = [
        GroupMembership(
            group_id="GRP001",
            platform="Azure AD",
            group_name="root-admins",
            grants_role="Global Administrator",
            parent_group_id=None,
            direct_members=[],
        ),
        GroupMembership(
            group_id="GRP002",
            platform="Azure AD",
            group_name="delegated-admins",
            grants_role="Support Engineer",
            parent_group_id="GRP001",
            direct_members=["alice@company.com"],
        ),
        GroupMembership(
            group_id="GRP003",
            platform="Azure AD",
            group_name="users",
            grants_role="Employee",
            parent_group_id=None,
            direct_members=["alice@company.com"],
        ),
    ]
    monkeypatch.setattr(privilege_graph, "load_group_memberships", lambda: memberships)

    roles = privilege_graph.effective_privilege("alice@company.com")

    assert roles == ["Support Engineer", "Global Administrator", "Employee"]


def test_effective_privilege_returns_empty_list_for_unknown_email(monkeypatch):
    monkeypatch.setattr(privilege_graph, "load_group_memberships", lambda: [])

    roles = privilege_graph.effective_privilege("missing@company.com")

    assert roles == []
