#!/usr/bin/env python3
import sqlite3
import shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
SEED = DATA / "seed"
RUNTIME_DB = DATA / "hl7_messages.db"
SEED_DB = SEED / "hl7_messages_demo.db"

NUM_DEMO_MESSAGES = 20   # <--- change this number anytime

## OPTION A) Generate NUM_DEMO_MESSAGES of demo messages:
def generate_demo_messages(n):
    messages = []
    for i in range(n):
        ctrl = f"CTRL{i:04d}"
        raw = (
            f"MSH|^~\\&|SRC|HOSP|EHR|HOSP|20240220||ORU^R01|{ctrl}|P|2.5.1\r"
            f"PID|1||{10000+i}^^^HOSP^MR||Doe^John\r"
            f"OBR|1||5555|GLUCOSE^Glucose Test^L\r"
            f"OBX|1|NM|2345-7^Glucose^LOINC||{5.0 + (i % 3)}|mmol/L"
        )
        messages.append((ctrl, "ORU", "R01", raw))
    return messages

DEMO_MESSAGES = generate_demo_messages(NUM_DEMO_MESSAGES)

## OPTION B) Generate a hard-coded set of 2 demo messages:
# DEMO_MESSAGES = [
#     (
#         "CTRL001",
#         "ORU",
#         "R01",
#         "MSH|^~\\&|SRC|HOSP|EHR|HOSP|20240220||ORU^R01|CTRL001|P|2.5.1\rPID|1||12345^^^HOSP^MR||Doe^John\rOBR|1||5555|GLUCOSE^Glucose Test^L\rOBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L",
#     ),
#     (
#         "CTRL002",
#         "ADT",
#         "A01",
#         "MSH|^~\\&|SRC|HOSP|EHR|HOSP|20240220||ADT^A01|CTRL002|P|2.3.1\rPID|1||67890^^^HOSP^MR||Smith^Jane",
#     ),
# ]

def main():
    SEED.mkdir(parents=True, exist_ok=True)

    if RUNTIME_DB.exists():
        RUNTIME_DB.unlink()

    conn = sqlite3.connect(RUNTIME_DB)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            control_id TEXT,
            msg_type TEXT,
            trigger TEXT,
            raw_hl7 TEXT,
            received_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.executemany(
        "INSERT INTO messages (control_id, msg_type, trigger, raw_hl7) VALUES (?, ?, ?, ?)",
        DEMO_MESSAGES,
    )

    conn.commit()
    conn.execute("VACUUM")
    conn.close()

    shutil.copy(RUNTIME_DB, SEED_DB)
    print(f"Seed DB regenerated → {SEED_DB}")

if __name__ == "__main__":
    main()