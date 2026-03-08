# hl7engine/utils/ack_utils.py

import datetime

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