"""Gates that keep the documented data format honest.

`FORMATS.md` specifies `apg-plane-rotation-v1` and carries a dependency-free
reference reader, so that a depositor of this archive can read the certificates
without any code from this repository.  A specification that is never executed
drifts from the thing it specifies, so these gates execute it: the reader is
extracted from the markdown and run against every certificate, and its answers
are compared with the repository's own face tracing.
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

import pytest

import bridge_lemma as bl
from certificate_tools import alpha_from_certificate, cycles_from_degrees

HERE = Path(__file__).resolve().parent
# `UPSTREAM_PROVENANCE.json` lives under `certificates/` but is a digest record,
# not a certificate; it declares its own format and has no `vertices`.
NOT_CERTIFICATES = {"UPSTREAM_PROVENANCE.json"}

CERTIFICATES = sorted(
    p for p in glob.glob(str(HERE / "certificates" / "**" / "*.json"), recursive=True)
    if Path(p).name not in NOT_CERTIFICATES
)


def _reference_reader():
    """The exact code block published in FORMATS.md, compiled and returned."""

    text = (HERE / "FORMATS.md").read_text()
    blocks = [
        chunk.split("```", 1)[0]
        for chunk in text.split("```python")[1:]
    ]
    assert blocks, "FORMATS.md no longer carries a python reference reader"
    namespace: dict[str, object] = {}
    exec(compile(blocks[0], "FORMATS.md", "exec"), namespace)  # noqa: S102
    assert "faces" in namespace, "the reference reader must define faces(path)"
    return namespace["faces"]


def test_the_provenance_record_is_excluded_and_declares_its_own_format():
    """Control: the exclusion must be narrow and the excluded file must exist."""

    record = HERE / "certificates" / "UPSTREAM_PROVENANCE.json"
    assert record.exists()
    assert str(record) not in CERTIFICATES
    assert json.loads(record.read_text())["format"] == "apg-upstream-provenance-v1"


def test_every_certificate_declares_the_documented_format():
    assert CERTIFICATES
    for path in CERTIFICATES:
        assert json.loads(Path(path).read_text())["format"] == "apg-plane-rotation-v1", path


@pytest.mark.parametrize("path", CERTIFICATES, ids=lambda p: Path(p).stem)
def test_documented_reference_reader_agrees_with_the_repository(path):
    """FORMATS.md's reader and this repository's face tracing must agree.

    The reference reader recomputes faces from the rotations alone and asserts
    Euler itself, so a disagreement means either the specification is wrong or
    the certificate is not the plane map the repository thinks it is.
    """

    documented = sorted(_reference_reader()(path))
    degrees, alpha = alpha_from_certificate(Path(path))
    _, _, _, sigma_inverse = cycles_from_degrees(degrees)
    _, sizes = bl.faces(alpha, sigma_inverse)
    assert documented == sorted(sizes)


def test_reference_reader_rejects_a_broken_rotation(tmp_path):
    """Control: the documented reader must not accept a non-spherical map.

    Without this, `test_documented_reference_reader_agrees_with_the_repository`
    would still pass if the reader silently returned whatever it was given.
    """

    source = json.loads(Path(CERTIFICATES[0]).read_text())
    rings = {row["id"]: list(row["clockwise"]) for row in source["vertices"]}
    victim = next(v for v, ring in rings.items() if len(ring) >= 3)
    rings[victim] = rings[victim][1:] + rings[victim][:1]
    rings[victim][0], rings[victim][1] = rings[victim][1], rings[victim][0]
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps({
        "format": "apg-plane-rotation-v1",
        "vertices": [{"id": v, "clockwise": ring} for v, ring in rings.items()],
    }))
    with pytest.raises(AssertionError):
        _reference_reader()(str(broken))
