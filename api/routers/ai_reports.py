"""AI report endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.dependencies import get_runtime_data
from api.schemas.ai_report import AIReportResponse
from services.ai_explainer import (
    generate_ai_report_for_person,
    generate_reports_for_all_profiles,
    load_ai_reports,
    save_ai_reports,
)


router = APIRouter(prefix="/ai-reports", tags=["ai-reports"])


@router.get("", response_model=list[AIReportResponse])
def list_ai_reports() -> list[AIReportResponse]:
    reports = load_ai_reports()
    if not reports:
        reports = generate_reports_for_all_profiles()
        save_ai_reports(reports)
        get_runtime_data.cache_clear()
    return [AIReportResponse(**item.to_dict()) for item in reports]


@router.get("/{person_id}", response_model=AIReportResponse)
def get_ai_report(person_id: str) -> AIReportResponse:
    existing = next((report for report in load_ai_reports() if report.person_id == person_id), None)
    if existing is not None:
        return AIReportResponse(**existing.to_dict())

    report = generate_ai_report_for_person(person_id)
    if report is None:
        raise HTTPException(status_code=404, detail="AI report not found")
    get_runtime_data.cache_clear()
    return AIReportResponse(**report.to_dict())
