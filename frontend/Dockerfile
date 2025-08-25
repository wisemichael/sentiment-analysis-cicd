FROM python:3.12-slim

WORKDIR /app

# Install deps (reuse root requirements to keep simple)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend /app/frontend

# Compose injects API_URL env; default for local manual runs
ENV API_URL="http://localhost:8000"

EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
