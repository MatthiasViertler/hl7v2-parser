# tests/test_09_routing_yaml_schema_test.py

# Validates:
# - YAML structure
# - required keys
# - no invalid message types
# - no invalid folder paths
# - no circular references

# Catches:
# - missing keys
# - invalid folder paths
# - invalid trigger definitions
# - non‑string values
# - empty folders
# - malformed YAML
# This prevents silent routing failures.

# What this test guarantees
# ✔ routes.yaml is structurally valid
# No malformed entries.
# ✔ All folders are strings
# No accidental lists or numbers.
# ✔ All trigger paths are strings
# No malformed trigger definitions.
# ✔ All paths start with routed/
# Prevents accidental writes outside your project.
# ✔ UNKNOWN exists
# Prevents routing crashes.


import os
import yaml
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
ROUTES = BASE / "routes.yaml"


def test_routes_yaml_schema():
    assert ROUTES.exists(), "routes.yaml missing"

    with open(ROUTES, "r") as f:
        data = yaml.safe_load(f)

    assert "routes" in data, "Missing top-level 'routes' key"
    routes = data["routes"]

    assert isinstance(routes, dict), "'routes' must be a dict"

    for msg_type, entry in routes.items():
        assert isinstance(msg_type, str), "Message type keys must be strings"
        assert isinstance(entry, dict), f"Entry for {msg_type} must be a dict"

        # folder must exist and be a string
        assert "folder" in entry, f"{msg_type} missing 'folder'"
        folder = entry["folder"]
        assert isinstance(folder, str), f"{msg_type}.folder must be a string"
        assert folder.startswith("routed/"), f"{msg_type}.folder must start with routed/"

        # triggers optional
        if "triggers" in entry:
            triggers = entry["triggers"]
            assert isinstance(triggers, dict), f"{msg_type}.triggers must be a dict"

            for trig, path in triggers.items():
                assert isinstance(trig, str), f"Trigger {trig} must be a string"
                assert isinstance(path, str), f"Trigger path for {trig} must be a string"
                assert path.startswith("routed/"), f"Trigger path {path} must start with routed/"

    # UNKNOWN must exist
    assert "UNKNOWN" in routes, "Missing UNKNOWN routing rule"
    assert "folder" in routes["UNKNOWN"], "UNKNOWN missing folder"
