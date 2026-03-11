# metrics/metrics.py

import threading
from collections import defaultdict

def _label_key(labels):
    """
    Convert a dict of labels into a stable, hashable key.
    """
    if not labels:
        return frozenset()
    return frozenset(sorted(labels.items()))

class Metrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)

    def inc(self, name, amount=1, labels=None):
        key = (name, _label_key(labels))
        with self._lock:
            self.counters[key] += amount

    def set(self, name, value, labels=None):
        key = (name, _label_key(labels))
        with self._lock:
            self.gauges[key] = value

    def observe(self, name, value, labels=None):
        key = (name, _label_key(labels))
        with self._lock:
            self.histograms[key].append(value)

    def snapshot(self):
        with self._lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: list(v) for k, v in self.histograms.items()},
            }

metrics = Metrics()