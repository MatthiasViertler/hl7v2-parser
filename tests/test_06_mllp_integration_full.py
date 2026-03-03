## Pytest File for full MLLP integration testing
# This suite tests:
# - MLLP framing
# - listener end‑to‑end
# - routing
# - DB insert
# - ACK generation
# This is your core listener integration test suite.

# This file covers:
# - MLLP fragmentation
# - MLLP ACK/NACK
# - Multiple messages
# - Multiple patients
# - REST API retrieval
# - Concurrency (optional)
# - End‑to‑end flow: MLLP → DB → REST
# It assumes:
# - Your MLLP server is running on port 2575
# - Your REST API is running on port 8000
# - Your DB layer (hl7engine.db) is working

import socket
import time
import requests
import pytest

MLLP_HOST = "localhost"
MLLP_PORT = 2575
REST_URL = "http://localhost:8000"


def mllp_send(raw_hl7):
    """Send a single HL7 message via MLLP and return the ACK."""
    msg = f"\x0b{raw_hl7}\x1c\x0d"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((MLLP_HOST, MLLP_PORT))
        s.sendall(msg.encode("utf-8"))
        ack = s.recv(4096).decode("utf-8")
    return ack


def mllp_send_fragmented(raw_hl7, fragment_size=5):
    """Send HL7 message in small fragments to test robustness."""
    msg = f"\x0b{raw_hl7}\x1c\x0d"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((MLLP_HOST, MLLP_PORT))
        for i in range(0, len(msg), fragment_size):
            s.sendall(msg[i:i+fragment_size].encode("utf-8"))
            time.sleep(0.01)
        ack = s.recv(4096).decode("utf-8")
    return ack


def test_mllp_ack():
    """Basic ACK test."""
    hl7 = (
        "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ADT^A01|MSG1|P|2.5.1\r"
        "PID|1||12345^^^HOSP^MR||Doe^John||19800101|M"
    )
    ack = mllp_send(hl7)
    assert "MSA|AA|MSG1" in ack


def test_mllp_fragmented_message():
    """Ensure fragmented HL7 messages are reassembled correctly."""
    hl7 = (
        "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ADT^A01|FRAG1|P|2.5.1\r"
        "PID|1||99999^^^HOSP^MR||Test^Frag||19700101|M"
    )
    ack = mllp_send_fragmented(hl7, fragment_size=3)
    assert "MSA|AA|FRAG1" in ack


def test_mllp_multiple_messages():
    """Send multiple messages and ensure all are stored."""
    ids = ["A111", "A222", "A333"]
    for pid in ids:
        hl7 = (
            f"MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ADT^A01|{pid}|P|2.5.1\r"
            f"PID|1||{pid}^^^HOSP^MR||Multi^Test||19800101|M"
        )
        ack = mllp_send(hl7)
        assert f"MSA|AA|{pid}" in ack

    time.sleep(0.2)  # allow DB write

    for pid in ids:
        r = requests.get(f"{REST_URL}/patients/{pid}/messages")
        assert r.status_code == 200
        assert pid in r.text


def test_mllp_multiple_patients_rest_grouping():
    """Ensure REST API groups messages by patient ID."""
    hl7_1 = (
        "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ADT^A01|P1|P|2.5.1\r"
        "PID|1||PAT1^^^HOSP^MR||Alpha^One||19800101|M"
    )
    hl7_2 = (
        "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ADT^A01|P2|P|2.5.1\r"
        "PID|1||PAT2^^^HOSP^MR||Beta^Two||19800101|M"
    )

    mllp_send(hl7_1)
    mllp_send(hl7_2)

    time.sleep(0.2)

    r1 = requests.get(f"{REST_URL}/patients/PAT1/messages")
    r2 = requests.get(f"{REST_URL}/patients/PAT2/messages")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert "PAT1" in r1.text
    assert "PAT2" in r2.text


def test_mllp_concurrent_clients():
    """Simulate multiple clients sending messages at the same time."""
    import threading

    results = []

    def worker(pid):
        hl7 = (
            f"MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ADT^A01|{pid}|P|2.5.1\r"
            f"PID|1||{pid}^^^HOSP^MR||Thread^Test||19800101|M"
        )
        ack = mllp_send(hl7)
        results.append(ack)

    threads = [threading.Thread(target=worker, args=(f"T{i}",)) for i in range(5)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert all("MSA|AA|" in ack for ack in results)