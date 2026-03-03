# tests/test_02_mllp.py
import socket
import time
import os
from pathlib import Path

from hl7apy.parser import parse_message
from hl7engine.hl7_listener import normalize_version, normalize_hl7
import requests

HOST = "localhost"
PORT = 2575

BASE = Path.cwd() # Do NOT use 'Path(__file__).resolve().parent.parent' since pytest rewrites test files and runs them from different location (temp cache dir)
SAMPLES = BASE / "samples"  # put your .hl7 files here
ROUTED = BASE / "routed"


def send_hl7_message(raw_hl7: str, delay_chunks=None):
    """Send one HL7 message over MLLP, optionally fragmented."""
    msg = raw_hl7.replace("\n", "\r")
    framed = b"\x0b" + msg.encode() + b"\x1c\x0d"

    s = socket.socket()
    s.connect((HOST, PORT))

    if delay_chunks:
        # send in chunks with delays (fragmentation test)
        start = 0
        for size, delay in delay_chunks:
            end = start + size
            s.sendall(framed[start:end])
            start = end
            time.sleep(delay)
        if start < len(framed):
            s.sendall(framed[start:])
    else:
        s.sendall(framed)

    s.settimeout(2.0)
    ack = s.recv(4096)
    s.close()
    return ack

def wait_for_new_file(before, timeout=3.0):
    start = time.time()
    while time.time() - start < timeout:
        after = set(list_routed())
        new = after - before
        if new:
            return new
        time.sleep(0.05)
    return set()

def read_sample(name: str) -> str:
    return (SAMPLES / name).read_text()


def list_routed():
    if not ROUTED.exists():
        return []
    return [p for p in ROUTED.rglob("*.hl7")]


def test_single_oru():
    print("TEST ROUTED DIR:", ROUTED)
    print("EXISTS:", ROUTED.exists())

    before = set(list_routed())
    raw = read_sample("sample_oru_glucose.hl7")

    ack = send_hl7_message(raw)

    new_files = wait_for_new_file(before, timeout=4.0)

    assert new_files, "No routed file created for ORU"
    assert b"MSA|AA|" in ack, "ACK does not contain MSA AA segment"


def test_multiple_messages_one_connection():
    before = set(list_routed())
    raw1 = read_sample("sample_adt_a01.hl7")
    raw2 = read_sample("sample_oru_glucose.hl7")

    msg1 = raw1.replace("\n", "\r")
    msg2 = raw2.replace("\n", "\r")

    framed = (
        b"\x0b" + msg1.encode() + b"\x1c\x0d" +
        b"\x0b" + msg2.encode() + b"\x1c\x0d"
    )

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(framed)

    s.settimeout(2.0)
    ack1 = s.recv(4096)
    ack2 = s.recv(4096)
    s.close()

    time.sleep(0.5)
    after = set(list_routed())
    new_files = after - before

    assert len(new_files) >= 2, "Expected at least 2 routed files"
    assert b"MSA|AA|" in ack1 and b"MSA|AA|" in ack2


def test_fragmented_message():
    before = set(list_routed())
    raw = read_sample("sample_oru_glucose.hl7")

    # send in small chunks with delays
    ack = send_hl7_message(
        raw,
        delay_chunks=[
            (10, 0.1),
            (15, 0.1),
            (20, 0.1),
        ],
    )

    time.sleep(0.5)
    after = set(list_routed())
    new_files = after - before

    assert new_files, "No routed file created for fragmented ORU"
    assert b"MSA|AA|" in ack


def test_invalid_message_skipped():
    before = set(list_routed())

    invalid = "FOO|bar|baz\r"
    ack = send_hl7_message(invalid)

    time.sleep(0.5)
    after = set(list_routed())
    new_files = after - before

    # We still send an ACK (UNKNOWN), but no routing should happen
    assert not new_files, "Invalid message should not be routed"
    assert b"MSA|AE|" in ack  # ACK with UNKNOWN control ID is still fine

def test_multiple_patients():
    before = set(list_routed())

    patients = [
        "sample_oru_glucose_anna.hl7",
        "sample_oru_hb_peter.hl7",
        "sample_adt_a01_lisa.hl7",
        "sample_adt_a01_markus.hl7"
    ]

    for fname in patients:
        raw = read_sample(fname)
        send_hl7_message(raw)
        time.sleep(0.1)

    after = set(list_routed())
    new_files = after - before

    assert len(new_files) >= 4, "Expected at least 4 routed messages"

    # Now test patient search
    for pid in ["A12345", "P99887", "L55667", "M77777"]:
        res = requests.get(f"http://localhost:8000/patients/{pid}/messages")
        assert res.status_code == 200
        assert len(res.json()) >= 1, f"No messages found for patient {pid}"