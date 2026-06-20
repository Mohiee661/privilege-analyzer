"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import CORS_ORIGINS, API_PREFIX
from api.routers.ai_reports import router as ai_reports_router
from api.routers.accuracy import router as accuracy_router
from api.routers.analytics import router as analytics_router
from api.routers.dashboard import router as dashboard_router
from api.routers.findings import router as findings_router
from api.routers.identities import router as identities_router
from api.routers.incidents import router as incidents_router
from api.routers.risks import router as risks_router
from api.routers.search import router as search_router


app = FastAPI(
    title="Identity Risk Intelligence Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(accuracy_router, prefix=API_PREFIX)
app.include_router(identities_router, prefix=API_PREFIX)
app.include_router(findings_router, prefix=API_PREFIX)
app.include_router(incidents_router, prefix=API_PREFIX)
app.include_router(risks_router, prefix=API_PREFIX)
app.include_router(ai_reports_router, prefix=API_PREFIX)
app.include_router(search_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}
