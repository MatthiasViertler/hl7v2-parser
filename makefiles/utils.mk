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
# === Local (DEV) prometheus Install ===
PROM_HOME := $(HOME)/prometheus
PROM_BIN := $(PROM_HOME)/prometheus

# Destination paths inside Prometheus install
PROM_CONF_DST := $(PROM_HOME)/prometheus.yml
PROM_ALERTS_DST := $(PROM_HOME)/alerts
PROM_RECORDING_DST := $(PROM_ALERTS_DST)/recording_rules.yml

# Source files in repo
PROM_CONF_SRC := $(shell pwd)/prometheus/prometheus.yml
PROM_ALERTS_SRC := $(shell pwd)/prometheus/alerts/hl7-engine.yml
PROM_RECORDING_SRC := $(shell pwd)/prometheus/alerts/recording_rules.yml
# (DEPRECATED) Rule files in our repo
#PROM_RULES_SRC := $(shell pwd)/prometheus
#PROM_RULES := alerts/recording_rules.yml alerts/hl7-engine.yml prometheus.yml

# Logs + PID
PROM_LOG := $(PROM_HOME)/logs/prometheus.log
PROM_PID := $(PROM_HOME)/logs/prometheus.pid
#PROM_LOG := $(shell pwd)/monitoring/logs/prometheus.log
#PROM_PID := $(shell pwd)/monitoring/prometheus.pid

# HL7 engine metrics exporter @ port 8010, scraped by Prometheus:
PROM_METRICS_URL := http://localhost:8010/metrics

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
#GRAFANA_CONF := $(GRAFANA_HOME)/conf/defaults.ini
GRAFANA_CONF := $(GRAFANA_HOME)/conf/grafana.ini
GRAFANA_DB := $(GRAFANA_HOME)/data/grafana.db
GRAFANA_LOG := $(GRAFANA_HOME)/logs/grafana.log

# Provisioning directories inside Grafana
GRAFANA_PROVISIONING_DST := $(GRAFANA_HOME)/conf/provisioning
GRAFANA_DASH_DST := $(GRAFANA_PROVISIONING_DST)/dashboards
GRAFANA_DATASOURCE_DST := $(GRAFANA_PROVISIONING_DST)/datasources

# Source files in our repo
GRAFANA_DASH_SRC := $(shell pwd)/grafana/hl7-engine
GRAFANA_PROVISIONING_FILE_SRC := $(shell pwd)/grafana/provisioning/dashboards/hl7-engine.yaml
GRAFANA_DATASOURCE_FILE_SRC := $(shell pwd)/grafana/provisioning/datasources/prometheus.yaml


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

define get_uptime ## Parse server uptime
	@ps -p $(1) -o etime= 2>/dev/null
endef

define check_port ## Check server port
	@nc -z localhost $(1) >/dev/null 2>&1 && echo "open" || echo "closed"
endef

define check_http ## Check server address
	@curl -s -o /dev/null -w "%{http_code}" $(1)
endef
