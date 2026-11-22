import json
import subprocess
import sys
from pathlib import Path

SERVER = Path(__file__).parent.parent


def test_committed_openapi_is_current():
    """server/openapi.json is what the app codes against; regenerate with
    `python -m mathsmaster_server openapi > openapi.json` after changing the API."""
    out = subprocess.run([sys.executable, "-m", "mathsmaster_server", "openapi"], capture_output=True, text=True,
                         cwd=SERVER, check=True).stdout
    assert json.loads(out) == json.loads((SERVER / "openapi.json").read_text())


def test_every_route_is_documented_in_api_md():
    spec = json.loads((SERVER / "openapi.json").read_text())
    doc = (SERVER / "API.md").read_text()
    for path, ops in spec["paths"].items():
        for method in ops:
            assert f"{method.upper()} {path}" in doc, f"{method.upper()} {path} missing from API.md"
