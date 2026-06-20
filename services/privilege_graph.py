"""Privilege graph utilities built from nested group memberships."""

from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, MutableSet, Sequence

from services.data_loader import GroupMembership, load_group_memberships


def _normalize_email(email: str) -> str:
    return email.lower().strip()


def _build_indexes(
    memberships: Sequence[GroupMembership],
) -> tuple[Dict[str, GroupMembership], Dict[str, List[str]]]:
    groups_by_id: Dict[str, GroupMembership] = {}
    memberships_by_email: Dict[str, List[str]] = {}

    for membership in memberships:
        groups_by_id[membership.group_id] = membership
        for email in membership.direct_members:
            normalized = _normalize_email(email)
            if not normalized:
                continue
            memberships_by_email.setdefault(normalized, []).append(membership.group_id)

    return groups_by_id, memberships_by_email


def _append_unique(roles: List[str], role: str, seen_roles: MutableSet[str]) -> None:
    normalized = role.strip()
    if not normalized or normalized in seen_roles:
        return
    roles.append(normalized)
    seen_roles.add(normalized)


def _walk_group_lineage(
    group_id: str,
    groups_by_id: Mapping[str, GroupMembership],
    roles: List[str],
    seen_roles: MutableSet[str],
    visited_groups: MutableSet[str],
) -> None:
    if group_id in visited_groups:
        return
    visited_groups.add(group_id)

    group = groups_by_id.get(group_id)
    if group is None:
        return

    _append_unique(roles, group.grants_role, seen_roles)

    if group.parent_group_id:
        _walk_group_lineage(group.parent_group_id, groups_by_id, roles, seen_roles, visited_groups)


def effective_privilege(email: str) -> List[str]:
    memberships = load_group_memberships()
    groups_by_id, memberships_by_email = _build_indexes(memberships)
    direct_group_ids = memberships_by_email.get(_normalize_email(email), [])

    roles: List[str] = []
    seen_roles: set[str] = set()
    visited_groups: set[str] = set()

    for group_id in direct_group_ids:
        _walk_group_lineage(group_id, groups_by_id, roles, seen_roles, visited_groups)

    return roles
