hl7v2-parser/
│
├── hl7engine/                 # main application package
│   ├── __init__.py
│   ├── api.py
│   ├── db.py
│   ├── hl7_listener.py
│   ├── mllp_server.py
│   ├── parse_hl7.py
│   ├── router.py
│   ├── validator.py
│   ├── json_logger.py
│   ├── profiles/              # HL7 profile definitions
│   └── ...
│
├── config/                    # all YAML configuration
│   ├── routes.yaml
│   ├── validation.yaml
│   └── logging.yaml (optional)
│
├── data/                      # runtime data (ignored by git)
│   ├── hl7_messages.db
│   └── ...
│
├── routed/                    # runtime output (ignored by git)
│   └── ...
│
├── received/                  # incoming raw messages (if used)
│   └── ...
│
├── samples/                   # sample HL7 messages for tests/tools
│   └── ...
│
├── tests/                     # full test suite
│   ├── conftest.py
│   ├── test_00_debug_path.py
│   ├── test_01_parser.py
│   ├── test_02_mllp.py
│   ├── ...
│   └── manual/
│
├── tools/                     # helper scripts
│   ├── build_oru_r01_profile.py
│   ├── convert_profile.py
│   └── ...
│
├── scripts/                   # shell scripts for manual testing
│   ├── fragmented-msg-test.sh
│   ├── multiple-msg-types.sh
│   ├── multiple-ORU-msgs.sh
│   ├── stress-test-100msgs.sh
│   └── convert_profile.sh
│
├── ui/                        # optional UI assets
│   ├── index.html
│   └── static/ (optional)
│
├── docs/                      # architecture documentation (new)
│   ├── architecture.md
│   ├── sequence-diagram.png
│   ├── data-flow.png
│   └── ...
│
├── Makefile
├── pyproject.toml
├── pytest.ini
├── README.md
└── .gitignore