.DEFAULT_GOAL := help

# Benchmark configuration (override via: make run-benchmark BENCHMARK=--sweep)
BENCHMARK ?= --max-throughput
DURATION ?= 10
EXTRA ?=

PYTEST=pytest

# ---------------------------------------------------------
# HL7 Engine Makefile
# ---------------------------------------------------------

ROUTED_DIR=routed
DB_PATH=data/hl7_messages.db
BENCH=python3 -m benchmarking.run_benchmark

HL7_ENGINE_LOG=hl7engine.log

# ---------------------------------------------------------
# PROMETHEUS
# ---------------------------------------------------------
PROM_DIR := /opt/prometheus
PROMETHEUS_BIN := /opt/prometheus/prometheus
PROM_RULES_SRC := $(shell pwd)/monitoring
PROM_RULES := recording_rules.yml alert_rules.yml prometheus.yml
PROM_CONFIG := $(shell pwd)/monitoring/prometheus.yml
PROM_LOG := prometheus.log
PROM_METRICS_URL := http://localhost:8010/metrics

# ---------------------------------------------------------
# GRAFANA (DEVELOPMENT SETTINGS)
# ---------------------------------------------------------
# APT INSTALL bin dir:
GRAFANA_DEV_BIN := $(HOME)/grafana/bin/grafana
GRAFANA_DEV_HOME := $(HOME)/grafana
GRAFANA_DEV_CONF := $(HOME)/grafana/conf/defaults.ini
GRAFANA_LOG := grafana.log
GRAFANA_DASH_SRC := $(shell pwd)/monitoring/dashboards
GRAFANA_PROVISIONING_FILE_SRC := $(shell pwd)/monitoring/dashboards/hl7.yaml
GRAFANA_DASH_DST := $(HOME)/grafana/conf/provisioning/dashboards

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

run-server-prom:
	@echo "Starting HL7 engine with Prometheus ..."
	python3 -m hl7engine.mllp_server --prometheus

run-server-prom-bg:
	@echo "Starting HL7 engine with Prometheus in background..."
	@nohup python3 -m hl7engine.mllp_server --prometheus > $(HL7_ENGINE_LOG) 2>&1 &
	@echo $$! > hl7engine.pid
	@echo "HL7 engine started (PID: $$(cat hl7engine.pid)). Logs: $(HL7_ENGINE_LOG)"

restart-server:
	make kill-own-server
	make run-server

restart-server-prom-bg:
	make kill-own-server
	make run-server-prom-bg

server-status:
	@echo "Checking for running HL7 MLLP server..."
	@ps aux | grep "hl7engine.mllp_server" | grep -v grep || echo "No server running."

server-status-all:
	@echo "=== HL7 Engine Status ==="
	@ps aux | grep "hl7engine.mllp_server" | grep -v grep || echo "No HL7 MLLP server running."

	@echo "\n=== REST API Status ==="
	@ps aux | grep "uvicorn hl7engine.api" | grep -v grep || echo "No REST API server running."

#	@echo "\n=== Prometheus Status ==="
	@$(MAKE) --no-print-directory prometheus-status

#	@echo "\n=== Grafana Status ==="
	@$(MAKE) --no-print-directory grafana-status

# ---------------------------------------------------------
# Kill own running HL7 MLLP server
# ---------------------------------------------------------
kill-own-server:
	@echo "Killing HL7 MLLP server..."
	@ps aux | grep "python3 -m hl7engine.mllp_server" | grep -v grep | awk '{print $$2}' | xargs -r kill
	@echo "Done."

# kill-own-server:
# 	@echo "Killing HL7 MLLP server..."
# 	@ps -eo pid,cmd | grep "[p]ython3 -m hl7engine.mllp_server" | awk '{print $$1}' | xargs -r kill
# 	@echo "Done."

# ---------------------------------------------------------
# Kill any running HL7 MLLP server (based on binary)
# ---------------------------------------------------------
kill-server:
	@echo "Killing any running HL7 MLLP server processes..."
	@pkill -f "hl7engine.mllp_server" || true
	@echo "Done."

# ---------------------------------------------------------
# Kill any running Prometheus server (based on binary)
# ---------------------------------------------------------
kill-prometheus-all:
	@echo "Stopping Prometheus server..."
	@pkill -f "/opt/prometheus/prometheus" || true
	@echo "Done."

# ---------------------------------------------------------
# Kill Prometheus server (based on PID)
# ---------------------------------------------------------
kill-prometheus:
	@if [ -f prometheus.pid ]; then \
		echo "Stopping Prometheus (PID: $$(cat prometheus.pid))..."; \
		kill $$(cat prometheus.pid) 2>/dev/null || true; \
		rm -f prometheus.pid; \
	else \
		echo "No prometheus.pid found. Killing by process name..."; \
		pkill -x "prometheus" 2>/dev/null || true; \
	fi
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
	make clean-results

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
# RESULTS JSON CLEANUP
# ---------------------------------------------------------
clean-results:
	rm -f benchmarking/results/run_*.json

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
# Do NOT kill server instance with 
#    pkill -f "hl7engine.mllp_server" || true;
# To not kill Prometheus server instance
# ---------------------------------------------------------
run-benchmark-max-throughput-against-server:
	@echo "Starting HL7 MLLP server in background..."
	@{ \
	python3 -m hl7engine.mllp_server &
	@SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	echo "Waiting for server to start..."; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --max-throughput; \
	echo "Stopping server..."; \
	kill $$SERVER_PID || true; \
	echo "Done."
	}

run-benchmark-sweep-against-server:
	@echo "Starting HL7 MLLP server in background..."
	@{ \
	python3 -m hl7engine.mllp_server &
	@SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	echo "Waiting for server to start..."; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --sweep; \
	echo "Stopping server..."; \
	kill $$SERVER_PID || true; \
	echo "Done."
	}

# ---------------------------------------------------------
# Run any benchmark against a temporary server instance
# Do NOT kill server instance with 
#    pkill -f "hl7engine.mllp_server" || true;
# To not kill Prometheus server instance
# ---------------------------------------------------------
run-benchmark:
#	@echo "Starting HL7 MLLP server in background..."
#	@{ \
#	python3 -m hl7engine.mllp_server & \
#	SERVER_PID=$$!; \
#	echo "Server PID: $$SERVER_PID"; \
#	echo "Waiting for server to start..."; \
#	sleep 1; \
#	echo "Stopping server..."; \
#	kill $$SERVER_PID || true;
	@{ \
	echo "Running benchmark: $(BENCHMARK)"; \
	$(BENCH) --duration $(DURATION) $(BENCHMARK) $(EXTRA); \
	echo "Done."; \
	}

# -----------------------------------------------------------
#   PROMETHEUS TARGETS
# -----------------------------------------------------------
# - $(shell pwd) ensures absolute paths
# - cd $(shell pwd) ensures Prometheus resolves relative paths inside YAML
# - Works from any directory, not just project root
# - Works from VS Code, PyCharm, terminals, CI, etc.
# - Background version logs cleanly
prometheus:
	@echo "Starting Prometheus using config: $(PROM_CONFIG)"
	@cd $(shell pwd) && $(PROMETHEUS_BIN) --config.file="$(PROM_CONFIG)"

prometheus-bg:
	@echo "Starting Prometheus in background using config: $(PROM_CONFIG)"
	@cd $(shell pwd) && nohup $(PROMETHEUS_BIN) --config.file="$(PROM_CONFIG)" > $(PROM_LOG) 2>&1 &
	@echo $$! > prometheus.pid
	@echo "Prometheus started in background (PID: $$(cat prometheus.pid)). Logs: $(PROM_LOG)"

# -----------------------------------------------------------
# This checks Prometheus Status:
# -----------------------------------------------------------
# - If Prometheus is running
# - Shows PID
# - Shows listening port
# - Shows the config file use
# -----------------------------------------------------------
prometheus-status:
#	@echo "Checking Prometheus status..."
	@echo "\n=== Prometheus Status ==="
	@if pgrep -x "$(notdir $(PROMETHEUS_BIN))" > /dev/null; then \
		pgrep -fl "$(notdir $(PROMETHEUS_BIN))"; \
	else \
		echo "Prometheus is NOT running."; \
	fi

# - Curl the /metrics endpoint
# - Fail gracefully if Prometheus is not running
# - Show the first few lines of metric
prometheus-test:
	@echo "Testing Prometheus /metrics endpoint..."
	@if curl -s $(PROM_METRICS_URL) | head -n 20; then \
		echo "\nPrometheus endpoint OK."; \
	else \
		echo "Prometheus endpoint NOT reachable."; \
	fi

restart-prometheus:
	@echo "Restarting Prometheus..."
	make kill-prometheus
	make prometheus-bg
	@echo "Prometheus restarted."

# -----------------------------------------------------------
# PROMETHEUS RULE SYNC / VALIDATION / RELOAD
# -----------------------------------------------------------

# Copy rule files into /opt/prometheus (requires sudo)
prometheus-sync-rules:
	@echo "Copying Prometheus rule/config files into $(PROM_DIR)..."
	@for f in $(PROM_RULES); do \
		echo "  - Copying $$f"; \
		sudo cp $(PROM_RULES_SRC)/$$f $(PROM_DIR)/$$f; \
	done
	@echo "Done."

# Validate Prometheus config + rules
prometheus-validate:
	@echo "Validating Prometheus configuration..."
	@cd $(PROM_DIR) && ./promtool check config prometheus.yml
	@echo "Validating rule files..."
	@cd $(PROM_DIR) && ./promtool check rules recording_rules.yml
	@cd $(PROM_DIR) && ./promtool check rules alert_rules.yml
	@echo "Validation OK."

# Reload Prometheus via SIGHUP
prometheus-reload:
	@echo "Reloading Prometheus configuration..."
	@if pgrep -x "prometheus" > /dev/null; then \
		pkill -HUP -x "prometheus"; \
		echo "Prometheus reloaded."; \
	else \
		echo "Prometheus is not running. Start it first."; \
	fi

# Full workflow: sync → validate → reload
prometheus-full-reload: prometheus-sync-rules prometheus-validate prometheus-reload
	@echo "Prometheus rules synced, validated, and reloaded."

# First-time install of rule files (creates missing files)
prometheus-install-rules:
	@echo "Installing Prometheus rule/config files into $(PROM_DIR)..."
	@sudo cp $(PROM_RULES_SRC)/prometheus.yml $(PROM_DIR)/prometheus.yml
	@sudo cp $(PROM_RULES_SRC)/recording_rules.yml $(PROM_DIR)/recording_rules.yml
	@sudo cp $(PROM_RULES_SRC)/alert_rules.yml $(PROM_DIR)/alert_rules.yml
	@echo "Installation complete."


# -----------------------------------------------------------
#   GRAFANA TARGETS
# -----------------------------------------------------------
# Start Grafana Server in foreground.
# Grafana usually needs sudo because it binds to system directories.
grafana:
#	make grafana-disable-systemd
	@echo "Starting Grafana..."
	@$(GRAFANA_DEV_BIN) server --homepath=$(GRAFANA_DEV_HOME) --config=$(GRAFANA_DEV_CONF) > $(GRAFANA_LOG) 2>&1 &
	@echo $$! > grafana.pid
	@echo "Grafana started (PID: $$(cat grafana.pid)). Logs: $(GRAFANA_LOG)"

# Start Grafana Server in background.
# Grafana usually needs sudo because it binds to system directories.
grafana-bg:
#	make grafana-disable-systemd
	@echo "Starting Grafana in background..."
	@nohup $(GRAFANA_DEV_BIN) server --homepath=$(GRAFANA_DEV_HOME) --config=$(GRAFANA_DEV_CONF) > $(GRAFANA_LOG) 2>&1 &
	@echo $$! > grafana.pid
# 	@sleep 1
# 	@pgrep -f "$(GRAFANA_DEV_BIN)" > grafana.pid
	@echo "Grafana started (PID: $$(cat grafana.pid)). Logs: $(GRAFANA_LOG)"

grafana-disable-systemd:
	@echo "Disabling Grafana systemd services..."
	@sudo systemctl disable grafana-server
	@sleep 1
	@sudo systemctl stop grafana-server
	@echo "Grafana systemd services disabled."


# grafana-status:
# 	@echo "\n=== Grafana Status ==="
# 	@if pgrep -f "$(GRAFANA_DEV_BIN)" > /dev/null; then \
# 		pgrep -fl "$(GRAFANA_DEV_BIN)"; \
# 	else \
# 		echo "Grafana is NOT running."; \
# 	fi
# 	@echo "\n=== Grafana Status ==="
# 	@if pgrep -f "grafana-server|grafana" > /dev/null; then \
# 		pgrep -fl "grafana-server|grafana"; \
# 	else \
# 		echo "Grafana is NOT running."; \
# 	fi

# 	@echo "\n=== Grafana Status ==="
# 	@if pgrep -x "$(notdir $(GRAFANA_BIN))" > /dev/null; then \
# 		pgrep -fl "$(notdir $(GRAFANA_BIN))"; \
# 	else \
# 		echo "Grafana is NOT running."; \
# 	fi


kill-grafana:
	@echo "Stopping Grafana..."
	@if [ -f grafana.pid ]; then \
		kill $$(cat grafana.pid) 2>/dev/null || true; \
		rm -f grafana.pid; \
	else \
		pkill -f "$(HOME)/grafana/bin/grafana" 2>/dev/null || true; \
	fi
	@echo "Grafana stopped (if it was running)."
# 	@if [ -f grafana.pid ]; then \
# 		echo "Stopping Grafana (PID: $$(cat grafana.pid))..."; \
# 		sudo kill $$(cat grafana.pid) || true; \
# 		rm grafana.pid; \
# 	else \
# 		echo "No grafana.pid found. Killing by process name..."; \
# 		sudo pkill -f "$(GRAFANA_BIN)" || true; \
# 	fi
# 	@echo "Done."



# Clear Grafana DB via SQLite
# sqlite3 ~/grafana/data/grafana.db \
#   "delete from dashboard where uid='hl7-mllp-server';"


restart-grafana:
	@echo "Restarting Grafana..."
	make kill-grafana
	make grafana-bg
	@echo "Grafana restarted."



grafana-status:
	@echo "=== Grafana Status ==="
	@ps -eo pid,cmd | grep "[g]rafana-server" || echo "Grafana not running."

grafana-restart: grafana-kill grafana-bg
	@echo "Grafana restarted."

grafana-pid:
	@ps -eo pid,cmd | grep "[g]rafana-server" | awk '{print $$1}'

grafana-kill:
	@echo "Stopping Grafana..."
	@PIDS=`ps -eo pid,cmd | grep "[g]rafana-server" | awk '{print $$1}'`; \
	if [ -n "$$PIDS" ]; then \
		kill $$PIDS; \
		echo "Grafana stopped."; \
	else \
		echo "Grafana was not running."; \
	fi

grafana-clear-dashboard:
	@if [ -z "$(UID)" ]; then \
		echo "Usage: make grafana-clear-dashboard UID=<dashboard_uid>"; \
		exit 1; \
	fi
	@echo "Deleting dashboard with UID=$(UID)..."
	@sqlite3 $(GRAFANA_DB) "delete from dashboard where uid='$(UID)';"
	@echo "Dashboard removed. Restart Grafana to re-import."

grafana-sync-dashboards:
	@echo "Copying Grafana dashboards into $(GRAFANA_DASH_DST)..."
	@mkdir -p $(GRAFANA_DASH_DST)
	@cp $(GRAFANA_DASH_SRC)/*.json $(GRAFANA_DASH_DST)/
	@cp $(GRAFANA_PROVISIONING_FILE_SRC) $(GRAFANA_DASH_DST)/
	@echo "Dashboards synced."

# ---------------------------------------------------------
# Start all servers (MLLP, Grafana + Prometheus) in background
# This allows executing test bench, benchmarks, etc. afterwards
# ---------------------------------------------------------
monitoring-stack:
	make run-server-prom-bg
	make prometheus-bg
	make grafana-bg

# ---------------------------------------------------------
# Kill MLLP, Grafana + Prometheus servers (based on PID)
# ---------------------------------------------------------
kill-monitoring:
	make kill-prometheus
	make kill-grafana
	make kill-own-server

monitoring-stack-restart:
	make kill-monitoring
	make monitoring-stack

monitoring-logs:
	@echo "=== Prometheus Logs ==="
	@if [ -f "$(PROM_LOG)" ]; then \
		tail -n 50 $(PROM_LOG); \
	else \
		echo "No Prometheus log file found."; \
	fi

	@echo "\n=== Grafana Logs ==="
	@if [ -f "$(GRAFANA_LOG)" ]; then \
		tail -n 50 $(GRAFANA_LOG); \
	else \
		echo "No Grafana log file found."; \
	fi

observability-clean:
	@echo "Stopping all observability services..."
	- make kill-server
	- make kill-prometheus
	- make kill-grafana

	@echo "Removing PID and log files..."
	- rm -f hl7engine.pid prometheus.pid grafana.pid
	- rm -f hl7engine.log prometheus.log grafana.log

	@echo "Cleaning routed files..."
	- rm -rf routed/*

	@echo "Cleaning SQLite DB..."
	- rm -f data/hl7_messages.db

	@echo "Observability environment cleaned."

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
	@echo "  make clean-results     - Remove results JSON files"
	@echo "  make reset             - Clean DB and routed + results folders"
	@echo ""
	@echo "  make prometheus        - Start Prometheus service as configured in PROM_CONFIG"
	@echo "  make prometheus-bg     - Start Prometheus service in background"
	@echo "  make prometheus-status - Show Prometheus server status"
	@echo "  make restart-prometheus - Restart Prometheus server"
	@echo "  make prometheus-test   - Curl /metrics to verify Prometheus endpoint"
	@echo "  make kill-prometheus   - Stop Prometheus server"
	@echo ""
	@echo "  make grafana           - Start Grafana server in foreground"
	@echo "  make grafana-bg        - Start Grafana server in background"
	@echo "  make kill-grafana      - Stop Grafana server"
	@echo "  make restart-grafana   - Restart Grafana server"
	@echo "  make grafana-status    - Show Grafana server status"
	@echo ""
	@echo "  make server-status-all - Show status of HL7 engine, REST API, Prometheus, Grafana"
	@echo "  make monitoring-stack  - Start Prometheus, Grafana and MLLP server (HL7 engine) with Prometheus enabled"
	@echo "  make monitoring-logs   - Show logs for Prometheus and Grafana"
	@echo "  make kill-monitoring   - Stop HL7 MLLP server, Prometheus + Grafana"
