import argparse
from pathlib import Path
from .coordinator import run_benchmark


# Resolve the directory where THIS script lives
BASE_DIR = Path(__file__).resolve().parent
MESSAGES_DIR = BASE_DIR / "messages"


def load_messages():
    required = ["adt.hl7", "orm.hl7", "oru.hl7"]
    messages = []

    for fname in required:
        path = MESSAGES_DIR / fname
        if not path.exists():
            raise FileNotFoundError(f"Missing HL7 sample message: {path}")
        messages.append(path.read_text())

    return messages

def percentile(data, p):
    if not data:
        return None
    k = int(len(data) * p)
    return sorted(data)[k]


def main():
    parser = argparse.ArgumentParser(description="HL7 MLLP Benchmark Runner")
    parser.add_argument("--host", default="127.0.0.1", help="MLLP server host")
    parser.add_argument("--port", type=int, default=2575, help="MLLP server port")
    parser.add_argument("--duration", type=int, default=300, help="Benchmark duration in seconds")

    args = parser.parse_args()

    message_pool = load_messages()

    print(f"Starting benchmark for {args.duration} seconds...")
    print(f"Target: {args.host}:{args.port}")
    print(f"Loaded {len(message_pool)} HL7 message templates.")

    metrics = run_benchmark(
        host=args.host,
        port=args.port,
        message_pool=message_pool,
        duration_sec=args.duration
    )

    # print("\n--- Benchmark Summary ---")
    # print(f"Messages sent: {metrics['sent']}")
    # print(f"ACK latencies (ms): {[round(x * 1000, 2) for x in metrics['ack_latencies'][:10]]} ...")
    # print(f"Connection times (ms): {[round(x * 1000, 2) for x in metrics['connection_times'][:10]]} ...")
    # print(f"Errors: {metrics['errors']}")
    
    p50 = percentile(metrics["ack_latencies"], 0.50)
    p95 = percentile(metrics["ack_latencies"], 0.95)
    p99 = percentile(metrics["ack_latencies"], 0.99)

    print("\n--- Benchmark Summary ---")
    print(f"Messages sent: {metrics['sent']}")
    print(f"Connection failures: {metrics['conn_failures']}")
    print(f"ACK failures: {metrics['ack_failures']}")
    print(f"Error types: {metrics['error_types']}")
    print(f"ACK latency p50: {p50*1000:.2f} ms" if p50 else "ACK latency p50: n/a")
    print(f"ACK latency p95: {p95*1000:.2f} ms" if p95 else "ACK latency p95: n/a")
    print(f"ACK latency p99: {p99*1000:.2f} ms" if p99 else "ACK latency p99: n/a")


if __name__ == "__main__":
    main()


# from coordinator import run_benchmark
# from pathlib import Path

# # Resolve the directory where THIS script lives
# BASE_DIR = Path(__file__).resolve().parent

# # Path to the messages folder
# MESSAGES_DIR = BASE_DIR / "messages"

# if __name__ == "__main__":
#     # Load your HL7 messages from files or templates
    
#     message_pool = [
#     (MESSAGES_DIR / "adt.hl7").read_text(),
#     (MESSAGES_DIR / "orm.hl7").read_text(),
#     (MESSAGES_DIR / "oru.hl7").read_text(),
#     ]

#     # Benchmarks are supposed to be run from project root ->
#     # below path is correct. More robust despite usage: above.
#     # message_pool = [
#     #     open("benchmarking/samples/adt.hl7").read(),
#     #     open("benchmarking/samples/orm.hl7").read(),
#     #     open("benchmarking/samples/oru.hl7").read(),
#     # ]

#     for f in ["adt.hl7", "orm.hl7", "oru.hl7"]:
#         if not (MESSAGES_DIR / f).exists():
#             raise FileNotFoundError(f"Missing HL7 sample: {f}")

#     metrics = run_benchmark("127.0.0.1", 2575, message_pool, duration_sec=300)

#     print("Messages sent:", metrics["sent"])
#     print("ACK latencies (ms):", [round(x * 1000, 2) for x in metrics["ack_latencies"][:10]], "...")
#     print("Errors:", metrics["errors"])