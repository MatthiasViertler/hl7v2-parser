Benchmarking goals
The engine has three performance‑critical areas:
• 	MLLP ingestion: how fast messages can be accepted, framed, and handed to the listener.
• 	Processing pipeline: parsing, validation, routing, and DB writes.
• 	I/O subsystems: SQLite writes, file writes, and logging.
A good benchmarking plan should measure each area independently and then measure end‑to‑end throughput.

What to measure
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

How to benchmark
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

What improvements to benchmark next
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

How to structure the benchmarking plan
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
