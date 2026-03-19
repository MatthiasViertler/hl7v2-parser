
# -----------------------------------------------------------
#   PROMETHEUS TARGETS
# -----------------------------------------------------------

prometheus-pid: ## Fetch Prometheus PID
	@ps -eo pid,cmd | grep "[p]rometheus" | awk '{print $$1}'

prom-start-fg: ## Start Prometheus in foreground
	cd $(PROM_HOME) && $(PROM_BIN) --config.file="$(PROM_CONF_DST)"

prom-start: ## Start Prometheus in background with -config=PROM_CONF_DST
	@echo "Starting Prometheus in background using config: $(PROM_CONF_DST)..."
	@mkdir -p $(PROM_HOME)/logs
	@nohup $(PROM_BIN) \
		--config.file="$(PROM_CONF_DST)" \
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

prometheus-sync-config: ## Sync Prometheus config + alert + recording rules
	@echo "Syncing Prometheus configuration and rule files..."

	# Ensure alerts directory exists
	@mkdir -p $(PROM_ALERTS_DST)

	# Copy main Prometheus config
	@cp $(PROM_CONF_SRC) $(PROM_CONF_DST)

	# Copy alert rules
	@cp $(PROM_ALERTS_SRC) $(PROM_ALERTS_DST)/

	# Copy recording rules (even if empty)
	@cp $(PROM_RECORDING_SRC) $(PROM_RECORDING_DST)

	@echo "Prometheus config sync complete. Reload Prometheus to apply changes."

prometheus-validate: ## Validate Prometheus config + rules
	@echo "Validating Prometheus configuration..."
	@cd $(PROM_HOME) && ./promtool check config prometheus.yml

	@echo "Validating alert rules..."
	@cd $(PROM_HOME) && ./promtool check rules alerts/hl7-engine.yml

	@echo "Validating recording rules..."
	@cd $(PROM_HOME) && ./promtool check rules alerts/recording_rules.yml

	@echo "Validation OK."

prometheus-reload: ## Reload Prometheus via HTTP API
	@echo "Reloading Prometheus configuration..."
	@curl -X POST http://localhost:9090/-/reload
	@echo "Prometheus reloaded."

prometheus-full-reload: prometheus-sync-config prometheus-validate prometheus-reload
	@echo "Prometheus config synced, validated, and reloaded."

# prometheus-reload: ## (DEPRECATE) Reload Prometheus via SIGHUP
# 	@echo "Reloading Prometheus configuration..."
# 	@if pgrep -x "$(notdir $(PROM_BIN))" > /dev/null; then \
# 		pkill -HUP -x "$(notdir $(PROM_BIN))"; \
# 		echo "Prometheus reloaded."; \
# 	else \
# 		echo "Prometheus is not running. Start it first."; \
# 	fi

# prometheus-full-reload: prometheus-sync-rules prometheus-validate prometheus-reload ## (DEPRECATE) Full workflow: sync → validate → reload
# 	@echo "Prometheus rules synced, validated, and reloaded."

# prometheus-install-rules: ## (DEPRECATE) First-time install of rule files (creates missing files)
# 	@echo "Installing Prometheus rule/config files into $(PROM_HOME)..."
# 	@sudo cp $(PROM_RULES_SRC)/prometheus.yml $(PROM_HOME)/prometheus.yml
# 	@sudo cp $(PROM_RULES_SRC)/recording_rules.yml $(PROM_HOME)/recording_rules.yml
# 	@sudo cp $(PROM_RULES_SRC)/alert_rules.yml $(PROM_HOME)/alert_rules.yml
# 	@echo "Installation complete."
