# benchmarking/visualize.py

import json
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path

def load_results(path):
    results_path = Path(__file__).parent / path
    with open(results_path, "r") as f:
        return json.load(f)

def plot_sweep(results):
    workers = [r["workers"] for r in results]
    throughput = [r["throughput"] for r in results]
    ack_fails = [r["ack_failures"] for r in results]

    fig, ax1 = plt.subplots()

    ax1.set_title("Throughput vs Concurrency")
    ax1.set_xlabel("Number of Workers")
    ax1.set_ylabel("Throughput (msg/sec)", color="tab:blue")
    ax1.plot(workers, throughput, marker="o", color="tab:blue")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()
    ax2.set_ylabel("ACK Failures", color="tab:red")
    ax2.plot(workers, ack_fails, marker="x", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    fig.tight_layout()
    plt.show()

def plot_latency(latencies_ms):
    if not latencies_ms:
        print("No latency data available.")
        return

    plt.hist(latencies_ms, bins=20, color="skyblue", edgecolor="black")
    plt.title("ACK Latency Histogram")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Count")
    plt.show()

def plot_percentiles(latencies_ms):
    if not latencies_ms:
        print("No latency data available.")
        return

    percentiles = [50, 90, 95, 99]
    values = [np.percentile(latencies_ms, p) for p in percentiles]

    plt.plot(percentiles, values, marker="o")
    plt.title("ACK Latency Percentiles")
    plt.xlabel("Percentile")
    plt.ylabel("Latency (ms)")
    plt.grid(True)
    plt.show()