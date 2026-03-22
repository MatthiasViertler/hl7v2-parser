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
        
        # -----------------------------------------------------------------
        # METRIC INITIALIZATION (ensures metrics always appear in /metrics)
        # -----------------------------------------------------------------

        # ============================================================
        # PARSER METRICS
        # ============================================================

        # --- Parse Errors (syntactic failures before validation) ---
        self.inc("parser_parse_errors_total", amount=0, labels={"error_code": "EMPTY"})
        self.inc("parser_parse_errors_total", amount=0, labels={"error_code": "NO_MSH"})
        self.inc("parser_parse_errors_total", amount=0, labels={"error_code": "PARSE"})
        self.inc("parser_parse_errors_total", amount=0, labels={"error_code": "VERSION"})
        self.inc("parser_parse_errors_total", amount=0, labels={"error_code": "MSH9"})

        # --- Validation Errors (semantic failures after parsing) ---
        self.inc("parser_validation_errors_total", amount=0, labels={"error_code": "AE"})
        self.inc("parser_validation_errors_total", amount=0, labels={"error_code": "AR"})

        # --- Message Types & Versions ---
        self.inc("parser_message_types_total", amount=0, labels={"message_type": "UNKNOWN"})
        self.inc("parser_versions_total", amount=0, labels={"version": "UNKNOWN"})

        # ============================================================
        # ROUTER METRICS
        # ============================================================

        # --- Successful routing by message type ---
        self.inc("router_messages_routed_total", amount=0, labels={"route": "UNKNOWN"})

        # --- Routing errors (unknown message type or trigger) ---
        self.inc("router_routing_errors_total", amount=0, labels={"route": "UNKNOWN"})

        # ==========================
        # MLLP Metrics: Connections, Bytes, Frames
        # ==========================
        self.inc("mllp_connections_total", amount=0)
        self.inc("mllp_bytes_received_total", amount=0)
        self.inc("mllp_bytes_sent_total", amount=0)
        self.inc("mllp_frame_starts_total", amount=0)

        # ==========================
        # ACK Metrics
        # ==========================
        self.inc("ack_generated_total", amount=0, labels={"code": "AA"})
        self.inc("ack_generated_total", amount=0, labels={"code": "AE"})
        self.inc("ack_generated_total", amount=0, labels={"code": "AR"})
        self.inc("ack_sent_total", amount=0)

        # ==========================
        # Throughput Metrics
        # ==========================
        self.inc("messages_received_total", amount=0)
        self.inc("messages_processed_total", amount=0)

        # ======================================
        # Latency Histograms (initialized empty)
        # ======================================
        self.observe("parser_latency_seconds", 0)
        self.observe("processing_latency_seconds", 0)
        self.observe("router_latency_seconds", 0)
        self.observe("store_write_latency_seconds", 0)
        self.observe("message_end_to_end_latency_seconds", 0)
        self.observe("ack_rtt_seconds", 0)


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