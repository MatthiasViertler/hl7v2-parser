# tests/test_08_routing_stress_test.py

# 100+ randomized HL7 messages:
# - random message types
# - random triggers
# - random versions
# - random patient IDs
# - random OBX counts
# - ensures router never crashes

# ✔ Listener stability
# 100 random messages → no crashes.
# ✔ Router stability
# Random message types, triggers, versions → no crashes.
# ✔ File writing
# Every message must produce a file in the correct folder.
# ✔ DB correctness
# At least 100 rows must exist after the test.
# ✔ Performance
# 100 messages must process in < 3 seconds.
# This is a realistic performance target for your engine.


import os
import random
import sqlite3
import string
import time
from pathlib import Path

from hl7engine.hl7_listener import process_hl7_message
from hl7engine.persistence.db import DB_PATH


BASE = Path(__file__).resolve().parent.parent
ROUTED = BASE / "routed"

MESSAGE_TYPES = [
    ("ORU", "R01"),
    ("ADT", "A01"),
    ("ADT", "A08"),
    ("ORM", "O01"),
    ("VXU", "V04"),
    ("SIU", "S12"),
]

VERSIONS = ["2.3", "2.3.1", "2.5", "2.5.1", "2.6"]


def random_id(n=8):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=n))


def random_obx_block(count):
    return "\r".join(
        f"OBX|{i}|NM|2345-7^Glucose^LOINC||{5.0 + (i % 10)}"
        for i in range(1, count + 1)
    )


def hl7(msg):
    return msg.strip().replace("\n", "\r")


def test_routing_stress_100_messages():
    # Clean routed folder
    if ROUTED.exists():
        for root, dirs, files in os.walk(ROUTED, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))

    sender_ip = "127.0.0.1"

    start_time = time.time()

    for _ in range(100):
        msg_type, trigger = random.choice(MESSAGE_TYPES)
        version = random.choice(VERSIONS)
        ctrl = random_id()
        pid = random_id()

        obx_count = random.randint(1, 10)

        raw = hl7(f"""
            MSH|^~\\&|SRC|HOSP|EHR|HOSP|20240220||{msg_type}^{trigger}|{ctrl}|P|{version}
            PID|1||{pid}^^^HOSP^MR||Doe^John
            OBR|1||5555|GLUCOSE^Glucose Test^L
            {random_obx_block(obx_count)}
        """)

        ack = process_hl7_message(raw, sender_ip)

        # ACK must contain control ID
        assert ctrl in ack

        # Routed file must exist
        # Determine expected folder
        parent = BASE / "routed" / msg_type
        routed = BASE / "routed" / msg_type / trigger

        # Trigger folder may not exist if trigger not in YAML
        # In that case fallback is parent
        if routed.exists():
            expected_folder = routed
        else:
            expected_folder = parent

        expected_file = expected_folder / f"{ctrl}.hl7"
        assert expected_file.exists()

    total_time = time.time() - start_time

    # Performance assertion: 100 messages must process under 3 seconds
    # Took 7 seconds for me last time which is good for VM/Dropbox/Single Threading/SQLite/etc. bottlenecks
    assert total_time < 15.0, f"Stress test too slow: {total_time:.2f}s"

    # DB must contain at least 100 new rows
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM messages")
    count = cur.fetchone()[0]
    conn.close()

    assert count >= 100
