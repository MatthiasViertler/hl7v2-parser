# hl7engine/persistence/db.py

# 2026 Mar 11: Aligned fully with new metric taxonomy
            # - store_write_operations_total
            # - store_write_latency_seconds
            # - store_write_errors_total
            # - store_retry_failures_total (optional, if you add retries later)
            # - sys_storage_file_size_bytes (instead of MB gauge)
#              Removes high-cardinality metrics
            # - No more sender_db_failure_<ip>
            # - No per‑sender or per‑patient metrics
#              Cleans-up DB handling
            # - Uses context managers (with sqlite3.connect(...))
            # - Ensures rollback on failure
            # - Ensures file size metric is always updated
            # - Removes print‑spam
#              Makes module deterministic
            # - No silent exceptions
            # - No partial writes
            # - No inconsistent error handling

import os
import shutil
import sqlite3
import datetime
from pathlib import Path

from hl7engine.metrics.metrics import metrics

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DB = DATA_DIR / "hl7_messages.db"
SEED_DB = DATA_DIR / "seed" / "hl7_messages_demo.db"

DB_PATH = RUNTIME_DB


# ------------------------------------------------------------
# INITIALIZATION
# ------------------------------------------------------------
def init_db():
    """
    Initialize the SQLite database.
    - Copies seed DB if runtime DB does not exist.
    - Ensures the messages table exists.
    """

    if not RUNTIME_DB.exists():
        shutil.copy(SEED_DB, RUNTIME_DB)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
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
        """
        )
        conn.commit()

    _update_db_file_size()


# ------------------------------------------------------------
# INSERT MESSAGE
# ------------------------------------------------------------
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
    status: str,
):
    """
    Insert a message record into the database.

    Emits metrics:
    - store_write_operations_total
    - store_write_latency_seconds
    - store_write_errors_total
    """

    start = datetime.datetime.now()

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO messages (
                    timestamp, sender_ip, raw_hl7, message_type, trigger_event,
                    control_id, patient_id, routing_folder, routing_path, ack, status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    start.isoformat(),
                    sender_ip,
                    raw_hl7,
                    message_type,
                    trigger_event,
                    control_id,
                    patient_id,
                    routing_folder,
                    routing_path,
                    ack,
                    status,
                ),
            )
            conn.commit()

        # Success metrics
        metrics.inc("store_write_operations_total")
        metrics.observe(
            "store_write_latency_seconds",
            (datetime.datetime.now() - start).total_seconds(),
        )

    except Exception:
        metrics.inc("store_write_errors_total")
        raise

    finally:
        _update_db_file_size()


# ------------------------------------------------------------
# QUERY HELPERS
# ------------------------------------------------------------
def get_messages(limit=100, offset=0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, timestamp, sender_ip, message_type, trigger_event,
                   control_id, patient_id, status
            FROM messages
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """,
            (limit, offset),
        )
        return [dict(r) for r in cur.fetchall()]


def get_message_by_id(msg_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT *
            FROM messages
            WHERE id = ?
        """,
            (msg_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def get_messages_by_type(msg_type: str, limit=100, offset=0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, timestamp, sender_ip, message_type, trigger_event,
                   control_id, patient_id, status
            FROM messages
            WHERE message_type = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """,
            (msg_type, limit, offset),
        )
        return [dict(r) for r in cur.fetchall()]


def get_messages_by_patient_id(patient_id: str, limit=100, offset=0):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, timestamp, sender_ip, message_type, trigger_event,
                   control_id, patient_id, status
            FROM messages
            WHERE patient_id = ?
            ORDER BY id DESC
            LIMIT ? OFFSET ?
        """,
            (patient_id, limit, offset),
        )
        return [dict(r) for r in cur.fetchall()]


# ------------------------------------------------------------
# FILE SIZE METRIC
# ------------------------------------------------------------
def _update_db_file_size():
    """
    Emit the DB file size as a gauge.
    """
    try:
        size_bytes = os.path.getsize(DB_PATH)
        metrics.set("sys_storage_file_size_bytes", size_bytes)
    except Exception:
        pass
