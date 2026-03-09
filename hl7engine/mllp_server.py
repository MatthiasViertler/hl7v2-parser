# MLLP server with early ACK + async routing
# - fast ACK path (ACK sent immediately after parse + validation)
# - async slow path (routing, file writing, DB insert, logging)
# - worker pool
# - queue
# - backpressure
# - structured logging
# 2026 Mar 3: first high-performance MLLP server version

import socket
import threading
import logging
import logging.config
import yaml
import time
import argparse


from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Full

from hl7engine.metrics.metrics import metrics
from hl7engine.metrics.prometheus_http import start_metrics_http_server
from hl7engine.metrics.metrics_reporter import start_metrics_reporter

from hl7engine.hl7_listener import (
    fast_ack_phase,
    slow_processing_phase,
    normalize_hl7,
)
from hl7engine.utils.json_logger import logger

START_BLOCK = b"\x0b"
END_BLOCK = b"\x1c\x0d"


def setup_logging():
    config_path = Path("config/logging.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)


class MLLPServer:
    def __init__(self, host="0.0.0.0", port=2575, max_workers=8, queue_size=10000):
        self.host = host
        self.port = port
        self.queue: Queue = Queue(maxsize=queue_size)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.slow_executor = ThreadPoolExecutor(max_workers=max_workers)
        self._shutdown = threading.Event()
        self._server_socket: socket.socket | None = None
                
        metrics.set("workers_max", max_workers)
        metrics.set("workers_busy", 0)
        metrics.set("active_connections", 0)

    # ------------------------------------------------------------
    # SERVER START
    # ------------------------------------------------------------
    def start(self):
        logger.info({"event": "server_start", "host": self.host, "port": self.port})
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(5)

        print(f"HL7 MLLP listener running on {self.host}:{self.port}")

        # Start worker pool threads
        for _ in range(self.executor._max_workers):
            self.executor.submit(self._worker_loop)

        # Accept loop
        try:
            while not self._shutdown.is_set():
                conn, addr = self._server_socket.accept()
                logger.info({"event": "connection_accepted", "addr": addr})
                threading.Thread(
                    target=self._handle_connection,
                    args=(conn, addr),
                    daemon=True,
                ).start()
        finally:
            self.stop()

    # ------------------------------------------------------------
    # SERVER STOP
    # ------------------------------------------------------------
    def stop(self):
        logger.info({"event": "server_stop"})
        self._shutdown.set()
        if self._server_socket:
            try:
                self._server_socket.close()
            except Exception:
                pass
        self.executor.shutdown(wait=True)
        self.slow_executor.shutdown(wait=True)

    # ------------------------------------------------------------
    # CONNECTION HANDLER
    # ------------------------------------------------------------
    def _handle_connection(self, conn: socket.socket, addr):
        sender_ip = addr[0]
        buffer = b""
        try:
            metrics.set("active_connections", metrics.gauges["active_connections"] + 1)
            while not self._shutdown.is_set():
                chunk = conn.recv(4096)
                if not chunk:
                    logger.info({"event": "connection_closed", "addr": addr})
                    break

                buffer += chunk

                # Process ALL complete frames in buffer
                while True:
                    start = buffer.find(START_BLOCK)
                    if start == -1:
                        buffer = b""
                        break

                    end = buffer.find(END_BLOCK, start + 1)
                    if end == -1:
                        break

                    frame = buffer[start + 1 : end]
                    buffer = buffer[end + len(END_BLOCK) :]

                    raw_hl7 = frame.decode(errors="ignore")
                    raw_hl7 = normalize_hl7(raw_hl7)

                    self._enqueue_message(raw_hl7, conn, sender_ip)
        finally:
            metrics.set("active_connections", metrics.gauges["active_connections"] - 1)
            try:
                conn.close()
            except Exception:
                metrics.inc("connection_errors")
                pass

    # ------------------------------------------------------------
    # QUEUE ENQUEUE + BACKPRESSURE
    # ------------------------------------------------------------
    def _enqueue_message(self, raw_hl7: str, conn: socket.socket, sender_ip: str):
        try:
            self.queue.put_nowait((raw_hl7, conn, sender_ip))
            
            metrics.inc("messages_received")
            metrics.set("queue_depth", self.queue.qsize())

            logger.info(
                {
                    "event": "message_enqueued",
                    "sender_ip": sender_ip,
                    "queue_size": self.queue.qsize(),
                }
            )
        except Full:
            metrics.inc("queue_overflow")
            logger.warning(
                {
                    "event": "queue_full",
                    "sender_ip": sender_ip,
                    "queue_size": self.queue.qsize(),
                }
            )
            # Optional: send "busy" ACK here

    # ------------------------------------------------------------
    # WORKER LOOP
    # ------------------------------------------------------------
    def _worker_loop(self):
        logger.info({"event": "worker_start"})

        while not self._shutdown.is_set():
            try:
                raw_hl7, conn, sender_ip = self.queue.get(timeout=1.0)
            except Exception:
                continue

            metrics.inc("worker_tasks")
            metrics.set("workers_busy", metrics.gauges["workers_busy"] + 1)

            try:
                self._process_message(raw_hl7, conn, sender_ip)
            finally:
                self.queue.task_done()
                metrics.set("workers_busy", metrics.gauges["workers_busy"] - 1)

    # ------------------------------------------------------------
    # PROCESS MESSAGE (FAST ACK + ASYNC SLOW PHASE)
    # ------------------------------------------------------------
    def _process_message(self, raw_hl7: str, conn: socket.socket, sender_ip: str):
        try:
            e2e_start = time.time()
            logger.info({"event": "message_processing_start", "sender_ip": sender_ip})

            start = time.time()
            # FAST PHASE → parse + validate + build ACK
            ack, ctx = fast_ack_phase(raw_hl7, sender_ip)
            ack_latency = (time.time() - start) * 1000
            metrics.observe("ack_latency_ms", ack_latency)
            facility = ctx.get("facility", "UNKNOWN")
            # Prometheus metric names cannot contain dots
            sender_ip_prometheus = sender_ip.replace(".", "_")
            facility_prometheus = facility.replace(".", "_")
            metrics.observe(f"sender_ack_latency_ms_{sender_ip_prometheus}", ack_latency)
            metrics.observe(f"facility_ack_latency_ms_{facility_prometheus}", ack_latency)
        except Exception as e:
            logger.error({"event": "worker_exception_1", "error": str(e)})
            raise

        # Send ACK immediately
        framed_ack = START_BLOCK + ack.encode() + END_BLOCK
        try:
            conn.sendall(framed_ack)
        except Exception as e:
            logger.error(
                {
                    "event": "ack_send_error",
                    "sender_ip": sender_ip,
                    "error": str(e),
                }
            )

        metrics.inc("acks_sent")
        logger.info({"event": "ack_sent", "sender_ip": sender_ip})

        try:
            # SLOW PHASE → routing, file writing, DB insert, logging
            self.slow_executor.submit(slow_processing_phase, ctx)

            metrics.inc("messages_processed")
            logger.info({"metrics_id": id(metrics)})
            logger.info({"event": "message_processing_done", "sender_ip": sender_ip})
            e2e_latency = (time.time() - e2e_start) * 1000
            metrics.observe("end_to_end_latency_ms", e2e_latency)
            facility = ctx.get("facility", "UNKNOWN")
            # Prometheus metric names cannot contain dots
            sender_ip_prometheus = sender_ip.replace(".", "_")
            facility_prometheus = facility.replace(".", "_")
            metrics.observe(f"sender_e2e_latency_ms_{sender_ip_prometheus}", e2e_latency)
            metrics.observe(f"facility_e2e_latency_ms_{facility_prometheus}", e2e_latency)
        except Exception as e:
            logger.error({"event": "worker_exception_2", "error": str(e)})
            raise

# ------------------------------------------------------------
# RUN SERVER
# ------------------------------------------------------------
def run_server(host="0.0.0.0", port=2575, max_workers=8, queue_size=10000, enable_metrics=True, enable_prometheus=False, prometheus_port=8010):
    if enable_metrics:
        start_metrics_reporter(interval=1.0)

    if enable_prometheus:
        start_metrics_http_server(port=prometheus_port)

    server = MLLPServer(host=host, port=port, max_workers=max_workers, queue_size=queue_size)
    server.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prometheus", action="store_true",
                        help="Enable Prometheus /metrics endpoint")
    parser.add_argument("--prometheus-port", type=int, default=8010)
    args = parser.parse_args()

    setup_logging()
    run_server(
        enable_prometheus=args.prometheus,
        prometheus_port=args.prometheus_port
    )

    # setup_logging()
    # #run_server()
    # # Run server with Prometheus
    # run_server(enable_prometheus=True)