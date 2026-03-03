# ---------------------------------------------------------
# HL7 Engine Makefile
# ---------------------------------------------------------

PYTEST=pytest
ROUTED_DIR=routed
DB_PATH=hl7engine/messages.db

# ---------------------------------------------------------
# INSTALL packages in editable mode for your Python env
# ---------------------------------------------------------
install:
	pip install -e .

# ---------------------------------------------------------
# Populate the SEED DB for demo purpose (HTML viewer)
# ---------------------------------------------------------
seed-db:
	python3 tools/regenerate_seed_db.py

# ---------------------------------------------------------
# CLEAN the runtime DB (after it became too large running tests)
# ---------------------------------------------------------
clean-db:
	rm -f data/hl7_messages.db
	cp data/seed/hl7_messages_demo.db data/hl7_messages.db

# ---------------------------------------------------------
# Prints the runtime of every test, sorted by slowest.
# ---------------------------------------------------------
benchmark:
	$(PYTEST) $(PYTEST_FLAGS) --durations=0

# ---------------------------------------------------------
# Run full test suite
# ---------------------------------------------------------
test:
#   clean-db
	$(PYTEST) $(PYTEST_FLAGS)
#	$(PYTEST) -q

# ---------------------------------------------------------
# Run a single test file
# Usage: make test-file FILE=tests/test_07_listener_router_integration.py
# ---------------------------------------------------------
test-file:
	$(PYTEST) -q $(FILE)

# ---------------------------------------------------------
# Run a single test by name
# Usage: make test-name NAME=test_oru_r01_routing
# ---------------------------------------------------------
test-name:
	$(PYTEST) -q -k $(NAME)

# ---------------------------------------------------------
# Clean routed/ folder
# ---------------------------------------------------------
clean-routed:
	@if [ -d "$(ROUTED_DIR)" ]; then \
		echo "Cleaning routed/ folders..."; \
		find $(ROUTED_DIR) -type f -name "*.hl7" -delete; \
		find $(ROUTED_DIR) -type d -empty -delete; \
	fi

# ---------------------------------------------------------
# Clean SQLite DB
# ---------------------------------------------------------
clean-db:
	@if [ -f "$(DB_PATH)" ]; then \
		echo "Removing SQLite DB..."; \
		rm $(DB_PATH); \
	fi

# ---------------------------------------------------------
# Reset environment (clean DB + routed)
# ---------------------------------------------------------
reset:
	make clean-db
	make clean-routed

# ---------------------------------------------------------
# Coverage report
# ---------------------------------------------------------
coverage:
	$(PYTEST) --cov=hl7engine --cov-report=term-missing

# ---------------------------------------------------------
# Help
# ---------------------------------------------------------
help:
	@echo "Available commands:"
	@echo "  make test              - Run full test suite"
	@echo "  make test-file FILE=…  - Run a specific test file"
	@echo "  make test-name NAME=…  - Run a specific test by name"
	@echo "  make clean-routed      - Remove routed HL7 files"
	@echo "  make clean-db          - Remove SQLite DB"
	@echo "  make reset             - Clean DB and routed folders"
	@echo "  make coverage          - Run coverage report"