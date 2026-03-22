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

MLLP_START = b"\x0b"
MLLP_END = b"\x1c\x0d"

BASE = Path.cwd() # Do NOT use 'Path(__file__).resolve().parent.parent' since pytest rewrites test files and runs them from different location (temp cache dir)
SAMPLES = BASE / "samples"  # put your .hl7 files here
ROUTED = BASE / "routed"


def send_mllp_frame(host: str, port: int, framed: bytes) -> bytes:
    """Low-level MLLP sender. Sends a fully framed HL7 message."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.sendall(framed)
    s.settimeout(2.0)
    data = s.recv(4096)
    s.close()
    return data


def send_hl7_message(raw_hl7: str, delay_chunks=None) -> bytes:
    """
    High-level HL7 sender.
    - Normalizes line endings
    - Applies MLLP framing
    - Supports optional fragmentation
    """
    msg = raw_hl7.replace("\n", "\r").encode()
    framed = MLLP_START + msg + MLLP_END

    s = socket.socket()
    s.connect((HOST, PORT))

    if delay_chunks:
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


def send_multiple_hl7_messages(raw_messages: list[str]) -> tuple[bytes, bytes]:
    """
    Sends multiple HL7 messages in a single MLLP connection.
    Returns the ACKs in order.
    """
    framed = b"".join(
        MLLP_START + raw.replace("\n", "\r").encode() + MLLP_END
        for raw in raw_messages
    )

    s = socket.socket()
    s.connect((HOST, PORT))
    s.sendall(framed)

    s.settimeout(2.0)
    ack1 = s.recv(4096)
    ack2 = s.recv(4096)
    s.close()

    return ack1, ack2

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

    ack1, ack2 = send_multiple_hl7_messages([raw1, raw2])

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


def test_mllp_invalid_message_increments_metric():
    """
    Sends an invalid HL7 message via MLLP.
    Expects:
    - NACK returned (AE or AR)
    - parser_parse_errors_total incremented
    """

    invalid_msg = "FOO|bar|baz\r"

    # Send invalid HL7
    ack = send_hl7_message(invalid_msg)

    # ACK must be a NACK (AE or AR)
    assert b"MSA" in ack
    assert b"AE" in ack or b"AR" in ack

    # Give Prometheus client a moment to flush
    time.sleep(0.2)

    # Check metrics
    metrics = requests.get("http://localhost:8010/metrics").text
    assert "parser_parse_errors_total" in metrics

def test_mllp_validation_error_increments_metric():
    """
    Sends a syntactically valid HL7 message that fails YAML validation.
    Expects:
    - NACK returned (AE or AR)
    - parser_validation_errors_total incremented
    """

    raw = (
        "MSH|^~\\&|LAB|HOSP|EHR|HOSP|20240220||ORU^R01|X99|P|2.5.1\r"
        "PID|1|||\r"
    )

    ack = send_hl7_message(raw)

    # ACK must be a validation NACK
    assert b"MSA" in ack
    assert b"AE" in ack or b"AR" in ack

    # Give Prometheus client a moment to flush
    time.sleep(0.2)

    metrics = requests.get("http://localhost:8010/metrics").text
    assert "parser_validation_errors_total" in metrics

def test_mllp_unknown_message_type_increments_router_error():
    """
    Sends a syntactically valid HL7 message with an unknown message type.
    Expects:
    - router_routing_errors_total incremented
    - message routed to UNKNOWN folder
    """

    raw = (
        "MSH|^~\\&|LAB|HOSP|EHR|HOSP|20240220||ZZZ^Z01|X404|P|2.5.1\r"
        "PID|1||12345^^^HOSP^MR\r"
    )

    before = set(list_routed())

    ack = send_hl7_message(raw)

    # ACK should still be AA (validation passes)
    assert b"MSA|AA|" in ack

    time.sleep(0.3)

    metrics = requests.get("http://localhost:8010/metrics").text
    assert "router_routing_errors_total" in metrics

    after = set(list_routed())
    new_files = after - before

    # Should be routed to UNKNOWN folder
    assert any("UNKNOWN" in str(p) for p in new_files)