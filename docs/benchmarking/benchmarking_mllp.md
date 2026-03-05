# MLLP Benchmarking

A realistic mix of long‑lived and short‑lived MLLP connections shapes the benchmark design in a very specific way, because it mirrors how HL7 systems behave in hospitals: some systems keep a socket open for hours, others reconnect for every message or small batch. The goal is to capture both patterns without introducing complexity or optimizations that violate your maintainability constraints.

## How a realistic MLLP workload behaves
Real HL7 traffic typically falls into three categories:
- Long‑lived streams — ADT feeds, lab systems, radiology systems, and EMRs often keep a single TCP connection open and push messages continuously. These streams test sustained throughput, framing efficiency, and backpressure behavior.
- Short‑lived bursts — Some systems open a connection, send 1–10 messages, wait for ACKs, and disconnect. These bursts test connection setup overhead, ACK latency, and socket churn.
- Mixed patterns — Real environments often have both at the same time, which stresses concurrency, thread scheduling, and I/O coordination.
A realistic benchmark must simulate all three.

## Benchmark structure for mixed MLLP workloads
A balanced benchmark suite includes three complementary test types.
1) Long‑lived high‑volume streams
These measure sustained throughput and CPU efficiency.
- One connection sending thousands of messages
- Multiple long‑lived connections in parallel (e.g., 2, 4, 8)
- Continuous message flow at controlled rates (50–500 msg/s)
This reveals:
- framing/deframing overhead
- ACK turnaround time under load
- thread scheduling behavior
- memory stability over long runs
2) Short‑lived connection bursts
These measure connection overhead and ACK latency.
- Each connection sends 1–20 messages
- Hundreds or thousands of connections over time
- Randomized delays between bursts
This reveals:
- TCP handshake overhead
- socket creation/destruction cost
- routing latency under churn
- how well the server handles many small workloads
3) Mixed workload scenario
This is the “real hospital” simulation.
- 1–2 long‑lived streams sending steady traffic
- 5–20 short‑lived clients sending bursts
- Randomized message sizes (ADT, ORU, ORM)
- Randomized routing paths
This reveals:
- fairness between clients
- latency variance (p95, p99)
- stability under uneven load
- interaction between I/O and concurrency

## How this fits our maintainability constraints
The mixed‑workload benchmark focuses on architectural behavior rather than micro‑optimizations. It aligns well with our restrictions:
- No parser rewrites
- No Pydantic shortcuts
- No caching layers unless proven necessary
- No compiled or vectorized paths
Instead, the benchmark highlights the areas where clean, maintainable improvements are possible:
- concurrency model
- file I/O strategy
- logging overhead
- SQLite mode
- connection handling
These are the levers that give meaningful performance gains without making the code harder to understand.

## What we should define next
To build the benchmark harness, we need to specify:
- how many long‑lived connections to simulate
- how many short‑lived clients to simulate
- message rate targets
- message sizes (small ADT vs large ORU)
- ACK timeout expectations
- total test duration
A good starting point is:
- 2 long‑lived connections @ 50 msg/s each
- 10 short‑lived clients sending 5–20 messages every few seconds
- 10–20 minute test duration

## What this benchmark reveals without violating maintainability
Your constraints steer us toward architectural and I/O insights rather than low‑level tuning. The benchmark will show:
- Whether the MLLP server needs a concurrency upgrade (threads or asyncio)
- How much ACK latency is caused by file I/O vs parsing vs routing
- Whether SQLite’s default mode is a bottleneck
- How logging affects throughput
- Whether directory creation or YAML loading slows routing
- How the engine behaves under burst traffic and connection churn
These are the areas where improvements are both high‑impact and easy to maintain.

## What we intentionally avoid
Our maintainability rules exclude:
- Parser rewrites
- Pydantic model reduction
- Object‑creation minimization
- Vectorization or compiled paths
- Aggressive caching
- Complex batching strategies
- Custom logging frameworks
- Multiprocessing architectures
This keeps the codebase clean and predictable.

## What we add because it matters in real deployments
Two additional dimensions strengthen the benchmark:
- Stability under load — memory growth, connection handling, ACK correctness
- Predictability — latency variance, burst behavior, slow‑client handling
These matter more than raw speed in healthcare systems.

## Expected outcomes from the first run
A five‑minute run won’t give perfect statistical stability, but it will reveal:
- whether the MLLP server can sustain 60 msg/s steady load
- whether bursts cause ACK delays
- whether file I/O or logging becomes the bottleneck
- whether the concurrency model needs to be upgraded
- whether SQLite (if enabled) introduces latency spikes
- whether memory usage stays stable
This is enough to validate the harness and decide what to refine before running a longer 20‑minute or 1‑hour benchmark.

## With this structure in place, you can now:
- compare engine versions
- compare configuration changes
- detect regressions
- tune connection backlog, thread pools, ACK handling
- export results to CSV/JSON later if needed
Your benchmark is now a proper load‑testing tool.

## Sample Run Output

$ python3 -m benchmarking.run_benchmark --duration 45
Starting benchmark for 45 seconds...
Target: 127.0.0.1:2575
Loaded 3 HL7 message templates.
[Progress]   5.4s elapsed,  39.6s remaining | sent=72 conn_fail=0 ack_fail=3
[Progress]  10.7s elapsed,  34.3s remaining | sent=144 conn_fail=13 ack_fail=6
[Progress]  15.8s elapsed,  29.2s remaining | sent=210 conn_fail=31 ack_fail=6
[Progress]  21.1s elapsed,  23.9s remaining | sent=282 conn_fail=47 ack_fail=6
[Progress]  26.3s elapsed,  18.7s remaining | sent=349 conn_fail=63 ack_fail=6
[Progress]  31.7s elapsed,  13.3s remaining | sent=418 conn_fail=80 ack_fail=6
[Progress]  36.9s elapsed,   8.1s remaining | sent=487 conn_fail=98 ack_fail=6
[Progress]  42.2s elapsed,   2.8s remaining | sent=560 conn_fail=114 ack_fail=6

--- Benchmark Summary ---
Messages sent: 600
Connection failures: 123
ACK failures: 6
Error types: {'ack_timeout', 'conn_timeout'}
ACK latency p50: 39.43 ms
ACK latency p95: 61.70 ms
ACK latency p99: 72.71 ms
Throughput: 13.33 msg/sec
