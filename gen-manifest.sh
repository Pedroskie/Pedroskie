#!/usr/bin/env bash
set -euo pipefail

MANIFEST_FILE="manifest.txt"
README_FILE="README-Notarization.txt"

tmp_readme=$(mktemp)
tmp_treasury=$(mktemp)

sha256sum README.md > "$tmp_readme"
sha256sum docs/treasury-policy.md > "$tmp_treasury"

{
  echo "UnityFund Integrity Manifest"
  echo "Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "Git Commit: $(git rev-parse HEAD)"
  echo ""
  echo "Artifacts:"
  echo "  - README.md sha256: $(cut -d' ' -f1 "$tmp_readme")"
  echo "  - docs/treasury-policy.md sha256: $(cut -d' ' -f1 "$tmp_treasury")"
  echo ""
  echo "Anchors:"
  echo "  - Bitcoin OTS: {{ots_proof}}"
  echo "  - Ethereum Tx: {{eth_tx}}"
} > "$MANIFEST_FILE"

if [[ ! -f "$README_FILE" ]]; then
  {
    echo "# UnityFund Notarization Log"
    echo ""
    echo "This log records the dual-chain proofs for each notarized release."
    echo ""
    echo "| Timestamp (UTC) | Commit | Bitcoin OTS | Ethereum Tx |"
    echo "| --- | --- | --- | --- |"
  } > "$README_FILE"
fi

rm "$tmp_readme" "$tmp_treasury"
