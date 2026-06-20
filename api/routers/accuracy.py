"""Accuracy endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas.accuracy import AccuracyResponse
from scripts.evaluate_accuracy import compute_accuracy_metrics


router = APIRouter(tags=["accuracy"])


@router.get("/accuracy", response_model=AccuracyResponse)
def get_accuracy() -> AccuracyResponse:
    metrics = compute_accuracy_metrics()
    return AccuracyResponse(
        precision=metrics.precision,
        recall=metrics.recall,
        f1=metrics.f1,
        trap_suppression_rate=metrics.trap_suppression_rate,
    )
