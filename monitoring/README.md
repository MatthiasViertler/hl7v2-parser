# Monitoring & Observability

Monitoring & Observability
This directory contains everything related to monitoring the HL7 Engine, including Prometheus configuration, Grafana dashboards, and runtime logs.
The monitoring stack is intentionally lightweight and easy to run locally.

It consists of:
- Prometheus for metrics collection
- Grafana for dashboards
- Logs for debugging


```
monitoring/
│
├── grafana/            # Dashboards, provisioning, datasources
├── prometheus/         # Prometheus config (scrape targets, rules)
├── logs/               # Runtime logs (Prometheus, REST API, etc.)
└── README.md           # This file
```

## Prometheus

Prometheus scrapes metrics from the HL7 Engine at:
```
http://localhost:8010/metrics
```

### Start Prometheus

./prometheus --config.file=monitoring/prometheus/prometheus.yml

or

```
make prom-start
```

or check out the promoetheus.mk and utils.mk make file in makefiles/ for more details.

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
Grafana dashboards are stored under:
```
monitoring/grafana/
```

It includes:
- Message throughput
- ACK latency (p50/p95/p99)
- Queue depth
- Worker utilization
- Error counters
- Message volume over time

### Start Grafana

```
make grafana-start
```

## Alerting
Alert rules are not included yet.
A new alert_rules.yml will be added once the metric set stabilizes.

These can be enabled by adding them to your Prometheus configuration.
