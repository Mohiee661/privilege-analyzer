"""Risk profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import get_runtime_data
from api.schemas.ai_report import AIReportResponse
from api.schemas.finding import FindingResponse
from api.schemas.risk import RiskProfileDetailResponse, RiskProfileResponse


router = APIRouter(prefix="/risks", tags=["risks"])


def _to_risk_profile_response(profile: dict) -> RiskProfileResponse:
    return RiskProfileResponse(
        person_id=str(profile.get("person_id", "")),
        name=str(profile.get("name", "")),
        email=str(profile.get("email", "")),
        score=int(profile.get("score", 0) or 0),
        risk_level=str(profile.get("risk_level", "")),
        findings=[str(item) for item in profile.get("findings", [])],
    )


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


@router.get("", response_model=list[RiskProfileResponse])
def list_risks(level: str | None = Query(default=None)) -> list[RiskProfileResponse]:
    profiles = get_runtime_data()["risk_profiles"]
    if level:
        normalized = level.upper()
        if normalized not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise HTTPException(status_code=400, detail="Invalid risk level")
        profiles = [profile for profile in profiles if str(profile.get("risk_level", "")).upper() == normalized]
    return [_to_risk_profile_response(profile) for profile in profiles]


@router.get("/{person_id}", response_model=RiskProfileDetailResponse)
def get_risk(person_id: str) -> RiskProfileDetailResponse:
    runtime = get_runtime_data()
    profile = next((item for item in runtime["risk_profiles"] if str(item.get("person_id")) == person_id), None)
    if not profile:
        raise HTTPException(status_code=404, detail="Risk profile not found")

    findings = [item for item in runtime["findings"] if str(item.get("person_id")) == person_id]
    ai_report = next((item for item in runtime["ai_reports"] if str(item.get("person_id")) == person_id), None)

    return RiskProfileDetailResponse(
        profile=_to_risk_profile_response(profile),
        findings=[_to_finding_response(item) for item in findings],
        ai_report=AIReportResponse(**ai_report) if isinstance(ai_report, dict) else None,
    )
