FROM python:3.12-slim

WORKDIR /app

# Install deps (use the root requirements.txt)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY api /app/api

# If you have artifacts you want to ship, you can later add:
# COPY ml/artifacts /app/api/app/artifacts

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
