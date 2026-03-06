# HL7v2 Parser & Benchmarking Suite

A high‑performance HL7v2 message parser written in Python, accompanied by a comprehensive benchmarking toolkit for evaluating throughput, latency, and concurrency behavior of HL7 MLLP servers.

This project is designed for experimentation, performance tuning, and deep analysis of HL7 message processing pipelines.

---

## Features

### **HL7v2 Parser**
- Lightweight, fast HL7v2 message parsing
- Support for multiple message templates
- Clean separation between parsing, ACK generation, and transport

### **Benchmarking Toolkit**
Located under `benchmarking/`, the toolkit provides:
- **Max Throughput Mode** — measures pure message‑processing capacity
- **Connection‑Only Stress Mode** — isolates TCP accept loop performance
- **Mixed Workload Mode** — simulates real‑world long‑lived + burst traffic
- **Concurrency Sweep Mode** — automatically tests 1, 2, 4, 8, 16 workers
- **Warm‑up Phase** — stabilizes server state before measurement
- **JSON Export** — structured results for analysis and plotting
- **Visualization Tools** — throughput curves, latency histograms, percentiles

---

## Project Structure

hl7v2-parser/
│
├── hl7engine/                     # Main application package
│   ├── __init__.py
│   ├── api.py                     # REST API (if used)
│   ├── db.py                      # SQLite or other persistence layer
│   ├── hl7_listener.py            # HL7 message ingestion
│   ├── mllp_server.py             # MLLP TCP server implementation
│   ├── parse_hl7.py               # HL7 parsing utilities
│   ├── router.py                  # Message routing logic
│   ├── validator.py               # HL7 profile validation
│   ├── json_logger.py             # Structured JSON logging
│   ├── profiles/                  # HL7 profile definitions
│   │   ├── oru_r01.yaml
│   │   └── ...
│   └── ...
│
├── benchmarking/                  # Full benchmarking suite
│   ├── run_benchmark.py           # CLI entry point
│   ├── coordinator.py             # Orchestrates benchmark modes
│   ├── long_lived_worker.py       # Persistent connection workers
│   ├── burst_worker.py            # Burst traffic workers
│   ├── connection_worker.py       # Connection-only stress workers
│   ├── visualize.py               # Throughput & latency plotting
│   ├── results/                   # JSON output files (gitignored)
│   │   └── ...
│   └── ...
│
├── config/                        # YAML configuration files
│   ├── routes.yaml
│   ├── validation.yaml
│   └── logging.yaml               # Optional logging config
│
├── data/                          # Runtime data (ignored by git)
│   ├── hl7_messages.db
│   └── ...
│
├── routed/                        # Routed HL7 messages (ignored)
│   └── ...
│
├── received/                      # Raw incoming HL7 messages
│   └── ...
│
├── samples/                       # Sample HL7 messages
│   └── ...
│
├── tests/                         # Full test suite
│   ├── conftest.py
│   ├── test_00_debug_path.py
│   ├── test_01_parser.py
│   ├── test_02_mllp.py
│   ├── ...
│   └── manual/                    # Manual test helpers
│
├── tools/                         # Helper scripts & converters
│   ├── build_oru_r01_profile.py
│   ├── convert_profile.py
│   └── ...
│
├── scripts/                       # Shell scripts for manual testing
│   ├── fragmented-msg-test.sh
│   ├── multiple-msg-types.sh
│   ├── multiple-ORU-msgs.sh
│   ├── stress-test-100msgs.sh
│   └── convert_profile.sh
│
├── ui/                            # Optional UI assets
│   ├── index.html
│   └── static/
│       └── ...
│
├── docs/                          # Architecture & design docs
│   ├── architecture.md
│   ├── sequence-diagram.png
│   ├── data-flow.png
│   └── ...
│
├── Makefile                       # Build/test shortcuts
├── pyproject.toml                 # Project metadata & dependencies
├── pytest.ini                     # Pytest configuration
├── README.md                      # Main project documentation
└── .gitignore

---

## Documentation

Full documentation is available under the `docs/` directory:

- **Architecture Overview**  
  `docs/architecture.md`

- **Benchmarking Modes Explained**  
  `docs/benchmarking.md`

- **Performance Notes & Tuning Guide**  
  `docs/performance-notes.md`

These documents describe the internal design, message flow, and how to interpret benchmark results.

---

## Running Benchmarks

### **Max Throughput**

python3 -m benchmarking.run_benchmark --duration 30 --max-throughput

### **Connection-Only Stress Test**

python3 -m benchmarking.run_benchmark --duration 30 --conn-stress

### **Concurrency Sweep**

python3 -m benchmarking.run_benchmark --duration 10 --sweep

### **Visualize Results**

python3 -m benchmarking.run_benchmark --visualize results/<file>.json

---

## Requirements

- Python 3.10+
- matplotlib (for visualization)
- A running HL7 MLLP server (default: `127.0.0.1:2575`)

Install dependencies:

pip install -r requirements.txt

---

## Contributing

Contributions, ideas, and performance experiments are welcome.  
Feel free to open issues or submit pull requests.

---

## 📄 License

MIT License — see `LICENSE` for details.
