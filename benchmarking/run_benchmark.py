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

    # Outsourced Benchmark Summary into run_benchmark()
    # print("\n--- Benchmark Summary ---")
    # print(f"Messages sent: {metrics['sent']}")
    # print(f"ACK latencies (ms): {[round(x * 1000, 2) for x in metrics['ack_latencies'][:10]]} ...")
    # print(f"Connection times (ms): {[round(x * 1000, 2) for x in metrics['connection_times'][:10]]} ...")
    # print(f"Errors: {metrics['errors']}")

if __name__ == "__main__":
    main()