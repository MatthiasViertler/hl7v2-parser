# makefiles/utils.mk

# Colors
GREEN  := \\033[0;32m
RED    := \\033[0;31m
YELLOW := \\033[1;33m
BLUE   := \\033[0;34m
RESET  := \\033[0m

# Ports
HL7_PORT      := 2575
REST_PORT     := 8000
HTML_PORT     := 8080
PROM_PORT     := 9090
GRAFANA_PORT  := 3000

# Benchmark configuration (override via: make run-benchmark BENCHMARK=--sweep)
BENCHMARK ?= --max-throughput
DURATION ?= 10
EXTRA ?=
PYTEST=pytest
BENCH=python3 -m benchmarking.run_benchmark

# ---------------------------------------------------------
# HL7 Engine Makefile
# ---------------------------------------------------------
ROUTED_DIR=routed
HL7_ENGINE_LOG=hl7engine.log
DB_PATH=data/hl7_messages.db

# ---------------------------------------------------------
# REST API Server
# ---------------------------------------------------------
REST_LOG := $(shell pwd)/monitoring/logs/restapi.log
REST_PID := $(shell pwd)/monitoring/restapi.pid

# ---------------------------------------------------------
# PROMETHEUS
# ---------------------------------------------------------
# === Sudo apt install Prometheus Install ===
# PROM_HOME := /opt/prometheus
# PROM_BIN := $(PROM_HOME)/prometheus
# PROM_CONF := $(PROM_HOME)/prometheus.yml
# PROM_LOG := $(PROM_HOME)/prometheus.log
# === Local prometheus Install ===
PROM_HOME := $(HOME)/prometheus
PROM_BIN := $(PROM_HOME)/prometheus
PROM_CONF := $(PROM_HOME)/prometheus.yml

PROM_LOG := $(shell pwd)/monitoring/logs/prometheus.log
PROM_PID := $(shell pwd)/monitoring/prometheus.pid

# HL7 engine metrics exporter @ port 8010, scraped by Prometheus:
PROM_METRICS_URL := http://localhost:8010/metrics
# (DEPRECATED) Rule files in our repo
PROM_RULES_SRC := $(shell pwd)/monitoring
PROM_RULES := recording_rules.yml alert_rules.yml prometheus.yml

# ---------------------------------------------------------
# GRAFANA (DEVELOPMENT SETTINGS)
# ---------------------------------------------------------
# GRAFANA_DEV_BIN := $(HOME)/grafana/bin/grafana
# GRAFANA_DEV_HOME := $(HOME)/grafana
# GRAFANA_DEV_CONF := $(HOME)/grafana/conf/defaults.ini
# GRAFANA_LOG := grafana.log
# GRAFANA_DASH_SRC := $(shell pwd)/monitoring/dashboards
# GRAFANA_PROVISIONING_FILE_SRC := $(shell pwd)/monitoring/dashboards/hl7.yaml
# GRAFANA_DASH_DST := $(HOME)/grafana/conf/provisioning/dashboards

# === Local Grafana Install ===
GRAFANA_HOME := $(HOME)/grafana
GRAFANA_BIN := $(GRAFANA_HOME)/bin/grafana
GRAFANA_CONF := $(GRAFANA_HOME)/conf/defaults.ini
GRAFANA_DB := $(GRAFANA_HOME)/data/grafana.db
GRAFANA_LOG := $(GRAFANA_HOME)/logs/grafana.log
GRAFANA_PROVISIONING := $(GRAFANA_HOME)/conf/provisioning/dashboards
GRAFANA_DASH_DST := $(GRAFANA_HOME)/conf/provisioning/dashboards
GRAFANA_DASH_SRC := $(shell pwd)/monitoring/dashboards


# ---------------------------------------------------------
# GENERAL & HELPER TARGETS
# ---------------------------------------------------------
define status_line
	@printf "%-20s %-10s %-10s %-40s\n" "$(1)" "$(2)" "$(3)" "$(4)"
endef

define ok_fail
	$(if $(1),$(GREEN)OK$(RESET),$(RED)FAIL$(RESET))
endef

define color_http
	$(if $(filter 200,$(1)),$(GREEN)$(1)$(RESET),$(RED)$(1)$(RESET))
endef

define color_port
	$(if $(filter open,$(1)),$(GREEN)open$(RESET),$(RED)closed$(RESET))
endef

define get_uptime
	@ps -p $(1) -o etime= 2>/dev/null
endef

define check_port
	@nc -z localhost $(1) >/dev/null 2>&1 && echo "open" || echo "closed"
endef

define check_http
	@curl -s -o /dev/null -w "%{http_code}" $(1)
endef
