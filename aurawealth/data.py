"""Loading helpers for the single-client demo data set."""

import json
from pathlib import Path
from typing import Any


DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "mock_client.json"


def load_client_data() -> dict[str, Any]:
    return json.loads(DATA_PATH.read_text())
