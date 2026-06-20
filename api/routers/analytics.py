"""Analytics endpoint."""

from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from api.dependencies import get_runtime_data
from api.schemas.dashboard import AnalyticsResponse


router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics() -> AnalyticsResponse:
    data = get_runtime_data()
    risk_profiles = data["risk_profiles"]
    unified_identities = data["unified_identities"]
    findings = data["findings"]

    risk_distribution = Counter(str(profile.get("risk_level", "")).lower() for profile in risk_profiles)
    platform_distribution: dict[str, int] = Counter()
    for identity in unified_identities:
        accounts = identity.get("accounts", {}) or {}
        for platform in accounts:
            platform_distribution[platform] += 1
    top_risk_types = Counter(str(finding.get("risk_type", "")) for finding in findings)

    return AnalyticsResponse(
        risk_distribution={
            "critical": risk_distribution.get("critical", 0),
            "high": risk_distribution.get("high", 0),
            "medium": risk_distribution.get("medium", 0),
            "low": risk_distribution.get("low", 0),
            "none": risk_distribution.get("none", 0),
        },
        platform_distribution=dict(platform_distribution),
        top_risk_types=dict(top_risk_types),
    )
