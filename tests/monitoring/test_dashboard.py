# tests/monitoring/test_dashboard.py
import os
import sys
import time
import subprocess
from pathlib import Path


def test_streamlit_can_start():
    """
    Boot the Streamlit app headless for a few seconds and make sure it doesn't crash.
    We don't need full UI assertions for CI, just that the process starts cleanly.
    """
    # Make sure the dashboard script exists
    script = Path("monitoring/app.py")
    assert script.exists()

    # Create a tiny log so the app doesn't slow with missing files
    os.makedirs("logs", exist_ok=True)
    with open("logs/prediction_logs.json", "w", encoding="utf-8") as f:
        f.write('{"timestamp":"now","request_text":"hi","predicted_sentiment":"positive"}\n')

    # Mark that we're in CI
    env = os.environ.copy()
    env["CI"] = "true"

    # Start streamlit headless on a throwaway port
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            str(script),
            "--server.headless",
            "true",
            "--server.port",
            "9999",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    try:
        # Give it a moment to boot
        time.sleep(7)
        # Assert the process hasn't died immediately
        assert proc.poll() is None
    finally:
        # Clean up the subprocess so the test doesn't hang
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
