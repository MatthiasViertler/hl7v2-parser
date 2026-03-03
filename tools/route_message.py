#!/usr/bin/env python3
import sys
from pathlib import Path

from hl7apy.parser import parse_message
from hl7engine.router import Router


def load_hl7_file(path: Path) -> str:
    with open(path, "r") as f:
        raw = f.read()
    return raw.replace("\r\n", "\r").replace("\n", "\r")


def print_report(msg, parent, routed):
    print("\n=== ROUTING REPORT ===")

    try:
        msg_type = msg.msh.msh_9.msh_9_1.value
        trigger = msg.msh.msh_9.msh_9_2.value
        control_id = msg.msh.msh_10.value
    except Exception:
        msg_type = trigger = control_id = "(unavailable)"

    print(f"Message Type: {msg_type}")
    print(f"Trigger Event: {trigger}")
    print(f"Control ID: {control_id}")

    print("\nParent Folder:", parent)
    print("Routed Folder:", routed)

    if parent == routed:
        print("\nRouting Mode: fallback-to-parent (trigger not defined)")
    else:
        print("\nRouting Mode: trigger-specific route")

    print("\n========================\n")


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m tools.route_message <hl7_file>")
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

    try:
        msg_type = msg.msh.msh_9.msh_9_1.value
    except Exception:
        print("ERROR: Missing or invalid MSH-9")
        sys.exit(1)

    router = Router("config/routes.yaml")
    parent, routed = router.route(msg_type, raw)

    print_report(msg, parent, routed)


if __name__ == "__main__":
    main()