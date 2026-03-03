# Full HL7 Validator Test Suite (flat + nested + repeats + missing fields)
# It tests:
# - flat vs nested
# - missing segments
# - missing components
# - missing subcomponents
# - v2.3 normalization
# - v2.6 compatibility
# - large messages
# This is your core validator test suite.

from hl7apy import load_message_profile
from hl7apy.parser import parse_message
from hl7engine.validator import YAMLValidator

validator = YAMLValidator()

def load_profile(path):
    return load_message_profile(path)

def hl7(s):
    return s.strip().replace("\n", "\r")

def parse_hl7(raw_hl7: str):
    """
    Normalize HL7 version and parse message with hl7apy.
    Special-case: HL7 v2.3 → v2.3.1 (hl7apy does not support 2.3).
    """

    # Split into segments
    segments = raw_hl7.split("\r")
    msh = segments[0].split("|")

    # Extract version from MSH-12
    version = msh[11].strip() if len(msh) > 11 else ""

    # Normalize unsupported version 2.3 → 2.3.1
    if version == "2.3":
        msh[11] = "2.3.1"
        segments[0] = "|".join(msh)
        raw_hl7 = "\r".join(segments)

    # Parse using hl7apy's built-in model
    # find_groups=False keeps segments flat (PID, OBR, OBX at root)
    msg = parse_message(raw_hl7, find_groups=False)

    return msg


# ---------------------------------------------------------
# 1. FLAT ORU STRUCTURE (HL7 2.3 / 2.4)
# ---------------------------------------------------------
# ATTENTION: w/o 'version="2.3"', hl7apy defaults to 2.5.1 and PID/OBR/OBX definitions differ. It'll parse them as a group, not a segment -> validation fails!
def test_flat_oru_structure():
    #msg = parse_message(hl7("""
    msg = parse_hl7(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X100|P|2.3
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """)) 

    code, err = validator.validate(msg)
    print("error: ", err)
    assert code == "AA"


# ---------------------------------------------------------
# 2. NESTED ORU STRUCTURE (HL7 2.5.1)
# ---------------------------------------------------------
def test_nested_oru_structure():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X101|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AA"


# ---------------------------------------------------------
# 3. MULTIPLE OBX SEGMENTS
# ---------------------------------------------------------
def test_multiple_obx_segments():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X102|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
        OBX|2|NM|7890-1^Sodium^LOINC||140|mmol/L|135-145|N
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AA"


# ---------------------------------------------------------
# 4. MULTIPLE ORDER_OBSERVATION GROUPS
# ---------------------------------------------------------
def test_multiple_order_observation_groups():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X103|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M

        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H

        OBR|2||7777|SODIUM^Sodium Test^L
        OBX|1|NM|7890-1^Sodium^LOINC||140|mmol/L|135-145|N
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AA"


# ---------------------------------------------------------
# 5. MISSING SEGMENTS
# ---------------------------------------------------------
def test_missing_pid_segment():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X104|P|2.5.1
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AE"
    assert "PID" in err


def test_missing_obr_segment():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X105|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AE"
    assert "OBR" in err


def test_missing_obx_segment():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X106|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AE"
    assert "OBX" in err


# ---------------------------------------------------------
# 6. MISSING COMPONENTS
# ---------------------------------------------------------
def test_missing_pid_3_1():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X107|P|2.5.1
        PID|1||^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AE"
    assert "PID.3.1" in err


def test_missing_pid_3_4():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X108|P|2.5.1
        PID|1||12345^^^|Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AE"
    assert "PID.3.4" in err


def test_missing_obx_5_1():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X109|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||^mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AE"
    assert "OBX.5.1" in err


def test_missing_obr_4_2():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X110|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^| 
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AE"
    assert "OBR.4.2" in err


# ---------------------------------------------------------
# 7. SUBCOMPONENT TESTS
# ---------------------------------------------------------
def test_pid_3_4_2_subcomponent():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X111|P|2.5.1
        PID|1||12345^^^HOSP&X^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AA"

# ---------------------------------------------------------
# 8. HL7 v2.6 ORU^R01 TESTS
# ---------------------------------------------------------
def test_oru_v26_structure():
    msg = parse_message(hl7(r"""
        MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X200|P|2.6
        PID|1||98765^^^HOSP^MR||Doe^Jane||19800101|F
        OBR|1||9999|GLUCOSE^Glucose Test^L
        OBX|1|NM|2345-7^Glucose^LOINC||6.1|mmol/L|3.9-5.5|H
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AA"

# ---------------------------------------------------------
# 9. HL7 v2.6 ADT^A01 TESTS
# ---------------------------------------------------------
def test_adt_v26_structure():
    msg = parse_message(hl7(r"""
        MSH|^~\&|ADT|HOSP|EHR|HOSP|202402201400||ADT^A01|X201|P|2.6
        PID|1||A123456^^^HOSP^MR||Miller^Tom||19750505|M
        PV1|1|I|WARD^101^1^HOSP||||1234^Physician^Primary
    """), find_groups=False)

    code, err = validator.validate(msg)
    assert code == "AA"

# ---------------------------------------------------------
# 10. Large HL7 Message (>50KB) TESTS
# ---------------------------------------------------------
def test_large_hl7_message():
    # Build a large ORU message with ~3000 OBX segments
    obx_segments = "\r".join(
        f"OBX|{i}|NM|2345-7^Glucose^LOINC||{5.0 + (i % 10)}|mmol/L|3.9-5.5|N"
        for i in range(1, 3001)
    )

    raw = hl7(f"""
        MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X300|P|2.5.1
        PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
        OBR|1||5555|GLUCOSE^Glucose Test^L
        {obx_segments}
    """)

    msg = parse_message(raw, find_groups=False)
    code, err = validator.validate(msg)

    assert code == "AA"
    assert len(msg.children) > 2000  # sanity check