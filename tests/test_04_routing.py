# tests/test_04_routing.py

# A focused routing test suite gives you confidence that the new message‑type +
# trigger‑event router behaves exactly as intended across all realistic HL7 
# inputs. The goal is to verify:
# - correct extraction of MSH‑9.1 and MSH‑9.2
# - correct parent folder selection
# - correct trigger‑folder selection
# - correct fallback behavior
# - correct UNKNOWN routing
# - correct auto‑creation of folders
# - correct integration with your listener’s expectations

import os
import shutil
from pathlib import Path

from hl7engine.router import Router


BASE = Path(__file__).resolve().parent.parent
ROUTED = BASE / "routed"


def setup_module(module):
    # Clean routed/ folder before tests
    if ROUTED.exists():
        shutil.rmtree(ROUTED)
    ROUTED.mkdir(parents=True, exist_ok=True)


def test_oru_r01_routing():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|LAB|HOSP|EHR|HOSP|20240220||ORU^R01|X1|P|2.5.1\rPID|1||12345"

    parent, path = router.route("ORU", raw)

    assert parent == "routed/ORU"
    assert path == "routed/ORU/R01"
    assert Path(path).exists()


def test_oru_unknown_trigger_falls_back_to_parent():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|LAB|HOSP|EHR|HOSP|20240220||ORU^Z99|X2|P|2.5.1\rPID|1||12345"

    parent, path = router.route("ORU", raw)

    assert parent == "routed/ORU"
    assert path == "routed/ORU"
    assert Path(parent).exists()


def test_adt_a08_routing():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|ADT|HOSP|EHR|HOSP|20240220||ADT^A08|X3|P|2.6\rPID|1||A123"

    parent, path = router.route("ADT", raw)

    assert parent == "routed/ADT"
    assert path == "routed/ADT/A08"
    assert Path(path).exists()


def test_orm_o01_routing():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|ORM|HOSP|EHR|HOSP|20240220||ORM^O01|X4|P|2.6\rPID|1||B998"

    parent, path = router.route("ORM", raw)

    assert parent == "routed/ORM"
    assert path == "routed/ORM/O01"
    assert Path(path).exists()


def test_vxu_v04_routing():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|IMM|HOSP|EHR|HOSP|20240220||VXU^V04|X5|P|2.6\rPID|1||C112"

    parent, path = router.route("VXU", raw)

    assert parent == "routed/VXU"
    assert path == "routed/VXU/V04"
    assert Path(path).exists()


def test_siu_s12_routing():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|SIU|HOSP|EHR|HOSP|20240220||SIU^S12|X6|P|2.6\rPID|1||D445"

    parent, path = router.route("SIU", raw)

    assert parent == "routed/SIU"
    assert path == "routed/SIU/S12"
    assert Path(path).exists()


def test_unknown_message_type_goes_to_unknown():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|ZZZ|HOSP|EHR|HOSP|20240220||ZZZ^Z01|X7|P|2.5.1\rPID|1||999"

    parent, path = router.route("ZZZ", raw)

    assert parent == "routed/UNKNOWN"
    assert path == "routed/UNKNOWN"
    assert Path(path).exists()


def test_missing_trigger_event_falls_back_to_parent():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|ORU|HOSP|EHR|HOSP|20240220||ORU|X8|P|2.5.1\rPID|1||12345"

    parent, path = router.route("ORU", raw)

    assert parent == "routed/ORU"
    assert path == "routed/ORU"
    assert Path(parent).exists()


def test_trigger_event_parsing_with_extra_fields():
    router = Router("routes.yaml")
    raw = "MSH|^~\\&|ORU|HOSP|EHR|HOSP|20240220||ORU^R01^EXTRA|X9|P|2.5.1\rPID|1||12345"

    parent, path = router.route("ORU", raw)

    assert parent == "routed/ORU"
    assert path == "routed/ORU/R01"
    assert Path(path).exists()