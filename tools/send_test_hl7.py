# Generates 2 messages per second, enough to populate all Grafana dashboards.

import time
import socket

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

while True:
    send_hl7(HL7)
    time.sleep(0.5)
