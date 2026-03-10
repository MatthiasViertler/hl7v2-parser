MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

include $(MAKEFILE_DIR)/makefiles/utils.mk
include $(MAKEFILE_DIR)/makefiles/hl7.mk
include $(MAKEFILE_DIR)/makefiles/rest.mk
include $(MAKEFILE_DIR)/makefiles/ui.mk
include $(MAKEFILE_DIR)/makefiles/prometheus.mk
include $(MAKEFILE_DIR)/makefiles/grafana.mk
include $(MAKEFILE_DIR)/makefiles/monitoring.mk
include $(MAKEFILE_DIR)/makefiles/orchestration.mk
include $(MAKEFILE_DIR)/makefiles/help.mk

.DEFAULT_GOAL := help

# ---------------------------------------------------------
# INSTALL packages in editable mode for your Python env
# ---------------------------------------------------------
install: ## Install project in editable mode
	pip install -e .


# ---------------------------------------------------------
# DATABASE MANAGEMENT
# ---------------------------------------------------------
seed-db: ## Restore seed HL7 message SQLite DB
	python3 tools/regenerate_seed_db.py

clean-db: ## Clean HL7 message SQLite DB
	@if [ -f "$(DB_PATH)" ]; then \
		echo "Removing SQLite DB..."; \
		rm $(DB_PATH); \
	fi

clear-persistence: ## Clean HL7 message DB, routed/ and results/
	make clean-db
	make clean-routed
	make clean-results

# ---------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------

clean-routed: ## ROUTED FOLDER CLEANUP
	@if [ -d "$(ROUTED_DIR)" ]; then \
		echo "Cleaning routed/ folders..."; \
		find $(ROUTED_DIR) -type f -name "*.hl7" -delete; \
		find $(ROUTED_DIR) -type d -empty -delete; \
	fi

clean-results: ## RESULTS JSON CLEANUP
	rm -f benchmarking/results/run_*.json

# ---------------------------------------------------------
# TESTING
# ---------------------------------------------------------
test:
	$(PYTEST) $(PYTEST_FLAGS)

test-file:
	$(PYTEST) -q $(FILE)

test-name:
	$(PYTEST) -q -k $(NAME)

benchmark-tests:
	$(PYTEST) $(PYTEST_FLAGS) --durations=0

coverage:
	$(PYTEST) --cov=hl7engine --cov-report=term-missing

# ---------------------------------------------------------
# BENCHMARKING SUITE
# ---------------------------------------------------------
bench-max:
	$(BENCH) --duration 30 --max-throughput

bench-conn:
	$(BENCH) --duration 30 --conn-stress

bench-sweep:
	$(BENCH) --duration 10 --sweep

bench-visualize:
	$(BENCH) --visualize $(FILE)

# ---------------------------------------------------------
# Run benchmark against a temporary server instance
# Do NOT kill server instance with 
#    pkill -f "hl7engine.mllp_server" || true;
# To not kill Prometheus server instance
# ---------------------------------------------------------
run-benchmark-max-throughput-against-server:
	@echo "Starting HL7 MLLP server in background..."
	@{ \
	python3 -m hl7engine.mllp_server &
	@SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	echo "Waiting for server to start..."; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --max-throughput; \
	echo "Stopping server..."; \
	kill $$SERVER_PID || true; \
	echo "Done."
	}

run-benchmark-sweep-against-server:
	@echo "Starting HL7 MLLP server in background..."
	@{ \
	python3 -m hl7engine.mllp_server &
	@SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	echo "Waiting for server to start..."; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --sweep; \
	echo "Stopping server..."; \
	kill $$SERVER_PID || true; \
	echo "Done."
	}

# ---------------------------------------------------------
# Run any benchmark against a temporary server instance
# Do NOT kill server instance with 
#    pkill -f "hl7engine.mllp_server" || true;
# To not kill Prometheus server instance
# ---------------------------------------------------------
run-benchmark:
#	@echo "Starting HL7 MLLP server in background..."
#	@{ \
#	python3 -m hl7engine.mllp_server & \
#	SERVER_PID=$$!; \
#	echo "Server PID: $$SERVER_PID"; \
#	echo "Waiting for server to start..."; \
#	sleep 1; \
#	echo "Stopping server..."; \
#	kill $$SERVER_PID || true;
	@{ \
	echo "Running benchmark: $(BENCHMARK)"; \
	$(BENCH) --duration $(DURATION) $(BENCHMARK) $(EXTRA); \
	echo "Done."; \
	}

observability-clean:
	@echo "Stopping all observability services..."
	- make kill-server
	- make prometheus-kill
	- make grafana-kill

	@echo "Removing PID and log files..."
	- rm -f hl7engine.pid prometheus.pid grafana.pid
	- rm -f hl7engine.log prometheus.log grafana.log

	@echo "Cleaning routed files..."
	- rm -rf routed/*

	@echo "Cleaning SQLite DB..."
	- rm -f data/hl7_messages.db

	@echo "Observability environment cleaned."


