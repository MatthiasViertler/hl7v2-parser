
# -----------------------------------------------------------
#   PROMETHEUS TARGETS
# -----------------------------------------------------------

prometheus-pid: ## Fetch Prometheus PID
	@ps -eo pid,cmd | grep "[p]rometheus" | awk '{print $$1}'

prom-start-fg: ## Start Prometheus in foreground
	cd $(PROM_HOME) && $(PROM_BIN) --config.file="$(PROM_CONF)"

prom-start: ## Start Prometheus in background with -config=PROM_CONF
	@echo "Starting Prometheus in background using config: $(PROM_CONF)..."
	@mkdir -p $(shell pwd)/monitoring/logs
	@nohup $(PROM_BIN) \
		--config.file="$(PROM_CONF)" \
		--web.listen-address=":$(PROM_PORT)" \
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

prom-stop: ## Stop Prometheus
	@PID=$$(pgrep -f "^$(PROM_BIN)"); \
	if [ -n "$$PID" ]; then \
		echo "Stopping Prometheus (PID $$PID)"; \
		kill $$PID; \
	else \
		echo "Prometheus not running."; \
	fi

prometheus-validate: ## (DEPRECATED) Validate Prometheus config + rules
	@echo "Validating Prometheus configuration..."
	@cd $(PROM_HOME) && ./promtool check config prometheus.yml
	@echo "Validating rule files..."
	@cd $(PROM_HOME) && ./promtool check rules recording_rules.yml
	@cd $(PROM_HOME) && ./promtool check rules alert_rules.yml
	@echo "Validation OK."

prometheus-reload: ## (DEPRECATE) Reload Prometheus via SIGHUP
	@echo "Reloading Prometheus configuration..."
	@if pgrep -x "$(notdir $(PROM_BIN))" > /dev/null; then \
		pkill -HUP -x "$(notdir $(PROM_BIN))"; \
		echo "Prometheus reloaded."; \
	else \
		echo "Prometheus is not running. Start it first."; \
	fi

prometheus-full-reload: prometheus-sync-rules prometheus-validate prometheus-reload ## (DEPRECATE) Full workflow: sync → validate → reload
	@echo "Prometheus rules synced, validated, and reloaded."

prometheus-install-rules: ## (DEPRECATE) First-time install of rule files (creates missing files)
	@echo "Installing Prometheus rule/config files into $(PROM_HOME)..."
	@sudo cp $(PROM_RULES_SRC)/prometheus.yml $(PROM_HOME)/prometheus.yml
	@sudo cp $(PROM_RULES_SRC)/recording_rules.yml $(PROM_HOME)/recording_rules.yml
	@sudo cp $(PROM_RULES_SRC)/alert_rules.yml $(PROM_HOME)/alert_rules.yml
	@echo "Installation complete."
