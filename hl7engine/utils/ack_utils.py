# hl7engine/utils/ack_utils.py

# 2026 Mar 11:  Add taxonomy-aligned metrics:
#               Metric                      |  Type      |  Labels
#               ---------------------------------------------------------------------------
#               ack_generated_total         | Counter    | {code="AA"}
#               ack_generation_errors_total | Counter    | {error_code="..."}
#               ack_rtt_seconds             | histogram  | (already emitted in MLLP server)
#               ---------------------------------------------------------------------------
#               Keep ACK builders pure + predictable (no side effects except metrics)
#               Add defensive coding (ACK building should never crash in pipeline)
#               No high-cardinality labels (no sender IP, no control ID, no facility)

import datetime
from hl7engine.metrics.metrics import metrics

# ------------------------------------------------------------
# ACK BUILDERS
# ------------------------------------------------------------

def build_ack_from_msg(original_msg, code="AA", text="OK") -> str:
    """
    Build ACK using fields from the original message.

    Emits:
    - ack_generated_total{code="AA"}
    - ack_generation_errors_total{error_code="..."} on failure
    """
    try:
        msh = original_msg.msh
        control_id = msh.msh_10.value or "UNKNOWN"

        ack = (
            f"MSH|^~\\&|{msh.msh_5.value}|{msh.msh_6.value}|"
            f"{msh.msh_3.value}|{msh.msh_4.value}|"
            f"{msh.msh_7.value}||ACK^{msh.msh_9.msh_9_2.value}|{control_id}|P|{msh.msh_12.value}\r"
            f"MSA|{code}|{control_id}|{text}\r"
        )

        metrics.inc("ack_generated_total", labels={"code": code})
        return ack

    except Exception as e:
        metrics.inc(
            "ack_generation_errors_total",
            labels={"error_code": "BUILD_FROM_MSG"},
        )
        # Fallback ACK
        return build_ack_simple("UNKNOWN", "AE", f"ACK build error: {e}")


def build_ack_simple(control_id: str, code="AA", text="OK") -> str:
    """
    Fallback ACK when we don't have a parsed message.

    Emits:
    - ack_generated_total{code="AA"}
    - ack_generation_errors_total{error_code="..."} on failure
    """
    try:
        now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        ack = (
            f"MSH|^~\\&|RECEIVER|HOSP|SENDER|HOSP|{now}||ACK^A01|ACK{control_id}|P|2.5.1\r"
            f"MSA|{code}|{control_id}|{text}\r"
        )

        metrics.inc("ack_generated_total", labels={"code": code})
        return ack

    except Exception:
        metrics.inc(
            "ack_generation_errors_total",
            labels={"error_code": "BUILD_SIMPLE"},
        )
        # Last‑ditch fallback
        return "MSH|^~\\&|ERR|ERR|ERR|ERR|000000000000||ACK^A01|ACKUNKNOWN|P|2.5.1\rMSA|AE|UNKNOWN|ACK generation failure\r"