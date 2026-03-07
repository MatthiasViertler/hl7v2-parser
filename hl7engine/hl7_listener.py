# HL7 advanced listener including:
# - MLLP frame splitting (handled by caller / extractor)
# - MSG routing
# - JSON logging
# - SQLite DB Message Storage
# - Field, Component and Subcomponent support
#
# 2026-Mar-01 (revised with HL7 v2.3 → v2.3.1 normalization)
# 2026-Mar-07 (refactored for fast & slow track to handle early ACKs)

import os
import datetime

from hl7apy.parser import parse_message
from hl7apy.exceptions import HL7apyException

from hl7engine.db import init_db, insert_message
from hl7engine.json_logger import log_event
from hl7engine.router import Router
from hl7engine.validator import YAMLValidator

validator = YAMLValidator("validation.yaml")
router = Router("routes.yaml")
init_db()

print(">>> USING hl7engine.hl7_listener FROM:", __file__)


# ------------------------------------------------------------
# NORMALIZATION HELPERS
# ------------------------------------------------------------

def normalize_hl7(raw: str) -> str:
    """Normalize line endings to HL7 standard (CR)."""
    return raw.replace("\r\n", "\r").replace("\n", "\r")


def normalize_version(raw_hl7: str) -> str:
    """
    Normalize HL7 version:
    - If MSH-12 is empty → set to 2.5
    - If MSH-12 is 2.3 → rewrite to 2.3.1 (hl7apy requirement)
    """
    segments = raw_hl7.split("\r")
    msh = segments[0].split("|")

    if len(msh) < 12:
        msh += [""] * (12 - len(msh))

    version = msh[11].strip()

    if not version:
        version = "2.5"
        msh[11] = version

    if version == "2.3":
        print("Normalizing HL7 version 2.3 → 2.3.1 for hl7apy compatibility")
        msh[11] = "2.3.1"

    segments[0] = "|".join(msh)
    return "\r".join(segments)


# ------------------------------------------------------------
# ACK BUILDERS
# ------------------------------------------------------------

def build_ack_from_msg(original_msg, code="AA", text="OK") -> str:
    """Build ACK using fields from the original message."""
    msh = original_msg.msh
    control_id = msh.msh_10.value or "UNKNOWN"

    ack = (
        f"MSH|^~\\&|{msh.msh_5.value}|{msh.msh_6.value}|"
        f"{msh.msh_3.value}|{msh.msh_4.value}|"
        f"{msh.msh_7.value}||ACK^{msh.msh_9.msh_9_2.value}|{control_id}|P|{msh.msh_12.value}\r"
        f"MSA|{code}|{control_id}|{text}\r"
    )
    return ack


def build_ack_simple(control_id: str, code="AA", text="OK") -> str:
    """Fallback ACK when we don't have a parsed message."""
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    ack = (
        f"MSH|^~\\&|RECEIVER|HOSP|SENDER|HOSP|{now}||ACK^A01|ACK{control_id}|P|2.5.1\r"
        f"MSA|{code}|{control_id}|{text}\r"
    )
    return ack


# ------------------------------------------------------------
# NEW: FAST PHASE (parse + validate + build ACK)
# ------------------------------------------------------------

def fast_ack_phase(raw_hl7: str, sender_ip: str):
    """
    FAST PHASE:
    - normalize
    - version fix
    - parse
    - extract metadata
    - validate
    - build ACK

    Returns:
        ack (str)
        context (dict) → used later for routing, DB, logging
    """

    raw_hl7 = normalize_hl7(raw_hl7)

    # Empty frame
    if not raw_hl7.strip():
        ack = build_ack_simple("UNKNOWN", "AE", "Empty HL7 frame")
        return ack, {
            "raw_hl7_norm": "",
            "msg": None,
            "msg_type": None,
            "trigger_event": None,
            "control_id": None,
            "patient_id": None,
            "folder": None,
            "routed_path": None,
            "ack_code": "AE",
            "error_text": "Empty HL7 frame",
            "sender_ip": sender_ip,
        }

    # Invalid HL7 (no MSH)
    if not raw_hl7.startswith("MSH"):
        ack = build_ack_simple("UNKNOWN", "AE", "Invalid HL7 message")
        return ack, {
            "raw_hl7_norm": raw_hl7,
            "msg": None,
            "msg_type": None,
            "trigger_event": None,
            "control_id": "UNKNOWN",
            "patient_id": None,
            "folder": None,
            "routed_path": None,
            "ack_code": "AE",
            "error_text": "Invalid HL7 message",
            "sender_ip": sender_ip,
        }

    # Pretty-print incoming message
    print("\n--- Received HL7 Message ---")
    for line in raw_hl7.split("\r"):
        if line:
            print(line)
    print("----------------------------\n")

    raw_hl7_norm = normalize_version(raw_hl7)

    msg = None
    msg_type = "UNKNOWN"
    trigger_event = None
    control_id = "UNKNOWN"
    patient_id = None
    ack_code = "AE"
    error_text = None

    try:
        # Parse
        msg = parse_message(raw_hl7_norm, find_groups=False)

        # Extract metadata
        try:
            patient_id = msg.pid.pid_3.to_er7().split("^")[0]
        except Exception:
            patient_id = None

        try:
            control_id = msg.msh.msh_10.value or "UNKNOWN"
        except Exception:
            control_id = "UNKNOWN"

        try:
            msg_type = msg.msh.msh_9.msh_9_1.value or "UNKNOWN"
            trigger_event = msg.msh.msh_9.msh_9_2.value or None
        except Exception:
            msg_type = "UNKNOWN"
            trigger_event = None

        # VALIDATION
        ack_code, error_text = validator.validate(msg)

    except Exception as e:
        # Parsing error → fallback ACK
        ack = build_ack_simple("UNKNOWN", "AE", f"Parsing error: {e}")
        return ack, {
            "raw_hl7_norm": raw_hl7_norm,
            "msg": None,
            "msg_type": "UNKNOWN",
            "trigger_event": None,
            "control_id": "UNKNOWN",
            "patient_id": None,
            "folder": None,
            "routed_path": None,
            "ack_code": "AE",
            "error_text": str(e),
            "sender_ip": sender_ip,
        }

    # Build ACK (fast)
    if msg is not None:
        ack = build_ack_from_msg(msg, ack_code, error_text or "")
    else:
        ack = build_ack_simple(control_id, ack_code, error_text or "Error")

    # Return ACK + context for slow phase
    return ack, {
        "raw_hl7_norm": raw_hl7_norm,
        "msg": msg,
        "msg_type": msg_type,
        "trigger_event": trigger_event,
        "control_id": control_id,
        "patient_id": patient_id,
        "folder": None,
        "routed_path": None,
        "ack_code": ack_code,
        "error_text": error_text,
        "sender_ip": sender_ip,
    }


# ------------------------------------------------------------
# NEW: SLOW PHASE (routing, file writing, DB insert, logging)
# ------------------------------------------------------------

def slow_processing_phase(ctx: dict):
    """
    SLOW PHASE:
    - routing
    - file writing
    - logging
    - DB insert

    This runs AFTER ACK is already sent.
    """

    raw_hl7_norm = ctx["raw_hl7_norm"]
    msg = ctx["msg"]
    msg_type = ctx["msg_type"]
    trigger_event = ctx["trigger_event"]
    control_id = ctx["control_id"]
    patient_id = ctx["patient_id"]
    sender_ip = ctx["sender_ip"]
    ack_code = ctx["ack_code"]
    error_text = ctx["error_text"]

    folder = None
    routed_path = None

    # ROUTING
    if msg is not None:
        try:
            folder, routed_path = router.route(msg_type, raw_hl7_norm)
            ctx["folder"] = folder
            ctx["routed_path"] = routed_path

            os.makedirs(routed_path, exist_ok=True)
            fname = f"{control_id or 'UNKNOWN'}.hl7"
            full_path = os.path.join(routed_path, fname)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(raw_hl7_norm)
                f.flush()
                os.fsync(f.fileno())

        except Exception as e:
            print(f"[ROUTER] ERROR writing routed file: {e}")

    # LOGGING
    log_event({
        "sender": sender_ip,
        "raw_hl7": raw_hl7_norm,
        "message_type": msg_type,
        "trigger_event": trigger_event,
        "control_id": control_id,
        "patient_id": patient_id,
        "routing_folder": folder,
        "routing_path": routed_path,
        "ack_sent": True,
        "status": ack_code,
    })

    # DB INSERT
    insert_message(
        sender_ip=sender_ip,
        raw_hl7=raw_hl7_norm,
        message_type=msg_type,
        trigger_event=trigger_event,
        control_id=control_id,
        patient_id=patient_id,
        routing_folder=folder,
        routing_path=routed_path,
        ack=build_ack_simple(control_id, ack_code, error_text or ""),
        status=ack_code,
    )


# ------------------------------------------------------------
# BACKWARD COMPATIBILITY: original API
# ------------------------------------------------------------

def process_hl7_message(raw_hl7: str, sender_ip: str) -> str:
    """
    Legacy API — preserved for compatibility.
    Performs BOTH fast and slow phases synchronously.
    """
    ack, ctx = fast_ack_phase(raw_hl7, sender_ip)
    slow_processing_phase(ctx)
    return ack