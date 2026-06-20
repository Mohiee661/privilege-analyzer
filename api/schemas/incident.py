"""Incident API schemas."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class IncidentResponse(BaseModel):
    incident_id: str
    person_id: str | None = None
    name: str | None = None
    email: str | None = None
    finding_count: int | None = None
    risk_types: List[str] = []
    combined_severity: str
    findings: List[Dict[str, Any]] = []
    department: str | None = None
    type: str | None = None  # "person" or "department"
    risk_type: str | None = None  # For department incidents
    person_count: int | None = None  # For department incidents
    description: str | None = None  # For department incidents
    person_incidents: List[str] = []  # For department incidents
