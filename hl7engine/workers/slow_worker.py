# hl7engine/workers/slow_worker.py

# 2026 Mar 11: Converted all latencies to seconds, added taxonomy-aligned metrics:
            # - router_messages_routed_total{route="ADT"} (already emitted in router)
            # - store_write_operations_total
            # - store_write_latency_seconds
            # - store_write_errors_total
            # - proc_stage_duration_seconds{stage="routing"}
            # - proc_stage_duration_seconds{stage="file_write"}
            # - proc_stage_duration_seconds{stage="db_insert"}
            # - proc_stage_errors_total{stage="routing"}
            # - proc_stage_errors_total{stage="file_write"}
            # - proc_stage_errors_total{stage="db_insert"}
            #  improve robustness of routing + file writing + DB insert

import os
import time

from hl7engine.router import Router
from hl7engine.persistence.db import insert_message
from hl7engine.utils.json_logger import log_event
from hl7engine.utils.ack_utils import build_ack_simple

from hl7engine.metrics.metrics import metrics

router = Router("routes.yaml")


# ------------------------------------------------------------
# SLOW PHASE (routing, file writing, DB insert, logging)
# ------------------------------------------------------------
def slow_processing_phase(ctx: dict):
    """
    SLOW PHASE:
    - routing
    - file writing
    - logging
    - DB insert

    Runs AFTER ACK is already sent.
    """

    slow_start = time.time()

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

    # ------------------------------------------------------------
    # ROUTING
    # ------------------------------------------------------------
    routing_start = time.time()

    if msg is not None:
        try:
            folder, routed_path = router.route(msg_type, raw_hl7_norm)
            ctx["folder"] = folder
            ctx["routed_path"] = routed_path

            metrics.observe(
                "proc_stage_duration_seconds",
                time.time() - routing_start,
                labels={"stage": "routing"},
            )

        except Exception as e:
            metrics.inc(
                "proc_stage_errors_total",
                labels={"stage": "routing"},
            )
            # Continue slow phase even if routing fails
            folder = None
            routed_path = None

    # ------------------------------------------------------------
    # FILE WRITE
    # ------------------------------------------------------------
    if routed_path:
        file_start = time.time()
        try:
            os.makedirs(routed_path, exist_ok=True)
            fname = f"{control_id or 'UNKNOWN'}.hl7"
            full_path = os.path.join(routed_path, fname)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(raw_hl7_norm)
                f.flush()
                os.fsync(f.fileno())

            metrics.observe(
                "proc_stage_duration_seconds",
                time.time() - file_start,
                labels={"stage": "file_write"},
            )

        except Exception:
            metrics.inc(
                "proc_stage_errors_total",
                labels={"stage": "file_write"},
            )

    # ------------------------------------------------------------
    # LOGGING
    # ------------------------------------------------------------
    log_event(
        {
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
        }
    )

    # ------------------------------------------------------------
    # DB INSERT
    # ------------------------------------------------------------
    db_start = time.time()
    try:
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

        metrics.inc("store_write_operations_total")
        metrics.observe(
            "store_write_latency_seconds",
            time.time() - db_start,
        )

    except Exception:
        metrics.inc(
            "store_write_errors_total",
        )
        metrics.inc(
            "proc_stage_errors_total",
            labels={"stage": "db_insert"},
        )

    # ------------------------------------------------------------
    # TOTAL SLOW PHASE LATENCY
    # ------------------------------------------------------------
    metrics.observe(
        "proc_stage_duration_seconds",
        time.time() - slow_start,
        labels={"stage": "slow_phase_total"},
    )