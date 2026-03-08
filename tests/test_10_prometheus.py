import time
import urllib.request

# This test:
# - Ensures the endpoint is reachable
# - Ensures metrics are present
# - Ensures Prometheus exporter works

def test_prometheus_metrics_endpoint():
    # Give the server a moment to start
    time.sleep(1)

    url = "http://localhost:8010/metrics"
    with urllib.request.urlopen(url) as response:
        body = response.read().decode("utf-8")

    # Basic sanity checks
    assert "hl7_messages_received" in body
    assert "hl7_workers_busy" in body