from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import services.ai_explainer as ai_explainer_module  # noqa: E402
from services.ai_explainer import (  # noqa: E402
    build_prompt,
    generate_ai_report_for_person,
    generate_ai_report,
    load_ai_reports,
    save_ai_reports,
    upsert_ai_report,
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


class CountingFakeClient(FakeClient):
    def __init__(self, content: str):
        super().__init__(content)
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return super().create(**kwargs)


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


def test_cache_reuses_matching_report(tmp_path, monkeypatch):
    cache = {}
    client = CountingFakeClient(
        json.dumps(
            {
                "summary": "John Smith is risky.",
                "security_impact": "This can lead to unauthorized access.",
                "recommended_actions": ["Disable accounts", "Review privileges"],
            }
        )
    )
    report = generate_ai_report(make_identity(), make_findings(), client=client, cache=cache)
    assert client.calls == 1

    cached_report = generate_ai_report(make_identity(), make_findings(), client=client, cache=cache)
    assert client.calls == 1
    assert cached_report.summary == report.summary


def test_generate_report_for_person_updates_ai_reports_file(tmp_path, monkeypatch):
    output_dir = tmp_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ai_explainer_module, "RISK_PROFILES_FILE", output_dir / "risk_profiles.json")
    monkeypatch.setattr(ai_explainer_module, "RISK_FINDINGS_FILE", output_dir / "risk_findings.json")
    monkeypatch.setattr(ai_explainer_module, "AI_REPORTS_FILE", output_dir / "ai_reports.json")
    monkeypatch.setattr(ai_explainer_module, "CACHE_FILE", output_dir / "ai_report_cache.json")
    (output_dir / "risk_profiles.json").write_text(
        json.dumps(
            [
                {
                    "person_id": "PID001",
                    "name": "John Smith",
                    "email": "john.smith@company.com",
                    "score": 92,
                    "risk_level": "CRITICAL",
                    "findings": ["OFFBOARDING_GAP"],
                }
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "risk_findings.json").write_text(
        json.dumps(
            [
                {
                    "finding_id": "F001",
                    "person_id": "PID001",
                    "risk_type": "OFFBOARDING_GAP",
                    "severity": "HIGH",
                    "description": "disabled in AD but active in AWS",
                    "evidence": {"ad": "disabled", "aws": "active"},
                }
            ]
        ),
        encoding="utf-8",
    )

    report = generate_ai_report_for_person("PID001", client=FakeClient(json.dumps({
        "summary": "John Smith is risky.",
        "security_impact": "This can lead to unauthorized access.",
        "recommended_actions": ["Disable accounts", "Review privileges"],
    })))
    assert report is not None
    assert report.person_id == "PID001"

    saved_reports = load_ai_reports(output_dir / "ai_reports.json")
    assert any(item.person_id == "PID001" for item in saved_reports)


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


def test_upsert_replaces_existing_report(tmp_path):
    output_path = tmp_path / "output" / "ai_reports.json"
    original = generate_ai_report(make_identity(), make_findings(), client=FakeClient(json.dumps({
        "summary": "John Smith is risky.",
        "security_impact": "This can lead to unauthorized access.",
        "recommended_actions": ["Disable accounts", "Review privileges"],
    })))
    updated = generate_ai_report(
        {**make_identity(), "score": 95},
        make_findings(),
        client=FakeClient(json.dumps({
            "summary": "John Smith remains risky.",
            "security_impact": "This can lead to unauthorized access.",
            "recommended_actions": ["Disable accounts", "Review privileges"],
        })),
    )

    save_ai_reports([original], output_path)
    upsert_ai_report(updated, output_path)
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert len(payload) == 1
    assert payload[0]["summary"] == "John Smith remains risky."
