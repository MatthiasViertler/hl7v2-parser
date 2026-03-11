# hl7engine/prometheus_exporter.py

from hl7engine.metrics.metrics import metrics

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

def _format_labels(label_set):
    if not label_set:
        return ""
    parts = [f'{k}="{v}"' for k, v in sorted(label_set)]
    return "{" + ",".join(parts) + "}"

def metrics_to_prometheus() -> str:
    snap = metrics.snapshot()
    lines = []

    # Counters
    for (name, label_set), value in snap["counters"].items():
        prom_name = f"hl7_{name}"
        labels = _format_labels(label_set)
        lines.append(f"# TYPE {prom_name} counter")
        lines.append(f"{prom_name}{labels} {int(value)}")

    # Gauges
    for (name, label_set), value in snap["gauges"].items():
        prom_name = f"hl7_{name}"
        labels = _format_labels(label_set)
        lines.append(f"# TYPE {prom_name} gauge")
        lines.append(f"{prom_name}{labels} {float(value)}")

    # Histograms → export p95/p99 as gauges
    for (name, label_set), values in snap["histograms"].items():
        qs = _quantiles(values, [0.95, 0.99])

        prom_p95 = f"hl7_{name}_p95_seconds"
        prom_p99 = f"hl7_{name}_p99_seconds"
        labels = _format_labels(label_set)

        lines.append(f"# TYPE {prom_p95} gauge")
        lines.append(f"{prom_p95}{labels} {qs[0.95]}")

        lines.append(f"# TYPE {prom_p99} gauge")
        lines.append(f"{prom_p99}{labels} {qs[0.99]}")

    return "\n".join(lines) + "\n"