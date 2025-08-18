from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import logging
import json
from datetime import datetime

# --- Generates setup for logging sentiments ---
LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "prediction_logs.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

class TextInput(BaseModel):
    text: str

app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

def predict_sentiment(text: str) -> str:
    """Simple sentiment prediction based on keywords."""
    if not text or len(text.strip()) == 0:
        raise ValueError("Text cannot be empty")

    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "perfect"]
    negative_words = ["bad", "terrible", "awful", "hate", "horrible", "worst", "disappointing"]

    text_lower = text.lower()
    positive_score = sum(1 for w in positive_words if w in text_lower)
    negative_score = sum(1 for w in negative_words if w in text_lower)

    if positive_score > negative_score:
        return "positive"
    if negative_score > positive_score:
        return "negative"
    return "neutral"

@app.get("/")
def root():
    return {"message": "Sentiment Analysis API is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/predict")
def predict(input_data: TextInput):
    try:
        logger.info("Received text: %s", input_data.text[:50])
        sentiment = predict_sentiment(input_data.text)
        logger.info("Predicted sentiment: %s", sentiment)

        # Append a log line to the shared volume.
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_text": input_data.text,
            "predicted_sentiment": sentiment,
        }
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as log_err:
            logger.warning("Could not write log file: %s", log_err)

        return {"text": input_data.text, "sentiment": sentiment}
    except ValueError as e:
        logger.error("Validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error") from e

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)