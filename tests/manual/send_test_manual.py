import socket

START = b"\x0b"
END = b"\x1c\x0d"

hl7 = (
    "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201400||ADT^A01|TEST123|P|2.5.1\r"
    "PID|1||12345^^^HOSP^MR||Doe^John||19800101|M"
)

msg = START + hl7.encode() + END

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect(("localhost", 2575))
    s.sendall(msg)
    ack = s.recv(4096)
    print("ACK received:")
    print(repr(ack))