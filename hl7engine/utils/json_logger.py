# json_logger.py
import logging
import json
import sys
import datetime
import os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# ------------------------------------------------------------
# NEW: module-level logger for stdout (used by metrics, server)
# ------------------------------------------------------------
logger = logging.getLogger("hl7engine")
logger.setLevel(logging.INFO)

# Avoid adding multiple handlers if module is imported repeatedly
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)


# ------------------------------------------------------------
# EXISTING: JSONL file logger (unchanged)
# ------------------------------------------------------------
def log_event(event: dict, filename="events.jsonl"):
    """
    Append a structured JSON log entry to a .jsonl file.
    Each line is one JSON object.
    """
    event["timestamp"] = datetime.datetime.now().isoformat()

    path = os.path.join(LOG_DIR, filename)
    with open(path, "a") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def log_message_json(raw_hl7, msg_type, control_id):
    os.makedirs("logs/messages", exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "raw_hl7": raw_hl7,
        "message_type": msg_type,
        "control_id": control_id
    }

    with open(f"logs/messages/msg_{ts}.json", "w") as f:
        json.dump(entry, f, indent=2)