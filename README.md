# HL7v2 Parser & Benchmarking Suite

A high‑performance HL7v2 MLLP server with routing, validation, benchmarking, and full Prometheus monitoring support.  
Designed for healthcare integration labs, message simulators, and performance testing environments.

Accompanied by a comprehensive benchmarking toolkit for evaluating throughput, latency, and concurrency behavior of HL7 MLLP servers.

This project is designed for experimentation, performance tuning, and deep analysis of HL7 message processing pipelines.

---

## Features

- **HL7v2 MLLP Server** (port 2575)
- **Config‑driven routing** (`routes.yaml`)
- **Schema‑based validation** (`validation.yaml`)
- **Worker pool + message queue**
- **REST API for HL7 engine (port 8000)
- **HL7 engine metrics endpoint** (port 8010)
- **Benchmarking suite** (throughput, latency, concurrency sweep)
- **UI viewer** for routed HL7 messages (port 8080)
- **VS Code debug configurations**
- **Zero‑downtime monitoring with Grafana**

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

```

hl7v2-parser/
│
├── hl7engine/                     # Main application package
│   ├── __init__.py
│   │
│   ├── api/ 
│   │    └──api.py                 # REST API (if used)
│   │
│   ├── persistence/ 
│   │   └── db.py                  # SQLite or other persistence layer
│   │
│   ├── metrics/
│   │   ├── metrics.py             # Counters, gauges, histograms
│   │   ├── metrics_reporter.py    # Periodic metrics logging
│   │   ├── prometheus_exporter.py # Prometheus metric formatting
│   │   └── prometheus_http.py     # /metrics HTTP endpoint
│   │
│   ├── workers/ 
│   │    └──slow_worker.py         # Routing, file writing, DB inserts
│   │
│   ├── utils/ 
│   │    └──json_logger.py         # Structured JSON logging
│   │
│   ├── hl7_listener.py            # HL7 message ingestion
│   ├── mllp_server.py             # MLLP TCP server implementation
│   ├── router.py                  # Message routing logic
│   ├── validator.py               # HL7 profile validation
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
├── monitoring/
│   ├── prometheus.yml             # Prometheus config
│   ├── alert_rules.yml
│   ├── grafana_dashboard.json     # Grafana dashboard
│   └── README.md
|
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
```

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

## Installation & Requirements

- Python 3.10+
- matplotlib (for visualization in benchmark)
- Prometheus (for scraping benchmark/test results)
- Grafana (for dashboards)
- A running HL7 MLLP server (default: `127.0.0.1:2575`)

Install dependencies:

```bash
pip install -e .
```

Optional extras:

```bash
pip install -e .[monitoring]
pip install -e .[benchmark]
pip install -e .[dev]
```

---

## Running the MLLP server

Run without Prometheus

```bash
python -m hl7engine.mllp_server
```

Run with Prometheus

```bash
python -m hl7engine.mllp_server --prometheus
```

---

## Ports

```
Component          |      Port      |    Description
-----------------------------------------------------------
MLLP Server        |      2575      |  HL7v2 MLLP Listener
REST API Server    |      8000      |  HL7 Engine REST APIs
HL7 Engine Metrics |      8010      |  /metrics endpoint
UI Viewer          |      8080      |  Static HTML viewer
Prometheus UI      |      9090      |  Prometheus dashboard
-----------------------------------------------------------

```

---

## Monitoring with Prometheus

1. Start Prometheus

```bash
./prometheus --config.file=./monitoring/prometheus.yml
```

2. Prometheus scrape config

```Yaml
scrape_configs:
  - job_name: "hl7_mllp_server"
    static_configs:
      - targets: ["localhost:8010"]
```

3. Available Metrics

```
Metric                         |      Type        |         Description
--------------------------------------------------------------------------------
hl7_messages_received          |     Counter      |  Total HL7 messages received
hl7_messages_processed         |     Counter      |  Messages fully processed
hl7_acks_sent                  |     Counter      |  ACKs returned
hl7_worker_tasks               |     Counter      |  Tasks executed by workers
hl7_workers_max                |      Gauge       |  Max worker count
hl7_workers_busy               |      Gauge       |  Busy workers
hl7_queue_depth                |      Gauge       |  Queue size
hl7_ack_latency_ms_p50/p95/p99 |      Gauge       |  ACK latency percentiles
---------------------------------------------------------------------------------

```

4. Example PromQL Queries

Messages per second:
```
rate(hl7_messages_received[1m])
```

ACK latency:
```
hl7_ack_latency_ms_p95
```

Worker utilitzation:
```
hl7_workers_busy / hl7_workers_max
```

---

## Grafana Dashboard

A ready‑to‑import dashboard is available in:

```
monitoring/grafana/dashboard.json
```

The dashboard includes:
- Throughput (msg/sec)
- ACK latency (p50/p95/p99)
- Queue depth
- Worker utilization
- Error counters
- Message volume over time

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

## UI Viewer

```bash
make run-ui
```

Then open:
```
http://localhost:8000
```
This displays routed HL7 messages grouped by destination.

---

## Developer Workflow

### VS Code Debug Configurations
The project includes .vscode/launch.json with:
- Run MLLP Server (with Prometheus)
- Run MLLP Server (no Prometheus)

### Optional Keyboard Shortcut
Add to keybindings.json:
```Json
{
  "key": "ctrl+alt+m",
  "command": "workbench.action.debug.start",
  "args": { "config": "Run MLLP Server (with Prometheus)" }
}
```

### Kill running servers

```bash
make kill-server
```

### Clean-up old benchmark results

To clean old benchmark results:

```bash
make clean-bench-results
# or
python run_benchmark.py --clean-results
# or
BENCH_CLEAN_RESULTS=1 python run_benchmark.py

```

---

## Troubleshooting

### Prometheus target DOWN
- Ensure server started with --prometheus
- Ensure port 8010 is free
- Check /metrics manually

### Benchmark kills my server
- Use VS Code launch config for manual server
- Makefile kills only the temporary server

### Port already in use

```bash
make kill-server
```

### Metrics not increasing
- Run a benchmark
- Ensure messages are being processed

---

## Contributing

Contributions, ideas, and performance experiments are welcome.  
Feel free to open issues or submit pull requests.

---

## 📄 License

MIT License — see `LICENSE` for details.
