# hl7engine/utils/json_logger.py

# 2026 Mar 11:  Structured stdout logs: timestamp, level, message, merged event fields
#               JSONL logs are safe + consistent
#               Logging failures are observable (hl7_sys_logging_errors_total)
#               No high-cardinality labels
#               Ready for future enhancements (log rotatin, log shipping, correlation IDs, trace IDs)

import logging
import json
import sys
import datetime
import os

from hl7engine.metrics.metrics import metrics

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)


# ------------------------------------------------------------
# STRUCTURED STDOUT LOGGER
# ------------------------------------------------------------
logger = logging.getLogger("hl7engine")
logger.setLevel(logging.INFO)

# Avoid duplicate handlers if module is imported multiple times
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)

    # Structured JSON for stdout
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            base = {
                "timestamp": datetime.datetime.now().isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
            }
            # If the message is already a dict, merge it
            try:
                msg_obj = json.loads(record.getMessage())
                if isinstance(msg_obj, dict):
                    base.update(msg_obj)
            except Exception:
                pass
            return json.dumps(base, ensure_ascii=False)

    handler.setFormatter(JsonFormatter())
   