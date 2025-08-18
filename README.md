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


---

## 2) Local Development (no Docker)

**Prereqs:** Python 3.11 and `pip`.

```bash```
# 1) Create & activate a virtual environment
python -m venv .venv

# Windows PowerShell
. .venv/Scripts/Activate.ps1
# macOS/Linux
# source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run the API (http://localhost:8000)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 4) In a NEW terminal, set API_URL for Streamlit
# Windows PowerShell:
$env:API_URL="http://localhost:8000"
# macOS/Linux:
# export API_URL="http://localhost:8000"

# 5) Run the dashboard (http://localhost:8501)
streamlit run monitoring/app.py

# 6) Quick checks
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d '{"text":"I love this!"}'

# 7) Lint & tests
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

---

## EC2 Deployment

Launch EC2
EC2 → Launch instance
AMI: Ubuntu 22.04 LTS
Instance type: t2.micro
Key pair: create or select (.pem)

Security Group inbound rules (during setup you can start open, then lock down later):
22 (SSH) – for now 0.0.0.0/0 (later: “My IP”)
8000 (API) – 0.0.0.0/0 (optional if you’ll use SSH tunnel)
8501 (Streamlit) – 0.0.0.0/0 (optional if you’ll use SSH tunnel)

Launch and note the Public IPv4 DNS/IP. 
34.226.191.36

# SSH/Server Info
cd $HOME\Downloads
# (Optional) restrict key permissions if Windows complains
icacls .\aws-key.pem /inheritance:r
icacls .\aws-key.pem /grant:r "$($env:USERNAME):(R)"

ssh -i .\aws-key.pem ubuntu@34.226.191.36

# Install Docker
On the EC2 box
sudo apt-get update -y
sudo apt-get install -y docker.io git
sudo systemctl enable --now docker
sudo usermod -aG docker ubuntu
sudo systemctl enable --now docker
newgrp docker   # or reconnect SSH after 'usermod -aG docker ubuntu'
# Reconnect SSH so your user has docker perms, or run 'newgrp docker'

# Cloning
cd ~
git clone https://github.com/wisemichael/sentiment-analysis-cicd.git
cd sentiment-analysis-cicd
git branch -a   # confirm branches

# Build Images on EC2
docker build -t sentiment-api -f Dockerfile.api .
docker build -t sentiment-monitor -f Dockerfile.monitoring .

# Shared volume + network
docker volume create app-logs
docker network create sentiment-net

# API
docker run -d --name api --network sentiment-net \
  -p 8000:8000 \
  -v app-logs:/app/logs \
  sentiment-api

# Monitoring (points to 'api' by service name)
docker run -d --name monitoring --network sentiment-net \
  -p 8501:8501 \
  -e API_URL=http://api:8000 \
  -v app-logs:/app/logs \
  sentiment-monitor

# Verify from EC2
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text":"This is great!"}'

# See that both containers share the logs volume
docker exec api        ls -l /app/logs
docker exec api        tail -n 5 /app/logs/prediction_logs.json
docker exec monitoring ls -l /app/logs

# Public IPs
[http://localhost:8000/docs](http://34.226.191.36:8000/docs)
[http://localhost:8000/health](http://34.226.191.36:8000/health)
[http://localhost:8501](http://34.226.191.36:8501)

