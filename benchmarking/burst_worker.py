import threading
import time
import random
from .mllp_client import MLLPClient


class BurstWorker(threading.Thread):
    def __init__(self, worker_id, host, port, message_pool, metrics, stop_event=None):
        super().__init__()
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.message_pool = message_pool
        self.metrics = metrics
        self._stop_event = stop_event or threading.Event()

    def stop(self):
        self._stop_event.set()

    def run(self):
        # If stop was requested before we even start, exit early
        if self._stop_event.is_set():
            return

        batch_size = random.randint(5, 15)
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
            # Always close before exiting
            client.close()
            return
        
        # Record connection time only in real benchmark mode
        if not is_warmup:
            self.metrics["connection_times"].append(t1 - t0)

        # --- WARM-UP MODE ---
        
        if is_warmup:
            # Warm-up: send each message once, ignore metrics
            try:
                for msg in self.message_pool:
                    if self._stop_event.is_set():
                        break
                    client.send_hl7(msg)
            except:
                pass
            client.close()
            return
        
        # --- REAL BENCHMARK MODE ---

        for _ in range(batch_size):
            if self._stop_event.is_set():
                break

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

        client.close()
