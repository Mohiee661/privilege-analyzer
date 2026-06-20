# Identity Risk Intelligence Platform

> File-based identity risk analytics with a FastAPI backend, a React/TanStack frontend, and an optional Groq-powered AI Security Copilot.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-frontend-61DAFB?logo=react&logoColor=black)](https://react.dev/)

---

## Overview

This repository analyzes unified identity data across enterprise platforms, detects risky access patterns, scores identities, and exposes the results through:

- JSON/file-based processing pipelines
- a FastAPI API
- a browser-based frontend
- an optional Groq-backed AI report generator

There is no database layer. The system uses local JSON files in `output/` as its durable workspace.

---

## Documentation

- [Architecture](./docs/ARCHITECTURE.md)
- [Data Dictionary](./docs/DATA_DICTIONARY.md)

---

## Project Structure

```text
project-root/
├── api/                FastAPI app, routers, schemas, config
├── data/               Source datasets for correlation and detection
├── exports/            CSV and PDF exports
├── frontend/           React/TanStack frontend
├── models/             Backend dataclasses
├── output/             Generated JSON artifacts and AI report cache
├── prompts/            Groq prompt templates
├── reports/            Executive report utilities
├── services/           Correlation, risk, scoring, and AI services
├── tests/              Unit and API tests
├── requirements.txt
├── .env.example
├── render.yaml
└── README.md
```

---

## Data Flow

The backend pipeline writes and reads these files:

- `output/unified_identities.json`
- `output/risk_findings.json`
- `output/risk_profiles.json`
- `output/ai_reports.json`
- `output/ai_report_cache.json`

Pipeline stages:

1. `services/correlation_engine.py` merges platform records into unified identities.
2. `services/risk_engine.py` detects risk findings.
3. `services/scoring_engine.py` ranks identities and generates risk profiles.
4. `services/ai_explainer.py` generates AI reports with Groq or a deterministic fallback.
5. `api/main.py` exposes the results over HTTP.

---

## AI Copilot

The AI layer uses Groq when available and falls back safely when it is not.

Environment variable:

```env
GROQ_API_KEY=
```

Preferred model:

```text
llama-3.3-70b-versatile
```

Fallback model:

```text
llama-3.1-8b-instant
```

Behavior:

- generates concise executive-friendly security summaries
- generates security impact statements
- generates remediation recommendations
- caches reports locally
- reuses cached reports when identity score and findings have not changed
- falls back to deterministic local output if Groq is unavailable

---

## Environment

Root example:

```env
GROQ_API_KEY=
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app
```

Frontend example:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Endpoints

Verified endpoints include:

- `GET /health`
- `GET /api/v1/dashboard`
- `GET /api/v1/analytics`
- `GET /api/v1/identities`
- `GET /api/v1/identities/{person_id}`
- `GET /api/v1/risks`
- `GET /api/v1/risks/{person_id}`
- `GET /api/v1/findings`
- `GET /api/v1/search`
- `GET /api/v1/ai-reports`
- `GET /api/v1/ai-reports/{person_id}`

---

## Quickstart

### Backend

```bash
python -m uvicorn api.main:app --reload
```

### Generate local data

```bash
python services/correlation_engine.py
python services/risk_engine.py
python services/scoring_engine.py
python services/ai_explainer.py
```

### Run tests

```bash
python -m pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Validation

Current validation coverage includes:

- data generation
- identity correlation
- risk detection
- risk scoring
- AI report generation
- FastAPI endpoint tests

The project currently passes the Python test suite.

---

## Deployment

### Render backend

Use `render.yaml` in the repo root.

Required environment variables:

- `GROQ_API_KEY`
- `CORS_ORIGINS`

Startup command:

```bash
python services/correlation_engine.py && python services/risk_engine.py && python services/scoring_engine.py && python services/ai_explainer.py && uvicorn api.main:app --host 0.0.0.0 --port $PORT
```

### Vercel frontend

Set:

```env
NEXT_PUBLIC_API_URL=https://<your-render-service>
```

The frontend already consumes backend data through the service layer.

---

## Development Notes

- Keep the file-based architecture intact.
- Do not add a database for AI or reporting.
- Use `output/` as the source of truth for generated artifacts.
- Prefer deterministic fallbacks when external services are unavailable.

---

## License

MIT. See [LICENSE](./LICENSE) and [NOTICE](./NOTICE).
