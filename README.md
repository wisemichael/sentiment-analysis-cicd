# Assignment 6: CI/CD & Testing – Sentiment System

This project deploys a sentiment analysis system consisting of:
- **FastAPI backend** (in `api/`) with `/predict` and `/health`
- **Streamlit monitoring dashboard** (in `monitoring/`)
- **CI/CD** pipeline (GitHub Actions) that lints with **flake8** and tests with **pytest**
- **Docker** images for both services
- **Manual AWS EC2** deployment guide

---

## Project Architecture

- **Compute**: Single Ubuntu EC2 instance
- **Containers**:
  - `api` → FastAPI served by Uvicorn on port **8000**
  - `monitoring` → Streamlit dashboard on port **8501**
- **Networking**:
  - Both containers can share a Docker network
  - Dashboard uses `API_URL` env var to call the API (defaults to `http://api:8000/predict` in Docker)
- **CI/CD**:
  - PRs to `main` trigger GitHub Actions (`.github/workflows/ci.yml`)
  - Steps: checkout → set up Python → `pip install` → `flake8` → `pytest`

---

## Local Development (Docker)

> The rubric asks for Docker instructions for local running.

### Prereqs
- Docker Desktop
- Git

### Clone
```bash
git clone < https://github.com/wisemichael/sentiment-analysis-cicd >
cd < sentiment-analysis-cicd >


# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Running

# Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Start Dashboard (new terminal)
streamlit run monitoring/app.py

# Testing

# Run custom tests
python run_tests.py

# Run linting
flake8 api/ monitoring/

# Docker

# Docker build images
docker build -t sentiment-api -f Dockerfile.api .
docker build -t sentiment-monitoring -f Dockerfile.monitoring .


# Docker Run
# Create network and volume
docker network create sentiment-net
docker volume create app-logs

# Run API
docker run -d --name api --network sentiment-net \
  -p 8000:8000 -v app-logs:/logs sentiment-api

# Monitoring API
docker run -d --name monitoring --network sentiment-net \
  -p 8501:8501 -e API_URL=http://api:8000/predict \
  -v app-logs:/logs sentiment-monitoring

# Access
API docs: http://localhost:8000
Dashboard: http://localhost:8501