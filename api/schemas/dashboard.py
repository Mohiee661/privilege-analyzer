"""Dashboard and analytics API schemas."""

from __future__ import annotations

from typing import Dict

from pydantic import BaseModel


class DashboardResponse(BaseModel):
    total_identities: int
    critical_risks: int
    high_risks: int
    offboarding_gaps: int
    admin_accounts: int


class AnalyticsResponse(BaseModel):
    risk_distribution: Dict[str, int]
    platform_distribution: Dict[str, int]
    top_risk_types: Dict[str, int]
