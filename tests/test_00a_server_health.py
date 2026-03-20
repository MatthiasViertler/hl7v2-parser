import socket
import pytest
import time

REST_HOST = "localhost"
REST_PORT = 8000

MLLP_HOST = "localhost"
MLLP_PORT = 2575

@pytest.mark.order(0)
def can_connect(host, port, timeout=1.0):
    """Return True if a TCP connection can be established."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.05)
    return False


@pytest.mark.order(1)
def test_rest_server_running(pytestconfig):
    """Verify REST server is accepting connections."""
    use_external = pytestconfig.getoption("--use-external-servers")

    assert can_connect(REST_HOST, REST_PORT), (
        "REST server is NOT running.\n"
        "If you're in developer mode, start it manually.\n"
        "If you're in CI mode, pytest should have started it."
    )

    if use_external:
        print(">>> REST server reachable (external mode).")
    else:
        print(">>> REST server reachable (pytest-managed).")


@pytest.mark.order(2)
def test_mllp_server_running(pytestconfig):
    """Verify MLLP server is accepting connections."""
    use_external = pytestconfig.getoption("--use-external-servers")

    assert can_connect(MLLP_HOST, MLLP_PORT), (
        "MLLP server is NOT running.\n"
        "If you're in developer mode, start it manually.\n"
        "If you're in CI mode, pytest should have started it."
    )

    if use_external:
        print(">>> MLLP server reachable (external mode).")
    else:
        print(">>> MLLP server reachable (pytest-managed).")