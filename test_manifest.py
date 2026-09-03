"""Gates for the evidence-tree checksum manifest.

The manifest exists so that a depositor can confirm every byte of evidence
without running the mathematics.  A manifest that is merely present proves
nothing, so these gates check it in both directions and then check that the
check itself can fail.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import tools_manifest

HERE = Path(__file__).resolve().parent


def test_manifest_covers_the_tree_exactly():
    assert tools_manifest.differences() == []


def test_manifest_is_not_empty_and_covers_the_target_certificates():
    listed = tools_manifest.recorded()
    assert len(listed) >= 80
    for order in (46, 47, 48, 49, 50, 109, 110):
        assert f"certificates/targets/TARGET_{order}.json" in listed


def test_manifest_agrees_with_the_older_targets_only_manifest():
    """Two manifests of the same files must not disagree."""

    listed = tools_manifest.recorded()
    older = HERE / "certificates" / "targets" / "SHA256SUMS"
    for line in older.read_text().splitlines():
        if not line.strip():
            continue
        digest, name = line.split()
        assert listed[f"certificates/targets/{name.lstrip('*')}"] == digest


def test_a_changed_byte_is_detected(tmp_path, monkeypatch):
    """Control: the checker must fail when a file's content changes.

    Without this, `differences() == []` could pass for a checker that never
    compares anything.
    """

    victim = HERE / "certificates" / "targets" / "TARGET_46.json"
    original = victim.read_bytes()
    real = tools_manifest.digests

    def tampered():
        rows = real()
        rows[str(victim.relative_to(HERE))] = hashlib.sha256(original + b" ").hexdigest()
        return rows

    monkeypatch.setattr(tools_manifest, "digests", tampered)
    problems = tools_manifest.differences()
    assert any("digest changed" in problem for problem in problems)
