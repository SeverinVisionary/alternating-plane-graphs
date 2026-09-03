"""Shared fixtures, and the skip for tests that need the upstream byte corpus.

The published planar_code files this project was built against are **not
redistributed here**: no licence statement was found at their source, and
absence of a licence is not permission.  Each graph they carried is instead
re-expressed in this repository's own `apg-plane-rotation-v1` format, which
records the same rotation system in an encoding defined here, with the digests
of the originals kept in `certificates/UPSTREAM_PROVENANCE.json`.

Nothing that is settled depends on the bytes: Conjectures 10.1, 10.2 and 10.3
all verify without them, and `witness_coverage.residue()` is empty.  What does
depend on them is a handful of tests whose *subject* is the bytes -- the
planar_code decoder, the byte-level census, and search-lane seed replays.  Those
skip here and pass for anyone who restores the corpus alongside this tree.
"""
from __future__ import annotations

import glob
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def upstream_corpus_present() -> bool:
    return bool(glob.glob(str(HERE / "certificates" / "**" / "*.plc"), recursive=True))


requires_upstream_corpus = pytest.mark.skipif(
    not upstream_corpus_present(),
    reason=(
        "needs the published planar_code corpus, which is not redistributed here; "
        "see certificates/UPSTREAM_PROVENANCE.json and NOTICE.md"
    ),
)
