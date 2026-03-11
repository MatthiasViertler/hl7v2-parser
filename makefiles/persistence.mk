# ---------------------------------------------------------
# DATABASE & PERSISTENCE MANAGEMENT
# ---------------------------------------------------------

seed-db: ## Restore seed HL7 message SQLite DB
	python3 tools/regenerate_seed_db.py

clean-db: ## Remove HL7 message SQLite DB
	@if [ -f "$(DB_PATH)" ]; then \
		echo "Removing SQLite DB..."; \
		rm $(DB_PATH); \
	fi

clean-routed: ## Clean routed/ folder
	@if [ -d "$(ROUTED_DIR)" ]; then \
		echo "Cleaning routed/ folders..."; \
		find $(ROUTED_DIR) -type f -name "*.hl7" -delete; \
		find $(ROUTED_DIR) -type d -empty -delete; \
	fi

clean-results: ## Clean benchmark result JSON files
	rm -f benchmarking/results/run_*.json

clear-persistence: ## Clean DB, routed/, and results/
	make clean-db
	make clean-routed
	make clean-results

observability-clean:
	@echo "Stopping all observability services..."
	- make stack-stop

	@echo "Removing PID and log files..."
	- rm -f hl7engine.pid prometheus.pid grafana.pid
	- rm -f hl7engine.log prometheus.log grafana.log

	@echo "Cleaning routed files..."
	- rm -rf routed/*

	@echo "Cleaning SQLite DB..."
	- rm -f data/hl7_messages.db

	@echo "Observability environment cleaned."