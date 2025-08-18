# Tests/monitoring/test_dashboard.py
import os
import subprocess
import sys
import time
from pathlib import Path


def test_dashboard_imports_without_crashing():
    # Simple test of streamlit can function without crashing.
    module = __import__("monitoring.app")
    assert module is not None


    # Chunks inputs into small files
    os.makedirs("logs", exist_ok=True)
    with open("logs/prediction_logs.json", "w", encoding="utf-8") as f:
        f.write('{"timestamp":"now","request_text":"hi","predicted_sentiment":"positive","true_sentiment":"positive"}\n')


    env = os.environ.copy()
    # Marks that we’re in CI
    env["CI"] = "true"

    # Starts streamlit on test port.
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(script), "--server.headless", "true", "--server.port", "9999"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    try:
        time.sleep(7)
        # It’s enough that it didn’t crash immediately
        assert proc.poll() is None
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
