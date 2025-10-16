#!/usr/bin/env python3
"""Pre-flight environment validation for the Dwolla ACH gtp5 pipeline."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import importlib.metadata as metadata

REQUIRED_PYTHON = (3, 10)

REQUIRED_ENV_VARS: Dict[str, str] = {
    "DWOLLA_APP_KEY": "Dwolla application key used for OAuth authentication.",
    "DWOLLA_APP_SECRET": "Dwolla application secret used for OAuth authentication.",
    "DWOLLA_ENVIRONMENT": "Dwolla environment identifier (e.g., sandbox or production).",
    "DWOLLA_WEBHOOK_SECRET": "Shared secret for validating Dwolla webhook callbacks.",
    "DATABASE_URL": "SQLAlchemy-compatible database URL for ACH ledger persistence.",
    "REDIS_URL": "Redis connection string for idempotency keys and caching.",
    "GTP5_PIPELINE_ID": "Identifier for the gtp5 deployment pipeline run context.",
}

OPTIONAL_FLOWLEDGER_VARS: Dict[str, str] = {
    "FLOW_LEDGER_ENDPOINT": "FlowLedger anchoring endpoint (https URL).",
    "FLOW_LEDGER_API_TOKEN": "API token for FlowLedger anchoring service.",
}

TARGET_FILES: Tuple[Path, ...] = (
    Path("requirements.txt"),
    Path(".env.example"),
    Path("README_SETUP.md"),
    Path("verify_env.py"),
)


@dataclass
class CheckResult:
    name: str
    status: str  # "ok", "warning", "error"
    details: str

    def is_failure(self, strict: bool) -> bool:
        if self.status == "error":
            return True
        if strict and self.status == "warning":
            return True
        return False


def check_python_version() -> CheckResult:
    current = sys.version_info
    required = REQUIRED_PYTHON
    version_str = f"{current.major}.{current.minor}.{current.micro}"
    if (current.major, current.minor) < required:
        return CheckResult(
            name="Python Version",
            status="error",
            details=(
                f"Detected Python {version_str}. Minimum required version is "
                f"{required[0]}.{required[1]}."
            ),
        )
    return CheckResult(
        name="Python Version",
        status="ok",
        details=f"Detected Python {version_str} (meets >= {required[0]}.{required[1]}).",
    )


def parse_requirements(requirements_path: Path) -> Dict[str, str]:
    requirements: Dict[str, str] = {}
    for raw_line in requirements_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(
                f"Requirement '{raw_line}' is not pinned. Use the 'package==version' format."
            )
        package, version = line.split("==", 1)
        requirements[package.strip().lower()] = version.strip()
    return requirements


def check_packages(requirements_path: Path) -> List[CheckResult]:
    if not requirements_path.exists():
        return [
            CheckResult(
                name="Python Dependencies",
                status="error",
                details=f"Missing requirements file: {requirements_path}",
            )
        ]

    try:
        requirements = parse_requirements(requirements_path)
    except ValueError as exc:
        return [
            CheckResult(
                name="Python Dependencies",
                status="error",
                details=str(exc),
            )
        ]

    results: List[CheckResult] = []
    for package_name, expected_version in requirements.items():
        try:
            installed_version = metadata.version(package_name)
        except metadata.PackageNotFoundError:
            results.append(
                CheckResult(
                    name=f"Dependency: {package_name}",
                    status="error",
                    details="Package is not installed.",
                )
            )
            continue

        if installed_version != expected_version:
            results.append(
                CheckResult(
                    name=f"Dependency: {package_name}",
                    status="error",
                    details=f"Expected {expected_version}, found {installed_version}.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name=f"Dependency: {package_name}",
                    status="ok",
                    details=f"Pinned version {installed_version} installed.",
                )
            )
    return results


def parse_env_file(env_path: Path) -> Dict[str, str]:
    contents = env_path.read_text(encoding="utf-8")
    env: Dict[str, str] = {}
    for raw_line in contents.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(
                f"Malformed line in {env_path}: '{raw_line}'. Expected 'KEY=VALUE'."
            )
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_env(env_path: Path) -> Tuple[Dict[str, str], List[CheckResult]]:
    if env_path.exists():
        try:
            return parse_env_file(env_path), []
        except ValueError as exc:
            return {}, [
                CheckResult(
                    name="Environment File",
                    status="error",
                    details=str(exc),
                )
            ]

    fallback = env_path.with_suffix(".example")
    if fallback.exists():
        return {}, [
            CheckResult(
                name="Environment File",
                status="warning",
                details=(
                    f"Primary env file '{env_path}' not found. Using template "
                    f"'{fallback}' as a reference only."
                ),
            )
        ]

    return {}, [
        CheckResult(
            name="Environment File",
            status="error",
            details=f"Neither '{env_path}' nor '{fallback}' exist.",
        )
    ]


def check_env_variables(env_values: Dict[str, str]) -> List[CheckResult]:
    results: List[CheckResult] = []
    for key, description in REQUIRED_ENV_VARS.items():
        value = env_values.get(key) or os.environ.get(key)
        if value:
            results.append(
                CheckResult(
                    name=f"Env: {key}",
                    status="ok",
                    details="Present.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name=f"Env: {key}",
                    status="error",
                    details=f"Missing value. {description}",
                )
            )

    for key, description in OPTIONAL_FLOWLEDGER_VARS.items():
        value = env_values.get(key) or os.environ.get(key)
        if value:
            results.append(
                CheckResult(
                    name=f"Env: {key}",
                    status="ok",
                    details="Present.",
                )
            )
        else:
            results.append(
                CheckResult(
                    name=f"Env: {key}",
                    status="warning",
                    details=f"Not set. Recommended for FlowLedger anchoring. {description}",
                )
            )
    return results


def check_anchor_files() -> List[CheckResult]:
    missing = [str(path) for path in TARGET_FILES if not path.exists()]
    if not missing:
        return [
            CheckResult(
                name="Bundle Contents",
                status="ok",
                details="All core bundle files are present.",
            )
        ]
    return [
        CheckResult(
            name="Bundle Contents",
            status="error",
            details=f"Missing required files: {', '.join(missing)}",
        )
    ]


def display_results(results: Iterable[CheckResult], strict: bool) -> int:
    exit_code = 0
    for result in results:
        label = result.status.upper().ljust(7)
        print(f"[{label}] {result.name}: {result.details}")
        if result.is_failure(strict):
            exit_code = 1
    return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate the Dwolla ACH environment before running pipelines.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        type=Path,
        help="Path to the environment file to validate (default: .env).",
    )
    parser.add_argument(
        "--requirements-file",
        default="requirements.txt",
        type=Path,
        help="Path to the pinned requirements file (default: requirements.txt).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors (useful for CI/CD gating).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    aggregated_results: List[CheckResult] = []
    aggregated_results.append(check_python_version())
    aggregated_results.extend(check_packages(args.requirements_file))

    env_values, env_results = load_env(args.env_file)
    aggregated_results.extend(env_results)
    if env_values:
        aggregated_results.extend(check_env_variables(env_values))
    else:
        aggregated_results.extend(check_env_variables({}))

    aggregated_results.extend(check_anchor_files())

    exit_code = display_results(aggregated_results, strict=args.strict)
    if exit_code == 0:
        print("\nEnvironment validation completed successfully.")
    else:
        print("\nEnvironment validation detected issues.")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
