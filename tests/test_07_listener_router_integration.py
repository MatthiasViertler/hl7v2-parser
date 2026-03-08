# tests/test_07_listener_router_integration.py

# End‑to‑end test without MLLP, verifying:
# - parser → validator → router → DB → ACK
# - correct folder + routed_path
# - correct logging
# - correct ACK codes

# End‑to‑end Listener‑Test (w/o MLLP), incl:
# - normalize_hl7
# - normalize_version
# - parse_message
# - validator
# - router
# - file writing
# - DB insert
# - ACK generation
# - Assertions für:
# - routing_folder
# - routing_path
# - file existence
# - file content
# - DB row correctness

import os
import sqlite3
import time
from pathlib import Path

from hl7engine.hl7_listener import process_hl7_message
from hl7engine.persistence.db import DB_PATH


BASE = Path(__file__).resolve().parent.parent
ROUTED = BASE / "routed"


def hl7(s):
    return s.strip().replace("\n", "\r")


def test_listener_router_integration_oru_r01():
    # Clean routed folder
    if ROUTED.exists():
        for root, dirs, files in os.walk(ROUTED, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))

    raw = hl7("""
        MSH|^~\\&|LAB|HOSP|EHR|HOSP|20240220||ORU^R01|CTRL123|P|2.5.1
        PID|1||12345^^^HOSP^MR||Doe^John
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8
    """)

    sender_ip = "127.0.0.1"

    ack = process_hl7_message(raw, sender_ip)

    # ACK must contain control ID
    assert "CTRL123" in ack
    assert "MSA|AA|CTRL123" in ack

    # Routed file must exist
    routed_path = BASE / "routed" / "ORU" / "R01" / "CTRL123.hl7"
    assert routed_path.exists()

    # File content must match normalized HL7
    with open(routed_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "ORU^R01" in content
    assert "CTRL123" in content

    # DB must contain the record
    time.sleep(0.1)  # small delay for SQLite write

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT message_type, trigger_event, control_id, routing_folder, routing_path FROM messages WHERE control_id = ?", ("CTRL123",))
    row = cur.fetchone()
    conn.close()

    assert row is not None
    msg_type, trigger, folder, path = row[0], row[1], row[3], row[4]

    assert msg_type == "ORU"
    assert trigger == "R01"
    assert folder == "routed/ORU"
    assert path == "routed/ORU/R01"
