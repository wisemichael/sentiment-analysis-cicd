# api/app/main.py
from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

import joblib
import mlflow
import mlflow.pyfunc
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from fastapi.middleware.cors import CORSMiddleware


APP_DIR = Path(__file__).resolve().parent
ART_DIR = APP_DIR / "artifacts"

# ---------- Environment ----------
DATABASE_URL = os.getenv("DATABASE_URL")  # for prod, this should be RDS
TESTING = os.getenv("TESTING", "0") == "1"

MODEL_VERSION = os.getenv("MODEL_VERSION", "baseline-tfidf-logreg")
ALLOW_FALLBACK_MODEL = os.getenv("ALLOW_FALLBACK_MODEL", "true").lower() == "true"

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")
MLFLOW_MODEL_NAME = os.getenv("MLFLOW_MODEL_NAME", "toxic-comment-model")
MODEL_STAGE = os.getenv("MODEL_STAGE", "Production")

# ---------- DB helpers ----------
engine: Optional[Engine] = None


def get_engine() -> Optional[Engine]:
    """Return a SQLAlchemy engine or None (e.g., in tests)."""
    global engine
    if TESTING:
        return None  # skip DB in tests
    if engine is None and DATABASE_URL:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
    return engine


DDL = """
CREATE TABLE IF NOT EXISTS predictions (
  id BIGSERIAL PRIMARY KEY,
  input_text TEXT NOT NULL,
  predicted_label TEXT NOT NULL,
  probability DOUBLE PRECISION NOT NULL,
  latency_ms DOUBLE PRECISION NOT NULL,
  model_version TEXT NOT NULL,
  feedback BOOLEAN,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions (created_at DESC);
"""


def ensure_schema():
    eng = get_engine()
    if eng is None:
        return
    with eng.begin() as conn:
        conn.exec_driver_sql(DDL)


# ---------- Model wrapper ----------

class ModelWrapper:
    """
    Loads a model from one of:
      1) MLflow Model Registry (if MLFLOW_TRACKING_URI set)
      2) Local artifacts (vectorizer.joblib + classifier.joblib)
      3) TESTING fallback (tiny TF-IDF + LogisticRegression) when TESTING=1
    """
    def __init__(self):
        self.model = None            # Either ("local", vec, clf) or mlflow pyfunc
        self.source = None           # "mlflow:<uri>" or "local-artifacts" or "testing-stub"
        self.model_version = MODEL_VERSION

        # If training wrote MODEL_VERSION.txt, prefer that
        mv_txt = ART_DIR / "MODEL_VERSION.txt"
        if mv_txt.exists():
            try:
                self.model_version = mv_txt.read_text(encoding="utf-8").strip()
            except Exception:
                pass

    # ---- public API ----
    def is_loaded(self) -> bool:
        return self.model is not None

    def ensure_loaded(self):
        """Lazy-load the model if it hasn't been loaded yet."""
        if not self.is_loaded():
            self.load()

    def load(self):
        # 1) Try MLflow Registry (Production by default)
        if MLFLOW_TRACKING_URI:
            try:
                mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
                uri = f"models:/{MLFLOW_MODEL_NAME}/{MODEL_STAGE}"
                self.model = mlflow.pyfunc.load_model(uri)
                self.source = f"mlflow:{uri}"
                return
            except Exception as e:
                print(f"[warn] MLflow load failed: {e}")

        # 2) Fallback to local artifacts (vectorizer+classifier)
        if ALLOW_FALLBACK_MODEL:
            vec = ART_DIR / "vectorizer.joblib"
            clf = ART_DIR / "classifier.joblib"
            if vec.exists() and clf.exists():
                v = joblib.load(vec)
                c = joblib.load(clf)
                self.model = ("local", v, c)  # flag + objects
                self.source = "local-artifacts"
                return

        # 3) TESTING fallback
        if TESTING:
            print("[model] Using TESTING fallback model.")
            self._load_testing_stub()
            self.source = "testing-stub"
            if not self.model_version:
                self.model_version = "testing-stub"
            return

        raise RuntimeError("No model available (MLflow/local/testing all unavailable).")

    def predict_proba(self, text: str) -> float:
        """Return probability of 'toxic' (float in [0,1])."""
        if not self.is_loaded():
            raise RuntimeError("Model not loaded")

        # Local artifacts or testing stub (both use vec+clf)
        if isinstance(self.model, tuple) and self.model[0] == "local":
            _, vec, clf = self.model
            X = vec.transform([str(text)])
            return float(clf.predict_proba(X)[:, 1][0])

        # MLflow pyfunc path: expect DataFrame with column 'prob' or 'label'
        import pandas as pd
        res = self.model.predict(pd.Series([str(text)]))
        if hasattr(res, "columns"):
            if "prob" in res.columns:
                return float(res["prob"].iloc[0])
            if "label" in res.columns:
                return float(res["label"].iloc[0])
        try:
            val = float(res.iloc[0])  # type: ignore[attr-defined]
            return val
        except Exception:
            pass
        raise RuntimeError("Unexpected model output from pyfunc")

    # ---- helpers ----
    def _load_testing_stub(self):
        """Tiny in-memory TF-IDF + LogisticRegression for TESTING=1."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression

        texts = [
            "you are nice", "great work", "awesome job",   # 0
            "you suck", "idiot", "stupid",                 # 1
        ]
        labels = [0, 0, 0, 1, 1, 1]

        vec = TfidfVectorizer(min_df=1, ngram_range=(1, 2))
        X = vec.fit_transform(texts)
        clf = LogisticRegression(max_iter=200).fit(X, labels)

        self.model = ("local", vec, clf)  # reuse local tuple handler


model = ModelWrapper()

# ---------- FastAPI ----------

app = FastAPI(title="Toxic Comment API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev-friendly; for prod, restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictIn(BaseModel):
    text: str


class PredictOut(BaseModel):
    id: Optional[int]
    label: str
    probability: float
    model_version: str


class FeedbackIn(BaseModel):
    id: int
    correct: bool


@app.on_event("startup")
def _startup():
    # Best-effort eager load (tests will also lazy-load)
    try:
        model.load()
    except Exception as e:
        print(f"[startup] model load deferred: {e}")
    # Ensure DB schema
    ensure_schema()


@app.get("/health")
def health():
    # NEW: lazy-load for tests / edge cases
    try:
        model.ensure_loaded()
    except Exception as e:
        print(f"[health] lazy load failed: {e}")

    db_ok = False
    eng = get_engine()
    if eng is not None:
        try:
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False

    return {
        "ok": model.is_loaded(),
        "db": db_ok,
        "model_source": getattr(model, "source", None),
        "model_version": model.model_version,
    }


@app.post("/predict", response_model=PredictOut)
def predict(payload: PredictIn):
    text_in = (payload.text or "").strip()
    if not text_in:
        raise HTTPException(status_code=400, detail="text is required")

    # NEW: lazy-load before first prediction
    model.ensure_loaded()

    t0 = time.perf_counter()
    prob = model.predict_proba(text_in)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    label = "toxic" if prob >= 0.5 else "non-toxic"

    # Write to DB
    new_id: Optional[int] = None
    eng = get_engine()
    if eng is not None:
        try:
            with eng.begin() as conn:
                res = conn.execute(
                    text(
                        """
                        INSERT INTO predictions
                          (input_text, predicted_label, probability, latency_ms, model_version)
                        VALUES
                          (:t, :l, :p, :ms, :mv)
                        RETURNING id
                        """
                    ),
                    {"t": text_in, "l": label, "p": prob, "ms": latency_ms, "mv": model.model_version},
                )
                new_id = res.scalar_one()
        except Exception as e:
            # Don't fail the prediction if DB write fails
            print(f"[warn] DB insert failed: {e}")

    return PredictOut(
        id=new_id,
        label=label,
        probability=prob,
        model_version=model.model_version,
    )


@app.post("/feedback")
def feedback(payload: FeedbackIn):
    if TESTING:
        return {"ok": True, "testing": True}

    eng = get_engine()
    if eng is None:
        raise HTTPException(status_code=503, detail="database not configured")

    try:
        with eng.begin() as conn:
            n = conn.execute(
                text("UPDATE predictions SET feedback=:fb WHERE id=:id"),
                {"fb": bool(payload.correct), "id": int(payload.id)},
            ).rowcount
        if n == 0:
            raise HTTPException(status_code=404, detail="id not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
