# Benchmark Architecture Considerations

## Benchmarking goals
The engine has three performance‑critical areas:
• 	MLLP ingestion: how fast messages can be accepted, framed, and handed to the listener.
• 	Processing pipeline: parsing, validation, routing, and DB writes.
• 	I/O subsystems: SQLite writes, file writes, and logging.
A good benchmarking plan should measure each area independently and then measure end‑to‑end throughput.

## What to measure
MLLP throughput
This captures how many HL7 messages per second the server can ingest.
• 	Time to accept a connection.
• 	Time to read and deframe messages.
• 	Time to hand off to the listener.
• 	Behavior under multiple simultaneous connections.
Processing latency
This is the time from receiving raw HL7 to generating ACK/NACK.
• 	Parsing time.
• 	Validation time.
• 	Routing time (file write).
• 	DB write time.
• 	ACK generation time.
I/O performance
This is where most bottlenecks usually appear.
• 	SQLite write latency (normal vs WAL mode).
• 	File write latency (with and without fsync).
• 	Logging overhead (console vs file handler).
End‑to‑end throughput
This is the real‑world metric: messages per second under load.
• 	Single‑threaded baseline.
• 	Multi‑threaded or async MLLP server.
• 	Different message sizes (ADT vs ORU with many OBX segments).
• 	Different routing patterns (deep folder structures vs flat).

## How to benchmark
Synthetic HL7 load generator
You need a tool that can:
• 	Open many MLLP connections.
• 	Send messages at controlled rates (e.g., 10, 100, 500 msg/s).
• 	Measure round‑trip ACK latency.
• 	Simulate real‑world patterns (bursts, steady streams, parallel senders).
This can be a Python script or an external tool like hl7apy or mirth-test-tool.
Instrumentation inside the engine
Add timestamps at key points:
• 	t0: message received by MLLP server.
• 	t1: message handed to listener.
• 	t2: parsing done.
• 	t3: validation done.
• 	t4: routing done.
• 	t5: DB write done.
• 	t6: ACK returned.
This gives you a detailed latency profile.
Logging for benchmarking
Use a dedicated logger or JSON logs with fields:
• 	msg_type
• 	trigger
• 	control_id
• 	latency_ms
• 	stage_time
• 	thread_id
This makes it easy to analyze results later.

## What improvements to benchmark next
SQLite WAL mode
Expected benefits:
• 	Faster writes.
• 	Better concurrency.
• 	Reduced locking.
Benchmark:
• 	Normal mode vs WAL.
• 	Single writer vs multiple writers.
• 	Large batches of messages.
MLLP concurrency model
Your current server is single‑threaded and sequential. Benchmark:
• 	Single‑threaded baseline.
• 	Thread‑per‑connection model.
• 	Thread pool.
• 	Asyncio‑based MLLP server.
Measure:
• 	Throughput under load.
• 	ACK latency.
• 	CPU usage.
File write optimization
Benchmark:
• 	With fsync vs without fsync.
• 	Buffered writes vs unbuffered.
• 	Writing to SSD vs HDD (if applicable).
• 	Folder depth impact.
Logging overhead
Benchmark:
• 	Console + file logging.
• 	File‑only logging.
• 	Logging disabled.
• 	JSON logs vs plain text.
Logging can easily consume 20–40% of processing time in Python.

## How to structure the benchmarking plan
Phase 1 — Baseline
Measure the system exactly as it is now.
- Single‑threaded MLLP server.
- SQLite default mode.
- Full logging.
- fsync enabled.
This gives you the “v0.5.0 baseline”.
Phase 2 — Database improvements
Enable WAL mode and measure again.
- Expect 2–10× faster writes.
- Expect lower ACK latency.
Phase 3 — MLLP concurrency
Introduce threading or asyncio.
- Expect linear scaling up to CPU limits.
- Measure how many parallel connections the engine can sustain.
Phase 4 — File I/O tuning
Disable fsync or batch writes.
- Expect significant latency reduction.
- Measure risk of data loss under crash scenarios.
Phase 5 — Logging optimization
Reduce logging overhead.
- Expect smoother throughput.
- Measure CPU usage drop.

===========
# Restructuring Limitations

I don't want to optimize sacrificing code maintainability. So I don't want to do:
- Replacing slow Python loops with vectorized or compiled paths
- Reducing object creation (especially Pydantic models)
And depending on impact, I might not want to:
- Caching parsed routes
- Using faster HL7 parsing strategies

## What changes based on your maintainability rules

Your restrictions remove entire classes of micro‑optimizations:
- No compiled paths, vectorization, or low‑level rewrites.
- No object‑creation minimization or Pydantic bypassing.
- No aggressive caching unless the benefit is large and the logic stays simple.
- No parser swaps unless the current parser is proven to be the bottleneck.
This shifts the focus toward architecture, concurrency, and I/O, which are the areas where Python systems gain the most performance without sacrificing clarity
===========


# Plan Considerations

Your priorities give us a very clean boundary for how to approach performance work: you want the engine to get faster, but not at the cost of readability, maintainability, or architectural clarity. That’s a strong constraint, and it actually helps us focus on the optimizations that matter most for a real‑world HL7 router.

What your constraints imply for the optimization strategy
## What we will not do
- No rewriting hot loops in Cython, Rust, or vectorized NumPy.
- No replacing Pydantic with hand‑rolled dataclasses.
- No micro‑optimizing object creation.
- No exotic HL7 parsers that make the code harder to understand.
- No caching strategies that complicate correctness unless the gain is substantial.
This keeps the codebase clean, Pythonic, and easy to maintain.

## What we should focus on instead
These are the areas where Python systems typically gain the most performance without sacrificing maintainability.
1) I/O and filesystem behavior
HL7 routing is I/O‑heavy. The biggest wins usually come from:
- Reducing filesystem calls (stat, exists, mkdir)
- Avoiding repeated YAML loads
- Using buffered writes instead of many small writes
- Ensuring directory structure is created once, not per message
These changes are simple, readable, and safe.
2) Concurrency model
Your MLLP listener and routing pipeline can benefit from:
- Async I/O (if your architecture supports it)
- ThreadPoolExecutor for file writes
- Avoiding blocking operations in the main loop
This improves throughput without touching the parsing logic.
3) Message flow architecture
Small structural improvements can have large effects:
- Avoiding unnecessary deep copies
- Passing around lightweight objects (e.g., dicts) instead of full models when possible
- Ensuring the routing decision tree is O(1)
These changes keep the code clean and predictable.
4) Profiling to find real bottlenecks
Before optimizing anything, we should measure:
- CPU hotspots (cProfile, pyinstrument)
- I/O waits (strace, perf)
- Memory allocations (tracemalloc)
- Event loop latency (if async)
This ensures we only optimize what matters.

## What to benchmark first
To get a meaningful baseline inside your VM, we should measure:
Parsing throughput
- 1k, 10k, 50k messages
- Mixed ADT/ORM/ORU workloads
- Single-threaded and multi-threaded
Routing latency
- Time from message arrival → file write
- With and without YAML reloads
- With and without directory creation
MLLP server behavior
- Sustained throughput
- Burst handling
- Connection concurrency
These tests will tell us exactly where the time goes.

## A maintainability‑first optimization philosophy
Everything we do should follow these principles:
- Readable first: anyone can understand the code without comments.
- Predictable behavior: no hidden caches, no magic.
- Deterministic routing: correctness always beats speed.
- Replaceable components: parser, router, writer remain modular.
- Benchmark‑driven: no guessing, only measured improvements.
This keeps the project robust and future‑proof.

To move forward smoothly
The next step is to set up a baseline benchmark suite so we know where we stand before optimizing. A simple, clean structure is enough.

# Final Plan

Updated structure of the benchmarking plan
The core categories remain valid, but the emphasis changes.
MLLP throughput
This stays the top priority. It’s the most “pure” performance metric and the one least affected by internal design choices. We measure:
- Connection handling
- Message framing/deframing
- Hand‑off latency
- Behavior under concurrent senders
This aligns perfectly with your decision to start here.
Processing latency
Still important, but we drop any micro‑optimizations inside the parser or validator. We measure:
- Parsing time (as‑is, no parser swap)
- Validation time (as‑is)
- Routing time (file write)
- ACK generation
The goal is to understand the pipeline, not to rewrite it.
I/O performance
This becomes the most important optimization category because it offers large gains with minimal code changes.
We keep:
- SQLite WAL mode
- File write strategies (buffering, fsync)
- Logging overhead
We drop:
- Exotic filesystem tricks
- Complex caching layers
End‑to‑end throughput
This remains the “real‑world” metric. We measure:
- Single‑threaded baseline
- Threaded or async MLLP server
- Different message sizes
- Different routing patterns
No changes needed here.

Updated “How to benchmark”
The structure remains, but we simplify instrumentation and avoid over‑engineering.
Synthetic HL7 load generator
Still required. No change.
Instrumentation inside the engine
We keep the timestamp markers, but we avoid adding complex tracing frameworks. Simple, readable timestamps are enough.
Logging for benchmarking
We keep structured logs but avoid adding a full JSON logging subsystem unless needed. A simple structured format is fine.

Updated “What improvements to benchmark next”
This section changes the most.
SQLite WAL mode
Still a high‑impact, low‑complexity improvement. Keep it.
MLLP concurrency model
Still essential. Concurrency is where Python gains the most without sacrificing maintainability.
We keep:
- Single‑threaded baseline
- Thread‑per‑connection
- Thread pool
- Asyncio server
We drop:
- Any exotic concurrency models (multiprocessing, uvloop tuning, etc.)
File write optimization
We keep:
- fsync on/off
- buffered writes
- folder depth impact
We drop:
- batching writes (adds complexity)
- custom file writers
Logging overhead
We keep:
- console vs file
- file‑only vs disabled
- structured vs plain text
We drop:
- custom logging handlers
- async logging frameworks

Updated phased plan
This is the streamlined version that respects your constraints.
Phase 1 — Baseline
No change. This is your v0.5.0 performance baseline.
Phase 2 — Database improvements
Keep WAL mode. It’s simple and high‑impact.
Phase 3 — MLLP concurrency
This becomes the most important optimization phase. It’s where you’ll see the biggest gains without touching parsing logic.
Phase 4 — File I/O tuning
Keep fsync and buffering tests. Drop batching.
Phase 5 — Logging optimization
Keep it simple. Logging overhead is real and easy to measure.

What we drop entirely
These items are removed from the plan because they violate your maintainability constraints or offer poor ROI:
- Parser replacement
- Pydantic model reduction
- Object‑creation minimization
- Vectorization or compiled paths
- Aggressive caching
- Complex batching strategies
- Custom logging frameworks
- Multiprocessing architectures

What we add
Your constraints highlight two areas worth adding:
Stability under load
Measure:
- ACK correctness under high throughput
- Connection churn behavior
- Memory growth over long runs
Predictability
Measure:
- Latency variance (p95, p99)
- Behavior under burst traffic
- Behavior under slow clients
These matter more than raw speed in healthcare systems.

# What we can add next in the benchmark
Now that you’ve isolated the accept loop, we can go deeper.
Here are the next optional upgrades:
Step 5 — Max Throughput Mode
How many HL7 messages/sec can the server process when connections are stable?
Step 6 — Latency Under Saturation Mode
What happens to ACK latency when the server is overloaded?
Step 7 — Export histograms for connection times
Useful for diagnosing jitter.
Step 8 — Add a concurrency sweep
Automatically test with 1, 2, 4, 8, 16, 32 workers.
