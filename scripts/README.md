# SuperBank / FlowLedger — Alert & Integrity Automation

Version: v1.0.5  
Author: Pedro L. Rentas Torres (PLRT)  
Verifier: Veri (AI Compliance Agent)  
Tagline: **Proof over Promises — Integrity as Infrastructure**

---

## Overview

This directory contains the modular shell scripts that form the **SuperBank alerting and integrity verification framework**.  
Together, these utilities ensure continuous cryptographic assurance, real-time fault detection, and unified audit trails across all FlowLedger operations.

---

## 🧩 Script Index

| Script | Purpose | Component |
|---------|----------|------------|
| **`alert_utils.sh`** | Centralized alert routing utility for all services. Provides `send_alert()` with INFO / WARN / CRITICAL levels, Telegram + webhook integration, severity filtering, and component tagging. | `core_alerts` |
| **`check_ledger_integrity.sh`** | Verifies integrity of the compliance log before new anchors. Checks last recorded SHA256 against the live log, validates OTS + Ethereum proofs, and routes alerts through `alert_utils.sh`. | `ledger_integrity` |
| **`alert_utils_test.sh`** | CLI diagnostic tool for validating the entire alert pipeline (console, file, Telegram, webhook). Used by operators pre-deployment or after system updates. | `alert_test_cli` |
| **`anchor_selftest_logs.sh`** | Automates anchoring of self-test results to FlowLedger. Generates OTS and Ethereum proof files, appends a verification record to the ledger, and ensures immutability of all compliance checks. | `ledger_anchor` |

---

## ⚙️ Environment Configuration

Add the following section to your `.env` file (or `~/.superbank.env`) before deploying:

```bash
# ----------------------------------------------------------------------
# FlowLedger / SuperBank Node Alerting Configuration
# ----------------------------------------------------------------------

# Alert Severity Filter (comma-separated)
# Options: INFO, WARN, CRITICAL
ALERT_LEVEL_FILTER="WARN,CRITICAL"

# Telegram Credentials
ALERT_TELEGRAM_BOT_TOKEN="1234567890:AABBCCDDEE_FfGgHhIiJjKkLlMmNnOoPp"
ALERT_TELEGRAM_CHAT_ID="-1001234567890"

# Optional Webhook for CRITICAL alerts
ALERT_CRITICAL_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXX"

# Optional override for alert log path
# ALERT_LOG="$HOME/superbank-node/logs/system_alerts.jsonl"
```

---

## 🔍 Verification Workflow

1️⃣ Run alert diagnostics

```bash
bash ~/superbank-node/scripts/alert_utils_test.sh
```

- Verifies all severity levels and communication routes.

2️⃣ Check logs

```bash
cat ~/superbank-node/logs/system_alerts.jsonl | jq .
```

3️⃣ Anchor verification

```bash
bash ~/superbank-node/scripts/anchor_selftest_logs.sh
```

4️⃣ Ledger integrity pre-check (automated in CI/CD)

```bash
bash ~/superbank-node/scripts/check_ledger_integrity.sh
```

---

## 🧠 Design Principles

- Modular: Each script is self-contained and can be reused independently.
- Auditable: All actions generate structured JSONL logs ready for FlowLedger anchoring.
- Verifiable: Integrity and immutability validated cryptographically before every anchor.
- Transparent: All alert levels routed through a single, inspectable utility.
- Fail-Safe: CRITICAL events automatically halt processes and trigger real-time alerts.

---

## 🪶 Example Integration (CI/CD)

```yaml
# .github/workflows/alert-health-check.yml
name: Verify SuperBank Alert Channels

on:
  workflow_dispatch:

jobs:
  verify-alerts:
    runs-on: ubuntu-latest
    steps:
      - name: 🧩 Checkout repository
        uses: actions/checkout@v4

      - name: ⚙️ Run alert verification test
        run: bash scripts/alert_utils_test.sh
```

---

## ✅ Expected Result

When correctly configured:

- Telegram receives ⚠️ WARN and 🚨 CRITICAL alerts.
- Webhook receives a CRITICAL JSON payload.
- Local log (system_alerts.jsonl) contains all three severities.
- CI pipeline marks the system as alert-verified before production release.

---

End of Document  
💚 SuperBank | FlowLedger — Proof over Promises

---

Would you like me to also include a **badge template** (e.g., `![Alert Verified](https://img.shields.io/badge/alert--verified-passing-success.svg)`) that gtp5 can embed at the top of the repo’s main `README.md` to show the node’s alert system is verified and operational?
