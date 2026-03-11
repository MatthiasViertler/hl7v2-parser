# hl7engine_mllp_server.py

# MLLP server with early ACK + async routing
# - fast ACK path (ACK sent immediately after parse + validation)
# - async slow path (routing, file writing, DB insert, logging)
# - worker pool
# - queue
# - backpressure
# - structured logging
# 2026 Mar 3: first high-performance MLLP server version
# 2026 Mar 11: refactor for new metrics (low-cardinality, labelling)

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

        self._active_connections = 0
        self._workers_busy = 0
        self._queue_name = "ingress"

        # System / thread pool metrics
        metrics.set("sys_threads_total", max_workers, labels={"pool": "fast"})
        metrics.set("sys_threads_total", max_workers, labels={"pool": "slow"})
        metrics.set("sys_threads_active", 0, labels={"pool": "fast"})
        metrics.set("sys_threads_active", 0, labels={"pool": "slow"})

        # MLLP metrics
        metrics.set("mllp_connections_active", 0)
        metrics.set("sys_queue_depth", 0, labels={"queue": self._queue_name})

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
                try:
                    conn, addr = self._server_socket.accept()
                except OSError:
                    if self._shutdown.is_set():
                        break
                    raise

                logger.info({"event": "connection_accepted", "addr": addr})
                self._on_connection_open()

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
    # CONNECTION METRIC HELPERS
    # ------------------------------------------------------------
    def _on_connection_open(self):
        self._active_connections += 1
        metrics.set("mllp_connections_active", self._active_connections)
        metrics.inc("mllp_connections_total")

    def _on_connection_close(self):
        if self._active_connections > 0:
            self._active_connections -= 1
        metrics.set("mllp_connections_active", self._active_connections)

    # ------------------------------------------------------------
    # CONNECTION HANDLER
    # ------------------------------------------------------------
    def _handle_connection(self, conn: socket.socket, addr):
        sender_ip = addr[0]
        buffer = b""
        try:
            while not self._shutdown.is_set():
                try:
                    chunk = conn.recv(4096)
                except Exception:
                    metrics.inc("mllp_read_errors_total")
                    logger.error(
                        {
                            "event": "socket_read_error",
                            "addr": addr,
                        }
                    )
                    break

                if not chunk:
                    logger.info({"event": "connection_closed", "addr": addr})
                    break

                metrics.inc("mllp_bytes_received_total", amount=len(chunk))
                buffer += chunk

                # Process ALL complete frames in buffer
                while True:
                    start = buffer.find(START_BLOCK)
                    if start == -1:
                        buffer = b""
                        break

                    end = buffer.find(END_BLOCK, start + 1)
                    if end == -1:
                        # Incomplete frame, keep buffer
                        buffer = buffer[start:]
                        break

                    frame = buffer[start + 1 : end]
                    buffer = buffer[end + len(END_BLOCK) :]

                    metrics.inc("mllp_frame_starts_total")

                    try:
                        raw_hl7 = frame.decode(errors="ignore")
                        raw_hl7 = normalize_hl7(raw_hl7)
                    except Exception:
                        metrics.inc("mllp_frame_errors_total")
                        logger.error(
                            {
                                "event": "frame_decode_error",
                                "addr": addr,
                            }
                        )
                        continue

                    metrics.inc("messages_received_total")
                    self._enqueue_message(raw_hl7, conn, sender_ip)
        finally:
            self._on_connection_close()
            try:
                conn.close()
            except Exception:
                metrics.inc("mllp_connection_errors_total")
                logger.error(
                    {
                        "event": "connection_close_error",
                        "addr": addr,
                    }
                )

    # ------------------------------------------------------------
    # QUEUE ENQUEUE + BACKPRESSURE
    # ------------------------------------------------------------
    def _enqueue_message(self, raw_hl7: str, conn: socket.socket, sender_ip: str):
        try:
            self.queue.put_nowait((raw_hl7, conn, sender_ip))

            depth = self.queue.qsize()
            metrics.set(
                "sys_queue_depth",
                depth,
                labels={"queue": self._queue_name},
            )

            logger.info(
                {
                    "event": "message_enqueued",
                    "sender_ip": sender_ip,
                    "queue_size": depth,
                }
            )
        except Full:
            metrics.inc(
                "sys_queue_overflow_total",
                labels={"queue": self._queue_name},
            )
            metrics.inc(
                "router_backpressure_events_total",
                labels={"route": self._queue_name},
            )
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

            self._workers_busy += 1
            metrics.set(
                "sys_threads_active",
                self._workers_busy,
                labels={"pool": "fast"},
            )

            try:
                self._process_message(raw_hl7, conn, sender_ip)
            finally:
                self.queue.task_done()
                self._workers_busy = max(0, self._workers_busy - 1)
                metrics.set(
                    "sys_threads_active",
                    self._workers_busy,
                    labels={"pool": "fast"},
                )

    # ------------------------------------------------------------
    # PROCESS MESSAGE (FAST ACK + ASYNC SLOW PHASE)
    # ------------------------------------------------------------
    def _process_message(self, raw_hl7: str, conn: socket.socket, sender_ip: str):
        e2e_start = time.time()
        logger.info({"event": "message_processing_start", "sender_ip": sender_ip})

        # FAST PHASE → parse + validate + build ACK
        try:
            ack_start = time.time()
            ack, ctx = fast_ack_phase(raw_hl7, sender_ip)
            ack_latency_seconds = time.time() - ack_start

            metrics.inc("ack_generated_total")
            metrics.observe("ack_rtt", ack_latency_seconds)
        except Exception as e:
            logger.error({"event": "fast_ack_exception", "error": str(e)})
            metrics.inc("ack_generation_errors_total")
            raise

        # Send ACK immediately
        framed_ack = START_BLOCK + ack.encode() + END_BLOCK
        try:
            conn.sendall(framed_ack)
            metrics.inc("ack_sent_total")
            metrics.inc("mllp_bytes_sent_total", amount=len(framed_ack))
            logger.info({"event": "ack_sent", "sender_ip": sender_ip})
        except Exception as e:
            metrics.inc("mllp_write_errors_total")
            logger.error(
                {
                    "event": "ack_send_error",
                    "sender_ip": sender_ip,
                    "error": str(e),
                }
            )

        # SLOW PHASE → routing, file writing, DB insert, logging
        try:
            self.slow_executor.submit(slow_processing_phase, ctx)
            metrics.inc("messages_processed_total")
            logger.info(
                {
                    "event": "message_processing_done",
                    "sender_ip": sender_ip,
                }
            )

            e2e_latency_seconds = time.time() - e2e_start
            metrics.observe("message_end_to_end_latency", e2e_latency_seconds)
        except Exception as e:
            logger.error({"event": "slow_phase_exception", "error": str(e)})
            raise


# ------------------------------------------------------------
# RUN SERVER
# ------------------------------------------------------------
def run_server(
    host="0.0.0.0",
    port=2575,
    max_workers=8,
    queue_size=10000,
    enable_metrics=True,
    enable_prometheus=False,
    prometheus_port=8010,
):
    if enable_metrics:
        start_metrics_reporter(interval=1.0)

    if enable_prometheus:
        start_metrics_http_server(port=prometheus_port)

    server = MLLPServer(
        host=host,
        port=port,
        max_workers=max_workers,
        queue_size=queue_size,
    )
    server.start()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prometheus",
        action="store_true",
        help="Enable Prometheus /metrics endpoint",
    )
    parser.add_argument("--prometheus-port", type=int, default=8010)
    args = parser.parse_args()

    setup_logging()
    run_server(
        enable_prometheus=args.prometheus,
        prometheus_port=args.prometheus_port,
    )