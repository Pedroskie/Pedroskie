#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 8 ]]; then
  cat >&2 <<'USAGE'
Usage: ./issue_virtual_card_safe_with_mapping.sh "Cardholder Name" CARD_TYPE "Card Product" "Street" "City" "State" "Postal Code" "Country"

Example:
  ./issue_virtual_card_safe_with_mapping.sh \
    "Alice Example" \
    VIRTUAL \
    "Visa Virtual" \
    "123 Main St" \
    "Sample City" \
    "CA" \
    "94105" \
    "US"
USAGE
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "Error: jq is required to run this script." >&2
  exit 1
fi

cardholder_name="$1"
card_type="$2"
card_product="$3"
street="$4"
city="$5"
state="$6"
postal_code="$7"
country="$8"

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
repo_root="$script_dir"
mapping_file="$repo_root/config/virtual_card_safe_mapping.json"

if [[ ! -f "$mapping_file" ]]; then
  echo "Error: mapping file not found at $mapping_file" >&2
  exit 1
fi

if ! safe_program_json=$(jq -ce --arg product "$card_product" '.[$product]' "$mapping_file"); then
  echo "Error: no SAFE mapping found for card product '$card_product'." >&2
  exit 1
fi

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
slug=$(printf '%s' "$cardholder_name" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//' | sed 's/-$//')
if [[ -z "$slug" ]]; then
  slug="cardholder"
fi

output_dir="$repo_root/artifacts/virtual-card-requests"
mkdir -p "$output_dir"
output_file="$output_dir/${timestamp//[:]/}${slug:+_}$slug.json"

payload=$(jq -n \
  --arg cardholder "$cardholder_name" \
  --arg cardType "$card_type" \
  --arg cardProduct "$card_product" \
  --arg street "$street" \
  --arg city "$city" \
  --arg state "$state" \
  --arg postal "$postal_code" \
  --arg country "$country" \
  --arg timestamp "$timestamp" \
  --arg slug "$slug" \
  --argjson safeProgram "$safe_program_json" \
  '{
    cardholder: {
      name: $cardholder,
      address: {
        line1: $street,
        city: $city,
        region: $state,
        postal_code: $postal,
        country: $country
      }
    },
    card: {
      type: $cardType,
      product: $cardProduct
    },
    request: {
      reference: $slug,
      created_at: $timestamp
    },
    safe_program: $safeProgram
  }'
)

printf '%s\n' "$payload" > "$output_file"

cat <<'MESSAGE'
Virtual card issuance payload created.
MESSAGE

echo "Output file: $output_file"

jq -r '
  def safe: .safe_program.safe;
  [
    "Cardholder: \(.cardholder.name)",
    "Product: \(.card.product) [\(.card.type)]",
    "SAFE Address: \(safe.address) on \(safe.chain) (threshold \(safe.threshold) of \(safe.owners | length))",
    "Hot Wallet Cap: \(.safe_program.treasury_controls.hot_wallet_cap_percent)%",
    "Minimum Confirmations: \(.safe_program.treasury_controls.min_confirmations)"
  ]
  + ["SAFE Owners:"]
  + (safe.owners | map("  - \(.name) (\(.role)): \(.address)"))
  + [
    "Policy Reference: \(.safe_program.policy_reference)",
    "Funding Source: \(.safe_program.funding.source)"
  ]
  | .[]
' "$output_file"
