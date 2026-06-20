"""Dashboard endpoint."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from api.schemas.dashboard import AnalyticsResponse, DashboardResponse
from api.dependencies import get_runtime_data


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
def get_dashboard() -> DashboardResponse:
    data = get_runtime_data()
    risk_profiles = data["risk_profiles"]
    findings = data["findings"]

    counts = Counter(str(profile.get("risk_level", "")).upper() for profile in risk_profiles)
    dashboard = DashboardResponse(
        total_identities=len(data["unified_identities"]),
        critical_risks=counts.get("CRITICAL", 0),
        high_risks=counts.get("HIGH", 0),
        offboarding_gaps=sum(1 for finding in findings if finding.get("risk_type") == "OFFBOARDING_GAP"),
        admin_accounts=sum(1 for finding in findings if finding.get("risk_type") == "MULTI_PLATFORM_ADMIN"),
    )
    return dashboard
