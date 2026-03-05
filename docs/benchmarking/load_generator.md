# Load Generator

A Python‑based load generator gives you the most flexibility for shaping realistic HL7 traffic, and it keeps everything in one ecosystem so you can evolve the benchmark alongside the engine. With the five‑minute mixed‑pattern run confirmed, the next step is to outline the generator in a way that is maintainable, reproducible, and aligned with the traffic patterns you want to simulate.

## Core components of the Python load generator
A maintainable generator needs three building blocks that work together without becoming a complex framework.
Long‑lived stream workers
These maintain a persistent TCP socket for the full duration and send messages at a steady rate. They stress sustained throughput, framing, and ACK turnaround.
- One worker per long‑lived connection
- A simple loop: send → wait for ACK → sleep to maintain rate
- Randomized message types (ADT, ORM, ORU)
- No reconnection unless the server drops the socket
Short‑lived burst workers
These open a connection, send a small batch, and disconnect. They stress connection setup, teardown, and routing latency under churn.
- One worker per burst
- Randomized batch size (5–15 messages)
- Randomized inter‑burst delay (100–500 ms)
- Randomized message sizes
Coordinator
This orchestrates the five‑minute run:
- Starts long‑lived workers
- Starts burst workers on a schedule
- Tracks start/end timestamps
- Collects ACK latency and connection timing
- Stops everything cleanly at the five‑minute mark
This structure keeps the generator readable and easy to extend.

## How the generator measures performance
The goal is to capture enough detail to understand where time is spent without adding complexity.
Per‑message metrics
- ACK turnaround time
- Message size
- Message type
- Connection ID
Per‑connection metrics
- Connection setup time
- Connection teardown time
- Total messages sent
- Total ACKs received
Global metrics
- Total throughput
- p50/p95/p99 latency
- Error counts (timeouts, resets, malformed ACKs)
These metrics give you a clear picture of how the engine behaves under mixed load.

# Expected behavior during the five‑minute run
A short run is ideal for validating the harness and spotting early bottlenecks.
Long‑lived streams
You should see stable throughput and relatively consistent ACK latency. Any drift or spikes usually point to:
- file I/O pressure
- logging overhead
- SQLite locking
- thread scheduling issues
Short‑lived bursts
You should see higher latency variance and occasional spikes. These spikes reveal:
- connection setup overhead
- routing delays under churn
- ACK queuing effects
Combined load
This is where the most interesting behavior emerges:
- fairness between clients
- latency spikes during bursts
- CPU saturation points
- memory stability
This combined scenario is the closest to real hospital traffic.

## How the generator measures performance
The generator should collect metrics that help you understand where time is spent without adding complexity.
Per‑message metrics
- ACK turnaround time
- Message type and size
- Connection ID
Per‑connection metrics
- Connection setup time
- Connection teardown time
- Total messages sent and acknowledged
Global metrics
- Total throughput
- p50/p95/p99 latency
- Error counts (timeouts, resets, malformed ACKs)
These metrics give you a clear picture of how the engine behaves under mixed load.

## Implementation Architecture
- A clean, maintainable thread‑based load generator
- Realistic long‑lived and short‑lived connection behavior
- Accurate ACK latency measurement
- Minimal overhead so the benchmark reflects your server, not the generator
- A structure that can later be extended with asyncio for extreme concurrency
