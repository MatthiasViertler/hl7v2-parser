import threading
import time
import random
from .long_lived_worker import LongLivedWorker
from .burst_worker import BurstWorker
from .connection_worker import ConnectionWorker

def percentile(data, p):
    if not data:
        return None
    k = int(len(data) * p)
    return sorted(data)[k]

def histogram(data, bins=10):
    if not data:
        return None

    data = sorted(data)
    mn, mx = data[0], data[-1]
    step = (mx - mn) / bins if bins > 0 else 1

    # Avoid division by zero if all values are identical
    if step == 0:
        return [(mn, len(data))]

    hist = []
    start = mn
    idx = 0

    for b in range(bins):
        end = start + step
        count = 0
        while idx < len(data) and data[idx] < end:
            count += 1
            idx += 1
        hist.append((start, end, count))
        start = end

    return hist

def run_benchmark(host, port, message_pool, duration_sec=300, warmup=0, conn_stress=False, max_throughput=False, sweep=False):
    metrics = {
        "sent": 0,
        "ack_latencies": [],
        "connection_times": [],
        "conn_failures": 0,
        "ack_failures": 0,
        "error_types": set(), # only store each type of error once in a set
    }
    
    # ----- WARM UP ------
    if warmup > 0:
        print(f"Warm-up for {warmup} seconds...")

        warmup_end = time.time() + warmup
        stop_event = threading.Event()

        # Create temporary workers for warm-up
        warmup_workers = [
            LongLivedWorker(
                worker_id=random.randint(1000, 9999),
                host=host,
                port=port,
                rate_per_sec=30,
                message_pool=message_pool,
                metrics=None,
                stop_event=stop_event,
            ),
            BurstWorker(
                worker_id=random.randint(1000, 9999),
                host=host,
                port=port,
                message_pool=message_pool,
                metrics=None,
                stop_event=stop_event,
            ),
        ]

        for w in warmup_workers:
            w.start()

        # Let them run without collecting metrics
        while time.time() < warmup_end:
            time.sleep(0.1)

        # Stop warm-up workers
        for w in warmup_workers:
            w.stop()
        for w in warmup_workers:
            w.join()

        print("Warm-up complete.\n")
    # ---- END WARM UP ----

    # ---- SWEEP ----
    if sweep:
        print("Running concurrency sweep...")

        sweep_levels = [1, 2, 4, 8, 16]
        sweep_results = []

        for workers_count in sweep_levels:
            print(f"\n--- Sweep: {workers_count} workers ---")

            # fresh metrics for each run
            m = {
                "sent": 0,
                "ack_latencies": [],
                "connection_times": [],
                "conn_failures": 0,
                "ack_failures": 0,
                "error_types": set(),
            }

            stop_event = threading.Event()

            workers = [
                LongLivedWorker(
                    worker_id=i,
                    host=host,
                    port=port,
                    rate_per_sec=None,  # unlimited
                    message_pool=message_pool,
                    metrics=m,
                    stop_event=stop_event
                )
                for i in range(workers_count)
            ]

            for w in workers:
                w.start()

            start_time = time.time()
            while time.time() - start_time < duration_sec:
                time.sleep(0.05)

            stop_event.set()
            for w in workers:
                w.join()

            throughput = m["sent"] / duration_sec

            print(f"Workers={workers_count} | Throughput={throughput:.2f} msg/sec | "
                f"ACK fails={m['ack_failures']}")

            sweep_results.append({
                "workers": workers_count,
                "throughput": throughput,
                "ack_failures": m["ack_failures"],
                "latencies": m["ack_latencies"],
            })

        # Print Summary
        print("\n=== Concurrency Sweep Summary ===")
        print("Workers | Throughput (msg/sec) | ACK Failures")
        print("---------------------------------------------")

        for r in sweep_results:
            print(f"{r['workers']:7d} | {r['throughput']:20.2f} | {r['ack_failures']:12d}")

        # Optionally export sweep results
        return sweep_results
    # ---- END SWEEP -----

    # ---- MAX THROUGHPUT ----
    if max_throughput:
        print("Running max-throughput test (long-lived workers only)...")

        stop_event = threading.Event()

        # You can tune this number later
        workers = [
            LongLivedWorker(
                worker_id=i,
                host=host,
                port=port,
                rate_per_sec=None,  # unlimited
                message_pool=message_pool,
                metrics=metrics,
                stop_event=stop_event
            )
            for i in range(4)  # start with 4 long-lived workers
        ]

        for w in workers:
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
                print(
                    f"[MaxTP] {elapsed:5.1f}s elapsed, {remaining:5.1f}s remaining | "
                    f"sent={metrics['sent']} "
                    f"ack_fail={metrics['ack_failures']}"
                )
                next_progress = now + 5

            time.sleep(0.05)

        stop_event.set()
        for w in workers:
            w.join()

        print("\n--- Max Throughput Summary ---")
        print(f"Messages sent: {metrics['sent']}")
        print(f"ACK failures: {metrics['ack_failures']}")
        print(f"Error types: {metrics['error_types']}")

        if metrics["ack_latencies"]:
            p50 = percentile(metrics["ack_latencies"], 0.50)
            p95 = percentile(metrics["ack_latencies"], 0.95)
            p99 = percentile(metrics["ack_latencies"], 0.99)
            print(f"ACK latency p50: {p50:.2f} ms")
            print(f"ACK latency p95: {p95:.2f} ms")
            print(f"ACK latency p99: {p99:.2f} ms")

        print(f"Throughput: {metrics['sent'] / duration_sec:.2f} msg/sec")

        return metrics
    # ---- END MAX THROUGHPUT ----

    # ---- CONN STRESS MODE ----
    if conn_stress:
        print("Running connection-only stress test...")

        stop_event = threading.Event()

        # You can tune the number of workers later

        workers = [
            ConnectionWorker(
                worker_id=i,
                host=host,
                port=port,
                metrics=metrics,
                stop_event=stop_event
            )
            for i in range(10)  # number of concurrent connectors
        ]

        for w in workers:
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
                print(
                    f"[ConnStress] {elapsed:5.1f}s elapsed, {remaining:5.1f}s remaining | "
                    f"connections={metrics['sent']} "
                    f"conn_fail={metrics['conn_failures']}"
                )
                next_progress = now + 5

            time.sleep(0.05)

        stop_event.set()
        for w in workers:
            w.join()

        # Print Connection Stress Test Results
        print("\n--- Connection Stress Summary ---")
        print(f"Successful connections: {metrics['sent']}")
        print(f"Connection failures: {metrics['conn_failures']}")
        print(f"Error types: {metrics['error_types']}")

        if metrics["connection_times"]:
            avg = sum(metrics["connection_times"]) / len(metrics["connection_times"])
            print(f"Average connection time: {avg*1000:.2f} ms")
            print(f"Connections per second: {metrics['sent'] / duration_sec:.2f}")
        else:
            print("No successful connections recorded.")

        return metrics
    # ---- END CONN STRESS MODE ----

    stop_event = threading.Event()

    # Long-lived workers
    long_workers = [
        LongLivedWorker(
            worker_id=i,
            host=host,
            port=port,
            rate_per_sec=30,
            message_pool=message_pool,
            metrics=metrics,
            stop_event=stop_event,
        )
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
            metrics=metrics,
            stop_event=stop_event,
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

    print("\nACK Latency Histogram (ms):")
    h = histogram([x * 1000 for x in metrics["ack_latencies"]], bins=10)
    if h:
        for (start, end, count) in h:
            bar = "#" * (count // max(1, len(metrics["ack_latencies"]) // 50))
            print(f"{start:6.1f} – {end:6.1f} ms | {bar} ({count})")
    else:
        print("No latency data.")

    throughput = metrics["sent"] / duration_sec
    print(f"Throughput: {throughput:.2f} msg/sec") 

    return metrics
