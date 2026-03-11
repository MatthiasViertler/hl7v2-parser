# makefiles/orchestration.mk

# ---------------------------------------------------------
# Full Stack Targets (HL7 Engine, REST API, UI, Prometheus, Grafana)
# ---------------------------------------------------------

# Start order is important (DO NOT CHANGE)
stack-start: hl7-start rest-start ui-start prom-start grafana-start ## Start the complete server stack
	@echo "$(GREEN)All services started$(RESET)"

# Stop order (reverse) avoids race conditions and ensures dependencies are ready
stack-stop: grafana-stop prom-stop ui-stop rest-stop hl7-stop ## Stop the complete server stack
	@echo "$(YELLOW)All services stopped$(RESET)"

stack-restart: ## Restart the complete server stack
	@echo "Restarting full stack..."
	@$(MAKE) --no-print-directory stack-stop
	@sleep 1
	@$(MAKE) --no-print-directory stack-start
