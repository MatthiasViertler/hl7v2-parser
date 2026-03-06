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

$ python3 -m benchmarking.run_benchmark --duration 60
Starting benchmark for 60 seconds...
Target: 127.0.0.1:2575
Loaded 3 HL7 message templates.
[Progress]   5.3s elapsed,  54.7s remaining | sent=70 conn_fail=0 ack_fail=2
[Progress]  10.4s elapsed,  49.6s remaining | sent=139 conn_fail=15 ack_fail=6
[Progress]  15.7s elapsed,  44.3s remaining | sent=209 conn_fail=32 ack_fail=6
[Progress]  20.9s elapsed,  39.1s remaining | sent=279 conn_fail=49 ack_fail=6
[Progress]  26.2s elapsed,  33.8s remaining | sent=352 conn_fail=69 ack_fail=6
[Progress]  31.6s elapsed,  28.4s remaining | sent=426 conn_fail=86 ack_fail=6
[Progress]  36.7s elapsed,  23.3s remaining | sent=496 conn_fail=101 ack_fail=6
[Progress]  41.8s elapsed,  18.2s remaining | sent=565 conn_fail=117 ack_fail=6
[Progress]  47.1s elapsed,  12.9s remaining | sent=636 conn_fail=137 ack_fail=6
[Progress]  52.3s elapsed,   7.7s remaining | sent=706 conn_fail=153 ack_fail=6
[Progress]  57.6s elapsed,   2.4s remaining | sent=776 conn_fail=172 ack_fail=6

--- Benchmark Summary ---
Messages sent: 807
Connection failures: 181
ACK failures: 6
Error types: {'ack_timeout', 'conn_timeout'}
ACK latency p50: 38.77 ms
ACK latency p95: 60.44 ms
ACK latency p99: 71.95 ms
Throughput: 13.45 msg/sec
-------------------------

### Interpretation: Where the bottleneck is
1) ACK handling is stable
Only 6 ACK failures across 807 messages.
Our p50/p95/p99 latencies are tight and healthy:
- p50 ≈ 39 ms
- p95 ≈ 60 ms
- p99 ≈ 72 ms
This is excellent for an HL7 MLLP engine under load.
It means:
- The engine processes messages reliably once a connection is established.
- ACK generation is not the bottleneck.
- Internal parsing + routing + ACK logic is performing well.

2) Connection acceptance is the bottleneck
181 connection failures in 60 seconds is significant.
This is the signature of an MLLP listener that:
- accepts connections too slowly
- has a small backlog queue
- is single‑threaded or single‑process
- is blocked while processing messages
- or is using synchronous I/O without concurrency
Our burst workers are hammering the accept loop, and the engine can’t keep up.
This is exactly why the benchmark uses both long‑lived and burst workers — they expose different weaknesses.

3) Throughput: 13.45 msg/sec
This is the sustained throughput of our engine under mixed load.
Given:
- 2 long‑lived workers at 30 msg/sec each
- burst workers adding spikes
…our engine is only able to process ~13.5 msg/sec.
This is not unusual for a synchronous HL7 MLLP implementation, but it’s a clear indicator of where to optimize next.

### What to do next (in your HL7 engine)
Based on our results, the next tuning steps for the engine itself are:
1) Increase the TCP backlog
On Linux, this is controlled by:
- listen(backlog) in your server code
- /proc/sys/net/core/somaxconn
- /proc/sys/net/ipv4/tcp_max_syn_backlog

2) Ensure the accept loop is non‑blocking
If our engine processes messages on the same thread that accepts connections, it will choke under burst load.

3) Move message processing to worker threads
Accept → hand off → return to accept loop immediately.

4) Consider persistent connections
If our engine expects clients to keep connections open, burst‑style traffic will overwhelm it.
