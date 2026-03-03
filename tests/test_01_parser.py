# tests/test_01_parser.py

# This is a clean, minimal, production‑ready parser test suite that validates:
# - version normalization (2.3 → 2.3.1)
# - flat structure (find_groups=False)
# - correct segment order
# - correct field extraction
# - correct behavior for malformed messages
# - correct behavior for missing MSH‑12

import pytest
from hl7apy.parser import parse_message
from hl7engine.hl7_listener import normalize_version, normalize_hl7


def hl7(s):
    return s.strip().replace("\n", "\r")


def test_parse_v23_normalized_to_v231():
    raw = hl7("""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|20240220||ORU^R01|X1|P|2.3
        PID|1||12345^^^HOSP^MR
    """)

    norm = normalize_version(raw)
    msg = parse_message(norm, find_groups=False)

    assert msg.msh.msh_12.value == "2.3.1"
    assert msg.children[1].name == "PID"


def test_parse_v251_flat_structure():
    raw = hl7("""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|20240220||ORU^R01|X2|P|2.5.1
        PID|1||12345^^^HOSP^MR
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8
    """)

    msg = parse_message(raw, find_groups=False)

    names = [c.name for c in msg.children]
    assert names == ["MSH", "PID", "OBR", "OBX"]


def test_parse_missing_version_defaults_to_25():
    raw = hl7("""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|20240220||ORU^R01|X3|P|
        PID|1||12345^^^HOSP^MR
    """)

    norm = normalize_version(raw)
    msg = parse_message(norm, find_groups=False)

    assert msg.msh.msh_12.value == "2.5"


def test_parse_invalid_message_raises():
    raw = "FOO|bar|baz\r"
    with pytest.raises(Exception):
        parse_message(raw, find_groups=False)


def test_normalize_hl7_line_endings():
    raw = "MSH|A|B|C\nPID|1||123"
    norm = normalize_hl7(raw)
    assert "\r" in norm
    assert "\n" not in norm