import os
import requests
import streamlit as st

# Use base URL; the code will append /predict and /health
API_URL = os.getenv("API_URL", "http://localhost:8000")

def main():
    st.title("Sentiment Analysis Monitoring Dashboard")
    st.markdown("---")

    text = st.text_area("Enter text to analyze:", height=100)

    if st.button("Analyze Sentiment", type="primary"):
        if text:
            try:
                response = requests.post(f"{API_URL}/predict", json={"text": text}, timeout=5)
                if response.status_code == 200:
                    result = response.json()
                    sentiment = result.get("sentiment", "unknown")
                    if sentiment == "positive":
                        st.success(f"✅ Sentiment: **{sentiment.upper()}**")
                    elif sentiment == "negative":
                        st.error(f"❌ Sentiment: **{sentiment.upper()}**")
                    else:
                        st.info(f"⚪ Sentiment: **{sentiment.upper()}**")
                    with st.expander("View full response"):
                        st.json(result)
                else:
                    st.error(f"API Error: {response.status_code}")
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {e}")
                st.warning(f"Make sure the API is running at {API_URL}")
        else:
            st.warning("Please enter some text to analyze")

    with st.sidebar:
        st.header("API Status")
        if st.button("Check Health"):
            try:
                r = requests.get(f"{API_URL}/health", timeout=5)
                st.success("🟢 API is healthy" if r.status_code == 200 else "🔴 API unhealthy")
            except Exception:
                st.error("🔴 API not reachable")

if __name__ == "__main__":
    main()
