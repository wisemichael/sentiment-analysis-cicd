# api/app/model.py
import time
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from .config import ALLOW_FALLBACK_MODEL, MODEL_VERSION as _VER, TESTING

# Globals
_vec = None
_clf = None

ART_DIR = Path(__file__).parent / "artifacts"
VEC_PATH = ART_DIR / "vectorizer.joblib"
CLF_PATH = ART_DIR / "classifier.joblib"


def _build_fallback():
    """Tiny in-memory model so tests never depend on disk/DB."""
    global _vec, _clf
    _vec = TfidfVectorizer(min_df=1)
    _clf = LogisticRegression(max_iter=200)
    X = _vec.fit_transform(
        [
            "you are nice",
            "i love this",
            "this is great",
            "you are stupid",
            "i hate you",
            "this is awful",
        ]
    )
    y = [0, 0, 0, 1, 1, 1]  # 1 = toxic
    _clf.fit(X, y)


def load_model() -> None:
    """Load artifacts in normal runs; fallback during tests."""
    global _vec, _clf

    if TESTING:
        _build_fallback()
        return

    if VEC_PATH.exists() and CLF_PATH.exists():
        _vec = joblib.load(VEC_PATH)
        _clf = joblib.load(CLF_PATH)
        print(f"Model loaded from {ART_DIR}")
        return

    if not ALLOW_FALLBACK_MODEL:
        raise RuntimeError(
            f"Model artifacts not found in {ART_DIR} and fallback is disabled."
        )

    _build_fallback()
    print("Fallback model built (artifacts not found).")


def predict(text: str):
    """
    Return (pred_idx, probability_of_toxic, latency_ms).

    In TESTING mode, if the model wasn't loaded by a startup hook,
    we lazily build the fallback here so tests never 500.
    """
    global _vec, _clf
    if (_vec is None or _clf is None) and TESTING:
        _build_fallback()

    if _vec is None or _clf is None:
        raise RuntimeError("Model not loaded — call load_model() first.")

    t0 = time.perf_counter()
    X = _vec.transform([text])
    prob = float(_clf.predict_proba(X)[0, 1])  # prob of toxic
    pred_idx = int(prob >= 0.5)
    latency_ms = (time.perf_counter() - t0) * 1000.0
    return pred_idx, prob, latency_ms


# public version (used by API responses)
MODEL_VERSION = _VER
