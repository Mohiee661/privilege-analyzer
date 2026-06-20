"""Groq client helpers for the AI security copilot."""

from __future__ import annotations

import os
from typing import Iterable, Optional

from dotenv import load_dotenv


def load_groq_client() -> object | None:
    """Return an initialized Groq client or ``None`` when unavailable."""

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None

    try:
        from groq import Groq
    except Exception:
        return None

    return Groq(api_key=api_key)


def call_chat_completion(client: object, prompt: str, models: Iterable[str]) -> str:
    """Call Groq with a model fallback chain and return the assistant content."""

    last_error: Exception | None = None
    for model in models:
        try:
            response = client.chat.completions.create(  # type: ignore[attr-defined]
                model=model,
                messages=[
                    {"role": "system", "content": "You write concise security explanations in JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            content = response.choices[0].message.content
            if content:
                return content
            raise ValueError("Empty model response")
        except Exception as exc:  # pragma: no cover - network/model errors are environment-driven
            last_error = exc
            continue

    if last_error is None:
        raise RuntimeError("Groq request failed")
    raise last_error
