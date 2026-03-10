

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
