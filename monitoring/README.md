# Monitoring & Observability

This directory contains configuration files for Prometheus and Grafana used to monitor the HL7 Engine.
## Prometheus

### Start Prometheus
./prometheus --config.file=monitoring/Prometheus.yml


Prometheus will scrape the HL7 Engine at:
http://localhost:8010/metrics


───────────────────────────────────────────────────────────────────────────
│Key Metrics                     │  Type   │   Description                │
│                                │         │                              │ 
├──────────────────────────────────────────────────────────────────────────
│ hl7_messages_received          | Counter |  Total HL7 messages received │ 
│ hl7_messages_processed         | Counter |  Messages fully processed    │ 
│ hl7_acks_sent                  | Counter |  ACKs returned               │ 
│ hl7_worker_tasks               | Counter |  Tasks executed by workers   │ 
│ hl7_workers_max                |  Gauge  |  Max worker count            │ 
│ hl7_workers_busy               |  Gauge  |  Busy workers                │ 
│ hl7_queue_depth                |  Gauge  |  Queue size                  │ 
│ hl7_ack_latency_ms_p50/p95/p99 |  Gauge  |  ACK latency percentiles     │ 
└──────────────────────────────────────────────────────────────────────────


## Grafana
A ready‑to‑import dashboard is provided:
```
monitoring/Grafana_dashboard_hl7.json
```

It includes:
- Message throughput
- ACK latency (p50/p95/p99)
- Queue depth
- Worker utilization
- Error counters
- Message volume over time

## Alerting
Prometheus alert rules are defined in:
monitoring/alert_rules.yml


These can be enabled by adding them to your Prometheus configuration.

File Overview
monitoring/
│
├── Prometheus.yml                 # Prometheus scrape config
├── alert_rules.yml                # Optional alerting rules
├── Grafana_dashboard_hl7.json     # Grafana dashboard
└── README.md                      # This file




