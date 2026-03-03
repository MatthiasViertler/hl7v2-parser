import logging.config
import yaml
import socket

from pathlib import Path
from hl7engine.hl7_listener import process_hl7_message, normalize_hl7

print(">>> MLLP SERVER MODULE LOADED:", __file__)

START_BLOCK = b"\x0b"
END_BLOCK = b"\x1c\x0d"

def setup_logging():
    config_path = Path("config/logging.yaml")
    if config_path.exists():
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)

def run_server(host="0.0.0.0", port=2575):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)

    print(f"HL7 MLLP listener running on {host}:{port}")

    while True:
        conn, addr = server.accept()
        print(f"Connection from {addr}")
        sender_ip = addr[0]

        buffer = b""
        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break

            buffer += chunk
            
            # Process ALL complete frames in buffer
            while True:
                start = buffer.find(START_BLOCK)
                if start == -1:
                    # No start block → discard garbage
                    buffer = b""
                    break

                end = buffer.find(END_BLOCK, start + 1)
                if end == -1:
                    # Incomplete frame → wait for more data
                    break

                # Extract HL7 frame
                frame = buffer[start + 1:end]  # skip SB
                buffer = buffer[end + len(END_BLOCK):]

                # Decode + normalize
                raw_hl7 = frame.decode(errors="ignore")
                raw_hl7 = normalize_hl7(raw_hl7)

                # Process HL7
                ack = process_hl7_message(raw_hl7, sender_ip)

                # Send ACK
                framed_ack = START_BLOCK + ack.encode() + END_BLOCK
                conn.sendall(framed_ack)

        conn.close()


if __name__ == "__main__":
    setup_logging()
    run_server()
