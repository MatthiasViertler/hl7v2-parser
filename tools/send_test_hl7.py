import time
import socket
import argparse
from concurrent.futures import ThreadPoolExecutor

HL7 = (
    "MSH|^~\\&|TEST|LAB|ENGINE|HL7|202501010101||ADT^A01|MSG00001|P|2.5\r"
    "PID|1||123456^^^HOSP^MR||DOE^JOHN\r"
)

HOST = "localhost"
PORT = 2575  # your MLLP port

def send_hl7(msg):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(b"\x0b" + msg.encode() + b"\x1c\x0d")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=20)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--concurrency", type=int, default=1)
    args = parser.parse_args()

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for _ in range(args.count):
            pool.submit(send_hl7, HL7)
            time.sleep(args.delay)

if __name__ == "__main__":
    main()