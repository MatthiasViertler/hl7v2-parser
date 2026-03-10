
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


