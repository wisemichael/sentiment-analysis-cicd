import streamlit as st
import requests

st.title("Sentiment Monitoring Dashboard")

text = st.text_input("Enter text to analyze:")

if st.button("Analyze"):
    if text:
        try:
            response = requests.post(
                "http://localhost:8000/predict",
                json={"text": text},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                st.success(f"Sentiment: {result.get('sentiment', 'unknown')}")
                st.json(result)
            else:
                st.error(f"Error: {response.status_code}")
        except Exception as e:
            st.error(f"Connection error: {e}")
            st.info("Make sure FastAPI is running on port 8000")
    else:
        st.warning("Please enter some text")
