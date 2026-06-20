"""Risk profile model for prioritized identity scoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class RiskProfile:
    person_id: str
    name: str
    email: str
    score: int
    risk_level: str
    findings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "name": self.name,
            "email": self.email,
            "score": self.score,
            "risk_level": self.risk_level,
            "findings": list(self.findings),
        }
