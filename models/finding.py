"""Risk finding model for cross-platform identity detection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class Finding:
    finding_id: str
    person_id: str
    name: str
    email: str
    risk_type: str
    severity: str
    description: str
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "finding_id": self.finding_id,
            "person_id": self.person_id,
            "name": self.name,
            "email": self.email,
            "risk_type": self.risk_type,
            "severity": self.severity,
            "description": self.description,
            "evidence": self.evidence,
        }
