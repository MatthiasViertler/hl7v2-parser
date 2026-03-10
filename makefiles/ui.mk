
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

run-ui:
	@echo "Serving UI at http://localhost:8080"
	cd ui && python3 -m http.server 8080 >/dev/null 2>&1

run-ui-bg:
	@echo "Serving UI at http://localhost:8080"
	cd ui && python3 -m http.server 8080 >/dev/null 2>&1 &