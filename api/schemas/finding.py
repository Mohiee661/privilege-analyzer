"""Finding API schemas."""

from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class FindingResponse(BaseModel):
    finding_id: str
    person_id: str
    name: str
    email: str
    risk_type: str
    severity: str
    description: str
    evidence: Dict[str, Any]
