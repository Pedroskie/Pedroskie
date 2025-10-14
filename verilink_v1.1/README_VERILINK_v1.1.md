# VeriLink v1.1 – Meta-Anchoring Bundle

The VeriLink CLI extends UnityFund's release integrity process with explicit
digest continuity and reviewer attestations. This bundle contains everything
needed to anchor, verify, and chain manifests in CI, production queues, and
nightly integrity sweeps.

## Contents

- `verilink-cli.py` – CLI for anchor/verify/chain workflows (exit codes 0/10/11/12/13).
- `manifest_schema_v2.json` – JSON Schema for manifests with optional continuity digest.
- `metaReview.json` – Template reviewers fill after manifest verification.
- `records.json` – Sample records file to seed anchors.
- `.github/workflows/verify.yml` – GitHub Actions workflow exercising the CLI.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install jsonschema

# 1) Anchor from records → MANIFEST.json with manifest_digest
python verilink-cli.py anchor --records records.json --output MANIFEST.json

# 2) Verify manifest digest
python verilink-cli.py verify --manifest MANIFEST.json

# 3) Link to previous epoch (continuity) and recompute digest
python verilink-cli.py chain --manifest MANIFEST.json --previous <SHA256_PREV>

# 4) Re-verify with continuity
python verilink-cli.py verify --manifest MANIFEST.json --previous <SHA256_PREV>
```

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0    | Success |
| 10   | Usage error (file missing, invalid JSON) |
| 11   | Manifest failed schema validation |
| 12   | Computed digest mismatch |
| 13   | Continuity mismatch |

## Continuous Integration Notes

The bundled workflow (`.github/workflows/verify.yml`) runs on every push and
pull request when copied to a repository root. It anchors the sample
`records.json`, validates the manifest, then chains continuity against a dummy
previous digest to demonstrate exit code handling.

## Operational Checklist

1. Anchor with `verilink-cli.py anchor` to produce `MANIFEST.json`.
2. Sign and archive the resulting manifest digest in FlowLedger v8.
3. Stamp `MANIFEST.json` with OpenTimestamps and store `MANIFEST.json.ots`.
4. Collect reviewer attestations using `metaReview.json` and store alongside the manifest.
5. Schedule nightly `anchor → verify → chain → verify` runs in the gtp5 Integrity
   Cluster; persist output under `/opt/verilink/anchors/` and export metrics.

## Next Steps

- Wire Dwolla and Stripe modules to auto-emit `records.json` entries per run.
- Upgrade FlowLedger to v9 for dual anchoring (Ethereum Sepolia calldata + Bitcoin OTS).
- Start UnityWireless Phase I with TrustCredits anchoring through the v1.1 chain.
