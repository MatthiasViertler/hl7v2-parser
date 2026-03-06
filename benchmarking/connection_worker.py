import threading
import time
from .mllp_client import MLLPClient

class ConnectionWorker(threading.Thread):
    def __init__(self, worker_id, host, port, metrics, stop_event=None):
        super().__init__()
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.metrics = metrics
        self._stop_event = stop_event or threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        while not self._stop_event.is_set():
            client = MLLPClient(self.host, self.port)

            try:
                t0 = time.perf_counter()
                client.connect()
                t1 = time.perf_counter()

                self.metrics["connection_times"].append(t1 - t0)
                self.metrics["sent"] += 1  # count successful connections

            except Exception:
                self.metrics["conn_failures"] += 1
                self.metrics["error_types"].add("conn_timeout")

            finally:
                client.close()