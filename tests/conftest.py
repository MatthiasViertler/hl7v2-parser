## FILE LOADED PRIOR RUNNING TESTS
# Adding project root to pytests sys.path (not only /tests/) so it can find the hl7engine package, etc.

# tests/conftest.py
import pytest
import subprocess
import time
import socket
import sys
import os
import signal
import shutil
from pathlib import Path

REST_HOST = "localhost"
REST_PORT = 8000

MLLP_HOST = "localhost"
MLLP_PORT = 2575

# Prometheus server
PROM_HOST = "localhost"
PROM_PORT = 9090

# Prometheus HTTP metrics viewing server
PROM_HTTP_HOST = "localhost"
PROM_HTTP_PORT = 8010

# Project root (hl7v2-parser/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTED = PROJECT_ROOT / "routed"
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DB = DATA_DIR / "hl7_messages.db"
SEED_DB = DATA_DIR / "seed" / "hl7_messages_demo.db"

# Ensure project root is on sys.path --> NOT needed if package is installed via 'pip install -e .'
#PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)

# UNCOMMENT below to have pytest clean DB before each test session
# @pytest.fixture(scope="session", autouse=True)
# def reset_db_for_tests():
#     if RUNTIME_DB.exists():
#         RUNTIME_DB.unlink()
#     shutil.copy(SEED_DB, RUNTIME_DB)
#     yield

def wait_for_port(host, port, timeout=5.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return True
        except OSError:
            time.sleep(0.1)
    return False


def kill_process_on_port(port):
    try:
        out = subprocess.check_output(["lsof", "-t", f"-i:{port}"])
        for pid in out.decode().split():
            os.kill(int(pid), signal.SIGKILL)
    except subprocess.CalledProcessError:
        pass

@pytest.fixture(scope="session", autouse=True)
def clean_runtime_db():
    if RUNTIME_DB.exists():
        RUNTIME_DB.unlink()
    shutil.copy(SEED_DB, RUNTIME_DB)
    yield

@pytest.fixture(scope="session", autouse=True)
def start_servers():
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
        stdout=None,
        stderr=None,
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
        stdout=None,
        stderr=None,
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

# @pytest.fixture(scope="session", autouse=True)
@pytest.fixture(autouse=True)
def clean_routed():
    # Clean routed/ before every test
    if ROUTED.exists():
        shutil.rmtree(ROUTED)
    ROUTED.mkdir(parents=True, exist_ok=True)
    yield