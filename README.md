# Assignment 6: MLOps CI/CD Pipeline

## Overview
This project implements a sentiment analysis system with CI/CD pipeline using GitHub Actions, containerized services, and deployment on AWS EC2.

## Architecture
- **FastAPI Backend**: RESTful API for sentiment analysis
- **Streamlit Dashboard**: Web interface for monitoring and testing
- **GitHub Actions CI/CD**: Automated testing and linting
- **Docker Containers**: Containerized deployment
- **AWS EC2**: Production deployment environment

## Services
1. **API Service** (Port 8000): FastAPI with sentiment prediction endpoint
2. **Monitoring Service** (Port 8501): Streamlit dashboard for testing and monitoring

## Local Development

### Prerequisites
- Python 3.11+
- Docker Desktop
- Git

### Setup
```bash
# Clone repository
git clone <your-repo-url>
cd Assignment-6

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

# Docker Build
docker build -t sentiment-api -f Dockerfile.api .
docker build -t sentiment-monitoring -f Dockerfile.monitoring .

# Docker Run
# Create network and volume
docker network create sentiment-net
docker volume create app-logs

# Run API
docker run -d --name api --network sentiment-net \
  -p 8000:8000 -v app-logs:/logs sentiment-api

# Run Monitoring
docker run -d --name monitoring --network sentiment-net \
  -p 8501:8501 -e API_URL=http://api:8000/predict \
  -v app-logs:/logs sentiment-monitoring

