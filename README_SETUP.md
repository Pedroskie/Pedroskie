# Dwolla ACH Environment Setup

This guide describes how to configure and validate the Dwolla ACH integration bundle for the gtp5 pipeline. The bundle ships with pinned Python dependencies, a secure environment template, and tooling to verify that the workstation or CI runner matches the expected state prior to executing any irreversible operations.

## 1. Prerequisites
- Python 3.10 or later
- `pip` (Python package installer)
- Access credentials for Dwolla and FlowLedger anchoring services
- PostgreSQL and Redis endpoints (local or managed)

## 2. Bootstrap the Project
1. Clone this repository and switch to the desired branch.
2. Create a fresh virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install the pinned dependencies:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## 3. Configure Environment Variables
1. Copy the provided template and fill in the sensitive values:
   ```bash
   cp .env.example .env
   ```
2. Update `.env` with real API keys, database URLs, and secrets.
3. Keep `.env` out of version control. A default `.gitignore` entry for `.env` is recommended if one does not already exist.

## 4. Validate the Environment
Run the pre-flight validation script before invoking any Dwolla ACH workflows or CI/CD jobs:
```bash
python verify_env.py
```

The script performs the following checks:
- Python version and interpreter metadata
- Installed package versions against `requirements.txt`
- Presence and formatting of required environment variables (from `.env` by default)
- Optional FlowLedger anchoring configuration health

Pass `--help` to see additional options, including strict mode and custom file paths.

## 5. Regenerate Integrity Checksums (Optional)
Use the `integrity_checksum.sh` helper to produce deterministic SHA-256 hashes for anchoring or notarization workflows:
```bash
./integrity_checksum.sh
```

The script writes the digest list to `integrity_checksums.txt`. Provide `--stdout` to emit the hashes directly to standard output.

## 6. Continuous Integration Notes
- Add `python verify_env.py --strict` as a gating step before running migration or deployment pipelines.
- Fail the job if `verify_env.py` exits with a non-zero status; this indicates missing secrets, mismatched package versions, or other drift.
- Rotate Dwolla and FlowLedger credentials on a schedule that aligns with treasury policy requirements and audit controls.

## 7. Support & Escalation
- Security & Treasury Engineering: security@unityfund.example
- PagerDuty (24/7): `unityfund/treasury`

Document version: 1.0.0 (dwolla_ach_env_setup)
