# SLO Set

| Category           |      SLO      |      SLI                           |    Threshold             | 
| Availability       | 99.9% uptime  | up{job="hl7engine"}                |  downtime < 43min/month  | 
| ACK Latency        |   p95 < 50ms  | hl7_ack_latency_ms_p95             |  95% under 50ms          | 
| End-to-End Latency |  p95 < 500ms  | hl7_end_to_end_latency_ms_p95      |  95% under 500ms         | 
| Parse Quality      | >99% success  | hl7_parse_success                  |  <1% failures            | 
| Validation Quality |   >98% AA     | hl7_validation_AA                  |  <2% AE/AR               | 
| Message Loss       |    0 lost     | hl7_queue_overflow                 |  zero lost messages      | 
| DB Reliability     |99.99% success | hl7_db_insert_failure              |  <1 per 10k              | 
| Worker Saturation  |      <85%     | hl7_workers_busy / hl7_workers_max |  sustained <85%          | 


This is a professional‑grade SLO suite used in real integration engines (Rhapsody, Mirth, Cloverleaf, Ensemble).
