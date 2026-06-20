"""Incident endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.dependencies import get_runtime_data
from api.schemas.incident import IncidentResponse
from models.finding import Finding
from services.risk_engine import consolidate_findings


def _to_finding(record: dict) -> Finding:
    return Finding(
        finding_id=str(record.get("finding_id", "")),
        person_id=str(record.get("person_id", "")),
        name=str(record.get("name", "")),
        email=str(record.get("email", "")),
        risk_type=str(record.get("risk_type", "")),
        severity=str(record.get("severity", "")),
        description=str(record.get("description", "")),
        evidence=dict(record.get("evidence", {})),
        remediation_steps=list(record.get("remediation_steps", [])),
    )


router = APIRouter(prefix="/incidents", tags=["incidents"])


def _to_incident_response(incident: dict) -> IncidentResponse:
    return IncidentResponse(
        incident_id=str(incident.get("incident_id", "")),
        person_id=incident.get("person_id"),
        name=incident.get("name"),
        email=incident.get("email"),
        finding_count=incident.get("finding_count"),
        risk_types=incident.get("risk_types", []),
        combined_severity=str(incident.get("combined_severity", "")),
        findings=incident.get("findings", []),
        department=incident.get("department"),
        type=incident.get("type"),
        risk_type=incident.get("risk_type"),
        person_count=incident.get("person_count"),
        description=incident.get("description"),
        person_incidents=incident.get("person_incidents", []),
    )


@router.get("", response_model=list[IncidentResponse])
def list_incidents() -> list[IncidentResponse]:
    runtime = get_runtime_data()
    findings = [_to_finding(record) for record in runtime["findings"]]
    unified_identities = runtime["unified_identities"]
    incidents = consolidate_findings(findings, unified_identities)
    return [_to_incident_response(incident) for incident in incidents]
