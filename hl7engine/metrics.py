# hl7engine/metrics.py

import threading
from collections import defaultdict

class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)

    def inc(self, name, amount=1):
        with self._lock:
            self.counters[name] += amount

    def set(self, name, value):
        with self._lock:
            self.gauges[name] = value

    def observe(self, name, value):
        with self._lock:
            self.histograms[name].append(value)

    def snapshot(self):
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: list(v) for k, v in self.histograms.items()},
            }

metrics = Metrics()