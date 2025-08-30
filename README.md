# Itsakphyo Personal Assistant Bot

[![Live Demo](https://img.shields.io/badge/Demo-itsakphyo__bot-blue)](https://t.me/itsakphyo_bot)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Production%20API-009688?logo=fastapi&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram&logoColor=white)
![Vertex AI](https://img.shields.io/badge/Vertex%20AI-Gemini%201.5-4285F4?logo=googlecloud&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-Enabled-orange)
![Docker](https://img.shields.io/badge/Container-Docker-2496ED?logo=docker&logoColor=white)
![Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-4285F4?logo=googlecloud&logoColor=white)

Lightweight Telegram assistant that answers questions about Aung Khant Phyo using a private Retrieval-Augmented Generation (RAG) pipeline backed by Google Cloud Vertex AI (Gemini) and documents stored in Google Drive.

## Overview

The bot receives Telegram messages (webhook or polling), routes them through a FastAPI backend, retrieves relevant document context from a managed RAG corpus (Google Drive sourced), and composes a concise natural reply—without exposing underlying implementation details to end‑users. A single script (`update_documents.py`) refreshes the knowledge base and can optionally re‑deploy the container to Cloud Run and reset the webhook.

## Key Features

- Contextual answers powered by Vertex AI Gemini (RAG with embedding + retrieval)
- Automated corpus refresh + optional deployment workflow
- Clean separation of services (Telegram, RAG, HTTP layer)
- FastAPI health + webhook endpoints for production readiness
- Structured logging & rotating log files
- Docker + Cloud Run friendly (stateless, configurable via env vars)

## High-Level Architecture

```
Telegram → FastAPI (webhook/polling) → RAG Service (Vertex AI) → Gemini Model → Response
```

Components:
- `app/main.py` FastAPI application & lifecycle (startup initializes bot + webhook)
- `app/services/telegram_service.py` Telegram bot orchestration (commands, message routing)
- `app/services/rag_service.py` Vertex AI RAG setup (corpus creation/reuse, import, retrieval + generation)
- `app/handlers/http_handler.py` Webhook + health endpoints
- `update_documents.py` End‑to‑end refresh (purge + re-import Google Drive files, test sample queries, deploy)
- `config/settings.py` Environment-driven configuration & validation

## Tech Stack

- Python 3.11
- FastAPI + Uvicorn
- python-telegram-bot (async handlers)
- Google Cloud Vertex AI (Gemini 1.5 Flash, embeddings, RAG API)
- Docker / Cloud Run
- Logging: RotatingFileHandler + console

## Environment & Configuration

Primary env variables (see `.env.example`):
- `TOKEN` / `BOT_USERNAME` Telegram authentication
- `GOOGLE_CLOUD_PROJECT_ID`, `GOOGLE_CLOUD_REGION`
- `GOOGLE_DRIVE_FOLDER_ID` Source folder for documents (PDF, DOCX, TXT, MD)
- `SECRET_KEY`, `ENVIRONMENT`, `HOST`, optional logging parameters

If webhook hosting is desired set `WEBHOOK_URL`; otherwise polling starts automatically.

## Operational Flow

1. First start: RAG service checks for existing corpus (named `telegram-bot-rag-corpus`), creates if absent, imports folder contents.
2. User messages trigger classification (greeting / technical / identity / etc.) and style-guided prompt enrichment.
3. Gemini model generates response with retrieval augmentation; fallback logic used if RAG unavailable.
4. `update_documents.py` can purge + re-import corpus, sanity test queries, build & deploy, and set webhook.

## Endpoints (Public)

- `GET /` Basic service info
- `GET /health` Health status (bot + service)
- `POST /webhook` Telegram update intake (path configurable via `WEBHOOK_PATH`, default `/webhook`)

Docs (`/docs`, `/redoc`) available only outside production mode.

## Security & Privacy

- Secrets isolated in `.env` (never committed)
- Service Account + Vertex AI IAM boundary
- No user PII persisted; interactions processed in-memory
- Rotating log file at `logs/app.log` (size + backup limits via env)

## Deployment

Designed for Cloud Run (containerized, stateless, single port). CI build optional via `cloudbuild.yaml` (template in repo). `docker-compose.yml` provided for local container orchestration.

## License

MIT License. See `LICENSE`.

## Contact

Email: itsakphyo@gmail.com

