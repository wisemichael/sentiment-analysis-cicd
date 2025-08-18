# tests/monitoring/test_dashboard.py
import os
import subprocess
import sys
import time
from pathlib import Path


def test_dashboard_imports_without_crashing():
    # Simple test that streamlit can function without crashing.
    module = __import__("monitoring.app")
    assert module is not None


    # create tiny inputs so dashboard won't choke on missing files.
    os.makedirs("logs", exist_ok=True)
    with open("logs/prediction_logs.json", "w", encoding="utf-8") as f:
        f.write('{"timestamp":"now","request_text":"hi","predicted_sentiment":"positive","true_sentiment":"positive"}\n')

    # if your dashboard loads IMDB_Dataset.csv, ensure it exists in repo.
    # If it’s big, it’s fine—Streamlit starts before it renders everything.

    env = os.environ.copy()
    # Mark that we’re in CI; you can optionally check this in your app to do lighter work
    env["CI"] = "true"

    # start streamlit headless on a throwaway port
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(script), "--server.headless", "true", "--server.port", "9999"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    try:
        # give it a moment to boot
        time.sleep(7)
        # It’s enough that it didn’t crash immediately
        assert proc.poll() is None
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
