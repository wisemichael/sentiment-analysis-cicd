FROM python:3.12-slim

WORKDIR /app

# Install deps for monitoring; your dedicated list is fine:
COPY monitoring/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY monitoring /app/monitoring

# Compose injects DATABASE_URL; default below is only a fallback
ENV DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/preds"

EXPOSE 8502
CMD ["streamlit", "run", "monitoring/app.py", "--server.port", "8502", "--server.address", "0.0.0.0"]
