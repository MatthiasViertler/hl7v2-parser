import threading
import time
import random
from .long_lived_worker import LongLivedWorker
from .burst_worker import BurstWorker

def percentile(data, p):
    if not data:
        return None
    k = int(len(data) * p)
    return sorted(data)[k]

def run_benchmark(host, port, message_pool, duration_sec=300):
    metrics = {
        "sent": 0,
        "ack_latencies": [],
        "connection_times": [],
        "conn_failures": 0,
        "ack_failures": 0,
        "error_types": set(), # only store each type of error once in a set
    }

    stop_event = threading.Event()

    # Long-lived workers
    long_workers = [
        LongLivedWorker(i, host, port, rate_per_sec=30,
                        message_pool=message_pool,
                        metrics=metrics,
                        stop_event=stop_event)
        for i in range(2)
    ]

    for w in long_workers:
        w.start()

    start_time = time.time()
    next_progress = start_time + 5

    while True:
        now = time.time()
        elapsed = now - start_time

        if elapsed >= duration_sec:
            break

        if now >= next_progress:
            remaining = duration_sec - elapsed
            print(f"[Progress] {elapsed:5.1f}s elapsed, {remaining:5.1f}s remaining | "
                  f"sent={metrics['sent']} " #errors={len(metrics['errors'])}"
                  f"conn_fail={metrics['conn_failures']} "
                  f"ack_fail={metrics['ack_failures']}"
            )

            next_progress = now + 5

        burst = BurstWorker(
            worker_id=random.randint(1000, 9999),
            host=host,
            port=port,
            message_pool=message_pool,
            metrics=metrics
        )
        burst.start()

        time.sleep(random.uniform(0.1, 0.5))

    stop_event.set()

    for w in long_workers:
        w.join()

    # --------- PRINT BENCHMARK SUMMARY ----------
    p50 = percentile(metrics["ack_latencies"], 0.50)
    p95 = percentile(metrics["ack_latencies"], 0.95)
    p99 = percentile(metrics["ack_latencies"], 0.99)

    print("\n--- Benchmark Summary ---")
    print(f"Messages sent: {metrics['sent']}")
    print(f"Connection failures: {metrics['conn_failures']}")
    print(f"ACK failures: {metrics['ack_failures']}")
    print(f"Error types: {metrics['error_types']}")

    if p50 is not None:
        print(f"ACK latency p50: {p50*1000:.2f} ms")
        print(f"ACK latency p95: {p95*1000:.2f} ms")
        print(f"ACK latency p99: {p99*1000:.2f} ms")
    else:
        print("No ACK latencies recorded.")
        
    throughput = metrics["sent"] / duration_sec
    print(f"Throughput: {throughput:.2f} msg/sec") 

    return metrics
