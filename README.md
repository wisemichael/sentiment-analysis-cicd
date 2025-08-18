# Assignment 6 — CI/CD & Testing: Sentiment System

A minimal sentiment analysis system with:

- **FastAPI backend** (`api/`) exposing `/predict` and `/health`, and writing JSON logs to `/app/logs/prediction_logs.json`.
- **Streamlit dashboard** (`monitoring/`) calling the API and displaying responses.
- **CI** via GitHub Actions (`.github/workflows/ci.yml`) that runs **flake8** and **pytest** on pull requests to `main`.
- **Docker** images for both services, designed to run together on a single **Ubuntu EC2** instance with a **shared volume**.

---

## Project Architecture

- **Services**
  - **API (FastAPI/Uvicorn)** — listens on **port 8000**.
  - **Monitoring (Streamlit)** — listens on **port 8501**.
- **Shared state**
  - A named Docker volume mounted at **`/app/logs`** in both containers.
  - API appends one JSON object per line to `prediction_logs.json` (under `/app/logs/`).
- **Connectivity**
  - Containers share a Docker network (e.g., `sentiment-net`).
  - Dashboard uses an environment variable **`API_URL`** to reach the API:
    - **Local (no Docker):** `http://localhost:8000`
    - **Docker:** `http://api:8000`

# Project layout:
api/
  main.py
monitoring/
  app.py
tests/
  api/test_api.py
  monitoring/testdashboard.py
.github/workflows/ci.yml
Dockerfile.api
Dockerfile.monitoring
requirements.txt
README.md


---

## Local Development (no Docker)

**Prereqs:** Python 3.11, pip.

```bash```
# Create & activate venv
python -m venv .venv
# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt

# Running API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Running Streamlit dashboard
# Windows PowerShell:
$env:API_URL="http://localhost:8000"
# macOS/Linux:
# export API_URL="http://localhost:8000"

streamlit run monitoring/app.py

# Sanity checks
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"I love this!"}'
flake8 api/ monitoring/ tests/
pytest -q

---

# Docker Development

# Building Images
docker build -t sentiment-api -f Dockerfile.api .
docker build -t sentiment-monitor -f Dockerfile.monitoring .

# Create Shared Volumes and Network
docker volume create app-logs
docker network create sentiment-net

# Running Containers
# API
docker run -d --name api --network sentiment-net \
  -p 8000:8000 \
  -v app-logs:/app/logs \
  sentiment-api

# Monitoring (note API_URL points to the API service name)
docker run -d --name monitoring --network sentiment-net \
  -p 8501:8501 \
  -e API_URL=http://api:8000 \
  -v app-logs:/app/logs \
  sentiment-monitor

# Verification
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"text":"This is great!"}'

docker exec api ls -l /app/logs
docker exec api tail -n 5 /app/logs/prediction_logs.json
docker exec monitoring ls -l /app/logs
