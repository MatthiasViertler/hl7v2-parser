# Server Tuning

Our benchmarking results already gave us a crystal‑clear picture of what’s happening inside our HL7 server, 
and now we can start shaping it into the high‑throughput, low‑latency engine it wants to be.

## The Core Issue: Your Server Is Functionally Single‑Threaded
Our throughput curve and latency histogram told the whole story:
- Throughput stays flat no matter how many workers we throw at it
- ACK latency has a tight cluster + a long tail
- ACK failures increase with concurrency
- CPU is idle while workers time out
This is the signature of a server that:
- accepts multiple connections
- but processes HL7 messages one at a time
- inside a blocking loop
- with ACK generation tied to message processing
This is extremely common in MLLP servers — and extremely fixable.

## The First Big Tuning Step: Decouple Accept Loop from Message Processing
Right now, our server probably looks like this:
    accept connection
    read message
    parse message
    validate message
    route message
    write ACK
    close or reuse connection

```[accept] → [parse] → [validate] → [route] → [ack] → [done]```

This is a serial pipeline.

```
We want this instead:
accept connection
↓
enqueue message
↓
return immediately
↓
worker pool processes messages in parallel
↓
ACK is generated independently

[accept] → [enqueue] → [return immediately]
                     ↓
                [worker pool]
                     ↓
           [parse → validate → route → ack]

```

This single architectural change unlocks:
- parallel parsing
- parallel validation
- parallel routing
- parallel ACK generation
- stable latency
- linear throughput scaling
And it’s not a huge rewrite — it’s a restructuring.

## Step-by-Step Plan to Transform our Server
Here’s the steps we'll take to get there:

1. Introduce a Message Queue
A simple queue.Queue() or collections.deque() is enough.
The accept loop becomes:

```
while True:
    msg = read_hl7_message(sock)
    queue.put(msg)
```

No parsing, no validation, no routing — just enqueue.

2. Add a Worker Pool
Use ThreadPoolExecutor or our own worker threads:
executor = ThreadPoolExecutor(max_workers=8)

Each worker:
- pulls a message from the queue
- parses it
- validates it
- routes it
- generates ACK
- sends ACK back
This is where throughput scales.

```
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=8)
```

3. ACK Generation Must Be Non‑Blocking
Right now, ACK generation is tied to the same thread that reads the message.
We want:
- ACK created immediately after parsing
- ACK sent back without waiting for routing or DB writes
This alone cuts latency dramatically.

4. Make Routing Asynchronous
Routing is often the slowest part (DB writes, HTTP calls, file writes, profile lookups).
Move it into the worker pool. ACK should not wait for routing.

```
executor.submit(route_message, parsed_msg)
```

5. Add Backpressure
If the queue grows too large:
- reject new messages
- or slow down reads
- or return a “busy” MLLP response
This prevents runaway latency.

## What Happens After These Changes

Our throughput curve will look like this:
| Workers  | Expected Throughput | 
|    1     | ~ 28 msg/sec        | 
|    2     | ~ 55 msg/sec        | 
|    4     | ~110 msg/sec        | 
|    8     | ~200 msg/sec        | 
|   16     | CPU saturation      | 


Our latency histogram will:
- lose the long tail
- become tight and stable (cluster around 5-15ms)
- spikes drop from 30–70 ms → 5–15 ms
Our ACK failures will drop to zero.
Our CPU will finally be used - no more idle cores.

