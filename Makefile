# Benchmark configuration (override via: make run-benchmark BENCHMARK=--sweep)
BENCHMARK ?= --max-throughput
DURATION ?= 10
EXTRA ?=

# ---------------------------------------------------------
# HL7 Engine Makefile
# ---------------------------------------------------------

PYTEST=pytest
ROUTED_DIR=routed
DB_PATH=hl7engine/messages.db
BENCH=python3 -m benchmarking.run_benchmark

# ---------------------------------------------------------
# INSTALL packages in editable mode for your Python env
# ---------------------------------------------------------
install:
	pip install -e .

# ---------------------------------------------------------
# HL7 SERVER Targets
# ---------------------------------------------------------
run-server:
	@echo "Starting HL7 MLLP server..."
	python3 -m hl7engine.mllp_server

restart-server:
	make kill-server
	make run-server

server-status:
	@echo "Checking for running HL7 MLLP server..."
	@ps aux | grep "hl7engine.mllp_server" | grep -v grep || echo "No server running."

# ---------------------------------------------------------
# Kill own running HL7 MLLP server
# ---------------------------------------------------------
kill-own-server:
	@echo "Killing HL7 MLLP server..."
	@ps aux | grep "hl7engine.mllp_server" | grep -v grep | awk '{print $$2}' | xargs -r kill
	@echo "Done."

# ---------------------------------------------------------
# Kill any running HL7 MLLP server
# ---------------------------------------------------------
kill-server:
	@echo "Killing any running HL7 MLLP server processes..."
	@pkill -f "hl7engine.mllp_server" || true
	@echo "Done."

# ---------------------------------------------------------
# RUN UI (simple static file server)
# ---------------------------------------------------------
run-ui:
	@echo "Serving UI at http://localhost:8000"
	cd ui && python3 -m http.server 8000

# ---------------------------------------------------------
# DATABASE MANAGEMENT
# ---------------------------------------------------------
seed-db:
	python3 tools/regenerate_seed_db.py

clean-db:
	@if [ -f "$(DB_PATH)" ]; then \
		echo "Removing SQLite DB..."; \
		rm $(DB_PATH); \
	fi

reset:
	make clean-db
	make clean-routed

# ---------------------------------------------------------
# ROUTED MESSAGE CLEANUP
# ---------------------------------------------------------
clean-routed:
	@if [ -d "$(ROUTED_DIR)" ]; then \
		echo "Cleaning routed/ folders..."; \
		find $(ROUTED_DIR) -type f -name "*.hl7" -delete; \
		find $(ROUTED_DIR) -type d -empty -delete; \
	fi

# ---------------------------------------------------------
# TESTING
# ---------------------------------------------------------
test:
	$(PYTEST) $(PYTEST_FLAGS)

test-file:
	$(PYTEST) -q $(FILE)

test-name:
	$(PYTEST) -q -k $(NAME)

benchmark-tests:
	$(PYTEST) $(PYTEST_FLAGS) --durations=0

coverage:
	$(PYTEST) --cov=hl7engine --cov-report=term-missing

# ---------------------------------------------------------
# BENCHMARKING SUITE
# ---------------------------------------------------------
bench-max:
	$(BENCH) --duration 30 --max-throughput

bench-conn:
	$(BENCH) --duration 30 --conn-stress

bench-sweep:
	$(BENCH) --duration 10 --sweep

bench-visualize:
	$(BENCH) --visualize $(FILE)

# ---------------------------------------------------------
# Run benchmark against a temporary server instance
# ---------------------------------------------------------
run-benchmark-max-throughput-against-server:
	@echo "Starting HL7 MLLP server in background..."
	@python3 -m hl7engine.mllp_server &
	@SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	echo "Waiting for server to start..."; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --max-throughput; \
	echo "Stopping server..."; \
	pkill -f "hl7engine.mllp_server" || true; \
	echo "Done."

run-benchmark-sweep-against-server:
	@echo "Starting HL7 MLLP server in background..."
	@python3 -m hl7engine.mllp_server &
	@SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	echo "Waiting for server to start..."; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --sweep; \
	echo "Stopping server..."; \
	pkill -f "hl7engine.mllp_server" || true; \
	echo "Done."

# ---------------------------------------------------------
# Run any benchmark against a temporary server instance
# ---------------------------------------------------------
run-benchmark:
	@echo "Starting HL7 MLLP server in background..."
	@python3 -m hl7engine.mllp_server &
	@SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	echo "Waiting for server to start..."; \
	sleep 1; \
	echo "Running benchmark: $(BENCHMARK)"; \
	$(BENCH) --duration $(DURATION) $(BENCHMARK) $(EXTRA); \
	echo "Stopping server..."; \
	pkill -f "hl7engine.mllp_server" || true; \
	echo "Done."

# ---------------------------------------------------------
# HELP
# ---------------------------------------------------------
help:
	@echo "Available commands:"
	@echo ""
	@echo "  make install           - Install project in editable mode"
	@echo ""
	@echo "  make server-status     - Check MLLP server status"
	@echo "  make run-server        - Run MLLP server that hosts listener"
	@echo "  make restart-server    - Restart MLLP server that hosts listener"
	@echo "  make kill-own-server   - Kill own HL7 MLLP server if still running (safer)"
	@echo "  make kill-server       - Kill any running HL7 MLLP server"
	@echo "  make run-ui            - Run UI server to view HL7 messages"
	@echo ""
	@echo "  make test              - Run full test suite"
	@echo "  make test-file FILE=…  - Run a specific test file"
	@echo "  make test-name NAME=…  - Run a specific test by name"
	@echo "  make benchmark-tests   - Show slowest tests"
	@echo "  make coverage          - Run coverage report"
	@echo ""
	@echo "  make bench-max         - Max throughput benchmark"
	@echo "  make bench-conn        - Connection-only stress test"
	@echo "  make bench-sweep       - Concurrency sweep"
	@echo "  make bench-visualize FILE=…"
	@echo "                         - Visualize a benchmark JSON file"
	@echo "  make run-benchmark     - Run any benchmark against a temporary server instance. Usage:"
	@echo "                             + make run-benchmark BENCHMARK=--sweep"
	@echo "                             + make run-benchmark BENCHMARK=--conn-stress DURATION=30"
	@echo "                             + make run-benchmark BENCHMARK=--max-throughput EXTRA=\"--warmup 5\""
	@echo ""
	@echo "  make clean-db          - Remove SQLite DB"
	@echo "  make clean-routed      - Remove routed HL7 files"
	@echo "  make reset             - Clean DB and routed folders"
