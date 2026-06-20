"""Finding endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.dependencies import get_runtime_data
from api.schemas.finding import FindingResponse


router = APIRouter(prefix="/findings", tags=["findings"])


def _to_finding_response(finding: dict) -> FindingResponse:
    return FindingResponse(
        finding_id=str(finding.get("finding_id", "")),
        person_id=str(finding.get("person_id", "")),
        name=str(finding.get("name", "")),
        email=str(finding.get("email", "")),
        risk_type=str(finding.get("risk_type", "")),
        severity=str(finding.get("severity", "")),
        description=str(finding.get("description", "")),
        evidence=dict(finding.get("evidence", {})),
    )


@router.get("", response_model=list[FindingResponse])
def list_findings(risk_type: str | None = Query(default=None)) -> list[FindingResponse]:
    findings = get_runtime_data()["findings"]
    if risk_type:
        findings = [finding for finding in findings if finding.get("risk_type") == risk_type]
    return [_to_finding_response(finding) for finding in findings]
