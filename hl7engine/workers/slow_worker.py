# hl7engine/workers/slow_worker.py

import os

from hl7engine.router import Router

from hl7engine.persistence.db import insert_message
from hl7engine.utils.json_logger import log_event

from hl7engine.utils.ack_utils import build_ack_simple

router = Router("routes.yaml")

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