# makefiles/monitoring.mk

monitoring-watch: ## Watch Monitoring Server Stack Status with 1sec Refresh Rate
	@while true; do \
		clear; \
		$(MAKE) --no-print-directory monitoring-status; \
		sleep 1; \
	done

monitoring-status: ## Monitoring Server Stack Detailled Status
	@echo "==================== $(BLUE)HL7 CORE STACK$(RESET) ===================="
	@printf "%-15s %-8s %-12s %-8s %-8s %-10s\n" "Service" "PID" "Uptime" "Port" "Health" "Status"

	@PID=$$(pgrep -f "[h]l7engine.mllp_server"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost $(HL7_PORT) && echo "open" || echo "closed"); \
		STATUS="$(GREEN)OK$(RESET)"; HEALTH="n/a"; \
	else \
		PID="-"; UPTIME="-"; PORT="closed"; HEALTH="n/a"; STATUS="$(RED)DOWN$(RESET)"; \
	fi; \
	printf "%-15s %-8s %-12s %-8s %-8s %b\n" "HL7 Engine" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH" "$$STATUS"

	@PID=$$(pgrep -f "[u]vicorn hl7engine.api"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost $(REST_PORT) && echo "open" || echo "closed"); \
		HEALTH=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$(REST_PORT)/health || echo 000); \
		if [ "$$HEALTH" = "200" ] && [ "$$PORT" = "open" ]; then STATUS="$(GREEN)OK$(RESET)"; else STATUS="$(RED)DOWN$(RESET)"; fi; \
	else \
		PID="-"; UPTIME="-"; PORT="closed"; HEALTH="000"; STATUS="$(RED)DOWN$(RESET)"; \
	fi; \
	printf "%-15s %-8s %-12s %-8s %-8s %b\n" "REST API" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH" "$$STATUS"

	@echo
	@echo "================== $(BLUE)MONITORING STACK$(RESET) =================="
	@printf "%-15s %-8s %-12s %-8s %-14s %-10s\n" "Service" "PID" "Uptime" "Port" "Health" "Status"

	@PID=$$(pgrep -f "[p]ython.*http.server $(HTML_PORT)"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost $(HTML_PORT) && echo "open" || echo "closed"); \
		HROOT=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$(HTML_PORT)/ || echo 000); \
		HSTATIC=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$(HTML_PORT)/static/ || echo 000); \
		if [ "$$PORT" = "open" ] && [ "$$HROOT" = "200" ] && [ "$$HSTATIC" = "200" ]; then \
			STATUS="$(GREEN)OK$(RESET)"; \
		elif [ "$$PORT" = "open" ] && [ "$$HROOT" = "200" ]; then \
			STATUS="$(YELLOW)WARN$(RESET)"; \
		else \
			STATUS="$(RED)DOWN$(RESET)"; \
		fi; \
		HEALTH="root:$$HROOT static:$$HSTATIC"; \
	else \
		PID="-"; UPTIME="-"; PORT="closed"; HEALTH="root:000 static:000"; STATUS="$(RED)DOWN$(RESET)"; \
	fi; \
	printf "%-15s %-8s %-12s %-8s %-14s %b\n" "HTML Server" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH" "$$STATUS"

	@PID=$$(pgrep -f "^$(PROM_BIN)"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost $(PROM_PORT) && echo "open" || echo "closed"); \
		HEALTH=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$(PROM_PORT)/metrics || echo 000); \
		if [ "$$PORT" = "open" ] && [ "$$HEALTH" = "200" ]; then STATUS="$(GREEN)OK$(RESET)"; else STATUS="$(YELLOW)WARN$(RESET)"; fi; \
	else \
		PID="-"; UPTIME="-"; PORT="closed"; HEALTH="000"; STATUS="$(YELLOW)WARN$(RESET)"; \
	fi; \
	printf "%-15s %-8s %-12s %-8s %-14s %b\n" "Prometheus" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH" "$$STATUS"

	@PID=$$(pgrep -f "[g]rafana server"); \
	if [ -n "$$PID" ]; then \
		UPTIME=$$(ps -p $$PID -o etime= | head -n 1); \
		PORT=$$(nc -z localhost $(GRAFANA_PORT) && echo "open" || echo "closed"); \
		HEALTH=$$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$(GRAFANA_PORT)/api/health || echo 000); \
		if [ "$$PORT" = "open" ] && [ "$$HEALTH" = "200" ]; then STATUS="$(GREEN)OK$(RESET)"; else STATUS="$(YELLOW)WARN$(RESET)"; fi; \
	else \
		PID="-"; UPTIME="-"; PORT="closed"; HEALTH="000"; STATUS="$(YELLOW)WARN$(RESET)"; \
	fi; \
	printf "%-15s %-8s %-12s %-8s %-14s %b\n" "Grafana" "$$PID" "$$UPTIME" "$$PORT" "$$HEALTH" "$$STATUS"

	@$(MAKE) --no-print-directory monitoring-summary


monitoring-summary: ## Monitoring Server Stack Status Summary
	@HL7_PID=$$(pgrep -f "[h]l7engine.mllp_server"); \
	REST_PID=$$(pgrep -f "[u]vicorn hl7engine.api"); \
	HTML_PID=$$(pgrep -f "[p]ython.*http.server $(HTML_PORT)"); \
	PROM_PID=$$(pgrep -f "^$(PROM_BIN)"); \
	GRAF_PID=$$(pgrep -f "[g]rafana server"); \
	CORE_OK=1; MON_OK=1; \
	if [ -z "$$HL7_PID" ] || [ -z "$$REST_PID" ]; then CORE_OK=0; fi; \
	if [ -z "$$HTML_PID" ] || [ -z "$$PROM_PID" ] || [ -z "$$GRAF_PID" ]; then MON_OK=0; fi; \
	if [ "$$CORE_OK" -eq 1 ] && [ "$$MON_OK" -eq 1 ]; then \
		printf "\n%b\n" "$(GREEN)Summary: All systems operational$(RESET)"; \
	elif [ "$$CORE_OK" -eq 1 ] && [ "$$MON_OK" -eq 0 ]; then \
		printf "\n%b\n" "$(YELLOW)Summary: Core HL7 stack UP, monitoring degraded$(RESET)"; \
	else \
		printf "\n%b\n" "$(RED)Summary: Core HL7 stack degraded$(RESET)"; \
	fi


monitoring-health: ## Monitoring Server Stack Health Summary
	@HL7_PID=$$(pgrep -f "[h]l7engine.mllp_server"); \
	REST_PID=$$(pgrep -f "[u]vicorn hl7engine.api"); \
	HTML_PID=$$(pgrep -f "[p]ython.*http.server $(HTML_PORT)"); \
	PROM_PID=$$(pgrep -f "^$(PROM_BIN)"); \
	GRAF_PID=$$(pgrep -f "[g]rafana server"); \
	CORE_OK=1; MON_OK=1; \
	if [ -z "$$HL7_PID" ] || [ -z "$$REST_PID" ]; then CORE_OK=0; fi; \
	if [ -z "$$HTML_PID" ] || [ -z "$$PROM_PID" ] || [ -z "$$GRAF_PID" ]; then MON_OK=0; fi; \
	if [ "$$CORE_OK" -eq 1 ] && [ "$$MON_OK" -eq 1 ]; then \
		printf "%b\n" "$(GREEN)monitoring-health: GREEN (all systems up)$(RESET)"; \
		exit 0; \
	elif [ "$$CORE_OK" -eq 1 ] && [ "$$MON_OK" -eq 0 ]; then \
		printf "%b\n" "$(YELLOW)monitoring-health: YELLOW (core up, monitoring degraded)$(RESET)"; \
		exit 1; \
	else \
		printf "%b\n" "$(RED)monitoring-health: RED (core HL7 stack degraded)$(RESET)"; \
		exit 1; \
	fi

monitoring-status-compact: ## 1-line full Server Stack Status (ideal for CLI)
	@HL7_PID=$$(pgrep -f "[h]l7engine.mllp_server"); \
	REST_PID=$$(pgrep -f "[u]vicorn hl7engine.api"); \
	HTML_PID=$$(pgrep -f "[p]ython.*http.server $(HTML_PORT)"); \
	PROM_PID=$$(pgrep -f "^$(PROM_BIN)"); \
	GRAF_PID=$$(pgrep -f "[g]rafana server"); \
	HL7=$$( [ -n "$$HL7_PID" ] && echo "OK" || echo "DOWN" ); \
	REST=$$( [ -n "$$REST_PID" ] && echo "OK" || echo "DOWN" ); \
	HTML=$$( [ -n "$$HTML_PID" ] && echo "OK" || echo "DOWN" ); \
	PROM=$$( [ -n "$$PROM_PID" ] && echo "OK" || echo "DOWN" ); \
	GRAF=$$( [ -n "$$GRAF_PID" ] && echo "OK" || echo "DOWN" ); \
	CORE_OK=1; MON_OK=1; \
	[ "$$HL7" = "OK" ] && [ "$$REST" = "OK" ] || CORE_OK=0; \
	[ "$$HTML" = "OK" ] && [ "$$PROM" = "OK" ] && [ "$$GRAF" = "OK" ] || MON_OK=0; \
	if [ "$$CORE_OK" -eq 1 ] && [ "$$MON_OK" -eq 1 ]; then \
		STATUS="ALL GREEN"; COLOR="$(GREEN)"; \
	elif [ "$$CORE_OK" -eq 1 ] && [ "$$MON_OK" -eq 0 ]; then \
		STATUS="MONITORING DEGRADED"; COLOR="$(YELLOW)"; \
	else \
		STATUS="CORE DOWN"; COLOR="$(RED)"; \
	fi; \
	printf "%bHL7:%s REST:%s HTML:%s PROM:%s GRAF:%s → %s%b\n" \
		"$$COLOR" "$$HL7" "$$REST" "$$HTML" "$$PROM" "$$GRAF" "$$STATUS" "$(RESET)"

monitoring-logs: ## (Deprecated) Show Prometheus and Grafana log files (50 lines)
	@echo "=== Prometheus Logs ==="
	@if [ -f "$(PROM_LOG)" ]; then \
		tail -n 50 $(PROM_LOG); \
	else \
		echo "No Prometheus log file found."; \
	fi

	@echo "\n=== Grafana Logs ==="
	@if [ -f "$(GRAFANA_LOG)" ]; then \
		tail -n 50 $(GRAFANA_LOG); \
	else \
		echo "No Grafana log file found."; \
	fi