
help:
	@echo "$(GREEN)Available commands:$(RESET)"
	@echo
	@for file in $(MAKEFILE_DIR)/makefiles/*.mk; do \
		group=$$(basename $$file .mk | tr '[:lower:]' '[:upper:]'); \
		echo "$(YELLOW)$${group}$(RESET)"; \
		grep -hE '^[a-zA-Z0-9_-]+:.*##' $$file | \
			awk 'BEGIN {FS = ":.*##"}; {printf "  %-30s %s\n", $$1, $$2}'; \
		echo ""; \
	done


# ---------------------------------------------------------
# HELP
# ---------------------------------------------------------
# Available commands:
#   bench-max             Max throughput benchmark
#   bench-conn            Connection stress benchmark
#   bench-sweep           Sweep benchmark
#   bench-visualize       Visualize benchmark results
#   run-benchmark-max-throughput-against-server  Max throughput vs temp server
#   run-benchmark-sweep-against-server  Sweep vs temp server
#   run-benchmark         Generic benchmark runner
#   hl7-start             Start HL7 MLLP engine
#   hl7-stop              Stop HL7 MLLP engine
#   hl7-server-status     Simple Status for HL7 MLLP engine
#   hl7-server-status-full  Complete Status for HL7 MLLP engine
#   hl7-start-fg          Start HL7 MLLP server in foreground
#   hl7-start-prom-fg     Start HL7 MLLP server with prometheus in foreground
#   hl7-kill-own-server   Kill own running HL7 MLLP server
#   hl7-kill-server       Kill any running HL7 MLLP server (based on binary)
#   monitoring-watch      Watch Monitoring Server Stack Status with 1sec Refresh Rate
#   monitoring-status     Monitoring Server Stack Detailled Status
#   monitoring-summary    Monitoring Server Stack Status Summary
#   monitoring-health     Monitoring Server Stack Health Summary
#   monitoring-status-compact  1-line full Server Stack Status (ideal for CLI)
#   monitoring-logs       (Deprecated) Show Prometheus and Grafana log files (50 lines)
#   stack-start           Start the complete server stack
#   stack-stop            Stop the complete server stack
#   stack-restart         Restart the complete server stack
#   all-server-status     (Deprecated) List Server Status for some servers
#   seed-db               Restore seed HL7 message SQLite DB
#   clean-db              Remove HL7 message SQLite DB
#   clean-routed          Clean routed/ folder
#   clean-results         Clean benchmark result JSON files
#   clear-persistence     Clean DB, routed/, and results/
#   prometheus-sync-rules  Copy rule files into /opt/prometheus (requires sudo)
#   prometheus-validate   Validate Prometheus config + rules
#   prometheus-reload     Reload Prometheus via SIGHUP
#   prometheus-full-reload  Full workflow: sync → validate → reload
#   prometheus-install-rules  First-time install of rule files (creates missing files)
#   kill-prometheus-all   Kill any running Prometheus server (based on binary)
#   kill-prometheus       Kill Prometheus server (based on PID)
#   test                  Run full test suite
#   test-file             Run tests for a specific file: make test-file FILE=...
#   test-name             Run tests matching a name: make test-name NAME=...
#   benchmark-tests       Run pytest with duration reporting
#   coverage              Run coverage report

# help: // OLD
# 	@echo "Available commands:"
# 	@echo ""
# 	@echo "  make install           - Install project in editable mode"
# 	@echo ""
# 	@echo "  make server-status     - Check MLLP server status"
# 	@echo "  make run-server        - Run MLLP server that hosts listener"
# 	@echo "  make restart-server    - Restart MLLP server that hosts listener"
# 	@echo "  make kill-own-server   - Kill own HL7 MLLP server if still running (safer)"
# 	@echo "  make kill-server       - Kill any running HL7 MLLP server"
# 	@echo "  make run-ui            - Run UI server to view HL7 messages"
# 	@echo ""
# 	@echo "  make test              - Run full test suite"
# 	@echo "  make test-file FILE=…  - Run a specific test file"
# 	@echo "  make test-name NAME=…  - Run a specific test by name"
# 	@echo "  make benchmark-tests   - Show slowest tests"
# 	@echo "  make coverage          - Run coverage report"
# 	@echo ""
# 	@echo "  make bench-max         - Max throughput benchmark"
# 	@echo "  make bench-conn        - Connection-only stress test"
# 	@echo "  make bench-sweep       - Concurrency sweep"
# 	@echo "  make bench-visualize FILE=…"
# 	@echo "                         - Visualize a benchmark JSON file"
# 	@echo "  make run-benchmark     - Run any benchmark against a temporary server instance. Usage:"
# 	@echo "                             + make run-benchmark BENCHMARK=--sweep"
# 	@echo "                             + make run-benchmark BENCHMARK=--conn-stress DURATION=30"
# 	@echo "                             + make run-benchmark BENCHMARK=--max-throughput EXTRA=\"--warmup 5\""
# 	@echo ""
# 	@echo "  make clean-db          - Remove SQLite DB"
# 	@echo "  make clean-routed      - Remove routed HL7 files"
# 	@echo "  make clean-results     - Remove results JSON files"
# 	@echo "  make reset             - Clean DB and routed + results folders"
# 	@echo ""
# 	@echo "  make prometheus        - Start Prometheus service as configured in PROM_CONFIG"
# 	@echo "  make prometheus-bg     - Start Prometheus service in background"
# 	@echo "  make prometheus-status - Show Prometheus server status"
# 	@echo "  make restart-prometheus - Restart Prometheus server"
# 	@echo "  make prometheus-test   - Curl /metrics to verify Prometheus endpoint"
# 	@echo "  make kill-prometheus   - Stop Prometheus server"
# 	@echo ""
# 	@echo "  make grafana           - Start Grafana server in foreground"
# 	@echo "  make grafana-bg        - Start Grafana server in background"
# 	@echo "  make kill-grafana      - Stop Grafana server"
# 	@echo "  make restart-grafana   - Restart Grafana server"
# 	@echo "  make grafana-status    - Show Grafana server status"
# 	@echo ""
# 	@echo "  make server-status-all - Show status of HL7 engine, REST API, Prometheus, Grafana"
# 	@echo "  make monitoring-stack  - Start Prometheus, Grafana and MLLP server (HL7 engine) with Prometheus enabled"
# 	@echo "  make monitoring-logs   - Show logs for Prometheus and Grafana"
# 	@echo "  make kill-monitoring   - Stop HL7 MLLP server, Prometheus + Grafana"