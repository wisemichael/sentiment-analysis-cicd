## Toxic Comment Classifier

## What it does
Binary toxicity classifier (**TF-IDF + Logistic Regression**) served via **FastAPI**, with a **Streamlit** demo UI and a **Streamlit** monitoring dashboard.  
Predictions and user feedback are stored in **Postgres**.

## Architecture

[User] ---> [Frontend (Streamlit demo)] ---> [API (FastAPI)] ---> [Postgres DB]|v[Monitoring (Streamlit dashboard)]
---

## Project layout
ml/ # training & artifacts
api/ # FastAPI app
frontend/ # Streamlit demo
monitoring/ # Streamlit monitoring dashboard
infra/ # docker-compose.dev.yaml

## Contents

- [Architecture](#architecture)
- [Project Layout](#project-layout)
- [Prerequisites](#prerequisites)
- [Run with Docker (recommended)](#run-with-docker-recommended)
  - [Start, Stop, Rebuild](#start-stop-rebuild)
  - [Service URLs](#service-urls)
  - [Quick Smoke Tests](#quick-smoke-tests)
  - [Logs, Status, and Shell Access](#logs-status-and-shell-access)
  - [Database: persistence & inspection](#database-persistence--inspection)
- [Environment Variables](#environment-variables)
- [Endpoints](#endpoints)
- [Training (optional)](#training-optional)
- [Testing (optional)](#testing-optional)
- [Troubleshooting](#troubleshooting)
- [Cleanup](#cleanup)
- [Instructor Notes](#instructor-notes)

---

## Prereqs
- Docker Desktop
- Python 3.12 for local runs

## Run with Docker

Start everything (API + frontend + monitoring + Postgres):

```bash

# Start the app
docker compose -f infra/docker-compose.dev.yaml up --build


# Rebuild only one service
docker compose -f infra/docker-compose.dev.yaml up -d --build toxic-api
docker compose -f infra/docker-compose.dev.yaml up -d --build toxic-frontend
docker compose -f infra/docker-compose.dev.yaml up -d --build toxic-monitoring

## Services

Service URLs

API (FastAPI): http://localhost:8000
Swagger docs: http://localhost:8000/docs
Frontend (Streamlit demo): http://localhost:8501
Monitoring (Streamlit dashboard): http://localhost:8502
Postgres: localhost:5432 (inside compose: service name `postgres`)
DB user: postgres
DB password: postgres
DB name: preds
Table: predictions


## Monitoring/Health
curl http://localhost:8000/health
# -> {"ok":true,"model_version":"baseline-tfidf-logreg"}

Experiment Tracking & Monitoring (Weights & Biases)
This project also logs model metrics and monitoring data to Weights & Biases (W&B)

toxicity rate over time
number of predictions
average latency (ms)
live accuracy

# Access
Project dashboard (W&B): W&B Toxic Comment Moderation

If you are not a member of the project team, please request access.

## Prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"You are awesome!"}'
 
## Running in Powershell
curl.exe http://localhost:8000/health
curl.exe -X POST http://localhost:8000/predict `
  -H "Content-Type: application/json" `
  -d "{""text"":""You are awesome!""}"

# Service status
docker compose -f infra/docker-compose.dev.yaml ps

# Logs
docker compose -f infra/docker-compose.dev.yaml logs -f toxic-api
docker compose -f infra/docker-compose.dev.yaml logs -f toxic-frontend
docker compose -f infra/docker-compose.dev.yaml logs -f toxic-monitoring
docker compose -f infra/docker-compose.dev.yaml logs -f toxic-db

# Shell into API container
docker compose -f infra/docker-compose.dev.yaml exec toxic-api bash

# === API/Model ===
MODEL_VERSION=baseline-tfidf-logreg
ALLOW_FALLBACK_MODEL=true

# === MLflow (optional) ===
# MLFLOW_TRACKING_URI=
# MLFLOW_MODEL_NAME=toxic-comment-model
# MODEL_STAGE=Production

# === Database ===
DATABASE_URL=postgresql+psycopg2://postgres:postgres@postgres:5432/preds

# === Frontend ===
API_URL=http://api:8000

## Training
python -m ml.train --data ml\data\train.csv

## Testing
# Windows PowerShell
$env:PYTHONPATH="."
$env:TESTING="1"
PYTHONPATH=. TESTING=1 pytest -q

## Endpoints
GET /health → { ok: true, model_version }
POST /predict → { id, label, probability, model_version }
POST /feedback → { ok: true } (updates predictions.feedback)

## Troubleshooting
- If the API container logs show `Model not loaded`, ensure artifacts exist in `api/app/artifacts/` (vectorizer + classifier).
- If the monitoring dashboard cannot connect to Postgres, check that `DATABASE_URL` in `.env` matches the service name `postgres`.
- Windows users: prefer `curl.exe` instead of `curl` when testing endpoints in PowerShell.


## Cleanup
Remove:
__pycache__/, .pytest_cache/, .ruff_cache/ (caches)
The root Docker-compose.all.yaml (we use infra/docker-compose.dev.yaml)
Any unused “hello.py” samples if present

## Links

- **GitHub repository:** https://github.com/wisemichael/sentiment-analysis-cicd
- **Streamlit demo (local):** http://localhost:8501
- **Monitoring dashboard (local):** http://localhost:8502
- **Experiment tracking (W&B):** https://wandb.ai/wise-michael-t-university-of-denver/toxic-comment-moderation

