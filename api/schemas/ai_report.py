"""AI report API schemas."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel


class AIReportResponse(BaseModel):
    person_id: str
    risk_score: int
    risk_level: str
    summary: str
    security_impact: str
    recommended_actions: List[str]
