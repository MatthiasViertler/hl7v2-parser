# HL7 advanced listener including:
# - MLLP frame splitting (handled by caller / extractor)
# - MSG routing
# - JSON logging
# - SQLite DB Message Storage
# - Field, Component and Subcomponent support
#
# 2026-Mar-01 (revised with HL7 v2.3 → v2.3.1 normalization)

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


def process_hl7_message(raw_hl7: str, sender_ip: str) -> str:
    """
    Core HL7 processing:
    - normalize line endings
    - normalize version (2.3 → 2.3.1)
    - parse
    - validate
    - route
    - log
    - DB insert
    - return ACK string (no MLLP framing)
    """
    raw_hl7 = normalize_hl7(raw_hl7)

    # Empty frame
    if not raw_hl7.strip():
        print("Empty HL7 frame received — ignoring.")
        log_event({
            "sender": sender_ip,
            "raw_hl7": "",
            "status": "empty_frame",
            "ack_sent": False
        })
        ack = build_ack_simple("UNKNOWN", "AE", "Empty HL7 frame")
        insert_message(
            sender_ip=sender_ip,
            raw_hl7="",
            message_type=None,
            trigger_event=None,
            control_id=None,
            patient_id=None,
            routing_folder=None,
            routing_path=None,
            ack=ack,
            status="empty_frame"
        )
        return ack

    # Not starting with MSH
    if not raw_hl7.startswith("MSH"):
        print("Invalid HL7 message, skipping:", repr(raw_hl7[:80]))
        ack = build_ack_simple("UNKNOWN", "AE", "Invalid HL7 message")
        log_event({
            "sender": sender_ip,
            "raw_hl7": raw_hl7,
            "message_type": None,
            "trigger_event": None,
            "control_id": "UNKNOWN",
            "routing_folder": None,
            "ack_sent": True,
            "status": "invalid"
        })
        insert_message(
            sender_ip=sender_ip,
            raw_hl7=raw_hl7,
            message_type=None,
            trigger_event=None,
            control_id="UNKNOWN",
            patient_id=None,
            routing_folder=None,
            routing_path=None,
            ack=ack,
            status="invalid"
        )
        return ack

    # Pretty-print incoming message
    print("\n--- Received HL7 Message ---")
    for line in raw_hl7.split("\r"):
        if line:
            print(line)
    print("----------------------------\n")

    # Normalize version (2.3 → 2.3.1)
    raw_hl7_norm = normalize_version(raw_hl7)

    msg = None
    msg_type = "UNKNOWN"
    trigger_event = None
    control_id = "UNKNOWN"
    patient_id = None
    folder = None
    routed_path = None
    ack_code = "AE"
    error_text = None
    ack = None

    try:
        # 1) Parse HL7
        print("hl7_listener::ParseHL7 - Prior Call")
        msg = parse_message(raw_hl7_norm, find_groups=False)
        print("hl7_listener::ParseHL7 - Post Call")

        # 2) Extract metadata
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

        # 3) VALIDATION
        ack_code, error_text = validator.validate(msg)
        print(f"[VALIDATION] Result: {ack_code} ({error_text})")

        # 4a) ROUTING (YAML)
        print(f"[ROUTER] Routing {msg_type} ...")
        folder, routed_path = router.route(msg_type, raw_hl7_norm)
        print(f"[ROUTER] Parent folder: {folder}")
        print(f"[ROUTER] Routed path: {routed_path}")
        
        # 4b) WRITE ROUTED HL7 MESSAGE TO FILE
        try:
            # Ensure target directory exists (robust even if router already creates it)
            os.makedirs(routed_path, exist_ok=True)

            # Filename: CONTROLID.hl7 (fallback if missing)
            fname = f"{control_id or 'UNKNOWN'}.hl7"
            full_path = os.path.join(routed_path, fname)
            print(">>> Writing file:", full_path)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(raw_hl7_norm)
                print(">>> FLUSHING FILE NOW")
                f.flush()
                os.fsync(f.fileno())
            
            print(f"[ROUTER] Message written to file: {full_path}")

        except Exception as e:
            print(f"[ROUTER] ERROR writing routed file: {e}")

        # 5) LOGGING (parsed)
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
            "status": "parsed" if msg else "invalid"
        })

    except HL7apyException as e:
        print("HL7apy parsing error:", e)

        msg_type = "UNKNOWN"
        trigger_event = None
        control_id = "UNKNOWN"

        log_event({
            "sender": sender_ip,
            "raw_hl7": raw_hl7_norm,
            "error": str(e),
            "status": f"invalid - HL7apy parsing error: {e}"
        })

    except Exception as e:
        print("Unexpected parsing error:", e)

        msg_type = "UNKNOWN"
        trigger_event = None
        control_id = "UNKNOWN"

        log_event({
            "sender": sender_ip,
            "raw_hl7": raw_hl7_norm,
            "error": str(e),
            "status": f"invalid - Unexpected parsing error: {e}"
        })

    # ------------------------------------------------------------
    # ALWAYS SEND ACK (even on errors)
    # ------------------------------------------------------------
    if msg is not None:
        ack = build_ack_from_msg(msg, ack_code, error_text or "")
    else:
        ack = build_ack_simple(control_id, ack_code, error_text or "Error")

    print("ACK sent (pretty):")
    print(ack.replace("\r", "\n"))
    print("ACK raw (no MLLP framing):", repr(ack))

    # Final logging with ACK
    log_event({
        "sender": sender_ip,
        "control_id": control_id,
        "ack": ack,
        "ack_sent": True,
        "status": ack_code
    })

    # Final DB insert (single, consolidated record)
    print(">>> Inserting DB row for:", control_id)
    insert_message(
        sender_ip=sender_ip,
        raw_hl7=raw_hl7_norm,
        message_type=msg_type,
        trigger_event=trigger_event,
        control_id=control_id,
        patient_id=patient_id,
        routing_folder=folder,
        routing_path=routed_path,
        ack=ack,
        status=ack_code
    )

    return ack
