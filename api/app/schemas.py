from pydantic import BaseModel


class PredictRequest(BaseModel):
    text: str

class PredictResponse(BaseModel):
    id: int
    label: str
    probability: float
    model_version: str

class FeedbackRequest(BaseModel):
    id: int
    correct: bool
