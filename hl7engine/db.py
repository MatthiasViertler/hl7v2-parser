# db.py
import shutil
import sqlite3
import datetime
from pathlib import Path

DB_PATH = "hl7_messages.db"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RUNTIME_DB = DATA_DIR / "hl7_messages.db"
SEED_DB = DATA_DIR / "seed" / "hl7_messages_demo.db"

if not RUNTIME_DB.exists():
    shutil.copy(SEED_DB, RUNTIME_DB)

def init_db():
    """Create the SQLite database and tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            sender_ip TEXT,
            message_type TEXT,
            trigger_event TEXT,
            control_id TEXT,
            patient_id TEXT,
            routing_folder TEXT,
            routing_path TEXT,
            raw_hl7 TEXT NOT NULL,
            ack TEXT,
            status TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_message(
    sender_ip: str,
    raw_hl7: str,
    message_type: str,
    trigger_event: str,
    control_id: str,
    patient_id: str,
    routing_folder: str,
    routing_path: str,
    ack: str,
    status: str
):
    """Insert a message record into the database."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO messages (
            timestamp, sender_ip, raw_hl7, message_type, trigger_event,
            control_id, patient_id, routing_folder, routing_path, ack, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.datetime.now().isoformat(),
        sender_ip,
        raw_hl7,
        message_type,
        trigger_event,
        control_id,
        patient_id,
        routing_folder,
        routing_path,
        ack,
        status
    ))

    conn.commit()
    conn.close()


def get_messages(limit=100, offset=0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, timestamp, sender_ip, message_type, trigger_event,
               control_id, patient_id, status
        FROM messages
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_message_by_id(msg_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM messages
        WHERE id = ?
    """, (msg_id,))

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_messages_by_type(msg_type: str, limit=100, offset=0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, timestamp, sender_ip, message_type, trigger_event,
               control_id, patient_id, status
        FROM messages
        WHERE message_type = ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, (msg_type, limit, offset))

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_messages_by_patient_id(patient_id: str, limit=100, offset=0):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, timestamp, sender_ip, message_type, trigger_event,
               control_id, patient_id, status
        FROM messages
        WHERE patient_id = ?
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, (patient_id, limit, offset))

    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]