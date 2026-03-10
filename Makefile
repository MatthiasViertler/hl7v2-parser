MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

include $(MAKEFILE_DIR)/makefiles/utils.mk
include $(MAKEFILE_DIR)/makefiles/monitoring.mk

# include makefiles/utils.mk
# include makefiles/hl7.mk
# include makefiles/restapi.mk
# include makefiles/html.mk
# include makefiles/prometheus.mk
# include makefiles/grafana.mk
# include makefiles/monitoring.mk

.DEFAULT_GOAL := help

# Benchmark configuration (override via: make run-benchmark BENCHMARK=--sweep)
BENCHMARK ?= --max-throughput
DURATION ?= 10
EXTRA ?=

PYTEST=pytest

GREEN  := \033[0;32m
RED    := \033[0;31m
YELLOW := \033[1;33m
BLUE   := \033[0;34m
RESET  := \033[0m

# ---------------------------------------------------------
# HL7 Engine Makefile
# ---------------------------------------------------------

ROUTED_DIR=routed
DB_PATH=data/hl7_messages.db
BENCH=python3 -m benchmarking.run_benchmark

HL7_ENGINE_LOG=hl7engine.log

# ---------------------------------------------------------
# REST API Server
# ---------------------------------------------------------

REST_PORT := 8000
REST_LOG := $(shell pwd)/monitoring/logs/restapi.log
REST_PID := $(shell pwd)/monitoring/restapi.pid

# ---------------------------------------------------------
# HTML UI VIEWER
# ---------------------------------------------------------
HTML_PORT := 8080

# ---------------------------------------------------------
# PROMETHEUS
# ---------------------------------------------------------
# === Sudo apt install Prometheus Install ===
# PROM_HOME := /opt/prometheus
# PROM_BIN := $(PROM_HOME)/prometheus
# PROM_CONF := $(PROM_HOME)/prometheus.yml
# PROM_LOG := $(PROM_HOME)/prometheus.log
# === Local prometheus Install ===
PROM_HOME := $(HOME)/prometheus
PROM_BIN := $(PROM_HOME)/prometheus
PROM_CONF := $(PROM_HOME)/prometheus.yml

PROM_LOG := $(shell pwd)/monitoring/logs/prometheus.log
PROM_PID := $(shell pwd)/monitoring/prometheus.pid

PROM_METRICS_URL := http://localhost:8010/metrics
# Rule files in our repo
PROM_RULES_SRC := $(shell pwd)/monitoring
PROM_RULES := recording_rules.yml alert_rules.yml prometheus.yml

# ---------------------------------------------------------
# GRAFANA (DEVELOPMENT SETTINGS)
# ---------------------------------------------------------
# GRAFANA_DEV_BIN := $(HOME)/grafana/bin/grafana
# GRAFANA_DEV_HOME := $(HOME)/grafana
# GRAFANA_DEV_CONF := $(HOME)/grafana/conf/defaults.ini
# GRAFANA_LOG := grafana.log
# GRAFANA_DASH_SRC := $(shell pwd)/monitoring/dashboards
# GRAFANA_PROVISIONING_FILE_SRC := $(shell pwd)/monitoring/dashboards/hl7.yaml
# GRAFANA_DASH_DST := $(HOME)/grafana/conf/provisioning/dashboards

# === Local Grafana Install ===
GRAFANA_HOME := $(HOME)/grafana
GRAFANA_BIN := $(GRAFANA_HOME)/bin/grafana
GRAFANA_CONF := $(GRAFANA_HOME)/conf/defaults.ini
GRAFANA_DB := $(GRAFANA_HOME)/data/grafana.db
GRAFANA_LOG := $(GRAFANA_HOME)/logs/grafana.log
GRAFANA_PROVISIONING := $(GRAFANA_HOME)/conf/provisioning/dashboards
GRAFANA_DASH_DST := $(GRAFANA_HOME)/conf/provisioning/dashboards
GRAFANA_DASH_SRC := $(shell pwd)/monitoring/dashboards

# ---------------------------------------------------------
# GENERAL & HELPER TARGETS
# ---------------------------------------------------------
define status_line
	@printf "%-20s %-10s %-10s %-40s\n" "$(1)" "$(2)" "$(3)" "$(4)"
endef

define ok_fail
	$(if $(1),$(GREEN)OK$(RESET),$(RED)FAIL$(RESET))
endef

define color_http
	$(if $(filter 200,$(1)),$(GREEN)$(1)$(RESET),$(RED)$(1)$(RESET))
endef

define color_port
	$(if $(filter open,$(1)),$(GREEN)open$(RESET),$(RED)closed$(RESET))
endef

define get_uptime
	@ps -p $(1) -o etime= 2>/dev/null
endef

define check_port
	@nc -z localhost $(1) >/dev/null 2>&1 && echo "open" || echo "closed"
endef

define check_http
	@curl -s -o /dev/null -w "%{http_code}" $(1)
endef

print-green:
	@printf "$(GREEN)OK$(RESET)\n"

# ---------------------------------------------------------
# INSTALL packages in editable mode for your Python env
# ---------------------------------------------------------
install:
	pip install -e .

# ---------------------------------------------------------
# HL7 SERVER Targets
# ---------------------------------------------------------
hl7-start-fg:
	@echo "Starting HL7 MLLP server in foreground..."
	python3 -m hl7engine.mllp_server

hl7-start-prom-fg:
	@echo "Starting HL7 engine with Prometheus in foreground ..."
	python3 -m hl7engine.mllp_server --prometheus

#run-server-prom-bg:
hl7-start:
	@echo "Starting HL7 engine with Prometheus in background..."
	@nohup python3 -m hl7engine.mllp_server --prometheus > $(HL7_ENGINE_LOG) 2>&1 &
	@echo $$! > hl7engine.pid
	@echo "HL7 engine started (PID: $$(cat hl7engine.pid)). Logs: $(HL7_ENGINE_LOG)"

hl7-stop:
	@PID=$$(pgrep -f "[h]l7engine.mllp_server"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping HL7 Engine (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "HL7 Engine not running."; \
	fi

hl7-server-status:
	@echo "=== HL7 Engine Status ==="
	@ps aux | grep "hl7engine.mllp_server" | grep -v grep || echo "No HL7 MLLP server running."

hl7-server-status-full:
	@echo "=== HL7 Engine Status ==="
	@PID=$$(pgrep -f "[h]l7engine.mllp_server"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost 2575 && echo "open" || echo "closed"); \
		printf "%-20s %-10s %-10s %-10s\n" "Service" "PID" "Uptime" "Port"; \
		printf "%-20s %-10s %-10s %-10s\n" "HL7 Engine" "$$PID" "$$UPTIME" "$$PORT"; \
	else \
		echo "HL7 Engine is NOT running."; \
	fi

restart-server:
	make kill-own-server
	make run-server

restart-server-prom-bg:
	make kill-own-server
	make run-server-prom-bg

# Kill own running HL7 MLLP server
kill-own-server:
	@echo "Killing HL7 MLLP server..."
	@ps aux | grep "python3 -m hl7engine.mllp_server" | grep -v grep | awk '{print $$2}' | xargs -r kill
	@echo "Done."

# kill-own-server:
# 	@echo "Killing HL7 MLLP server..."
# 	@ps -eo pid,cmd | grep "[p]ython3 -m hl7engine.mllp_server" | awk '{print $$1}' | xargs -r kill
# 	@echo "Done."

# Kill any running HL7 MLLP server (based on binary)
kill-server:
	@echo "Killing any running HL7 MLLP server processes..."
	@pkill -f "hl7engine.mllp_server" || true
	@echo "Done."

# ---------------------------------------------------------
# REST API SERVER Targets
# ---------------------------------------------------------

#rest-api-bg:
rest-start:
	@echo "Starting REST API in background..."
	@mkdir -p $(shell pwd)/monitoring/logs
	@nohup uvicorn hl7engine.api:app \
		--host 0.0.0.0 \
		--port $(REST_PORT) \
		--reload \
		> "$(REST_LOG)" 2>&1 &
	@echo $$! > "$(REST_PID)"
	@echo "REST API started (PID: $$(cat $(REST_PID))). Logs: $(REST_LOG)"

rest-stop:
	@PID=$$(pgrep -f "[u]vicorn hl7engine.api"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping REST API (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "REST API not running."; \
	fi

rest-api-status:
	@echo "\n=== REST API Status ==="
	@ps aux | grep "uvicorn hl7engine.api" | grep -v grep || echo "No REST API server running."

rest-api-status-full:
	@echo "=== REST API Status ==="
	@PID=$$(pgrep -f "[u]vicorn hl7engine.api"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost $(REST_PORT) && echo "open" || echo "closed"); \
		HEALTH=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$(REST_PORT)/health); \
		printf "%-20s %-10s %-10s %-10s %-10s\n" "Service" "PID" "Uptime" "Port" "Health"; \
		printf "%-20s %-10s %-10s %-10s %-10s\n" "REST API" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH"; \
	else \
		echo "REST API is NOT running."; \
	fi

rest-api-kill:
	@echo "Stopping REST API..."
	@if [ -f "$(REST_PID)" ]; then \
		kill `cat $(REST_PID)` 2>/dev/null || true; \
		rm -f $(REST_PID); \
		echo "REST API stopped."; \
	else \
		echo "No PID file found. Trying process scan..."; \
		PIDS=`pgrep -f "uvicorn hl7engine.api"`; \
		if [ -n "$$PIDS" ]; then kill $$PIDS; echo "REST API stopped."; else echo "REST API was not running."; fi; \
	fi

# ---------------------------------------------------------
# ALL SERVER Targets
# ---------------------------------------------------------

all-server-status:
#	@echo "=== HL7 Engine Status ==="
	@$(MAKE) --no-print-directory hl7-server-status-full

#	@echo "\n=== REST API Status ==="
	@$(MAKE) --no-print-directory rest-api-status-full

#	@echo "\n=== Prometheus Status ==="
	@$(MAKE) --no-print-directory prometheus-status-full

#	@echo "\n=== Grafana Status ==="
	@$(MAKE) --no-print-directory grafana-status-full

# Kill any running Prometheus server (based on binary)
kill-prometheus-all:
	@echo "Stopping Prometheus server..."
	@pkill -f "/opt/prometheus/prometheus" || true
	@echo "Done."

# Kill Prometheus server (based on PID)
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

run-ui:
	@echo "Serving UI at http://localhost:8080"
	cd ui && python3 -m http.server 8080 >/dev/null 2>&1

run-ui-bg:
	@echo "Serving UI at http://localhost:8080"
	cd ui && python3 -m http.server 8080 >/dev/null 2>&1 &

ui-start:
	@echo "Starting UI server on port $(HTML_PORT)..."
	cd ui && nohup python3 -m http.server $(HTML_PORT) \
		>/dev/null 2>&1 &
	@echo "UI server started."

ui-stop:
	@PID=$$(pgrep -f "[p]ython.*http.server $(HTML_PORT)"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping UI server (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "UI server not running."; \
	fi

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
# CLEANUP
# ---------------------------------------------------------

# ROUTED FOLDER CLEANUP
clean-routed:
	@if [ -d "$(ROUTED_DIR)" ]; then \
		echo "Cleaning routed/ folders..."; \
		find $(ROUTED_DIR) -type f -name "*.hl7" -delete; \
		find $(ROUTED_DIR) -type d -empty -delete; \
	fi

# RESULTS JSON CLEANUP
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

prometheus-pid:
	@ps -eo pid,cmd | grep "[p]rometheus" | awk '{print $$1}'

# - $(shell pwd) ensures absolute paths
# - cd $(shell pwd) ensures Prometheus resolves relative paths inside YAML
# - Works from any directory, not just project root
# - Works from VS Code, PyCharm, terminals, CI, etc.
# - Background version logs cleanly
prometheus:
	@echo "Starting Prometheus using config: $(PROM_CONF)"
	@cd $(PROM_HOME) && $(PROM_BIN) --config.file="$(PROM_CONF)"

# prometheus-bg:
# 	@echo "Starting Prometheus in background using config: $(PROM_CONF)"
# 	@mkdir -p $(shell pwd)/monitoring/logs
# 	@cd $(PROM_HOME) && nohup $(PROM_BIN) --config.file="$(PROM_CONF)" > $(PROM_LOG) 2>&1 &
# 	@echo $$! > prometheus.pid
# 	@echo "Prometheus started in background (PID: $$(cat prometheus.pid)). Logs: $(PROM_LOG)"

#Starting Prometheus no subshell, PID works
prometheus-bg:
	@echo "Starting Prometheus in background using config: $(PROM_CONF)"
	@mkdir -p $(shell pwd)/monitoring/logs
	@nohup $(PROM_BIN) \
		--config.file="$(PROM_CONF)" \
		--web.listen-address=":9090" \
		--storage.tsdb.path="$(PROM_HOME)/data" \
		--web.console.libraries="$(PROM_HOME)/console_libraries" \
		--web.console.templates="$(PROM_HOME)/consoles" \
		--web.enable-lifecycle \
		--web.enable-admin-api \
		--web.enable-remote-write-receiver \
		> "$(PROM_LOG)" 2>&1 &
	@echo $$! > "$(PROM_PID)"
	@echo "Prometheus started in background (PID: $$(cat $(PROM_PID))). Logs: $(PROM_LOG)"

prom-start:
	@echo "Starting Prometheus in background using config: $(PROM_CONF)..."
	@mkdir -p $(shell pwd)/monitoring/logs
	@nohup $(PROM_BIN) \
		--config.file="$(PROM_CONF)" \
		--web.listen-address=":9090" \
		--storage.tsdb.path="$(PROM_HOME)/data" \
		--web.console.libraries="$(PROM_HOME)/console_libraries" \
		--web.console.templates="$(PROM_HOME)/consoles" \
		--web.enable-lifecycle \
		--web.enable-admin-api \
		--web.enable-remote-write-receiver \
		> "$(PROM_LOG)" 2>&1 &
	@echo $$! > "$(PROM_PID)"
	@echo "Prometheus started in background (PID: $$(cat $(PROM_PID))). Logs: $(PROM_LOG)"
#	@$(PROM_BIN) --config.file=$(PROM_CONFIG) >/dev/null 2>&1 &

prom-stop:
	@PID=$$(pgrep -f "^$(PROM_BIN)"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping Prometheus (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "Prometheus not running."; \
	fi

# -----------------------------------------------------------
# This checks Prometheus Status:
# -----------------------------------------------------------
# - If Prometheus is running
# - Shows PID
# - Shows listening port
# - Shows the config file use
# -----------------------------------------------------------

prometheus-status:
	@echo "=== Prometheus Status ==="
#	^$(PROM_BIN) matches only processes whose command starts with the full path
#	It won't match: HL7 engine (python3), make or anything else containing 'prometheus'
	@pgrep -fl "^$(PROM_BIN)" || echo "Prometheus is NOT running."
#	Too broad: matches any process containing "prometheus", thus 
#	also HL7 engine (python3) and Makefile process (make).
#	@pgrep -fl "[p]rometheus" || echo "Prometheus is NOT running."

# /opt/prometheus install version of status:
# prometheus-status:
# #	@echo "Checking Prometheus status..."
# 	@echo "\n=== Prometheus Status ==="
# 	@if pgrep -x "$(notdir $(PROM_BIN))" > /dev/null; then \
# 		pgrep -fl "$(notdir $(PROM_BIN))"; \
# 	else \
# 		echo "Prometheus is NOT running."; \
# 	fi

prometheus-status-full:
	@echo "=== Prometheus Status ==="
	@PID=$$(pgrep -f "^$(PROM_BIN)"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime=); \
		PORT=$$(nc -z localhost 9090 && echo "open" || echo "closed"); \
		HEALTH=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/metrics); \
		printf "%-20s %-10s %-10s %-10s %-10s\n" "Service" "PID" "Uptime" "Port" "Health"; \
		printf "%-20s %-10s %-10s %-10s %-10s\n" "Prometheus" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH"; \
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

restart-prometheus: prometheus-kill prometheus-bg
	@echo "Prometheus restarted."

# -----------------------------------------------------------
# PROMETHEUS RULE SYNC / VALIDATION / RELOAD
# -----------------------------------------------------------

prometheus-kill:
	@echo "Stopping Prometheus..."
	@PIDS=`ps -eo pid,cmd | grep "[p]rometheus" | awk '{print $$1}'`; \
	if [ -n "$$PIDS" ]; then \
		kill $$PIDS; \
		echo "Prometheus stopped."; \
	else \
		echo "Prometheus was not running."; \
	fi

# Copy rule files into /opt/prometheus (requires sudo)
prometheus-sync-rules:
	@echo "Copying Prometheus rule/config files into $(PROM_HOME)..."
	@for f in $(PROM_RULES); do \
		echo "  - Copying $$f"; \
		sudo cp $(PROM_RULES_SRC)/$$f $(PROM_HOME)/$$f; \
	done
	@echo "Done."

# Validate Prometheus config + rules
prometheus-validate:
	@echo "Validating Prometheus configuration..."
	@cd $(PROM_HOME) && ./promtool check config prometheus.yml
	@echo "Validating rule files..."
	@cd $(PROM_HOME) && ./promtool check rules recording_rules.yml
	@cd $(PROM_HOME) && ./promtool check rules alert_rules.yml
	@echo "Validation OK."

# Reload Prometheus via SIGHUP
prometheus-reload:
	@echo "Reloading Prometheus configuration..."
	@if pgrep -x "$(notdir $(PROM_BIN))" > /dev/null; then \
		pkill -HUP -x "$(notdir $(PROM_BIN))"; \
		echo "Prometheus reloaded."; \
	else \
		echo "Prometheus is not running. Start it first."; \
	fi

# Full workflow: sync → validate → reload
prometheus-full-reload: prometheus-sync-rules prometheus-validate prometheus-reload
	@echo "Prometheus rules synced, validated, and reloaded."

# First-time install of rule files (creates missing files)
prometheus-install-rules:
	@echo "Installing Prometheus rule/config files into $(PROM_HOME)..."
	@sudo cp $(PROM_RULES_SRC)/prometheus.yml $(PROM_HOME)/prometheus.yml
	@sudo cp $(PROM_RULES_SRC)/recording_rules.yml $(PROM_HOME)/recording_rules.yml
	@sudo cp $(PROM_RULES_SRC)/alert_rules.yml $(PROM_HOME)/alert_rules.yml
	@echo "Installation complete."


# -----------------------------------------------------------
#   GRAFANA TARGETS
# -----------------------------------------------------------

# Start Grafana Server in foreground.
# Grafana usually needs sudo because it binds to system directories.
# grafana:
# #	make grafana-disable-systemd
# 	@echo "Starting Grafana..."
# 	@$(GRAFANA_DEV_BIN) server --homepath=$(GRAFANA_DEV_HOME) --config=$(GRAFANA_DEV_CONF) > $(GRAFANA_LOG) 2>&1 &
# 	@echo $$! > grafana.pid
# 	@echo "Grafana started (PID: $$(cat grafana.pid)). Logs: $(GRAFANA_LOG)"

grafana:
	$(GRAFANA_BIN) server --homepath $(GRAFANA_HOME) --config $(GRAFANA_CONF)

# Start Grafana Server in background.
# Grafana usually needs sudo because it binds to system directories.
grafana-bg:
	@echo "Starting Grafana in background..."
	@mkdir -p $(GRAFANA_HOME)/logs
	@nohup $(GRAFANA_BIN) server \
	    --homepath $(GRAFANA_HOME) \
	    --config $(GRAFANA_CONF) \
	    > $(GRAFANA_LOG) 2>&1 &
	@echo $$! > grafana.pid
	@echo "Grafana started (PID: $$(cat grafana.pid)). Logs: $(GRAFANA_LOG)"

grafana-start:
	@echo "Starting Grafana in background..."
	@mkdir -p $(GRAFANA_HOME)/logs
	@sh -c ' \
		nohup $(GRAFANA_BIN) server \
			--homepath $(GRAFANA_HOME) \
			--config $(GRAFANA_CONF) \
			> $(GRAFANA_LOG) 2>&1 & \
		echo $$! > grafana.pid \
	'
	@echo "Grafana started (PID: $$(cat grafana.pid)). Logs: $(GRAFANA_LOG)"
#	@grafana server >/dev/null 2>&1 &

grafana-stop:
	@PID=$$(pgrep -f "[g]rafana server"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping Grafana (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "Grafana not running."; \
	fi

grafana-status:
	@echo "=== Grafana Status ==="
	@ps aux | grep "[g]rafana server" | grep -v grep || echo "Grafana not running."

grafana-status-full:
	@echo "=== Grafana Status ==="
	@PID=$$(pgrep -f "[g]rafana server"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost 3000 && echo "open" || echo "closed"); \
		HEALTH=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/health); \
		printf "%-20s %-10s %-10s %-10s %-10s\n" "Service" "PID" "Uptime" "Port" "Health"; \
		printf "%-20s %-10s %-10s %-10s %-10s\n" "Grafana" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH"; \
	else \
		echo "Grafana is NOT running."; \
	fi

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

restart-grafana:grafana-kill grafana-bg
	@echo "Grafana restarted."

grafana-clear-dashboard:
	@if [ -z "$(UID)" ]; then \
		echo "Usage: make grafana-clear-dashboard UID=<dashboard_uid>"; \
		echo " e.g.: make grafana-clear-dashboard UID=hl7-mllp-server"; \
		exit 1; \
	fi
	@echo "Deleting dashboard with UID=$(UID)..."
	@sqlite3 "$(GRAFANA_DB)" "DELETE FROM dashboard WHERE uid='$(UID)';"
	@echo "Dashboard removed. Restart Grafana to re-import."


grafana-sync-dashboards:
	@echo "Copying Grafana dashboards into $(GRAFANA_PROVISIONING)..."
	@mkdir -p $(GRAFANA_PROVISIONING)
	@cp $(GRAFANA_DASH_SRC)/*.json $(GRAFANA_PROVISIONING)/
	@echo "Dashboards synced. Restart Grafana to apply."

# 	@echo "Copying Grafana dashboards into $(GRAFANA_DASH_DST)..."
# 	@mkdir -p $(GRAFANA_DASH_DST)
# 	@cp $(GRAFANA_DASH_SRC)/*.json $(GRAFANA_DASH_DST)/ 
#   or
#	@cp monitoring/dashboards/*.json $(GRAFANA_PROVISIONING)/
# 	@cp $(GRAFANA_PROVISIONING_FILE_SRC) $(GRAFANA_DASH_DST)/
# 	@echo "Dashboards synced."

grafana-disable-systemd:
	@echo "Disabling Grafana systemd services..."
	@sudo systemctl disable grafana-server
	@sleep 1
	@sudo systemctl stop grafana-server
	@echo "Grafana systemd services disabled."

# Clear Grafana DB via SQLite
# sqlite3 ~/grafana/data/grafana.db \
#   "delete from dashboard where uid='hl7-mllp-server';"

# ---------------------------------------------------------
# Start all servers (MLLP, Grafana + Prometheus) in background
# This allows executing test bench, benchmarks, etc. afterwards
# ---------------------------------------------------------
monitoring-stack:
#	make run-server-prom-bg
	make hl7-start
	make prometheus-bg
	make grafana-bg

# ---------------------------------------------------------
# Kill MLLP, Grafana + Prometheus servers (based on PID)
# ---------------------------------------------------------
kill-monitoring:
	make prometheus-kill
	make grafana-kill
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
	- make prometheus-kill
	- make grafana-kill

	@echo "Removing PID and log files..."
	- rm -f hl7engine.pid prometheus.pid grafana.pid
	- rm -f hl7engine.log prometheus.log grafana.log

	@echo "Cleaning routed files..."
	- rm -rf routed/*

	@echo "Cleaning SQLite DB..."
	- rm -f data/hl7_messages.db

	@echo "Observability environment cleaned."

# ---------------------------------------------------------
# Full Stack Targets (HL7 Engine, REST API, UI, Prometheus, Grafana)
# ---------------------------------------------------------

# Start order is important (DO NOT CHANGE)
stack-start: hl7-start rest-start ui-start prom-start grafana-start
	@echo "$(GREEN)All services started$(RESET)"

# Stop order (reverse) avoids race conditions and ensures dependencies are ready
stack-stop: grafana-stop prom-stop ui-stop rest-stop hl7-stop
	@echo "$(YELLOW)All services stopped$(RESET)"

stack-restart:
	@echo "Restarting full stack..."
	@$(MAKE) --no-print-directory stack-stop
	@sleep 1
	@$(MAKE) --no-print-directory stack-start

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
