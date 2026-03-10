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

color-test:
	@printf "%b\n" "$(GREEN)Hello$(RESET)"