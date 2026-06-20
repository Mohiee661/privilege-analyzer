from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.ai_explainer import (  # noqa: E402
    build_prompt,
    generate_ai_report,
    save_ai_reports,
)


class FakeChoice:
    def __init__(self, content: str):
        self.message = type("Msg", (), {"content": content})()


class FakeResponse:
    def __init__(self, content: str):
        self.choices = [FakeChoice(content)]


class FakeClient:
    def __init__(self, content: str):
        self.content = content
        self.chat = type("Chat", (), {"completions": self})()

    def create(self, **kwargs):
        return FakeResponse(self.content)


def make_identity():
    return {
        "person_id": "PID001",
        "name": "John Smith",
        "email": "john.smith@company.com",
        "score": 92,
        "risk_level": "CRITICAL",
    }


def make_findings():
    return [
        {
            "finding_id": "F001",
            "person_id": "PID001",
            "risk_type": "OFFBOARDING_GAP",
            "severity": "HIGH",
            "description": "disabled in AD but active in AWS",
            "evidence": {"ad": "disabled", "aws": "active"},
        },
        {
            "finding_id": "F002",
            "person_id": "PID001",
            "risk_type": "MULTI_PLATFORM_ADMIN",
            "severity": "HIGH",
            "description": "admin in multiple systems",
            "evidence": {"aws": "Administrator", "azure": "Global Administrator"},
        },
    ]


def test_prompt_generation_contains_findings_score_and_risk_level():
    prompt = build_prompt(make_identity(), make_findings())
    assert "OFFBOARDING_GAP" in prompt
    assert "MULTI_PLATFORM_ADMIN" in prompt
    assert "92" in prompt
    assert "CRITICAL" in prompt


def test_valid_ai_response_parsing(monkeypatch):
    content = json.dumps(
        {
            "summary": "John Smith is risky.",
            "security_impact": "This can lead to unauthorized access.",
            "recommended_actions": ["Disable accounts", "Review privileges"],
        }
    )
    report = generate_ai_report(make_identity(), make_findings(), client=FakeClient(content))
    assert report.summary == "John Smith is risky."
    assert report.security_impact.startswith("This can")
    assert report.recommended_actions == ["Disable accounts", "Review privileges"]


def test_missing_api_key_falls_back_gracefully(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    report = generate_ai_report(make_identity(), make_findings(), client=None)
    assert report.person_id == "PID001"
    assert report.summary
    assert report.recommended_actions


def test_report_export(tmp_path):
    report = generate_ai_report(make_identity(), make_findings(), client=FakeClient(json.dumps({
        "summary": "John Smith is risky.",
        "security_impact": "This can lead to unauthorized access.",
        "recommended_actions": ["Disable accounts", "Review privileges"],
    })))
    output_path = tmp_path / "output" / "ai_reports.json"
    written = save_ai_reports([report], output_path)
    assert written.exists()
    payload = json.loads(written.read_text(encoding="utf-8"))
    assert isinstance(payload, list)
    assert payload[0]["person_id"] == "PID001"
