#!/usr/bin/env python3
"""Generate or check the SHA-256 manifest of every file under `certificates/`.

`certificates/targets/SHA256SUMS` already covers the 26 Conjecture 10.2
witnesses.  This covers the whole evidence tree -- the order-19 witnesses, the
surgery witnesses, the order-46 counterexample, the published corpora and the
search seeds -- which is what a deposit needs: a reader who fetches the archive
should be able to confirm that every byte of evidence is the byte that was
verified, without running any of the mathematics.

    python3 tools_manifest.py            # check, exit 1 on any difference
    python3 tools_manifest.py --write    # regenerate after adding a certificate
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TREE = ROOT / "certificates"
MANIFEST = TREE / "MANIFEST.sha256"
EXCLUDED = {"SHA256SUMS", "MANIFEST.sha256"}
HEADER = (
    "# SHA-256 of every file under certificates/, paths relative to the repository root.\n"
    "# Regenerate with: python3 tools_manifest.py --write\n"
    "# Verify with:     python3 tools_manifest.py   (also gated by test_manifest.py)\n"
)


def digests() -> dict[str, str]:
    """Every file under `certificates/`, hashed, keyed by repo-relative path."""

    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(TREE.rglob("*"))
        if path.is_file() and path.name not in EXCLUDED
    }


def recorded() -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in MANIFEST.read_text().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        digest, name = line.split(maxsplit=1)
        name = name.strip().lstrip("*")
        if ".." in Path(name).parts or Path(name).is_absolute():
            raise ValueError(f"manifest entry escapes the repository: {name}")
        entries[name] = digest
    return entries


def write() -> int:
    rows = digests()
    MANIFEST.write_text(HEADER + "".join(f"{d}  {n}\n" for n, d in rows.items()))
    return len(rows)


def differences() -> list[str]:
    """Every disagreement, in both directions -- missing, extra and changed."""

    actual, listed = digests(), recorded()
    problems = [f"not in the manifest: {name}" for name in sorted(set(actual) - set(listed))]
    problems += [f"missing from the tree: {name}" for name in sorted(set(listed) - set(actual))]
    problems += [
        f"digest changed: {name}"
        for name in sorted(set(actual) & set(listed))
        if actual[name] != listed[name]
    ]
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="regenerate the manifest")
    if parser.parse_args().write:
        print(f"wrote {write()} entries to {MANIFEST.relative_to(ROOT)}")
        return 0
    problems = differences()
    for problem in problems:
        print(problem, file=sys.stderr)
    print(f"{len(recorded())} entries checked, {len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
