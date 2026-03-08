# Developer Onboarding Guide

## First Steps

1. Clone the repository

```bash
git clone https://github.com/MatthiasViertler/hl7v2-parser.git
cd hl7v2-parser
```

2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Run the HL7 MLLP Server

```bash
make run-server
```

Or with Prometheus enabled:
```bash
make run-server-prom
```

Server runs on
```
MLLP:        localhost:2575
Prometheus:  localhost:8010/metrics
```
4. Send a test HL7 message

```bash
python tools/send_hl7.py samples/oru_r01.hl7
```

You should see:
- ACK returned
- Routed file written to routed/<destination>/...

5. Run the benchmark suite

```bash
make run-benchmark
```

Visualize results:

```bash
make visualize
```

Optional cleanup:

```bash
make clean-bench-results
```

6. Monitoring & Observability

Start Prometheus:
```bash
./prometheus --config.file=monitoring/Prometheus.yml
```

Import Grafana dashboard:

```
monitoring/Grafana_dashboard_hl7.json
```

You get:
- Throughput
- ACK latency
- Queue depth
- Worker utilization
- Error counters

7. VS Code Debugging
Launch configurations are included:
- Run MLLP Server (with Prometheus)
- Run MLLP Server (no Prometheus)
Open the debug panel and start the configuration.

8. Run the full test suite

```bash
pytest -q
```

All tests should pass.

9. Project Structure Overview

See `HL7v2-Parser/Readme.md#Project Structure`

10. Troubleshooting

### Port already in use
```bash
make kill-server
```

### Metrics not updating
- Ensure Prometheus is scraping localhost:8010
- Ensure server was started with --prometheus

### No routed files
- Check config/routes.yaml
- Check worker logs
- Ensure slow worker executor is running


