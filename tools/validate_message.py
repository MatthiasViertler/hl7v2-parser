#!/usr/bin/env python3
import sys
from pathlib import Path

from hl7apy.parser import parse_message
from hl7engine.validator import YAMLValidator


def load_hl7_file(path: Path) -> str:
    with open(path, "r") as f:
        raw = f.read()
    # Normalize line endings
    return raw.replace("\r\n", "\r").replace("\n", "\r")


def print_report(msg, ack_code, error):
    print("\n=== VALIDATION REPORT ===")

    try:
        msg_type = msg.msh.msh_9.msh_9_1.value
        trigger = msg.msh.msh_9.msh_9_2.value
        control_id = msg.msh.msh_10.value
    except Exception:
        msg_type = trigger = control_id = "(unavailable)"

    print(f"Message Type: {msg_type}")
    print(f"Trigger Event: {trigger}")
    print(f"Control ID: {control_id}")

    print("Segments Found:", [c.name for c in msg.children])

    print("\nValidation Result:", "ACCEPTED (AA)" if ack_code == "AA" else "REJECTED (AR)")

    if error:
        print("\nError:", error)

    print("\n==========================\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m tools.validate_message <hl7_file>")
        sys.exit(1)

    hl7_path = Path(sys.argv[1])
    if not hl7_path.exists():
        print(f"ERROR: File not found: {hl7_path}")
        sys.exit(1)

    raw = load_hl7_file(hl7_path)

    try:
        msg = parse_message(raw, find_groups=False)
    except Exception as e:
        print("ERROR: Unable to parse HL7 message:", e)
        sys.exit(1)

    validator = YAMLValidator("config/validation.yaml")
    ack_code, error = validator.validate(msg)

    print_report(msg, ack_code, error)


if __name__ == "__main__":
    main()