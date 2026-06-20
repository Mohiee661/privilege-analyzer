"""AI security copilot report model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class AIReport:
    person_id: str
    risk_score: int
    risk_level: str
    summary: str
    security_impact: str
    recommended_actions: List[str] = field(default_factory=list)
    confidence_label: str = "likely_true_positive"

    def to_dict(self) -> dict:
        return {
            "person_id": self.person_id,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "summary": self.summary,
            "security_impact": self.security_impact,
            "recommended_actions": list(self.recommended_actions),
            "confidence_label": self.confidence_label,
        }
