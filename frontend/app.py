# frontend/app.py
import os
import time
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="Toxic Comment Classifier", page_icon="🧪", layout="centered")
st.title("🧪 Toxic Comment Classifier")

# Keep last prediction id/label in session so feedback can use it
if "last_pred_id" not in st.session_state:
    st.session_state.last_pred_id = None
if "last_label" not in st.session_state:
    st.session_state.last_label = None

txt = st.text_area("Enter a comment:", height=140, placeholder="Type something…")

col1, _ = st.columns([1, 3])
with col1:
    if st.button("Predict", use_container_width=True):
        if not txt.strip():
            st.warning("Please enter some text.")
        else:
            try:
                t0 = time.perf_counter()
                r = requests.post(f"{API_URL}/predict", json={"text": txt}, timeout=10)
                r.raise_for_status()
                data = r.json()
                st.session_state.last_pred_id = data.get("id")
                st.session_state.last_label = data.get("label")
                st.success(f"Prediction: **{data['label']}** (p={data['probability']:.3f})")
                st.caption(f"Model: {data['model_version']} • API latency ~ {(time.perf_counter()-t0)*1000:.1f} ms")
            except Exception as e:
                st.error(f"Prediction failed: {e}")

st.divider()
st.subheader("Was this correct?")

c1, c2 = st.columns(2)

def send_feedback(correct: bool):
    pid = st.session_state.last_pred_id
    if pid is None:
        st.info("Make a prediction first.")
        return
    try:
        r = requests.post(f"{API_URL}/feedback", json={"id": pid, "correct": bool(correct)}, timeout=10)
        r.raise_for_status()
        st.success("Thanks! Feedback recorded.")
    except Exception as e:
        st.error(f"Could not send feedback: {e}")

with c1:
    st.button("👍 Yes", use_container_width=True, on_click=send_feedback, args=(True,))
with c2:
    st.button("👎 No", use_container_width=True, on_click=send_feedback, args=(False,))
