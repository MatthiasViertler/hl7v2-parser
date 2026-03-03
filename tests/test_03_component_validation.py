# test_03_component_validation.py

# This is core HL7 semantic validation, independent of routing or MLLP.
# These tests verify:
# - field extraction
# - component parsing
# - subcomponent parsing
# - missing component detection
# - missing subcomponent detection
# - correct behavior of your YAML‑driven validator

import pytest
from hl7apy.parser import parse_message
from hl7engine.validator import YAMLValidator

validator = YAMLValidator("validation.yaml")

# Helper to strip indentation
def hl7(msg):
    return "\r".join(line.strip() for line in msg.strip().splitlines())

def dump_tree(node, indent=0):
    print("  " * indent + node.name)
    for child in getattr(node, "children", []):
        dump_tree(child, indent + 1)

def test_valid_oru_all_components_ok():
    msg = parse_message(hl7("""
        MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|ORU1001|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)
    print("PARSED CHILDREN:", [c.name for c in msg.children])
    dump_tree(msg)
    code, err = validator.validate(msg)
    assert code == "AA"


def test_missing_pid_3_1_component():
    msg = parse_message(hl7("""
        MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|ORU1002|P|2.5.1
        PID|1||^Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)
    code, err = validator.validate(msg)
    assert code in ("AE", "AR")
    assert "PID.3.1" in err


def test_missing_pid_3_4_subcomponent():
    msg = parse_message(hl7("""
        MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|ORU1003|P|2.5.1
        PID|1||12345^^^|Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)
    code, err = validator.validate(msg)
    assert code in ("AE", "AR")
    assert "PID.3.4" in err


def test_missing_obx_5_1_component():
    msg = parse_message(hl7("""
        MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|ORU1004|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||^mmol/L|3.9-5.5|H
    """), find_groups=False)
    code, err = validator.validate(msg)
    assert code in ("AE", "AR")
    assert "OBX.5.1" in err


def test_missing_obr_4_2_component():
    msg = parse_message(hl7("""
        MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|ORU1005|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^|
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)
    code, err = validator.validate(msg)
    assert code in ("AE", "AR")
    assert "OBR.4.2" in err