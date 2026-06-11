"""Create or compare a pw_stealth audit baseline for authorized CI checks.

For authorized testing and your own properties only. See DISCLAIMER.md.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pw_stealth.audit import (
    compare_reports,
    format_diffs,
    read_report,
    run_audit_sync,
    write_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline", help="Path to the saved audit JSON baseline.")
    parser.add_argument(
        "--url",
        default="https://example.com",
        help="Authorized diagnostic URL. Defaults to example.com.",
    )
    parser.add_argument("--preset", default="chrome", help="Fingerprint preset to audit.")
    parser.add_argument(
        "--create",
        action="store_true",
        help="Create or replace the baseline instead of comparing.",
    )
    args = parser.parse_args()

    report = run_audit_sync(args.url, preset=args.preset, headless=True)
    baseline_path = Path(args.baseline)

    if args.create or not baseline_path.exists():
        write_report(report, baseline_path)
        print(f"Wrote baseline: {baseline_path}")
        return 0

    diffs = compare_reports(report, read_report(baseline_path))
    if diffs:
        print(format_diffs(diffs))
        return 1

    print("Audit matches baseline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
