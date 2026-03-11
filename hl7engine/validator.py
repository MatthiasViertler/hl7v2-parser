# hl7engine/validator.py

# 2026 Mar 11: Added validation metrics + parser-level error metrics, improved segment/field extraction,
#              removed high-cardinality lables, added docstring + type hints, keep YAML rules untouched.

# hl7engine/validator.py

import yaml
import os
from pathlib import Path

from hl7engine.metrics.metrics import metrics

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"


# ----------------------------------------------------------------------
# Segment finder (version‑agnostic)
# ----------------------------------------------------------------------
def get_segment(msg, seg_name):
    """
    Return the first segment with the given name (PID, OBR, OBX, ...).

    With find_groups=False, hl7apy places all segments at the root level:
        msg.children = [MSH, PID, OBR, OBX, ...]
    """
    seg_name = seg_name.upper()

    try:
        segs = msg.children.get(seg_name)
        if isinstance(segs, list) and segs:
            return segs[0]
        if segs:
            return segs
    except Exception:
        pass

    return None


# ----------------------------------------------------------------------
# YAML Validator
# ----------------------------------------------------------------------
class YAMLValidator:
    """
    YAML‑driven HL7 validation engine.

    Emits metrics:
    - parser_validation_errors_total{error_code="AR"}
    - parser_validation_errors_total{error_code="AE"}
    - parser_validation_errors_total{error_code="AA"} (rare)
    """

    def __init__(self, config_file="validation.yaml"):
        full_path = CONFIG_DIR / config_file

        with open(full_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.rules = self.config.get("validation", {})

    # ------------------------------------------------------------
    # VALIDATION
    # ------------------------------------------------------------
    def validate(self, msg):
        """
        Validate an HL7 message using YAML rules.

        Returns:
            (ack_code, error_text)
        """

        if msg is None:
            metrics.inc(
                "parser_validation_errors_total",
                labels={"error_code": "AR"},
            )
            return "AR", "Unable to parse HL7 message"

        # Extract type + trigger
        try:
            msg_type = msg.msh.msh_9.msh_9_1.value
            trigger = msg.msh.msh_9.msh_9_2.value
        except Exception:
            metrics.inc(
                "parser_validation_errors_total",
                labels={"error_code": "AR"},
            )
            return "AR", "Missing or invalid MSH-9 (Message Type)"

        # Universal required field: MSH-10
        try:
            if not msg.msh.msh_10.value:
                metrics.inc(
                    "parser_validation_errors_total",
                    labels={"error_code": "AR"},
                )
                return "AR", "Missing MSH-10 (Message Control ID)"
        except Exception:
            metrics.inc(
                "parser_validation_errors_total",
                labels={"error_code": "AR"},
            )
            return "AR", "Missing MSH-10 (Message Control ID)"

        # Load rules
        type_rules = self.rules.get(msg_type, {})
        event_rules = type_rules.get(trigger, {})
        default_rules = self.rules.get("default", {})

        required_segments = event_rules.get(
            "required_segments",
            type_rules.get(
                "required_segments",
                default_rules.get("required_segments", []),
            ),
        )

        required_fields = event_rules.get(
            "required_fields",
            type_rules.get(
                "required_fields",
                default_rules.get("required_fields", []),
            ),
        )

        severity = event_rules.get(
            "severity",
            type_rules.get(
                "severity",
                default_rules.get("severity", "AR"),
            ),
        )

        # --------------------------------------------------------------
        # Required segments
        # --------------------------------------------------------------
        for seg_name in required_segments:
            seg = get_segment(msg, seg_name)
            if seg is None:
                metrics.inc(
                    "parser_validation_errors_total",
                    labels={"error_code": severity},
                )
                return severity, f"Missing {seg_name} segment"

        # --------------------------------------------------------------
        # Required fields (ER7 string splitting)
        # --------------------------------------------------------------
        for field in required_fields:
            parts = field.split(".")
            seg_name = parts[0].upper()
            indexes = [int(p) for p in parts[1:]]

            seg = get_segment(msg, seg_name)
            if seg is None:
                metrics.inc(
                    "parser_validation_errors_total",
                    labels={"error_code": severity},
                )
                return severity, f"Missing {seg_name} segment"

            # Field level: PID.3
            try:
                fld = getattr(seg, f"{seg_name.lower()}_{indexes[0]}")
            except Exception:
                metrics.inc(
                    "parser_validation_errors_total",
                    labels={"error_code": severity},
                )
                return severity, f"Missing required field {field}"

            fld_str = fld.to_er7() or ""
            if not fld_str and len(indexes) == 1:
                metrics.inc(
                    "parser_validation_errors_total",
                    labels={"error_code": severity},
                )
                return severity, f"Missing required field {field}"

            current_str = fld_str

            # Component level: PID.3.1
            if len(indexes) >= 2:
                comps = current_str.split("^")
                comp_index = indexes[1] - 1
                if comp_index >= len(comps) or not comps[comp_index]:
                    metrics.inc(
                        "parser_validation_errors_total",
                        labels={"error_code": severity},
                    )
                    return severity, f"Missing required field {field}"
                current_str = comps[comp_index]

            # Subcomponent level: PID.3.1.4
            if len(indexes) == 3:
                subs = current_str.split("&")
                sub_index = indexes[2] - 1
                if sub_index >= len(subs) or not subs[sub_index]:
                    metrics.inc(
                        "parser_validation_errors_total",
                        labels={"error_code": severity},
                    )
                    return severity, f"Missing required field {field}"
                current_str = subs[sub_index]

            if not current_str:
                metrics.inc(
                    "parser_validation_errors_total",
                    labels={"error_code": severity},
                )
                return severity, f"Missing required field {field}"

        # All good
        return "AA", None