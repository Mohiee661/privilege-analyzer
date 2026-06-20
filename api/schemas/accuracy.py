"""Accuracy API schema."""

from __future__ import annotations

from pydantic import BaseModel


class AccuracyResponse(BaseModel):
    precision: float
    recall: float
    f1: float
    trap_suppression_rate: float
