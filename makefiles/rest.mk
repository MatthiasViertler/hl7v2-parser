#makefiles/rest.mk

# ---------------------------------------------------------
# REST API SERVER Targets
# ---------------------------------------------------------

rest-start-fg: ## Start REST API in foreground
	uvicorn hl7engine.api:app --host 0.0.0.0 --port $(REST_PORT)

rest-start: # Start REST API server on port REST_PORT
	@echo "Starting REST API in background..."
	@mkdir -p $(shell pwd)/monitoring/logs
	@nohup uvicorn hl7engine.api:app \
		--host 0.0.0.0 \
		--port $(REST_PORT) \
		--reload \
		> "$(REST_LOG)" 2>&1 &
	@echo $$! > "$(REST_PID)"
	@echo "REST API started (PID: $$(cat $(REST_PID))). Logs: $(REST_LOG)"

rest-stop: ## Stop REST API server
	@PID=$$(pgrep -f "[u]vicorn hl7engine.api"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping REST API (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "REST API not running."; \
	fi

rest-api-status: ## (DEPRECATED) Show a short status report of REST API
	@echo "\n=== REST API Status ==="
	@ps aux | grep "uvicorn hl7engine.api" | grep -v grep || echo "No REST API server running."

rest-api-status-full: ## (DEPRECATED) Show a full status report of REST API
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
