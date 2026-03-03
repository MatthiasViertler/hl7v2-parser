Developer Guide
This guide explains how to set up the development environment, run the HL7v2 engine, understand its internal components, extend routing and validation rules, add new message types, work with the database, and run the test suite. It is intended for developers who want to contribute to or customize the system.

1. Project Structure
The project is organized into clear domains to keep code, configuration, runtime data, and documentation separate.
hl7v2-parser/
│
├── hl7engine/          # Core application package
├── config/             # YAML configuration (routing, validation)
├── data/               # Runtime DB (ignored by Git)
│   └── seed/           # Seed DB (committed)
├── routed/             # Routed HL7 messages
├── received/           # Optional raw input capture
├── logs/               # Runtime logs
├── scripts/            # Shell scripts for manual testing
├── tools/              # Helper scripts (seed DB generator, profile tools)
├── tests/              # Full test suite
└── docs/               # Architecture + diagrams


Each folder has a single responsibility, and the engine loads configuration and data from predictable locations.

2. Development Environment Setup
Requirements
- Python 3.10+
- pip or Poetry
- SQLite (bundled with Python)
- Optional: VS Code with Python extension
Installation
git clone <repo-url>
cd hl7v2-parser
pip install -e .


This installs the package in editable mode so changes to the source code take effect immediately.
Runtime directories
The following directories must exist before running the engine:
mkdir -p routed received logs data


The runtime DB is created automatically from the seed DB if missing.

3. Running the Engine
Start the MLLP server
python -m hl7engine.mllp_server


This starts a blocking TCP server on the configured port (default: 2575).
Send a test HL7 message
You can use netcat:
printf "\x0bMSH|^~\\&|SRC|HOSP|EHR|HOSP|20240220||ORU^R01|CTRL001|P|2.5.1\rPID|1||12345^^^HOSP^MR||Doe^John\r\x1c\x0d" | nc localhost 2575


Or use one of your shell scripts in scripts/.
View routed messages
ls routed/ORU/R01/


View stored messages via API
Start the API:
python -m hl7engine.api


Open:
http://localhost:8000/messages



4. Configuration
Routing (config/routes.yaml)
Defines where messages are written based on message type and trigger.
Example:
ORU:
  R01: routed/ORU/R01
ADT:
  A01: routed/ADT/A01


Routing rules are hierarchical:
- If msg_type exists and trigger exists → use that folder.
- If only msg_type exists → use its parent folder.
- Otherwise → fallback or error.
Validation (config/validation.yaml)
Defines required segments for each message type/trigger.
Example:
ORU:
  R01:
    required_segments:
      - PID
      - OBR


Validation ensures structural correctness before routing.

5. Core Components
MLLP Server (hl7engine/mllp_server.py)
- Accepts TCP connections.
- Extracts MLLP‑framed HL7 messages.
- Sends ACK/NACK responses.
HL7 Listener (hl7engine/hl7_listener.py)
- Orchestrates parsing → validation → routing → DB storage.
- Generates ACK/NACK.
Parser (hl7engine/parse_hl7.py)
- Splits message into segments and fields.
- Extracts message type, trigger, control ID.
Validator (hl7engine/validator.py)
- Loads validation.yaml.
- Ensures required segments exist.
- Returns AA or AR.
Router (hl7engine/router.py)
- Loads routes.yaml.
- Determines output folder.
- Writes <control_id>.hl7.
Database Layer (hl7engine/db.py)
- Stores message metadata + raw HL7.
- Creates runtime DB from seed DB if missing.
REST API (hl7engine/api.py)
- Exposes stored messages.
- Provides UI backend.

6. Seed Database Workflow
Seed DB location
data/seed/hl7_messages_demo.db


This file is committed once and never changes.
Runtime DB
data/hl7_messages.db


Ignored by Git.
Regenerate seed DB
make seed-db


Reset runtime DB before tests
make clean-db


7. Extending the System
Add a new message type (e.g., ORU^R30)
- Update routes.yaml:
ORU:
  R30: routed/ORU/R30

- Update validation.yaml:
ORU:
  R30:
    required_segments:
      - PID
      - OBR

- Add tests:
tests/test_XX_oru_r30.py

- Restart the engine.
No code changes required unless the message type has special logic.

8. Logging
Logs are written to:
logs/hl7engine.log

Log levels can be configured in config/logging.yaml (optional).

Logging is controlled through a YAML file located at config/logging.yaml. This file follows Python’s logging.config.dictConfig structure and allows developers to adjust log levels, formats, and output destinations without modifying application code. The configuration defines two handlers: a console handler for real‑time feedback and a rotating file handler for persistent logs. The console handler defaults to a higher threshold to avoid noise, while the file handler captures more detailed information for debugging.
The logger named hl7engine is configured separately from the root logger so that internal engine modules can emit detailed logs without affecting third‑party libraries. This separation makes it easier to debug the engine while keeping external noise low. The file handler writes to logs/hl7engine.log and rotates automatically when the file reaches 1 MB, keeping log storage predictable.
A typical configuration looks like this:
version: 1

formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: standard
    filename: logs/hl7engine.log
    maxBytes: 1048576
    backupCount: 5

loggers:
  hl7engine:
    level: DEBUG
    handlers: [console, file]
    propagate: no

root:
  level: INFO
  handlers: [console]


The engine loads this configuration at startup. If the file is missing, it falls back to a simple default configuration using logging.basicConfig. Developers can adjust verbosity by changing the handler levels or the logger level. For example, setting the console handler to DEBUG is useful during development, while raising it to WARNING reduces noise in production. The file handler can also be tuned to capture only warnings or errors if disk usage is a concern.

9. Testing
Run all tests with pytest
pytest -vv

Clean DB:
make clean-db

Run tests:
make test

If you want to run clean-db every time you run 'make test', simply uncomment the 'clean-db' in the makefile target

Test categories
- Parser tests
- Validator tests
- Router tests
- MLLP integration tests
- Routing stress tests
- YAML schema tests
Test fixtures
- Clean routed/ before each test.
- Reset runtime DB before test session.

## Developer Test Tools
Two standalone command‑line tools are available under the  directory to help developers debug HL7 messages without running the full MLLP server. Both tools use the same parsing and configuration logic as the production engine, making them ideal for rapid iteration during development.

### Validation Test Harness ()
This tool loads an HL7 message from a file, parses it using hl7apy, applies the YAML validation rules from , and prints a human‑readable validation report. It mirrors the exact behavior of the engine’s  class.
#### Usage
  python -m tools.validate_message <path_to_hl7_file>
#### Example
  python -m tools.validate_message samples/sample_oru.hl7

#### What it shows
• 	Message type (MSH‑9.1)
• 	Trigger event (MSH‑9.2)
• 	Control ID (MSH‑10)
• 	All segments found in the message
• 	Validation result (AA or AR)
• 	Error message if validation failed
This tool is useful for debugging new message types, adjusting validation rules, or verifying that incoming HL7 messages conform to expected structure.

### Routing Test Harness ()
This tool determines how a message would be routed based on the rules in . It extracts the message type and trigger using hl7apy, then calls the engine’s  class to resolve the routing path.
#### Usage
  python -m tools.route_message <path_to_hl7_file>
#### Example
  python -m tools.route_message samples/sample_oru.hl7

#### What it shows
• 	Message type and trigger
• 	Control ID
• 	Parent folder for the message type
• 	Final routed folder (trigger‑specific or fallback)
• 	Whether the routing used a trigger‑specific rule or a fallback rule
This tool is ideal for verifying routing behavior, testing new routing rules, and ensuring folder structures are correct.

### How These Tools Fit Into Development
These harnesses provide a fast feedback loop for developers working on:
• 	new message types
• 	updated validation rules
• 	routing configuration changes
• 	troubleshooting malformed HL7 messages
• 	onboarding new contributors
Because they use the same parser, validator, and router as the engine, they give accurate results without requiring the MLLP server or API to be running.

10. Troubleshooting
Messages not routing
- Check routes.yaml.
- Ensure folders exist.
- Verify msg_type and trigger extracted correctly.
Validation failures
- Check validation.yaml.
- Inspect missing segments.
No messages in DB
- Ensure runtime DB exists.
- Check file permissions.
- Verify listener is calling DB layer.
ACK not returned
- Check MLLP framing.
- Inspect logs for exceptions.

## Debugging effectively
Debugging the HL7 engine relies on a combination of log inspection, targeted log‑level adjustments, and controlled test messages. The logging configuration in config/logging.yaml allows you to tune verbosity per subsystem, which is the most effective way to understand how messages move through the pipeline. Raising the log level for the hl7engine logger to DEBUG exposes detailed information about parsing, validation, routing, and database operations, while keeping external library noise low. During development, this level of detail is helpful for verifying that message types and triggers are extracted correctly and that routing rules behave as expected.
Routing issues are easiest to diagnose by enabling DEBUG logs for the router and then sending a small, known HL7 message. The logs show the extracted msg_type, trigger, the matched route from routes.yaml, and the final output path. If a message ends up in the wrong folder or fails to route, the logs will typically indicate whether the message type was missing from the configuration or whether the trigger fell back to a parent folder. Inspecting the resulting file in routed/ confirms whether the routing logic matched expectations.
MLLP‑level debugging focuses on message framing and ACK/NACK behavior. When the MLLP server runs with DEBUG logging, it logs the raw framed message, the extracted HL7 payload, and the ACK returned to the sender. This is useful when messages appear truncated, doubled, or malformed. If the sender does not receive an ACK, checking the logs for framing errors or exceptions in the listener is the fastest way to identify the cause.
Validation debugging is straightforward: the validator logs which required segments were found or missing and whether the message passed or failed. When a message is unexpectedly rejected, the logs show the exact segment names the validator expected, making it easy to adjust validation.yaml or correct the test message.
Database debugging is rarely needed, but enabling DEBUG logs for the database layer shows each insert operation and the assigned message ID. This helps confirm that messages are being stored and that the runtime database is being reset correctly during tests.
A simple and effective debugging workflow is to temporarily raise the console handler to DEBUG, send a single test message, and watch the full pipeline unfold in real time. This provides immediate visibility into parsing, validation, routing, and ACK generation, making it easier to pinpoint issues without digging through large log files.

A focused validation‑debugging section helps developers understand exactly why a message passed or failed, which segments were missing, and how to adjust rules or test data. Validation is one of the most common sources of confusion in HL7 pipelines, so having a clear workflow and recommended log settings makes troubleshooting much easier.

### Debugging validation issues
Validation problems usually fall into three categories: missing required segments, unexpected message structure, or mismatches between the message and the rules in validation.yaml. The validator logs each step of the process when DEBUG logging is enabled, which makes it straightforward to trace what happened.
What the validator checks
- The message type and trigger event extracted by the parser.
- Whether validation.yaml defines rules for that combination.
- The list of required segments for that message type.
- Whether each required segment appears at least once.
- Whether the message structure is parseable (segment boundaries, field separators, etc.).
How to enable detailed validation logs
The easiest way to see exactly what the validator is doing is to temporarily raise the log level for the validator module:
loggers:
  hl7engine.validator:
    level: DEBUG
    handlers: [console, file]
    propagate: no


This produces detailed output such as:
[DEBUG] validator: Checking required segments for ORU^R01
[DEBUG] validator: Required: ['PID', 'OBR']
[DEBUG] validator: Found segments: ['MSH', 'PID', 'OBR', 'OBX']
[DEBUG] validator: Validation passed (AA)

Or, for failures:
[DEBUG] validator: Missing required segment: OBR
[DEBUG] validator: Validation failed (AR)

These logs immediately show whether the issue is in the message or in the configuration.

#### Common validation failure patterns
Missing required segments
This is the most frequent cause of AR responses. For example, if validation.yaml requires OBR but the message only contains PID and OBX, the validator will reject it.
Fix:
Either update the test message to include the missing segment or adjust validation.yaml if the rule is too strict.
Wrong message type or trigger
If the parser extracts ORU^R01 but the message is actually an ADT, the validator will load the wrong rule set.
Fix:
Check the MSH segment in the test message and ensure it matches the intended type.
Unexpected segment order
The validator does not enforce strict ordering, but malformed messages (e.g., missing segment delimiters) can cause segments to merge or disappear.
Fix:
Inspect the raw HL7 message for missing \r separators.
No rule defined for the message type
If validation.yaml does not contain an entry for a message type, the validator may fall back to a default rule or reject the message.
Fix:
Add a rule block for the message type and trigger.

#### Techniques for debugging validation quickly
1. Enable DEBUG logs for the validator only
This keeps console output readable while still showing detailed validation steps.
2. Send a minimal test message
Start with a simple ORU^R01 containing only MSH, PID, and OBR. Add segments incrementally until validation passes.
3. Compare the message against validation.yaml
Ensure the required segments list matches what the message actually contains.
4. Inspect the parsed structure
Enable DEBUG logs for the parser to confirm that segments are being extracted correctly.
5. Use the routed output
Even rejected messages are stored in the database and can be inspected through the API or UI.

####  A practical debugging workflow
- Set hl7engine.validator to DEBUG.
- Send a single test message.
- Watch the console logs to see which segments were found and which were missing.
- Adjust the message or the rule set.
- Repeat until validation passes.
This workflow is fast, predictable, and avoids digging through large log files.


11. Future Enhancements
- Async MLLP server
- Threaded routing queue
- PostgreSQL backend
- Message replay
- Metrics + monitoring
- UI improvements
