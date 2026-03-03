import hl7


def parse_hl7_message(raw_message: str):
    # Normalize line endings
    raw_message = raw_message.replace("\r\n", "\r").replace("\n", "\r")
    return hl7.parse(raw_message)

def parse_test_hl7_message_manually():
    with open("sample_oru.hl7") as f:
        raw = f.read()

    # Normalize line endings to HL7 standard
    raw = raw.replace("\r\n", "\r").replace("\n", "\r")

    msg = hl7.parse(raw)

    # Extract fields
    msh = msg.segment("MSH")
    pid = msg.segment("PID")
    obr = msg.segment("OBR")
    obx = msg.segment("OBX")

    print("Message Type:", msh[8])
    print("Patient ID:", pid[3])
    print("Patient Name:", pid[5])
    print("Test Code:", obr[4])
    print("Result Value:", obx[5])
    print("Units:", obx[6])
    print("Reference Range:", obx[7])
    print("Abnormal Flag:", obx[8])
    
    return