import argparse
import json
from pathlib import Path
from datetime import datetime
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

def export_results_json(metrics, duration_sec, output_path=None):
    # Build a structured result object
    result = {
        "timestamp": datetime.now().isoformat(),
        "duration_sec": duration_sec,
        "sent": metrics["sent"],
        "conn_failures": metrics["conn_failures"],
        "ack_failures": metrics["ack_failures"],
        "error_types": list(metrics["error_types"]),
        "ack_latencies_ms": [x * 1000 for x in metrics["ack_latencies"]],
        "connection_times_ms": [x * 1000 for x in metrics["connection_times"]],
    }

    # Default filename if none provided
    if output_path is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(__file__).parent / "results" / f"run_{ts}.json"

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nJSON results saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="HL7 MLLP Benchmark Runner")
    parser.add_argument("--host", default="127.0.0.1", help="MLLP server host")
    parser.add_argument("--port", type=int, default=2575, help="MLLP server port")
    parser.add_argument("--duration", type=int, default=300, help="Benchmark duration in seconds")
    
    parser.add_argument("--warmup", type=int, default=5,
                    help="Warm-up duration in seconds (default: 5)")
    
    parser.add_argument("--json-out", type=str, default=None,
                        help="Optional path to save JSON results")

    args = parser.parse_args()

    message_pool = load_messages()

    print(f"Starting benchmark for {args.duration} seconds...")
    print(f"Target: {args.host}:{args.port}")
    print(f"Loaded {len(message_pool)} HL7 message templates.")

    metrics = run_benchmark(
        host=args.host,
        port=args.port,
        message_pool=message_pool,
        duration_sec=args.duration,
        warmup=args.warmup,
    )

    if args.json_out is not None:
        export_results_json(metrics, args.duration, args.json_out)
    else:
        export_results_json(metrics, args.duration)

if __name__ == "__main__":
    main()