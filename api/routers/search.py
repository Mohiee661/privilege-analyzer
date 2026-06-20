"""Search endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from api.dependencies import get_runtime_data
from api.routers.identities import _to_identity_response
from api.schemas.identity import IdentityResponse


router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[IdentityResponse])
def search_identities(q: str = Query(..., min_length=1)) -> list[IdentityResponse]:
    query = q.strip().lower()
    matches = []
    for identity in get_runtime_data()["unified_identities"]:
        person_id = str(identity.get("person_id", "")).lower()
        name = str(identity.get("name", "")).lower()
        email = str(identity.get("email", "")).lower()
        if query in person_id or query in name or query in email:
            matches.append(_to_identity_response(identity))
    return matches
