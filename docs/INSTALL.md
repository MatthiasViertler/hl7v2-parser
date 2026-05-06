# HL7v2 Engine — Installation Guide

This document provides a clean, reproducible installation workflow for new developers and deployment environments.  
It includes system dependencies, Python setup, Prometheus/Grafana configuration, and troubleshooting.

---

# 1. System Dependencies (Required for Python Builds)

If you install Python via **pyenv**, you must install development libraries for:

- bz2
- lzma
- sqlite3
- readline
- tkinter

Otherwise Python will build without these modules and you will see errors like:

- `ModuleNotFoundError: No module named '_sqlite3'`
- `Missing the bzip2 lib?`
- `Missing the GNU readline lib?`
- `Missing the lzma lib?`

Install everything:

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  libssl-dev \
  zlib1g-dev \
  libbz2-dev \
  libreadline-dev \
  libsqlite3-dev \
  libncursesw5-dev \
  xz-utils \
  tk-dev \
  liblzma-dev \
  libffi-dev \
  libxml2-dev \
  libxmlsec1-dev \
  libcurl4-openssl-dev
```

# 2. Install Python via pyenv

```bash
pyenv install 3.10.20
pyenv virtualenv 3.10.20 medicalIT-venv
pyenv activate medicalIT-venv
```

Verify:
```bash
python --version
```

# 3. Install the HL7 Engine (Editable Mode)

This project uses a PEP‑517 backend (no setup.py).
Editable installs require a backend that supports PEP‑660.

Upgrade pip first:

```bash
python -m pip install --upgrade pip
```

Then install:

```bash
pip install -e .
```

If you see:

    “build backend is missing the build_editable hook”

your pip version is too old.

# 4. Install Prometheus & Grafana Locally
Prometheus

Extract anywhere, e.g.:

```code
~/prometheus/
```

Grafana

Extract anywhere, e.g.:

```code
~/grafana/
```

# 5. Fixing Grafana Provisioning Paths (IMPORTANT)

Grafana does not expand ~ inside YAML files.

This will not work:

```Yaml
options:
  path: ~/grafana/conf/provisioning/dashboards
```

Use environment variables instead:
```Yaml
options:
  path: ${HOME}/grafana/conf/provisioning/dashboards
```

Or define your own:

```bash
export GRAFANA_HOME=$HOME/grafana
```

Then in Yaml:
```Yaml
options:
  path: ${GRAFANA_HOME}/conf/provisioning/dashboards
```

This makes provisioning portable across machines.

# 6. Sync Prometheus & Grafana Provisioning

Your Makefile provides helpers:

```bash
make prometheus-sync-config
make grafana-sync-provisioning
```

Restart the stack to apply changes:

```bash
make stack-restart
```

# 7. Starting the Full Stack

Start everything (HL7 engine, REST API, UI, Prometheus, Grafana):

```bash
make stack-start
```

Check status:

```bash
make monitoring-status
```

If HL7 engine or REST API show as DOWN:

    ensure ports 2575 and 8000 are free
    ensure the correct pyenv environment is active
    check logs under monitoring/logs/
    verify the engine installed correctly (pip install -e .)
    

# 8. Troubleshooting
HL7 engine DOWN

Check logs:

```bash
tail -f hl7engine.log
```

Typical causes:

    - wrong Python version
    - missing system dependencies
    - editable install failed

Prometheus target DOWN

    - ensure engine started with --prometheus
    - ensure port 8010 is free
    - open http://localhost:8010/metrics

Grafana dashboards not loading

    - provisioning path contains ~
    - forgot to run 'make grafana-sync-provisioning'
    - Grafana not restarted
    
# 9. Developer Mode vs CI Mode
CI Mode (default)

```bash
pytest
```

Starts:
    - HL7 engine
    - REST API
    - Prometheus exporter
    - cleans DB
    - cleans routed/

Developer Mode (manual servers)

```bash
pytest --use-external-servers
```

Use this when:

    - you want to run the engine manually
    - you want to keep DB state
    - you want to debug routing or metrics live

Start servers manually:

```bash
make hl7-start
make rest-start
make prom-start
make grafana-start
```

# 10. Quickstart Summary

```bash
# Install system deps
sudo apt install build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev \
                 libsqlite3-dev xz-utils tk-dev liblzma-dev libffi-dev

# Install Python
pyenv install 3.10.20
pyenv virtualenv 3.10.20 medicalIT-venv
pyenv activate medicalIT-venv

# Install engine
pip install -e .

# Sync monitoring
make prometheus-sync-config
make grafana-sync-provisioning

# Start everything
make stack-start
make monitoring-status
```

This completes the installation guide.

