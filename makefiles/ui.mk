# makefiles/ui.mk

ui-start: ## Start HTML viewer for REST API on port HTML_PORT
	@echo "Starting UI server at http://localhost:$(HTML_PORT)..."
	cd ui && nohup python3 -m http.server $(HTML_PORT) \
		>/dev/null 2>&1 &
	@echo "UI server started."

ui-stop: ## Stop HTML viewer
	@PID=$$(pgrep -f "[p]ython.*http.server $(HTML_PORT)"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping UI server (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "UI server not running."; \
	fi

ui-start-fg: ## (DEPRECATED) Start HTML viewer in foreground
	@echo "Serving UI at http://localhost:$(HTML_PORT)"
	cd ui && python3 -m http.server $(HTML_PORT) >/dev/null 2>&1

