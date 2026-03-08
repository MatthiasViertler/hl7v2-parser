from hl7apy.parser import parse_message

## HL7 v2.3 ORU R01 message test:
# raw = """MSH|^~\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X100|P|2.3
# PID|1||12345^^^HOSP^MR||Smith^John||19791201|M
# OBR|1||5555|GLUCOSE^Glucose Test^L
# OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H"""

# print("=== find_groups=False ===")
# msg = parse_message(raw, find_groups=False)
# print([c.name for c in msg.children])

# print("=== find_groups=True ===")
# msg = parse_message(raw, find_groups=True)
# print([c.name for c in msg.children])

## HL7 v2.3.1 ORU R01 message test:
raw = (
    "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ORU^R01|X100|P|2.3.1\r"
    "PID|1||12345^^^HOSP^MR||Smith^John||19791201|M\r"
    "OBR|1||5555|GLUCOSE^Glucose Test^L\r"
    "OBX|1|NM|2345-7^Glucose^LOINC||5.8|mmol/L|3.9-5.5|H\r"
)

msg = parse_message(raw, find_groups=False)

print("ROOT:", [c.name for c in msg.children])
print("PID:", msg.children.get("PID"))
print("OBR:", msg.children.get("OBR"))
print("OBX:", msg.children.get("OBX"))
## The method segments() does not exist on Message objects.
## hl7apy tries to interpret "PID" as a child class name, not a segment name, and eventually throws:
## ChildNotFound: No child named SEGMENTS
# print("PID:", msg.segments("PID"))
# print("OBR:", msg.segments("OBR"))
# print("OBX:", msg.segments("OBX"))
