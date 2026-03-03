import socket, time

HOST = "localhost"
PORT = 2575

msg = (
    "MSH|^~\\&|LAB|HOSP|EHR|HOSP|202402201200||ORU^R01|12345|P|2.5.1\r"
    "PID|1||123456^^^HOSP^MR||Doe^John||19800101|M\r"
    "OBR|1||987654|GLUCOSE^Glucose Test^L\r"
    "OBX|1|NM|2345-7^Glucose^LOINC||5.6|mmol/L|3.9-5.5|H\r"
)

framed = b"\x0b" + msg.encode() + b"\x1c\x0d"

chunks = [
    framed[:10],
    framed[10:25],
    framed[25:40],
    framed[40:55],
    framed[55:]
]

s = socket.socket()
s.connect((HOST, PORT))

for c in chunks:
    s.sendall(c)
    time.sleep(0.3)

ack = s.recv(4096)
print("ACK received:", repr(ack))
s.close()
