# HL7 advanced listener including:
# - MLLP frame splitting (handled by caller / extractor)
# - MSG routing
# - JSON logging
# - SQLite DB Message Storage
# - Field, Component and Subcomponent support
#
# 2026-Mar-01 (revised with HL7 v2.3 → v2.3.1 normalization)
# 2026-Mar-07 (refactored for fast & slow track to handle early ACKs)

from hl7apy.parser import parse_message
from hl7apy.exceptions import HL7apyException

from hl7engine.persistence.db import init_db
from hl7engine.validator import YAMLValidator
from hl7engine.workers.slow_worker import slow_processing_phase
from hl7engine.utils.ack_utils import build_ack_from_msg, build_ack_simple

from hl7engine.metrics.metrics import metrics

validator = YAMLValidator("validation.yaml")
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
        metrics.inc("invalid_frame")
        ack = build_ack_simple("UNKNOWN", "AE", "Empty HL7 frame")
        # Prometheus metric names cannot contain dots
        sender_ip_prometheus = sender_ip.replace(".", "_")
        metrics.inc(f"sender_messages_total_{sender_ip_prometheus}")
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
        metrics.inc("invalid_frame")
        ack = build_ack_simple("UNKNOWN", "AE", "Invalid HL7 message")
        # Prometheus metric names cannot contain dots
        sender_ip_prometheus = sender_ip.replace(".", "_")
        metrics.inc(f"sender_messages_total_{sender_ip_prometheus}")
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
    facility = "UNKNOWN"
    ack_code = "AE"
    error_text = None

    try:
        # Parse
        msg = parse_message(raw_hl7_norm, find_groups=False)

        # Extract metadata
        try:
            metrics.inc("parse_success")
            patient_id = msg.pid.pid_3.to_er7().split("^")[0]
            facility = msg.msh.msh_4.value
            # Prometheus metric names cannot contain dots
            facility_prometheus = facility.replace(".", "_")
            metrics.inc(f"facility_messages_total_{facility_prometheus}")
        except Exception:
            # Prometheus metric names cannot contain dots
            sender_ip_prometheus = sender_ip.replace(".", "_")
            facility_prometheus = facility.replace(".", "_")
            metrics.inc("parse_failure")
            metrics.inc(f"sender_parse_failure_{sender_ip_prometheus}")
            metrics.inc(f"facility_parse_failure_{facility_prometheus}")
            patient_id = None

        try:
            control_id = msg.msh.msh_10.value or "UNKNOWN"
        except Exception:
            control_id = "UNKNOWN"

        try:
            msg_type = msg.msh.msh_9.msh_9_1.value or "UNKNOWN"
            trigger_event = msg.msh.msh_9.msh_9_2.value or None
            
            if msg_type:
                metrics.inc(f"msg_type_{msg_type}")

            if trigger_event:
                metrics.inc(f"trigger_event_{trigger_event}")
        except Exception:
            msg_type = "UNKNOWN"
            trigger_event = None

        # VALIDATION
        ack_code, error_text = validator.validate(msg)
        metrics.inc(f"validation_{ack_code}")
        if ack_code != "AA":
            # Prometheus metric names cannot contain dots
            sender_ip_prometheus = sender_ip.replace(".", "_")
            facility_prometheus = facility.replace(".", "_")
            metrics.inc(f"sender_validation_failure_{sender_ip_prometheus}")
            metrics.inc(f"facility_validation_failure_{facility_prometheus}")

    except Exception as e:
        # Parsing error → fallback ACK
        ack = build_ack_simple("UNKNOWN", "AE", f"Parsing error: {e}")
        # Prometheus metric names cannot contain dots
        sender_ip_prometheus = sender_ip.replace(".", "_")
        metrics.inc(f"sender_validation_failure_{sender_ip_prometheus}")
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
            "facility_ip": facility,
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
        "facility_ip": facility,
    }

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