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
        self.stop_event = stop_event

    def run(self):
        client = MLLPClient(self.host, self.port)
        try:
            client.connect()
        except Exception as e:
            self.metrics["conn_failures"] += 1
            self.metrics["error_types"].add("conn_timeout")
            return

        interval = 1.0 / self.rate

        while not self.stop_event.is_set():
            msg = random.choice(self.message_pool)
            try:
                latency = client.send_hl7(msg)
                self.metrics["ack_latencies"].append(latency)
                self.metrics["sent"] += 1
            except Exception as e:
                self.metrics["error_types"].add("ack_timeout")
                self.metrics["ack_failures"] += 1
                # Counted above; suppress traceback
                #self.metrics["errors"].append(str(e))
                break

            time.sleep(interval)

        client.close()