"""Gates for the planar_code writer.

The writer exists so a certificate can be checked by software that has never
seen this project, so the gates have to pin it to the *real* format rather than
to our own reader's habits.  The strongest available evidence is third party:
33 planar_code files written by other people are decoded, re-encoded, and
required to come back as the same plane map -- and, where the upstream file is
already in the canonical ring order, byte for byte.
"""
from __future__ import annotations

import glob
import tempfile
from pathlib import Path

import pytest

import export_planar_code as ex
import import_planar_code as im
from certificate_tools import alpha_from_certificate, cycles_from_degrees
import bridge_lemma as bl
from conftest import requires_upstream_corpus

HERE = Path(__file__).resolve().parent
UPSTREAM = sorted(glob.glob(str(HERE / "certificates" / "**" / "upstream" / "*.plc"), recursive=True))
TARGETS = sorted(glob.glob(str(HERE / "certificates" / "targets" / "*.json")))


def _raw_rings(path: Path) -> list[list[int]]:
    """Decode without the canonicalisation, to see the file's own ring order."""

    data = Path(path).read_bytes()
    offset = len(ex.HEADER) if data.startswith(ex.HEADER) else 0
    order, offset = data[offset], offset + 1
    rings = []
    for _ in range(order):
        ring: list[int] = []
        while data[offset] != 0:
            ring.append(data[offset])
            offset += 1
        offset += 1
        rings.append(ring)
    return rings


def _decode_bytes(payload: bytes) -> list[list[int]]:
    with tempfile.NamedTemporaryFile(suffix=".plc", delete=False) as handle:
        handle.write(payload)
        scratch = Path(handle.name)
    try:
        return im.decode_first(scratch)
    finally:
        scratch.unlink()


@pytest.mark.parametrize("path", UPSTREAM, ids=lambda p: Path(p).stem)
def test_third_party_files_survive_a_round_trip_as_the_same_map(path):
    """Decode, re-encode, decode again: the plane map must be unchanged."""

    original = Path(path).read_bytes()
    rings = im.decode_first(Path(path))
    encoded = ex.encode(rings, header=original.startswith(ex.HEADER))
    assert _decode_bytes(encoded) == rings


@pytest.mark.parametrize("path", UPSTREAM, ids=lambda p: Path(p).stem)
def test_canonical_third_party_files_round_trip_byte_for_byte(path):
    """Byte identity, but only where the upstream file is already canonical.

    planar_code does not require a ring to start at its smallest entry, and two
    of these files do not. For those the writer emits the canonical rotation of
    each ring -- the same embedding read from a different starting point -- so
    byte identity is the wrong assertion and the test above is the right one.
    Asserting it here anyway, conditioned on the file's own ring order, keeps
    the writer honest wherever the comparison is meaningful.
    """

    original = Path(path).read_bytes()
    raw = _raw_rings(Path(path))
    if raw != ex.canonical(raw):
        pytest.skip("upstream file is not in canonical ring order")
    assert ex.encode(im.decode_first(Path(path)), header=original.startswith(ex.HEADER)) == original


@requires_upstream_corpus
def test_at_least_one_upstream_file_is_non_canonical_and_one_is_canonical():
    """Control: neither branch of the test above may be vacuous."""

    orders = [_raw_rings(Path(p)) for p in UPSTREAM]
    assert any(raw == ex.canonical(raw) for raw in orders)
    assert any(raw != ex.canonical(raw) for raw in orders)


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: Path(p).stem)
def test_certificates_export_and_come_back_unchanged(path):
    """A target certificate exported to planar_code is the same plane map."""

    rings = ex.rotations_from_certificate(Path(path))
    recovered = _decode_bytes(ex.encode(rings))
    assert recovered == ex.canonical(rings)

    before = {vertex: len(ring) for vertex, ring in enumerate(rings, start=1)}
    after = {vertex: len(ring) for vertex, ring in enumerate(recovered, start=1)}
    assert before == after

    degrees, alpha = alpha_from_certificate(Path(path))
    _, _, _, sigma_inverse = cycles_from_degrees(degrees)
    _, sizes = bl.faces(alpha, sigma_inverse)
    rotation = {vertex: ring for vertex, ring in enumerate(recovered, start=1)}
    degrees2, alpha2 = bl.alpha_from_rotation(rotation)
    _, _, _, sigma_inverse2 = cycles_from_degrees(degrees2)
    _, sizes2 = bl.faces(alpha2, sigma_inverse2)
    assert sorted(sizes) == sorted(sizes2)


def test_writer_refuses_what_the_one_byte_encoding_cannot_hold():
    """Control: silent truncation would produce a file describing another graph."""

    with pytest.raises(ValueError):
        ex.encode([[2, 3], [1, 3], [1, 2]] + [[1]] * 300)
    with pytest.raises(ValueError):
        ex.encode([[2, 300], [1], [1]])


def test_writer_refuses_a_certificate_not_labelled_one_to_n(tmp_path):
    import json

    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({
        "format": "apg-plane-rotation-v1",
        "vertices": [{"id": 7, "clockwise": [9]}, {"id": 9, "clockwise": [7]}],
    }))
    with pytest.raises(ValueError):
        ex.rotations_from_certificate(bad)
