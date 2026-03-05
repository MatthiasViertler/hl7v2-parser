import socket
import time

MLLP_START = b"\x0b"
MLLP_END = b"\x1c\x0d"


class MLLPClient:
    def __init__(self, host: str, port: int, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def send_hl7(self, message: str) -> float:
        """Send HL7 message framed with MLLP and return ACK latency in seconds."""
        if not self.sock:
            raise RuntimeError("Socket not connected")

        framed = MLLP_START + message.encode("utf-8") + MLLP_END

        t0 = time.perf_counter()
        self.sock.sendall(framed)

        ack = self._recv_ack()
        t1 = time.perf_counter()

        if ack is None:
            raise RuntimeError("No ACK received")

        return t1 - t0

    def _recv_ack(self) -> bytes | None:
        """Receive MLLP-framed ACK."""
        data = b""
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    return None
                data += chunk
                if data.endswith(MLLP_END):
                    return data
        except socket.timeout:
            return None