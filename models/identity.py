"""Unified identity models for cross-platform correlation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class UnifiedIdentity:
    person_id: str
    name: str
    email: str
    accounts: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "name": self.name,
            "email": self.email,
            "accounts": self.accounts,
        }
