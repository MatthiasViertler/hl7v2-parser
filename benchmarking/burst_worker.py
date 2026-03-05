import threading
import time
import random
from .mllp_client import MLLPClient


class BurstWorker(threading.Thread):
    def __init__(self, worker_id, host, port, message_pool, metrics):
        super().__init__()
        self.worker_id = worker_id
        self.host = host
        self.port = port
        self.message_pool = message_pool
        self.metrics = metrics

    def run(self):
        batch_size = random.randint(5, 15)

        client = MLLPClient(self.host, self.port)
        t0 = time.perf_counter()
        try:
            client.connect()
        except Exception as e:
            self.metrics["conn_failures"] += 1
            self.metrics["error_types"].add("conn_timeout")
            return
        t1 = time.perf_counter()

        self.metrics["connection_times"].append(t1 - t0)

        for _ in range(batch_size):
            msg = random.choice(self.message_pool)
            try:
                latency = client.send_hl7(msg)
                self.metrics["ack_latencies"].append(latency)
                self.metrics["sent"] += 1
            except Exception as e:
                self.metrics["ack_failures"] += 1
                self.metrics["error_types"].add("ack_timeout")
                # Counted above; suppress traceback
                #self.metrics["errors"].append(str(e))
                break

        client.close()