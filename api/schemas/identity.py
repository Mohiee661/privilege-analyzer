"""Identity API schemas."""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel


class IdentityAccountResponse(BaseModel):
    status: str
    role: str
    last_login: str | None = None


class IdentityResponse(BaseModel):
    person_id: str
    name: str
    email: str
    accounts: Dict[str, IdentityAccountResponse]
    platforms: List[str]


class IdentityListResponse(BaseModel):
    items: List[IdentityResponse]
    page: int
    page_size: int
    total: int
