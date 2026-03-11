MAKEFILE_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

include $(MAKEFILE_DIR)/makefiles/utils.mk
include $(MAKEFILE_DIR)/makefiles/hl7.mk
include $(MAKEFILE_DIR)/makefiles/rest.mk
include $(MAKEFILE_DIR)/makefiles/ui.mk
include $(MAKEFILE_DIR)/makefiles/prometheus.mk
include $(MAKEFILE_DIR)/makefiles/grafana.mk
include $(MAKEFILE_DIR)/makefiles/monitoring.mk
include $(MAKEFILE_DIR)/makefiles/orchestration.mk
include $(MAKEFILE_DIR)/makefiles/persistence.mk
include $(MAKEFILE_DIR)/makefiles/testing.mk
include $(MAKEFILE_DIR)/makefiles/benchmarking.mk
include $(MAKEFILE_DIR)/makefiles/help.mk

.DEFAULT_GOAL := help

# ---------------------------------------------------------
# INSTALL packages in editable mode for your Python env
# ---------------------------------------------------------
install: ## Install project in editable mode
	pip install -e .

