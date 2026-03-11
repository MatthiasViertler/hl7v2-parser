# ---------------------------------------------------------
# TESTING
# ---------------------------------------------------------

test: ## Run full test suite
	$(PYTEST) $(PYTEST_FLAGS)

test-file: ## Run tests for a specific file: make test-file FILE=...
	$(PYTEST) -q $(FILE)

test-name: ## Run tests matching a name: make test-name NAME=...
	$(PYTEST) -q -k $(NAME)

benchmark-tests: ## Run pytest with duration reporting
	$(PYTEST) $(PYTEST_FLAGS) --durations=0

coverage: ## Run coverage report
	$(PYTEST) --cov=hl7engine --cov-report=term-missing