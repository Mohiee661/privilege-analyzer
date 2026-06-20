from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from api.dependencies import get_runtime_data  # noqa: E402
from api.main import app  # noqa: E402


client = TestClient(app)


def setup_module(module):
    get_runtime_data.cache_clear()


def test_health_endpoint_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_dashboard_endpoint_returns_200():
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "total_identities" in payload
    assert "critical_risks" in payload


def test_identity_endpoint_returns_valid_record():
    response = client.get("/api/v1/identities/PID001")
    assert response.status_code == 200
    payload = response.json()
    assert payload["person_id"] == "PID001"
    assert "accounts" in payload


def test_invalid_person_id_returns_404():
    response = client.get("/api/v1/identities/DOES_NOT_EXIST")
    assert response.status_code == 404
    assert response.json()["detail"] == "Identity not found"


def test_risk_endpoint_filtering_works():
    response = client.get("/api/v1/risks?level=HIGH")
    assert response.status_code == 200
    payload = response.json()
    assert all(item["risk_level"] == "HIGH" for item in payload)


def test_analytics_endpoint_returns_data():
    response = client.get("/api/v1/analytics")
    assert response.status_code == 200
    payload = response.json()
    assert "risk_distribution" in payload
    assert "platform_distribution" in payload
    assert "top_risk_types" in payload


def test_findings_filtering_and_search():
    findings = client.get("/api/v1/findings?risk_type=OFFBOARDING_GAP")
    assert findings.status_code == 200
    assert all(item["risk_type"] == "OFFBOARDING_GAP" for item in findings.json())

    search = client.get("/api/v1/search?q=john")
    assert search.status_code == 200
    assert len(search.json()) > 0
