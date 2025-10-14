#!/usr/bin/env python3
"""VeriLink CLI for anchoring, verifying, and chaining manifest records.

This module provides three commands that support the VeriLink anchoring
workflow:

```
python verilink-cli.py anchor --records records.json --output MANIFEST.json
python verilink-cli.py verify --manifest MANIFEST.json [--previous <digest>]
python verilink-cli.py chain --manifest MANIFEST.json --previous <digest>
```

Exit codes:
    * 0  - success.
    * 10 - input/usage error (missing files, bad JSON, CLI misuse).
    * 11 - manifest schema validation failure.
    * 12 - manifest digest mismatch.
    * 13 - continuity/previous digest mismatch.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

try:  # noqa: C901 - no nested try/except for imports per repo guidance
    import jsonschema
except ModuleNotFoundError as exc:  # pragma: no cover - surfaced at runtime
    raise SystemExit(
        "jsonschema is required. Install with 'pip install jsonschema'."
    ) from exc


EXIT_OK = 0
EXIT_USAGE = 10
EXIT_SCHEMA = 11
EXIT_DIGEST = 12
EXIT_CONTINUITY = 13


class VeriLinkError(Exception):
    """Base exception for VeriLink errors."""


class ManifestDigestMismatch(VeriLinkError):
    """Raised when the manifest_digest does not match the computed digest."""


class ManifestContinuityError(VeriLinkError):
    """Raised when previous manifest digests do not align."""


class ManifestSchemaError(VeriLinkError):
    """Raised when the manifest fails schema validation."""


SCHEMA_NAME = "manifest_schema_v2.json"


def _cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="VeriLink manifest utility")
    sub = parser.add_subparsers(dest="command", required=True)

    anchor = sub.add_parser("anchor", help="Anchor records into a manifest")
    anchor.add_argument(
        "--records",
        required=True,
        type=Path,
        help="Path to the records JSON file used as input",
    )
    anchor.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination path for the manifest JSON file",
    )

    verify = sub.add_parser("verify", help="Validate a manifest digest")
    verify.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to the manifest JSON file to verify",
    )
    verify.add_argument(
        "--previous",
        type=str,
        help="Optional expected previous manifest digest for continuity checks",
    )

    chain = sub.add_parser("chain", help="Attach previous digest continuity")
    chain.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to the manifest JSON file to update",
    )
    chain.add_argument(
        "--previous",
        required=True,
        type=str,
        help="Digest of the previous manifest in the chain",
    )

    return parser


def _load_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise SystemExit(EXIT_USAGE) from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(EXIT_USAGE) from exc


def _dump_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _schema_validator(schema_path: Path) -> jsonschema.Draft202012Validator:
    schema = _load_json(schema_path)
    return jsonschema.Draft202012Validator(schema)


def _schema_path() -> Path:
    return Path(__file__).resolve().parent / SCHEMA_NAME


def _normalize_for_digest(payload: Dict[str, Any]) -> str:
    """Return canonical JSON string used for digest computation."""
    digest_payload = {k: v for k, v in payload.items() if k != "manifest_digest"}
    return json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def compute_manifest_digest(payload: Dict[str, Any]) -> str:
    """Compute a SHA-256 digest for the provided manifest payload."""
    canonical = _normalize_for_digest(payload)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return digest


def _extract_records(records_payload: Any) -> Iterable[Dict[str, Any]]:
    """Normalize records payload from either a list or an object with a records key."""
    if isinstance(records_payload, dict):
        if "records" not in records_payload:
            raise SystemExit(
                EXIT_USAGE
            )
        return records_payload["records"]
    if isinstance(records_payload, list):
        return records_payload
    raise SystemExit(EXIT_USAGE)


def _build_manifest(records_payload: Any) -> Dict[str, Any]:
    records = list(_extract_records(records_payload))
    metadata: Dict[str, Any] = {}
    if isinstance(records_payload, dict):
        metadata = {
            k: v for k, v in records_payload.items() if k != "records"
        }

    manifest: Dict[str, Any] = {
        "schema_version": 2,
        "generated_at": _dt.datetime.now(tz=_dt.timezone.utc).isoformat(),
        "records": records,
    }
    if metadata:
        manifest["records_metadata"] = metadata
    manifest["manifest_digest"] = compute_manifest_digest(manifest)
    return manifest


def anchor_manifest(records_path: Path, output_path: Path) -> None:
    records_payload = _load_json(records_path)
    manifest = _build_manifest(records_payload)
    _dump_json(output_path, manifest)


def _validate_manifest(manifest: Dict[str, Any]) -> None:
    validator = _schema_validator(_schema_path())
    errors = sorted(validator.iter_errors(manifest), key=lambda e: e.path)
    if errors:
        message = "; ".join(error.message for error in errors)
        raise ManifestSchemaError(message)


def _load_manifest(path: Path) -> Dict[str, Any]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        raise ManifestSchemaError("Manifest root must be an object")
    return payload


def verify_manifest(manifest_path: Path, expected_previous: Optional[str]) -> None:
    manifest = _load_manifest(manifest_path)
    _validate_manifest(manifest)

    stored_digest = manifest.get("manifest_digest")
    computed_digest = compute_manifest_digest(manifest)
    if stored_digest != computed_digest:
        raise ManifestDigestMismatch(
            "manifest_digest does not match computed digest"
        )

    if expected_previous is not None:
        recorded_previous = manifest.get("previous_manifest_digest")
        if recorded_previous != expected_previous:
            raise ManifestContinuityError(
                "previous_manifest_digest does not match expected digest"
            )


def chain_manifest(manifest_path: Path, previous_digest: str) -> None:
    manifest = _load_manifest(manifest_path)
    _validate_manifest(manifest)

    manifest["previous_manifest_digest"] = previous_digest
    manifest["manifest_digest"] = compute_manifest_digest(manifest)
    _dump_json(manifest_path, manifest)


def _handle_anchor(args: argparse.Namespace) -> int:
    try:
        anchor_manifest(args.records, args.output)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    return EXIT_OK


def _handle_verify(args: argparse.Namespace) -> int:
    try:
        verify_manifest(args.manifest, args.previous)
    except ManifestSchemaError:
        return EXIT_SCHEMA
    except ManifestDigestMismatch:
        return EXIT_DIGEST
    except ManifestContinuityError:
        return EXIT_CONTINUITY
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    return EXIT_OK


def _handle_chain(args: argparse.Namespace) -> int:
    try:
        chain_manifest(args.manifest, args.previous)
    except ManifestSchemaError:
        return EXIT_SCHEMA
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else EXIT_USAGE
    return EXIT_OK


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _cli_parser()
    args = parser.parse_args(argv)

    if args.command == "anchor":
        return _handle_anchor(args)
    if args.command == "verify":
        return _handle_verify(args)
    if args.command == "chain":
        return _handle_chain(args)
    return EXIT_USAGE


if __name__ == "__main__":
    sys.exit(main())
