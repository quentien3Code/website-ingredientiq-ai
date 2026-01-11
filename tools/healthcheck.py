#!/usr/bin/env python3
"""Deterministic HTTP healthcheck with retries.

Used by:
- local dev (VS Code tasks)
- CI (GitHub Actions)
- post-deploy smoke checks

Exit codes:
- 0: endpoint returned expected status
- 1: timeout / unexpected status / request failure

This script intentionally prints minimal output suitable for CI logs.
"""

from __future__ import annotations

import argparse
import time
import urllib.error
import urllib.request


def http_get(url: str, timeout_sec: float) -> int:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as e:
        return int(e.code)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Full URL to check, e.g. http://localhost:8000/readyz")
    parser.add_argument(
        "--expect",
        type=int,
        default=200,
        help="Expected HTTP status code (default: 200)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="Max seconds to keep retrying (default: 30)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between retries (default: 1)",
    )
    parser.add_argument(
        "--request-timeout",
        type=float,
        default=2.5,
        help="Per-request timeout seconds (default: 2.5)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    deadline = time.monotonic() + float(args.timeout)
    last_status: int | None = None

    while True:
        now = time.monotonic()
        if now > deadline:
            print(f"FAIL url={args.url} expected={args.expect} last_status={last_status}")
            return 1

        try:
            status = http_get(args.url, timeout_sec=float(args.request_timeout))
            last_status = status
            if status == int(args.expect):
                print(f"OK url={args.url} status={status}")
                return 0
        except Exception:
            last_status = None

        time.sleep(float(args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
