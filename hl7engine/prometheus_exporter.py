# hl7engine/prometheus_exporter.py

from hl7engine.metrics import metrics

def _quantiles(values, quantiles):
    if not values:
        return {q: 0.0 for q in quantiles}
    vs = sorted(values)
    n = len(vs)
    out = {}
    for q in quantiles:
        idx = int(q * (n - 1))
        out[q] = vs[idx]
    return out

def metrics_to_prometheus() -> str:
    snap = metrics.snapshot()
    lines = []

    # Counters
    for name, value in snap["counters"].items():
        prom_name = f"hl7_{name}"
        lines.append(f"# TYPE {prom_name} counter")
        lines.append(f"{prom_name} {int(value)}")

    # Gauges
    for name, value in snap["gauges"].items():
        prom_name = f"hl7_{name}"
        lines.append(f"# TYPE {prom_name} gauge")
        lines.append(f"{prom_name} {float(value)}")

    # Histograms → export p95/p99 as gauges
    for name, values in snap["histograms"].items():
        prom_p95 = f"hl7_{name}_p95"
        prom_p99 = f"hl7_{name}_p99"
        qs = _quantiles(values, [0.95, 0.99])
        lines.append(f"# TYPE {prom_p95} gauge")
        lines.append(f"{prom_p95} {qs[0.95]}")
        lines.append(f"# TYPE {prom_p99} gauge")
        lines.append(f"{prom_p99} {qs[0.99]}")

    return "\n".join(lines) + "\n"