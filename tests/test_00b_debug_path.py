import os, sys
import pytest

@pytest.mark.order(3)
def test_debug_path():
    print("PYTEST CWD:", os.getcwd())
    print("SYS.PATH:", sys.path)
    assert True