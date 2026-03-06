from __future__ import annotations

import sys
from pathlib import Path

# Ensure the backend directory is on sys.path so that imports like
# `from app.main import app` work when running pytest from the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

