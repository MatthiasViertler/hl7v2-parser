# hl7engine/metrics/prometheus_http.py

# 2026 Mar 11:  Emit exporter-level metrics: exporter_scrapes_total, exporter_scrape_errors_total, exporter_last_scrape_timestamp
#                   - essential for: detecting exporter failures + scrape stalls, monitoring Prometheus health
#               Clean, safe HTTP server: never crash the server, never log noisy HTTPServer messages, no blocking, no partial writes
#               Handle /metrics cleanly + predictably
#               Use correct Prometheus content type
#               Avoid blocking the main thread
#               Emit structured logs

import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

from hl7engine.utils.json_logger import logger
from hl7engine.metrics.metrics import metrics
from hl7engine.metrics.prometheus_exporter import metrics_to_prometheus


class MetricsHandler(BaseHTTPRequestHandler):
    """
    Minimal, production‑safe Prometheus metrics endpoint.
    """

    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        scrape_start = time.time()

        try:
            body = metrics_to_prometheus().encode("utf-8")

            metrics.inc("exporter_scrapes_total")
            metrics.set("exporter_last_scrape_timestamp", time.time())

            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        except Exception as e:
            metrics.inc("exporter_scrape_errors_total")
            logger.error(
                {
                    "event": "prometheus_scrape_error",
                    "error": str(e),
                }
            )
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        # Silence default HTTP logging
        return


def start_metrics_http_server(host="0.0.0.0", port=8010):
    """
    Start the Prometheus /metrics HTTP endpoint in a background thread.
    """

    try:
        server = HTTPServer((host, port), MetricsHandler)
    except OSError:
        logger.warning(
            {
                "event": "prometheus_port_in_use",
                "port": port,
                "message": "Prometheus metrics endpoint not started because port is already in use.",
            }
        )
        return None

    logger.info(
        {
            "event": "prometheus_http_start",
            "host": host,
            "port": port,
        }
    )

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server