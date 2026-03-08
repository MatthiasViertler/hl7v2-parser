# hl7engine/metrics_reporter.py

import threading
import time
from hl7engine.metrics.metrics import metrics
from hl7engine.utils.json_logger import logger

def start_metrics_reporter(interval=1.0):
    def loop():
        while True:
            snap = metrics.snapshot()
            logger.info({
                "event": "metrics",
                "counters": snap["counters"],
                "gauges": snap["gauges"],
            })
            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()