"""API configuration and CORS settings."""

from __future__ import annotations

import os
from typing import List


def _split_origins(raw: str | None) -> List[str]:
    if not raw:
        return [
            "http://localhost",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://*.vercel.app",
        ]
    return [item.strip() for item in raw.split(",") if item.strip()]


API_PREFIX = "/api/v1"
ALLOWED_ORIGINS = _split_origins(os.getenv("ALLOWED_ORIGINS"))
