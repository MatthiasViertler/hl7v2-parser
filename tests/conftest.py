# tests/conftest.py

## FILE LOADED PRIOR RUNNING TESTS
# Adding project root to pytests sys.path (not only /tests/) so it can find the hl7engine package, etc.

import pytest
import subprocess
import time
import socket
import sys
import os
import signal
import shutil
from pathlib import Path

# -------------------------------------------------------------------
# Paths & Constants
# -------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

REST_HOST = "localhost"
REST_PORT = 8000

MLLP_HOST = "localhost"
MLLP_PORT = 2575

ROUTED = PROJECT_ROOT / "routed"
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DB = DATA_DIR / "hl7_messages.db"
SEED_DB = DATA_DIR / "seed" / "hl7_messages_demo.db"

# # Ensure project root is on sys.path --> NOT needed if package is installed via 'pip install -e .'
# #PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# # if PROJECT_ROOT not in sys.path:
# #     sys.path.insert(0, PROJECT_ROOT)

# # CLI option '--use-external-servers' enables DEVELOPER mode: servers won't get killed/started automatically
# #USE_EXTERNAL_SERVERS = os.environ.get("HL7_TEST_EXTERNAL_SERVERS") == "1"
# def pytest_addoption(parser):
#     parser.addoption(
#         "--use-external-servers",
#         action="store_true",
#         default=False,
#         help="Use externally running servers instead of starting test servers",
#     )

# -------------------------------------------------------------------
# CLI Option: Developer Mode
# -------------------------------------------------------------------

def pytest_addoption(parser):
    parser.addoption(
        "--use-external-servers",
        action="store_true",
        default=False,
        help="Do not kill/start servers; use externally running ones",
    )


# -------------------------------------------------------------------
# Utility Functions
# -------------------------------------------------------------------

def wait_for_port(host, port, timeout=5.0):
    """Wait until a TCP port is accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def kill_process_on_port(port):
    """Kill any process listening on the given port."""
    try:
        out = subprocess.check_output(["lsof", "-t", f"-i:{port}"])
        for pid in out.decode().split():
            os.kill(int(pid), signal.SIGKILL)
    except subprocess.CalledProcessError:
        pass


# -------------------------------------------------------------------
# Fixture: Reset DB (session-scoped)
# -------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def clean_runtime_db(request):
    """Reset the runtime DB unless using external servers."""
    if request.config.getoption("--use-external-servers"):
        yield
        return

    if RUNTIME_DB.exists():
        RUNTIME_DB.unlink()

    shutil.copy(SEED_DB, RUNTIME_DB)
    yield


# -------------------------------------------------------------------
# Fixture: Start/Stop Servers (session-scoped)
# -------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def start_servers(request):
    """Start REST + MLLP servers unless using external servers."""
    use_external = request.config.getoption("--use-external-servers")

    if use_external:
        print(">>> Developer mode: using external servers.")
        yield
        return

    # Kill stale servers
    kill_process_on_port(REST_PORT)
    kill_process_on_port(MLLP_PORT)

    # Start REST server
    rest_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "hl7engine.api:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(REST_PORT),
        ],
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )

    if not wait_for_port(REST_HOST, REST_PORT):
        rest_proc.kill()
        raise RuntimeError("REST server failed to start")

    # Start MLLP server
    mllp_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "hl7engine.mllp_server",
            "--prometheus",
        ],
        cwd=PROJECT_ROOT,
        env={**os.environ, "PYTHONPATH": str(PROJECT_ROOT)},
    )

    if not wait_for_port(MLLP_HOST, MLLP_PORT):
        mllp_proc.kill()
        rest_proc.kill()
        raise RuntimeError("MLLP server failed to start")

    yield

    # Cleanup
    for proc in (rest_proc, mllp_proc):
        try:
            os.kill(proc.pid, signal.SIGTERM)
        except Exception:
            pass


# -------------------------------------------------------------------
# Fixture: Clean routed/ before each test
# -------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_routed(request):
    """Clean routed/ folder before each test."""
    use_external = request.config.getoption("--use-external-servers")

    if use_external:
        print(">>> Developer mode: cleaning routed/ folder anyway.")

    # Give async worker time to finish writing
    timeout = time.time() + 1.0
    while ROUTED.exists() and any(ROUTED.iterdir()):
        if time.time() > timeout:
            break
        time.sleep(0.01)

    # Clean routed/
    if ROUTED.exists():
        shutil.rmtree(ROUTED)
    ROUTED.mkdir(parents=True, exist_ok=True)

    yield
