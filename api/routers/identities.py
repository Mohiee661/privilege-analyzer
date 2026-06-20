"""Identity endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import get_runtime_data
from api.schemas.identity import IdentityAccountResponse, IdentityListResponse, IdentityResponse


router = APIRouter(prefix="/identities", tags=["identities"])


def _to_identity_response(identity: dict) -> IdentityResponse:
    accounts = identity.get("accounts", {}) or {}
    typed_accounts = {
        platform: IdentityAccountResponse(
            status=str(data.get("status", "")),
            role=str(data.get("role", "")),
            last_login=data.get("last_login"),
        )
        for platform, data in accounts.items()
        if isinstance(data, dict)
    }
    return IdentityResponse(
        person_id=str(identity.get("person_id", "")),
        name=str(identity.get("name", "")),
        email=str(identity.get("email", "")),
        accounts=typed_accounts,
        platforms=sorted(typed_accounts.keys()),
    )


@router.get("", response_model=IdentityListResponse)
def list_identities(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)) -> IdentityListResponse:
    identities = get_runtime_data()["unified_identities"]
    total = len(identities)
    start = (page - 1) * page_size
    end = start + page_size
    return IdentityListResponse(
        items=[_to_identity_response(item) for item in identities[start:end]],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get("/{person_id}", response_model=IdentityResponse)
def get_identity(person_id: str) -> IdentityResponse:
    for identity in get_runtime_data()["unified_identities"]:
        if str(identity.get("person_id")) == person_id:
            return _to_identity_response(identity)
    raise HTTPException(status_code=404, detail="Identity not found")
