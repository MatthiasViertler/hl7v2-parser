# hl7engine/hl7_listener.py

# HL7 advanced listener including:
# - MLLP frame splitting (handled by caller / extractor)
# - MSG routing
# - JSON logging
# - SQLite DB Message Storage
# - Field, Component and Subcomponent support
#
# 2026-Mar-01: revised with HL7 v2.3 → v2.3.1 normalization
# 2026-Mar-07: refactored for fast & slow track to handle early ACKs
# 2026-Mar-11: refactored for low-cardinality metrics incl. labelling, cleaned parsing logic, improved predictability/readability

# hl7engine/hl7_listener.py

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
        msh[11] = "2.3.1"

    segments[0] = "|".join(msh)
    return "\r".join(segments)


# ------------------------------------------------------------
# FAST PHASE (parse + validate + build ACK)
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
        context (dict)
    """

    raw_hl7 = normalize_hl7(raw_hl7)

    # Empty frame
    if not raw_hl7.strip():
        metrics.inc("parser_parse_errors_total", labels={"error_code": "EMPTY"})
        ack = build_ack_simple("UNKNOWN", "AE", "Empty HL7 frame")
        return ack, {
            "raw_hl7_norm": "",
            "msg": None,
            "msg_type": None,
            "trigger_event": None,
            "control_id": None,
            "patient_id": None,
            "ack_code": "AE",
            "error_text": "Empty HL7 frame",
            "sender_ip": sender_ip,
        }

    # Invalid HL7 (no MSH)
    if not raw_hl7.startswith("MSH"):
        metrics.inc("parser_parse_errors_total", labels={"error_code": "NO_MSH"})
        ack = build_ack_simple("UNKNOWN", "AE", "Invalid HL7 message")
        return ack, {
            "raw_hl7_norm": raw_hl7,
            "msg": None,
            "msg_type": None,
            "trigger_event": None,
            "control_id": "UNKNOWN",
            "patient_id": None,
            "ack_code": "AE",
            "error_text": "Invalid HL7 message",
            "sender_ip": sender_ip,
        }

    raw_hl7_norm = normalize_version(raw_hl7)

    msg = None
    msg_type = "UNKNOWN"
    trigger_event = None
    control_id = "UNKNOWN"
    patient_id = None
    version = None

    try:
        # Parse
        msg = parse_message(raw_hl7_norm, find_groups=False)
        metrics.inc("parser_messages_parsed_total")

        # Extract version
        try:
            version = msg.msh.msh_12.value or "UNKNOWN"
            metrics.inc("parser_versions_total", labels={"version": version})
        except Exception:
            metrics.inc("parser_parse_errors_total", labels={"error_code": "VERSION"})
            version = "UNKNOWN"

        # Extract message type + trigger event
        try:
            msg_type = msg.msh.msh_9.msh_9_1.value or "UNKNOWN"
            trigger_event = msg.msh.msh_9.msh_9_2.value or None

            metrics.inc("parser_message_types_total", labels={"message_type": msg_type})
        except Exception:
            metrics.inc("parser_parse_errors_total", labels={"error_code": "MSH9"})
            msg_type = "UNKNOWN"
            trigger_event = None

        # Extract control ID
        try:
            control_id = msg.msh.msh_10.value or "UNKNOWN"
        except Exception:
            control_id = "UNKNOWN"

        # Extract patient ID (optional)
        try:
            patient_id = msg.pid.pid_3.to_er7().split("^")[0]
        except Exception:
            patient_id = None

        # VALIDATION
        ack_code, error_text = validator.validate(msg)

        if ack_code != "AA":
            metrics.inc(
                "parser_validation_errors_total",
                labels={"error_code": ack_code},
            )

    except Exception as e:
        # Parsing error → fallback ACK
        metrics.inc("parser_parse_errors_total", labels={"error_code": "PARSE"})
        ack = build_ack_simple("UNKNOWN", "AE", f"Parsing error: {e}")
        return ack, {
            "raw_hl7_norm": raw_hl7_norm,
            "msg": None,
            "msg_type": "UNKNOWN",
            "trigger_event": None,
            "control_id": "UNKNOWN",
            "patient_id": None,
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
        "ack_code": ack_code,
        "error_text": error_text,
        "sender_ip": sender_ip,
        "version": version,
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