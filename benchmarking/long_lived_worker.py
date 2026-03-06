import threading
import time
import random
from .mllp_client import MLLPClient


class LongLivedWorker(threading.Thread):
    def __init__(self, worker_id, host, port, rate_per_sec, message_pool, metrics, stop_event):
        super().__init__()
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.rate = rate_per_sec
        self.message_pool = message_pool
        self.metrics = metrics
        self._stop_event = stop_event

    def stop(self):
        self._stop_event.set()

    def run(self):
        client = MLLPClient(self.host, self.port)
        is_warmup = self.metrics is None
        
        # --- CONNECT ---
        try:
            t0 = time.perf_counter()
            client.connect()
            t1 = time.perf_counter()
        except Exception:
            if not is_warmup:
                self.metrics["conn_failures"] += 1
                self.metrics["error_types"].add("conn_timeout")
            client.close()
            return

        # Record connection time only in real benchmark mode
        if not is_warmup:
            self.metrics["connection_times"].append(t1 - t0)

        # --- WARM-UP MODE ---
        if is_warmup:
            try:
                # Long-lived warm-up: keep connection open and send messages repeatedly
                while not self._stop_event.is_set():
                    for msg in self.message_pool:
                        try:
                            client.send_hl7(msg)
                        except:
                            # Ignore warm-up errors
                            pass
            finally:
                client.close()
            return

        # --- REAL BENCHMARK MODE ---
        try:
            interval = 1.0 / self.rate

            while not self._stop_event.is_set():
                msg = random.choice(self.message_pool)
                try:
                    latency = client.send_hl7(msg)
                    self.metrics["ack_latencies"].append(latency)
                    self.metrics["sent"] += 1
                except Exception:
                    self.metrics["ack_failures"] += 1
                    self.metrics["error_types"].add("ack_timeout")
                    # Counted above; suppress traceback
                    #self.metrics["errors"].append(str(e))
                    break

                time.sleep(interval)
        finally:
            client.close()
