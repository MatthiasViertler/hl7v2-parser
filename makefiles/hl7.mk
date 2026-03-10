

# ---------------------------------------------------------
# HL7 SERVER Targets
# ---------------------------------------------------------

hl7-start: ## Start HL7 MLLP engine
	@echo "Starting HL7 engine with Prometheus in background..."
	@nohup python3 -m hl7engine.mllp_server --prometheus > $(HL7_ENGINE_LOG) 2>&1 &
	@echo $$! > hl7engine.pid
	@echo "HL7 engine started (PID: $$(cat hl7engine.pid)). Logs: $(HL7_ENGINE_LOG)"

hl7-stop: ## Stop HL7 MLLP engine
	@PID=$$(pgrep -f "[h]l7engine.mllp_server"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping HL7 Engine (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "HL7 Engine not running."; \
	fi

hl7-server-status: ## Simple Status for HL7 MLLP engine
	@echo "=== HL7 Engine Status ==="
	@ps aux | grep "hl7engine.mllp_server" | grep -v grep || echo "No HL7 MLLP server running."

hl7-server-status-full: ## Complete Status for HL7 MLLP engine
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

hl7-start-fg: ## Start HL7 MLLP server in foreground
	@echo "Starting HL7 MLLP server in foreground..."
	python3 -m hl7engine.mllp_server

hl7-start-prom-fg: ## Start HL7 MLLP server with prometheus in foreground
	@echo "Starting HL7 engine with Prometheus in foreground ..."
	python3 -m hl7engine.mllp_server --prometheus

#run-server-prom-bg:
# 	@echo "Starting HL7 engine with Prometheus in background..."
# 	@nohup python3 -m hl7engine.mllp_server --prometheus > $(HL7_ENGINE_LOG) 2>&1 &
# 	@echo $$! > hl7engine.pid
# 	@echo "HL7 engine started (PID: $$(cat hl7engine.pid)). Logs: $(HL7_ENGINE_LOG)"

# restart-server:
# 	make kill-own-server
# 	make run-server

# restart-server-prom-bg:
# 	make kill-own-server
# 	make run-server-prom-bg

hl7-kill-own-server: ## Kill own running HL7 MLLP server
	@echo "Killing HL7 MLLP server..."
	@ps aux | grep "python3 -m hl7engine.mllp_server" | grep -v grep | awk '{print $$2}' | xargs -r kill
	@echo "Done."

hl7-kill-server: ## Kill any running HL7 MLLP server (based on binary)
	@echo "Killing any running HL7 MLLP server processes..."
	@pkill -f "hl7engine.mllp_server" || true
	@echo "Done."