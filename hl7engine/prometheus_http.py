# hl7engine/prometheus_http.py
import threading

from http.server import HTTPServer, BaseHTTPRequestHandler
from hl7engine.json_logger import logger

from hl7engine.prometheus_exporter import metrics_to_prometheus

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/metrics":
            self.send_response(404)
            self.end_headers()
            return

        body = metrics_to_prometheus().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # silence default HTTP logging
        return

def start_metrics_http_server(host="0.0.0.0", port=8010):
    try:
        server = HTTPServer((host, port), MetricsHandler)
    except OSError:
        logger.warning({
            "event": "prometheus_port_in_use",
            "port": port,
            "message": "Prometheus metrics endpoint not started because port is already in use."
        })
        return None

    logger.info({
        "event": "prometheus_http_start",
        "port": port
    })

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server
