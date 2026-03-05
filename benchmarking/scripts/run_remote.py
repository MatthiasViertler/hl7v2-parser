import sys
from benchmarking.run_benchmark import main

# Example: python -m benchmarking.scripts.run_remote 10.0.0.5 2575 300
if __name__ == "__main__":
    # Example: override arguments for a remote target
    sys.argv = [
        "run_remote",
        "--host", "10.0.0.5",
        "--port", "2575",
        "--duration", "300"
    ]
    main()
