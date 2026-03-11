# makefiles/grafana

# -----------------------------------------------------------
#   GRAFANA TARGETS
# -----------------------------------------------------------

grafana: ## (DEPRECATED) Start Grafana in foreground
	$(GRAFANA_BIN) server --homepath $(GRAFANA_HOME) --config $(GRAFANA_CONF)

grafana-start: ## Start Grafana in background
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

grafana-stop: ## Stop Grafana
	@PID=$$(pgrep -f "[g]rafana server"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping Grafana (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "Grafana not running."; \
	fi

grafana-status: ## (DEPRECATED) Short status report for Grafana
	@echo "=== Grafana Status ==="
	@ps aux | grep "[g]rafana server" | grep -v grep || echo "Grafana not running."

grafana-status-full: ## (DEPRECATED) Full status report for Grafana
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

grafana-clear-dashboard: ## Reset Grafana dashboards (for maintenance)
	@if [ -z "$(UID)" ]; then \
		echo "Usage: make grafana-clear-dashboard UID=<dashboard_uid>"; \
		echo " e.g.: make grafana-clear-dashboard UID=hl7-mllp-server"; \
		exit 1; \
	fi
	@echo "Deleting dashboard with UID=$(UID)..."
	@sqlite3 "$(GRAFANA_DB)" "DELETE FROM dashboard WHERE uid='$(UID)';"
	@echo "Dashboard removed. Restart Grafana to re-import."


grafana-sync-dashboards: ## Copy Grafana dashboards into provisioning
	@echo "Copying Grafana dashboards into $(GRAFANA_PROVISIONING)..."
	@mkdir -p $(GRAFANA_PROVISIONING)
	@cp $(GRAFANA_DASH_SRC)/*.json $(GRAFANA_PROVISIONING)/
	@echo "Dashboards synced. Restart Grafana to apply."

grafana-disable-systemd: ## (DEPRECATED) Disable systemd Grafana service (if installed via apt)
	@echo "Disabling Grafana systemd services..."
	@sudo systemctl disable grafana-server
	@sleep 1
	@sudo systemctl stop grafana-server
	@echo "Grafana systemd services disabled."
