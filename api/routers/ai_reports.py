"""AI report endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.dependencies import get_runtime_data
from api.schemas.ai_report import AIReportResponse


router = APIRouter(prefix="/ai-reports", tags=["ai-reports"])


@router.get("", response_model=list[AIReportResponse])
def list_ai_reports() -> list[AIReportResponse]:
    return [AIReportResponse(**item) for item in get_runtime_data()["ai_reports"] if isinstance(item, dict)]


@router.get("/{person_id}", response_model=AIReportResponse)
def get_ai_report(person_id: str) -> AIReportResponse:
    for item in get_runtime_data()["ai_reports"]:
        if str(item.get("person_id")) == person_id:
            return AIReportResponse(**item)
    raise HTTPException(status_code=404, detail="AI report not found")
