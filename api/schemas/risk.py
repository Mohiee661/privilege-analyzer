"""Risk profile API schemas."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel

from api.schemas.finding import FindingResponse
from api.schemas.ai_report import AIReportResponse


class RiskProfileResponse(BaseModel):
    person_id: str
    name: str
    email: str
    score: int
    risk_level: str
    findings: List[str]


class RiskProfileDetailResponse(BaseModel):
    profile: RiskProfileResponse
    findings: List[FindingResponse]
    ai_report: Optional[AIReportResponse] = None
