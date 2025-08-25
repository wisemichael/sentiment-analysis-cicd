import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine

st.set_page_config(page_title="Monitoring", page_icon="📊", layout="wide")
st.title("📊 Model Monitoring Dashboard")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/preds",
)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

@st.cache_data(ttl=15)
def load_preds(limit=5000):
    q = """
    SELECT id, input_text, predicted_label, probability, latency_ms,
           model_version, feedback, created_at
    FROM predictions
    ORDER BY id DESC
    LIMIT %(lim)s
    """
    with engine.connect() as conn:
        df = pd.read_sql(q, conn, params={"lim": int(limit)})
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["text_len"] = df["input_text"].astype(str).str.len()
    return df

df = load_preds()

if df.empty:
    st.info("No data yet. Use the frontend to send a few predictions.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total predictions", len(df))
c2.metric("Avg latency (ms)", f"{df['latency_ms'].mean():.2f}")
c3.metric("Toxic %", f"{(df['predicted_label'].eq('toxic').mean()*100):.1f}%")
acc = df["feedback"].mean() if df["feedback"].notna().any() else None
c4.metric("Live accuracy", f"{acc*100:.1f}%" if acc is not None else "n/a")

tab1, tab2, tab3, tab4 = st.tabs(["Latency", "Label mix", "Data drift", "Recent rows"])

with tab1:
    srt = df.sort_values("created_at")
    st.line_chart(srt.set_index("created_at")["latency_ms"])
    p50 = df["latency_ms"].quantile(0.5)
    p95 = df["latency_ms"].quantile(0.95)
    st.caption(f"Latency percentiles — p50: {p50:.1f} ms, p95: {p95:.1f} ms")

with tab2:
    st.bar_chart(df["predicted_label"].value_counts())

with tab3:
    srt = df.sort_values("created_at")
    st.line_chart(srt.set_index("created_at")["text_len"])
    # Simple drift proxy: compare earliest N vs latest N
    N = min(500, len(df)//3 if len(df) >= 60 else len(df)//2 or 1)
    early = df.tail(N)["text_len"]
    late = df.head(N)["text_len"]
    colA, colB, colC = st.columns(3)
    colA.metric("Early mean len", f"{early.mean():.1f}")
    colB.metric("Recent mean len", f"{late.mean():.1f}")
    colC.metric("Δ mean", f"{(late.mean()-early.mean()):.1f}")
    st.caption("Data drift proxy: text length (recent vs early).")

with tab4:
    st.dataframe(
        df[["id","created_at","predicted_label","probability","latency_ms","feedback","input_text"]]
          .sort_values("id", ascending=False)
          .reset_index(drop=True),
        use_container_width=True, hide_index=True
    )
