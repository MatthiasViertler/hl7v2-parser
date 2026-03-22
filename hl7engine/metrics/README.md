# HL7 Engine Metrics

This document describes all Prometheus metrics exposed by the HL7 engine,
grouped by subsystem.

---

## Parser Metrics

### parser_parse_errors_total{error_code}
Counts parsing failures before validation.

Error codes:
- EMPTY — empty HL7 frame
- NO_MSH — missing MSH segment
- PARSE — hl7apy parsing exception
- VERSION — invalid or missing MSH-12
- MSH9 — invalid message type/trigger format

### parser_validation_errors_total{error_code}
Counts semantic validation failures after parsing.

Error codes:
- AE — application error
- AR — application reject

### parser_message_types_total{message_type}
Counts parsed messages by HL7 message type (MSH-9.1).

### parser_versions_total{version}
Counts parsed messages by HL7 version (MSH-12).

---

## Router Metrics

### router_messages_routed_total{route}
Counts successfully routed messages by message type.

### router_routing_errors_total{route}
Counts routing failures (unknown message type or trigger).

---

## MLLP Metrics

### mllp_connections_total
Number of accepted MLLP TCP connections.

### mllp_bytes_received_total
Total bytes received via MLLP.

### mllp_bytes_sent_total
Total bytes sent via MLLP (ACKs).

### mllp_frame_starts_total
Number of MLLP frame start bytes (0x0B) detected.

---

## ACK Metrics

### ack_generated_total{code}
Counts generated ACKs by code:
- AA — success
- AE — application error
- AR — application reject

### ack_sent_total
Counts ACKs successfully sent over MLLP.

---

## Throughput Metrics

### messages_received_total
Counts all received HL7 messages.

### messages_processed_total
Counts messages that completed the fast phase.

---

## Latency Metrics

### parser_latency_seconds
Time spent parsing HL7 messages.

### processing_latency_seconds
Time spent in the fast phase (parse + validate + ACK).

### router_latency_seconds
Time spent routing messages.

### store_write_latency_seconds
Time spent writing routed messages to disk.

### message_end_to_end_latency_seconds
Total time from MLLP receive to file write completion.


# SLO Set

| Category           |      SLO      |      SLI                                   |    Threshold             | 
| Availability       | 99.9% uptime  | up{job="hl7engine"}                        |  downtime < 43min/month  | 
| ACK Latency        |   p95 < 50ms  | hl7_ack_latency_ms_p95                     |  95% under 50ms          | 
| End-to-End Latency |  p95 < 500ms  | hl7_message_end_to_end_latency_p95_seconds |  95% under 500ms         | 
| Parse Quality      | >99% success  | hl7_parser_parse_errors_total              |  <1% failures            | 
| Validation Quality |   >98% AA     | hl7_validation_AA                          |  <2% AE/AR               | 
| Message Loss       |    0 lost     | hl7_queue_overflow                         |  zero lost messages      | 
| DB Reliability     |99.99% success | hl7_store_write_errors_total               |  <1 per 10k              | 
| Worker Saturation  |      <85%     | hl7_workers_busy / hl7_workers_max         |  sustained <85%          | 


This is a professional‑grade SLO suite used in real integration engines (Rhapsody, Mirth, Cloverleaf, Ensemble).
