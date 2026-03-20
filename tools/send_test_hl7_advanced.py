import time
import socket
import argparse
import random
from concurrent.futures import ThreadPoolExecutor
from statistics import median

HL7_VALID = (
    "MSH|^~\\&|TEST|LAB|ENGINE|HL7|202501010101||ADT^A01|MSG00001|P|2.5\r"
    "PID|1||123456^^^HOSP^MR||DOE^JOHN\r"
)

HL7_INVALID = (
    "MSH|^~\\&|BAD|LAB|ENGINE|HL7|202501010101||ADT^A01|MSG00001|P|2.5\r"
    "PID|BROKEN\r"
)

def send_hl7(msg, host, port):
    start = time.time()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((host, port))
        s.sendall(b"\x0b" + msg.encode() + b"\x1c\x0d")
        ack = s.recv(4096)
    end = time.time()
    return (end - start) * 1000  # ms

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2575)
    parser.add_argument("--rate", type=float, default=5)
    parser.add_argument("--count", type=int, default=None)
    parser.add_argument("--infinite", action="store_true")
    parser.add_argument("--malformed", type=float, default=0.0)
    parser.add_argument("--router-fail", type=float, default=0.0)
    parser.add_argument("--db-latency", type=int, default=0)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    latencies = []
    errors = 0
    sent = 0

    def worker():
        nonlocal sent, errors
        msg = HL7_INVALID if random.random() < args.malformed else HL7_VALID
        try:
            latency = send_hl7(msg, args.host, args.port)
            latencies.append(latency)
        except Exception:
            errors += 1
        sent += 1

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        while args.infinite or (args.count is None or sent < args.count):
            pool.submit(worker)
            time.sleep(1.0 / args.rate)

    if latencies:
        print(f"ACK p50: {median(latencies):.2f} ms")
        print(f"ACK p95: {sorted(latencies)[int(0.95 * len(latencies))]:.2f} ms")
        print(f"ACK p99: {sorted(latencies)[int(0.99 * len(latencies))]:.2f} ms")

    print(f"Messages sent: {sent}")
    print(f"Errors: {errors}")