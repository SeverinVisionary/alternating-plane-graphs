#!/usr/bin/env python3
"""Run one cloud command and retain portable child-resource metadata.

Cloud images are not required to provide GNU ``/usr/bin/time``.  This small
wrapper runs a single child process, lets its stdout/stderr flow through
unchanged, and writes a JSON record after the child exits or fails to launch.
It deliberately performs no mathematical work and is suitable for the bounded
Boolean recovery jobs, where a killed child must still leave an audit record.
"""

from __future__ import annotations

import argparse
import json
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


def _utc_now() -> str:
    # ``datetime.UTC`` first appeared in Python 3.11.  The job wrapper is
    # intentionally compatible with the local Python 3.9 sanity gate too.
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _usage_snapshot() -> dict[str, int | float]:
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "user_seconds": usage.ru_utime,
        "system_seconds": usage.ru_stime,
        "max_rss": usage.ru_maxrss,
        "minor_page_faults": usage.ru_minflt,
        "major_page_faults": usage.ru_majflt,
        "involuntary_context_switches": usage.ru_nivcsw,
        "voluntary_context_switches": usage.ru_nvcsw,
    }


def _normal_exit_status(returncode: int) -> int:
    """Map ``subprocess`` signal return codes to conventional shell values."""

    return returncode if returncode >= 0 else 128 + (-returncode)


def run_command(command: Sequence[str], metadata_path: Path) -> int:
    """Run ``command`` once and write a JSON record before returning its status."""

    if not command:
        raise ValueError("command must not be empty")

    started_at = _utc_now()
    started = time.monotonic()
    before = _usage_snapshot()
    launch_error: str | None = None
    try:
        completed = subprocess.run(list(command), check=False)
        returncode = completed.returncode
    except OSError as exc:
        # Match the conventional shell status for a missing executable while
        # retaining the actual launch failure in the separate JSON record.
        returncode = 127 if isinstance(exc, FileNotFoundError) else 126
        launch_error = f"{type(exc).__name__}: {exc}"
    after = _usage_snapshot()
    payload: dict[str, Any] = {
        "format": "apg-cloud-resource-runner-v1",
        "command": list(command),
        "started_at_utc": started_at,
        "ended_at_utc": _utc_now(),
        "wall_seconds": time.monotonic() - started,
        "returncode": returncode,
        "normalized_exit_status": _normal_exit_status(returncode),
        # Linux reports KiB and macOS reports bytes.  Keep the raw field and
        # platform-neutral label rather than silently applying a wrong unit.
        "max_rss_platform_units": after["max_rss"],
        "child_user_seconds": after["user_seconds"] - before["user_seconds"],
        "child_system_seconds": after["system_seconds"] - before["system_seconds"],
        "child_minor_page_faults": after["minor_page_faults"]
        - before["minor_page_faults"],
        "child_major_page_faults": after["major_page_faults"]
        - before["major_page_faults"],
        "child_involuntary_context_switches": after["involuntary_context_switches"]
        - before["involuntary_context_switches"],
        "child_voluntary_context_switches": after["voluntary_context_switches"]
        - before["voluntary_context_switches"],
    }
    if launch_error is not None:
        payload["launch_error"] = launch_error
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return _normal_exit_status(returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--metadata", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("supply a command after --")
    return run_command(command, args.metadata)


if __name__ == "__main__":
    raise SystemExit(main())
