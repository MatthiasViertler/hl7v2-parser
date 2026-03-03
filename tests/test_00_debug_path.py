import os, sys

def test_debug_path():
    print("PYTEST CWD:", os.getcwd())
    print("SYS.PATH:", sys.path)
    assert True