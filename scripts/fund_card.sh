#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./scripts/fund_card.sh --amount <amount> [--currency USD] [--memo "Ops float"] [--cardholder "Name"]

Required environment variables:
  API_KEY           Issuing API key (bearer token)
  API_SECRET        Issuing API secret (used for X-API-SECRET header)
  API_ENDPOINT      Base card endpoint (e.g. https://api-issuer.example.com/v1/cards)

Optional environment variables:
  IDEMPOTENCY_KEY   Custom idempotency token (default: fund-$(uuidgen))
  SUPERBANK_LOG_DIR Override log directory (default: ~/superbank-node/logs)

The script locates the most recent provider_id from card_mappings.jsonl (or the one matching
--cardholder), submits a funding request, appends a CARD_FUND ledger entry, produces an
audit digest, anchors it with flowledger, and triggers a MetaSync cycle.
USAGE
}

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Error: required command '$cmd' not found in PATH" >&2
    exit 1
  fi
}

ensure_env() {
  local name="$1"
  if [[ -z "${!name-}" ]]; then
    echo "Error: environment variable '$name' must be set" >&2
    exit 1
  fi
}

parse_amount_minor() {
  python3 - "$1" <<'PY'
import sys
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

if len(sys.argv) != 2:
    sys.exit("Amount argument missing")
try:
    dec = Decimal(sys.argv[1]).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
except InvalidOperation:
    sys.exit("Invalid amount format: {}".format(sys.argv[1]))
if dec < 0:
    sys.exit("Amount must be non-negative")
minor = int(dec * 100)
print(minor)
PY
}

# Parse CLI options
AMOUNT=""
CURRENCY="USD"
MEMO=""
CARDHOLDER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --amount)
      AMOUNT="${2-}"
      shift 2
      ;;
    --currency)
      CURRENCY="${2-}"
      shift 2
      ;;
    --memo)
      MEMO="${2-}"
      shift 2
      ;;
    --cardholder)
      CARDHOLDER="${2-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$AMOUNT" ]]; then
  echo "Error: --amount is required" >&2
  usage
  exit 1
fi

ensure_env API_KEY
ensure_env API_SECRET
ensure_env API_ENDPOINT
require_cmd jq
require_cmd curl
require_cmd flowledger
require_cmd python3
require_cmd uuidgen

LOG_ROOT="${SUPERBANK_LOG_DIR:-$HOME/superbank-node/logs}"
MAPPING_FILE="$LOG_ROOT/card_mappings.jsonl"
LEDGER_FILE="$LOG_ROOT/ledger_card_fund.jsonl"
AUDIT_PREFIX="$LOG_ROOT/audit_fund"

if [[ ! -f "$MAPPING_FILE" ]]; then
  echo "Error: mapping file not found at $MAPPING_FILE" >&2
  exit 1
fi

mkdir -p "$LOG_ROOT"

IDEMPOTENCY_KEY="${IDEMPOTENCY_KEY:-fund-$(uuidgen)}"

if [[ -n "$CARDHOLDER" ]]; then
  provider_line=$(jq -r --arg name "$CARDHOLDER" 'select(.cardholder == $name)' "$MAPPING_FILE" | tail -n 1)
  if [[ -z "$provider_line" ]]; then
    echo "Error: no mapping entry found for cardholder '$CARDHOLDER'" >&2
    exit 1
  fi
else
  provider_line=$(tail -n 1 "$MAPPING_FILE")
fi

provider_id=$(jq -r '.provider_id // empty' <<<"$provider_line")
card_token=$(jq -r '.card_token // empty' <<<"$provider_line")
external_id=$(jq -r '.external_id // empty' <<<"$provider_line")

if [[ -z "$provider_id" || "$provider_id" == "null" ]]; then
  echo "Error: provider_id missing from mapping entry" >&2
  exit 1
fi

AMOUNT_MINOR=$(parse_amount_minor "$AMOUNT")

funding_payload=$(jq -n \
  --arg provider_id "$provider_id" \
  --arg card_token "$card_token" \
  --arg external_id "$external_id" \
  --arg currency "$CURRENCY" \
  --arg memo "$MEMO" \
  --argjson amount_minor "$AMOUNT_MINOR" \
  '{
    provider_id: $provider_id,
    card_token: ($card_token // empty),
    external_id: ($external_id // empty),
    amount_minor: $amount_minor,
    currency: $currency,
    memo: $memo,
    type: "CARD_FUND"
  } | with_entries(select(.value != "" and .value != null))
')

FUND_ENDPOINT="${API_ENDPOINT%/}/$provider_id/fund"

echo "🔄 Submitting funding request to $FUND_ENDPOINT"
response=$(curl -sS -X POST "$FUND_ENDPOINT" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -H "X-API-SECRET: $API_SECRET" \
  -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
  --data "$funding_payload")

if [[ -z "$response" ]]; then
  echo "Error: empty response from funding endpoint" >&2
  exit 1
fi

echo "$response" | jq . >/dev/null 2>&1 || {
  echo "Error: response is not valid JSON" >&2
  echo "$response" >&2
  exit 1
}

errored=$(jq -r '.error // .errors // empty' <<<"$response")
if [[ -n "$errored" ]]; then
  echo "Funding API returned an error:" >&2
  echo "$response" | jq >&2
  exit 1
fi

funding_id=$(jq -r '.funding_id // .id // .data.id // ""' <<<"$response")
status=$(jq -r '.status // .data.status // "PENDING"' <<<"$response")

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

ledger_entry=$(jq -n \
  --arg timestamp "$TIMESTAMP" \
  --arg provider_id "$provider_id" \
  --arg card_token "$card_token" \
  --arg external_id "$external_id" \
  --arg memo "$MEMO" \
  --arg currency "$CURRENCY" \
  --arg amount_minor "$AMOUNT_MINOR" \
  --arg idempotency "$IDEMPOTENCY_KEY" \
  --arg funding_id "$funding_id" \
  --arg status "$status" \
  --argjson response "$response" \
  '{
    timestamp: $timestamp,
    entry_type: "CARD_FUND",
    provider_id: $provider_id,
    card_token: ($card_token // empty),
    external_id: ($external_id // empty),
    amount_minor: ($amount_minor | tonumber),
    currency: $currency,
    memo: $memo,
    idempotency_key: $idempotency,
    funding_id: ($funding_id // empty),
    status: $status,
    response: $response
  } | with_entries(select(.value != "" and .value != null))
')

echo "$ledger_entry" >> "$LEDGER_FILE"

audit_uuid=$(uuidgen)
audit_file="$AUDIT_PREFIX_${audit_uuid}.json"
ledger_sha=$(printf '%s' "$ledger_entry" | sha256sum | awk '{print $1}')
response_sha=$(printf '%s' "$response" | sha256sum | awk '{print $1}')

audit_payload=$(jq -n \
  --arg timestamp "$TIMESTAMP" \
  --arg provider_id "$provider_id" \
  --arg funding_id "$funding_id" \
  --arg ledger_file "$LEDGER_FILE" \
  --arg ledger_sha "$ledger_sha" \
  --arg response_sha "$response_sha" \
  --arg status "$status" \
  --arg amount_minor "$AMOUNT_MINOR" \
  --arg currency "$CURRENCY" \
  --arg memo "$MEMO" \
  --arg idempotency "$IDEMPOTENCY_KEY" \
  '{
    audit_type: "CARD_FUND",
    timestamp: $timestamp,
    provider_id: $provider_id,
    funding_id: ($funding_id // empty),
    amount_minor: ($amount_minor | tonumber),
    currency: $currency,
    memo: $memo,
    status: $status,
    idempotency_key: $idempotency,
    ledger_file: $ledger_file,
    ledger_entry_sha256: $ledger_sha,
    response_sha256: $response_sha
  } | with_entries(select(.value != "" and .value != null))
')

echo "$audit_payload" > "$audit_file"

audit_sha=$(sha256sum "$audit_file" | awk '{print $1}')

echo "✅ Funding recorded"
echo "   Provider ID   : $provider_id"
echo "   Funding ID    : ${funding_id:-<pending>}"
echo "   Amount (minor): $AMOUNT_MINOR $CURRENCY"
echo "   Ledger entry  : $LEDGER_FILE"
echo "   Audit file    : $audit_file"
echo "   Audit SHA-256 : $audit_sha"

echo "⛓️  Anchoring audit file via FlowLedger..."
flowledger anchor --file "$audit_file"

echo "🔁 Running FlowLedger MetaSync cycle (cards target)"
flowledger metasync --target cards

echo "Done."
