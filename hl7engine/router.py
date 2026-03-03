import os
import yaml

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

class Router:
    def __init__(self, config_file="routes.yaml"):        
        full_path = CONFIG_DIR / config_file
        print("LOADING VALIDATOR FROM:", full_path)

        with open(full_path, "r") as f:
            config = yaml.safe_load(f)

        self.routes = config.get("routes", {})

    def _ensure_folder(self, path: str):
        """Create folder if it does not exist (Option A)."""
        if path and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def route(self, msg_type: str, raw_hl7: str):
        """
        Route based on:
        - message type (MSH-9.1)
        - trigger event (MSH-9.2)

        Returns:
            (parent_folder, routed_path)

        Behavior:
        - If message type exists and trigger exists → (parent, trigger_path)
        - If message type exists but trigger missing → (parent, parent)
        - If message type unknown → (UNKNOWN, UNKNOWN)
        - Auto-creates folders (Option A)
        """

        msg_type = (msg_type or "").upper()

        # Extract trigger event from raw HL7
        trigger = None
        try:
            first_line = raw_hl7.split("\r")[0]
            fields = first_line.split("|")
            if len(fields) > 8:
                msg9 = fields[8].split("^")
                if len(msg9) > 1:
                    trigger = msg9[1].upper()
        except Exception:
            trigger = None

        # 1) Message type exists in routes.yaml
        if msg_type in self.routes:
            entry = self.routes[msg_type]

            parent_folder = entry.get("folder")
            triggers = entry.get("triggers", {})

            # Ensure parent folder exists
            self._ensure_folder(parent_folder)

            # 1a) Trigger exists
            if trigger in triggers:
                routed_path = triggers[trigger]
                self._ensure_folder(routed_path)
                return parent_folder, routed_path

            # 1b) Trigger missing → fallback to parent folder
            return parent_folder, parent_folder

        # 2) Unknown message type → route to UNKNOWN
        unknown = self.routes.get("UNKNOWN", {})
        parent_folder = unknown.get("folder", "routed/UNKNOWN")

        self._ensure_folder(parent_folder)

        return parent_folder, parent_folder