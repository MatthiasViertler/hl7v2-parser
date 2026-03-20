import requests
import re
from collections import defaultdict

PROMETHEUS_METRICS_URL = "http://localhost:8010/metrics"

# ------------------------------------------------------------
# EXPECTED METRICS (based on your final backend implementation)
# ------------------------------------------------------------

EXPECTED_METRICS = {
    # MLLP
    "hl7_mllp_read_errors_total",
    "hl7_mllp_frame_errors_total",
    "hl7_mllp_connection_errors_total",
    "hl7_mllp_write_errors_total",
    "hl7_mllp_bytes_received_total",
    "hl7_mllp_bytes_sent_total",
    "hl7_mllp_connections_active",
    "hl7_mllp_connections_total",

    # Parser
    "hl7_parser_messages_parsed_total",
    "hl7_parser_parse_errors_total",
    "hl7_parser_validation_errors_total",
    "hl7_parser_message_types_total",
    "hl7_parser_versions_total",
    "hl7_parser_latency_seconds_p95_seconds",
    "hl7_parser_latency_seconds_p99_seconds",

    # Processing (fast phase)
    "hl7_processing_latency_seconds_p95_seconds",
    "hl7_processing_latency_seconds_p99_seconds",

    # ACK
    "hl7_ack_generated_total",
    "hl7_ack_sent_total",
    "hl7_ack_generation_errors_total",
    "hl7_ack_rtt_p95_seconds",
    "hl7_ack_rtt_p99_seconds",

    # End-to-end
    "hl7_message_end_to_end_latency_p95_seconds",
    "hl7_message_end_to_end_latency_p99_seconds",

    # Routing
    "hl7_router_messages_routed_total",
    "hl7_router_routing_errors_total",
    "hl7_proc_stage_duration_seconds_p95_seconds",
    "hl7_proc_stage_duration_seconds_p99_seconds",
    "hl7_proc_stage_errors_total",

    # Storage
    "hl7_store_write_operations_total",
    "hl7_store_write_latency_seconds_p95_seconds",
    "hl7_store_write_latency_seconds_p99_seconds",
    "hl7_store_write_errors_total",

    # Queues
    "hl7_sys_queue_depth",
    "hl7_processing_queue_depth",

    # Throughput
    "hl7_messages_received_total",
    "hl7_messages_processed_total",
}

# ------------------------------------------------------------
# METRIC NAME EXTRACTION
# ------------------------------------------------------------

def extract_metric_names(metrics_text):
    metric_names = set()
    label_map = defaultdict(set)

    for line in metrics_text.splitlines():
        if line.startswith("#"):
            continue

        match = re.match(r"^([a-zA-Z_:][a-zA-Z0-9_:]*)({.*})?\s", line)
        if match:
            name = match.group(1)
            metric_names.add(name)

            # Extract labels if present
            if match.group(2):
                labels = match.group(2).strip("{}")
                for label in labels.split(","):
                    if "=" in label:
                        key, _ = label.split("=", 1)
                        label_map[name].add(key)

    return metric_names, label_map

# ------------------------------------------------------------
# VALIDATION LOGIC
# ------------------------------------------------------------

def validate_metrics():
    print("Fetching metrics from:", PROMETHEUS_METRICS_URL)
    resp = requests.get(PROMETHEUS_METRICS_URL)
    resp.raise_for_status()

    metrics_text = resp.text
    actual_metrics, label_map = extract_metric_names(metrics_text)

    missing = EXPECTED_METRICS - actual_metrics
    extra = actual_metrics - EXPECTED_METRICS

    print("\n=== METRICS VALIDATION REPORT ===\n")

    if missing:
        print("❌ Missing metrics:")
        for m in sorted(missing):
            print("   -", m)
    else:
        print("✔ No missing metrics")

    if extra:
        print("\n⚠️ Extra metrics (not used in dashboards):")
        for m in sorted(extra):
            print("   -", m)

    print("\n✔ Present metrics:")
    for m in sorted(actual_metrics):
        print("   -", m)

    print("\n=== LABEL CHECK ===")
    for metric, labels in label_map.items():
        if labels:
            print(f"   {metric}: labels = {sorted(labels)}")

    print("\nDone.\n")

if __name__ == "__main__":
    validate_metrics()