from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TextInput(BaseModel):
    text: str

app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

def predict_sentiment(text: str) -> str:
    """Simple sentiment prediction based on keywords."""
    if not text or len(text.strip()) == 0:
        raise ValueError("Text cannot be empty")
    
    # Simple keyword-based sentiment
    positive_words = ["good", "great", "excellent", "amazing", "wonderful", "fantastic", "love", "perfect"]
    negative_words = ["bad", "terrible", "awful", "hate", "horrible", "worst", "disappointing"]
    
    text_lower = text.lower()
    
    positive_score = sum(1 for word in positive_words if word in text_lower)
    negative_score = sum(1 for word in negative_words if word in text_lower)
    
    if positive_score > negative_score:
        return "positive"
    elif negative_score > positive_score:
        return "negative"
    else:
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
        logger.info(f"Received prediction request for text: {input_data.text[:50]}...")
        sentiment = predict_sentiment(input_data.text)
        logger.info(f"Predicted sentiment: {sentiment}")
        return {"text": input_data.text, "sentiment": sentiment}
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=True)
