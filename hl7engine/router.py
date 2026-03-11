# hl7engine/router.py

# 2026 Mar 11: Refactored metrics (router_queue_depth handled in mllp_server -> no duplicate here), no high-cardinality labels,
#              clean-up trigger extraction, safe folder creation, added docstrings / type hints, deterministic router logic.

# hl7engine/router.py

import os
import yaml
from pathlib import Path

from hl7engine.metrics.metrics import metrics

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


class Router:
    """
    HL7 message router.

    Routes messages based on:
    - message type (MSH-9.1)
    - trigger event (MSH-9.2)

    Metrics emitted:
    - router_messages_routed_total{route="<msg_type>"}
    - router_routing_errors_total{route="UNKNOWN"}
    """

    def __init__(self, config_file="routes.yaml"):
        full_path = CONFIG_DIR / config_file

        with open(full_path, "r") as f:
            config = yaml.safe_load(f)

        self.routes = config.get("routes", {})

    # ------------------------------------------------------------
    # INTERNAL HELPERS
    # ------------------------------------------------------------

    def _ensure_folder(self, path: str):
        """Create folder if it does not exist."""
        if path and not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

    def _extract_trigger(self, raw_hl7: str) -> str | None:
        """
        Extract trigger event from MSH-9.2.
        """
        try:
            first_line = raw_hl7.split("\r")[0]
            fields = first_line.split("|")
            if len(fields) > 8:
                msg9 = fields[8].split("^")
                if len(msg9) > 1:
                    return msg9[1].upper()
        except Exception:
            pass
        return None

    # ------------------------------------------------------------
    # ROUTING
    # ------------------------------------------------------------

    def route(self, msg_type: str, raw_hl7: str):
        """
        Route based on message type and trigger event.

        Returns:
            (parent_folder, routed_path)
        """

        msg_type = (msg_type or "").upper()
        trigger = self._extract_trigger(raw_hl7)

        # 1) Known message type
        if msg_type in self.routes:
            entry = self.routes[msg_type]

            parent_folder = entry.get("folder")
            triggers = entry.get("triggers", {})

            self._ensure_folder(parent_folder)

            # 1a) Known trigger
            if trigger in triggers:
                routed_path = triggers[trigger]
                self._ensure_folder(routed_path)

                metrics.inc(
                    "router_messages_routed_total",
                    labels={"route": msg_type},
                )
                return parent_folder, routed_path

            # 1b) Unknown trigger → fallback to parent
            metrics.inc(
                "router_messages_routed_total",
                labels={"route": msg_type},
            )
            return parent_folder, parent_folder

        # 2) Unknown message type
        unknown = self.routes.get("UNKNOWN", {})
        parent_folder = unknown.get("folder", "routed/UNKNOWN")

        self._ensure_folder(parent_folder)

        metrics.inc(
            "router_routing_errors_total",
            labels={"route": "UNKNOWN"},
        )

        return parent_folder, parent_folder