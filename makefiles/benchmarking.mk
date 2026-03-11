# ---------------------------------------------------------
# BENCHMARKING SUITE
# ---------------------------------------------------------

bench-max: ## Max throughput benchmark
	$(BENCH) --duration 30 --max-throughput

bench-conn: ## Connection stress benchmark
	$(BENCH) --duration 30 --conn-stress

bench-sweep: ## Sweep benchmark
	$(BENCH) --duration 10 --sweep

bench-visualize: ## Visualize benchmark results
	$(BENCH) --visualize $(FILE)

# ---------------------------------------------------------
# Run benchmark against temporary server instance
# ---------------------------------------------------------

run-benchmark-max-throughput-against-server: ## Max throughput vs temp server
	@echo "Starting HL7 MLLP server in background..."
	@{ \
	python3 -m hl7engine.mllp_server & \
	SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --max-throughput; \
	echo "Stopping server..."; \
	kill $$SERVER_PID || true; \
	echo "Done."; \
	}

run-benchmark-sweep-against-server: ## Sweep vs temp server
	@echo "Starting HL7 MLLP server in background..."
	@{ \
	python3 -m hl7engine.mllp_server & \
	SERVER_PID=$$!; \
	echo "Server PID: $$SERVER_PID"; \
	sleep 1; \
	echo "Running benchmark..."; \
	$(BENCH) --duration 10 --sweep; \
	echo "Stopping server..."; \
	kill $$SERVER_PID || true; \
	echo "Done."; \
	}

run-benchmark: ## Generic benchmark runner
	@{ \
	echo "Running benchmark: $(BENCHMARK)"; \
	$(BENCH) --duration $(DURATION) $(BENCHMARK) $(EXTRA); \
	echo "Done."; \
	}