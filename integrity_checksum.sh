#!/usr/bin/env bash
set -euo pipefail

FILES=(
  "requirements.txt"
  ".env.example"
  "README_SETUP.md"
  "verify_env.py"
)

OUTPUT_FILE="integrity_checksums.txt"
PRINT_TO_STDOUT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output|-o)
      OUTPUT_FILE="$2"
      shift 2
      ;;
    --stdout)
      PRINT_TO_STDOUT=true
      shift
      ;;
    --help|-h)
      cat <<USAGE
Usage: ./integrity_checksum.sh [--output FILE] [--stdout]

Generate SHA-256 hashes for the Dwolla ACH environment bundle files.
  --output FILE   Write checksums to FILE (default: integrity_checksums.txt)
  --stdout        Print checksums to stdout in addition to writing the file
  --help          Display this help message
USAGE
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if ! command -v sha256sum >/dev/null 2>&1; then
  echo "sha256sum command not found. Please install coreutils." >&2
  exit 1
fi

missing_files=()
for file in "${FILES[@]}"; do
  if [[ ! -f "$file" ]]; then
    missing_files+=("$file")
  fi
done

if [[ ${#missing_files[@]} -gt 0 ]]; then
  printf 'Missing files: %s\n' "${missing_files[*]}" >&2
  exit 1
fi

sha256sum "${FILES[@]}" > "$OUTPUT_FILE"

if [[ "$PRINT_TO_STDOUT" == true ]]; then
  cat "$OUTPUT_FILE"
fi

echo "SHA-256 checksums written to $OUTPUT_FILE"
