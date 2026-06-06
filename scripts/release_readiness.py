#!/usr/bin/env python3
"""Summarize TeacherMarket OSS release readiness checks.

This script is intentionally read-only. It can run local verification commands
and, when an API URL is provided, perform negative HTTP smoke checks.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Check:
    name: str
    status: str
    detail: str


def status_icon(status: str) -> str:
    return {"pass": "PASS", "fail": "FAIL", "warn": "WARN", "skip": "SKIP"}[status]


def run_command(name: str, command: list[str], cwd: Path) -> Check:
    executable = Path(command[0])
    if not executable.is_absolute() and len(executable.parts) > 1:
        resolved = ROOT / executable
        if resolved.exists():
            command = [str(resolved), *command[1:]]
    try:
        completed = subprocess.run(command, cwd=cwd, check=False, text=True, capture_output=True)
    except FileNotFoundError as exc:
        return Check(name, "fail", f"{exc.filename} not found")

    if completed.returncode == 0:
        return Check(name, "pass", "ok")

    output = (completed.stderr or completed.stdout).strip().splitlines()
    detail = output[-1] if output else f"exit {completed.returncode}"
    return Check(name, "fail", detail[:220])


def http_status(url: str, *, method: str = "GET") -> tuple[int | None, str]:
    request = Request(url, method=method)
    try:
        with urlopen(request, timeout=8) as response:
            return response.status, "ok"
    except HTTPError as exc:
        return exc.code, exc.reason
    except URLError as exc:
        return None, str(exc.reason)
    except TimeoutError:
        return None, "timeout"


def check_http(args: argparse.Namespace) -> list[Check]:
    if not args.api_base_url:
        return [Check("HTTP smoke", "skip", "no --api-base-url provided")]

    base_url = args.api_base_url.rstrip("/")
    checks: list[Check] = []

    status, detail = http_status(f"{base_url}/health")
    checks.append(
        Check(
            "API health",
            "pass" if status == 200 else "fail",
            f"{status or 'unreachable'} {detail}",
        )
    )

    status, detail = http_status(f"{base_url}/admin/products/pending")
    checks.append(
        Check(
            "Admin routes reject anonymous access",
            "pass" if status in {401, 403} else "fail",
            f"{status or 'unreachable'} {detail}",
        )
    )

    status, detail = http_status(f"{base_url}/subscription-payments/mock/00000000-0000-0000-0000-000000000000/mark-paid", method="POST")
    checks.append(
        Check(
            "Mock mark-paid rejects anonymous access",
            "pass" if status in {401, 403} else "fail",
            f"{status or 'unreachable'} {detail}",
        )
    )

    if args.production:
        for path in ("/docs", "/openapi.json"):
            status, detail = http_status(f"{base_url}{path}")
            checks.append(
                Check(
                    f"Production {path} disabled",
                    "pass" if status == 404 else "fail",
                    f"{status or 'unreachable'} {detail}",
                )
            )
    else:
        checks.append(Check("Production docs/openapi HTTP checks", "skip", "pass --production for production target checks"))

    return checks


def file_contains(path: str, needles: Iterable[str]) -> bool:
    text = (ROOT / path).read_text(encoding="utf-8")
    return all(needle in text for needle in needles)


def check_static() -> list[Check]:
    checks = [
        Check(
            "Manual Telegram smoke gate documented",
            "pass" if file_contains("docs/release-gates.md", ["Manual Telegram Smoke", "initData"]) else "fail",
            "docs/release-gates.md",
        ),
        Check(
            "Storage privacy expectations documented",
            "pass" if file_contains("docs/self-hosting.md", ["Keep product files private", "S3/R2"]) else "fail",
            "docs/self-hosting.md",
        ),
        Check(
            "Payment scope excludes material checkout",
            "pass" if file_contains("docs/self-hosting.md", ["author subscriptions only", "does not process material purchases"]) else "fail",
            "docs/self-hosting.md",
        ),
        Check(
            "Production settings validation present",
            "pass" if file_contains("apps/api/app/config.py", ["validate_runtime_settings", "app_env", "S3/R2 storage settings"]) else "fail",
            "apps/api/app/config.py",
        ),
        Check(
            "Mock mark-paid is admin-gated",
            "pass" if file_contains("apps/api/app/modules/subscriptions/router.py", ["mock/{payment_id}/mark-paid", "require_admin"]) else "fail",
            "apps/api/app/modules/subscriptions/router.py",
        ),
    ]
    return checks


def command_checks(skip_commands: bool) -> list[Check]:
    if skip_commands:
        return [Check("Local verification commands", "skip", "requested with --skip-commands")]

    python = os.environ.get("PYTHON", sys.executable)
    return [
        run_command("API unit tests", [python, "-m", "unittest", "discover", "app/tests", "-v"], ROOT / "apps/api"),
        run_command("Bot compile", [python, "-m", "compileall", "bot"], ROOT / "apps/bot"),
        run_command("Webapp build", ["npm", "run", "build"], ROOT / "apps/webapp"),
        run_command("Git diff whitespace", ["git", "diff", "--check"], ROOT),
    ]


def print_report(checks: list[Check]) -> int:
    print("TeacherMarket OSS release readiness")
    print("This read-only check supports release gates; it does not replace real Telegram-client smoke.")
    print()
    for check in checks:
        print(f"{status_icon(check.status):4} {check.name} - {check.detail}")
    print()
    failed = [check for check in checks if check.status == "fail"]
    warnings = [check for check in checks if check.status == "warn"]
    if failed:
        print(f"Result: NOT READY ({len(failed)} failed, {len(warnings)} warnings)")
        return 1
    print(f"Result: READY for automated/read-only checks ({len(warnings)} warnings)")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run read-only TeacherMarket OSS release readiness checks.")
    parser.add_argument(
        "--api-base-url",
        "--api-url",
        default="",
        help="Optional running API base URL, e.g. http://localhost:8000",
    )
    parser.add_argument("--production", action="store_true", help="Expect production-only protections such as disabled docs.")
    parser.add_argument("--skip-commands", action="store_true", help="Skip local test/build/git commands.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks = []
    checks.extend(command_checks(args.skip_commands))
    checks.extend(check_static())
    checks.extend(check_http(args))
    return print_report(checks)


if __name__ == "__main__":
    raise SystemExit(main())
