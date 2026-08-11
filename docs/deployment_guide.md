# Deployment Guide (`powersrv-small`)

This document describes how to sync and deploy updates from this local development repository to the production server (`powersrv-small`).

## Prerequisites
- SSH access to `powersrv-small` configured in `~/.ssh/config` or accessible via `ssh powersrv-small`.

---

## Deployment Steps

### Step 1: Sync Code to Server
Run `rsync` from the root of this local repository to sync updated scrapers, configuration, and core files to the server:

```bash
rsync -avz --exclude 'venv' --exclude 'articles.db' --exclude '.git' --exclude 'combined.log' ./ powersrv-small:/home/cy/ntfy-self-hosted/
```

> **Note:** We exclude `venv`, `articles.db` (server database), `.git`, and `combined.log` to preserve server-side state and prevent overwriting the server's database.

---

### Step 2: Execute Installation Script on Server
Connect to `powersrv-small` over SSH and execute `./install.sh`:

```bash
ssh powersrv-small "cd /home/cy/ntfy-self-hosted && ./install.sh"
```

---

## What `./install.sh` Does
1. Ensures the Python virtual environment (`venv`) exists on the server.
2. Installs or updates dependencies from `requirements.txt`.
3. Runs `setup_cron.py`, which reads `config.json` and dynamically generates cron jobs for all enabled monitors with 10-minute staggered offsets (at `07:00`, `12:30`, and `18:30`).
