# conftest.py (root of the repo)
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Ensure the repo root is on sys.path for imports like "import api"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Also ensure the CWD is the repo root when pytest runs
os.chdir(ROOT)
