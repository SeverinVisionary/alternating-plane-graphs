"""Which verifier conditions have a negative control, and which do not.

A review leg deleted one APG condition at a time from each verifier and re-ran
the definition-of-done gate: **thirteen of thirteen mutants passed it**.  The
gate's only negative control is a rotation transposition, and that is rejected
by the Euler check alone -- so the alternation gates, the face-size gate, the
connectivity gate and the rest could all be removed with every test still
green.

`verifier_mutations.py` measures this instead of arguing about it.  This file
freezes the measurement: coverage may improve, but a condition that has a
control today cannot silently lose it, and a newly added condition cannot
arrive uncontrolled without failing here.
"""
from __future__ import annotations

import pytest

import verifier_mutations as vm


# Sites with no negative control at the time of writing.  Two kinds, kept
# apart deliberately.
#
# The six "Theorem 3.2" identity sites are the interesting ones.  Controlling
# them needs an input that satisfies every clause of Definition 3.1 and still
# violates `v_i = f_i`, `E = 2n-2`, `F = n` -- which exists only if Theorem 3.2
# is false.  So they are either redundant (implied by the other checks, in
# which case they are dead weight) or they are the only thing that would reject
# a genuine APG with an unexpected profile.  The theorem is cited in both
# verifiers by name, with no quote, page or proof committed anywhere in this
# repository; that is recorded in SEARCH_STATUS.md as an open item, not
# resolved here.
#
# The rest are ordinary corpus gaps: an input that reaches them has to survive
# every earlier check, and no perturbation of a real certificate does.
UNCONTROLLED = {
    'verify.py: _fail(f"{where}.clockwise must be a JSON array")',
    'verify.py: _fail(f"vertex {vertex} names missing vertex {neighbor}")',
    'verify.py: _fail("facial walk entered a previously traced face before closing")',
    'verify.py: _fail(f"facial walk from {start} repeated dart {dart} before closing")',
    'verify.py: _fail(f"face {face_id} repeats a vertex in its facial walk")',
    'verify.py: _fail( f"adjacent vertices {vertex} and {neighbor} both have " f"degree {degrees[vertex]}" )',
    'verify.py: _fail( "Theorem 3.2 histogram mismatch: " f"vertices={vertex_counts}, faces={face_counts}" )',
    'verify.py: _fail( "(3,4,5)-APG histogram formula failed: " f"order={order}, counts={vertex_counts}" )',
    'verify.py: _fail( "(3,4,5)-APG count identities failed: " f"V={order}, E={edge_count}, F={face_count}" )',
    'verify_darts.py: _fail("dart permutation entered a previously traced face")',
    'verify_darts.py: _fail(f"vertex {source} names missing vertex {target}")',
    'verify_darts.py: _fail(f"edge {source}-{target} is asymmetric")',
    'verify_darts.py: _fail(f"face {index} repeats a vertex")',
    'verify_darts.py: _fail(f"edge {source}-{target} joins equal face sizes")',
    'verify_darts.py: _fail(f"vertex/face histograms differ: {vertex_counts} != {face_counts}")',
    'verify_darts.py: _fail("APG histogram formula failed")',
    'verify_darts.py: _fail("APG edge/face count formula failed")',
}

# Conditions that MUST keep a control: each is a clause of Definition 2.1/3.1
# or a structural precondition, and each was uncontrolled before this harness.
MUST_BE_CONTROLLED = {
    "verify.py": (
        "graph is disconnected",
        "has forbidden degree",
        "has forbidden size",
        "is not symmetric",
        "has a loop",
        "has a repeated neighbor",
    ),
    "verify_darts.py": (
        "graph is disconnected",
        "a vertex degree is outside",
        "has forbidden size",
        "joins equal degrees",
        "sphere Euler equation failed",
        "has a loop",
        "repeats a neighbor",
    ),
}


@pytest.fixture(scope="module")
def coverage() -> dict[str, bool]:
    measured: dict[str, bool] = {}
    for verifier in vm.VERIFIERS:
        measured.update(vm.controlled_sites(verifier))
    return measured


def test_the_corpus_accepts_the_pristine_certificate() -> None:
    """Without this the whole measurement could be a constant `reject`."""

    names = [name for name, _, _ in vm.corpus()]
    assert names[0] == "pristine"
    for verifier in vm.VERIFIERS:
        source = (vm.HERE / verifier).read_text()
        module = vm._load(source, verifier)
        pristine = next(case for case in vm.corpus() if case[0] == "pristine")
        assert vm._verdict(module, pristine[1], pristine[2]) == "accept"
        broken = next(case for case in vm.corpus() if case[0] == "transposed-rotation")
        assert vm._verdict(module, broken[1], broken[2]) != "accept"


@pytest.mark.parametrize("verifier", vm.VERIFIERS)
def test_every_definition_clause_has_a_negative_control(verifier, coverage) -> None:
    for needle in MUST_BE_CONTROLLED[verifier]:
        sites = [site for site in coverage if site.startswith(verifier) and needle in site]
        assert sites, f"no {verifier} site matches {needle!r}; did the message change?"
        assert all(coverage[site] for site in sites), (
            f"{verifier}: {needle!r} can be deleted without any corpus member noticing"
        )


def test_the_uncontrolled_set_has_not_grown(coverage) -> None:
    """Coverage may improve; it may not regress, and new gaps must be declared."""

    uncontrolled = {
        site
        for site, controlled in coverage.items()
        if not controlled
        and not any(
            reason in site.split(": ", 1)[1]
            for reason in vm.UNREACHABLE[site.split(": ", 1)[0]]
        )
    }
    new = uncontrolled - UNCONTROLLED
    assert not new, f"new uncontrolled verifier conditions: {sorted(new)}"
    fixed = UNCONTROLLED - uncontrolled
    assert not fixed, (
        f"these now have controls — remove them from UNCONTROLLED: {sorted(fixed)}"
    )


def test_the_theorem_3_2_identities_are_the_documented_special_case(coverage) -> None:
    """They cannot be controlled unless Theorem 3.2 is false. Keep that visible."""

    identity_sites = [
        site
        for site in coverage
        if "Theorem 3.2" in site
        or "histogram" in site
        or "count identities" in site
        or "count formula" in site
    ]
    assert len(identity_sites) == 6, identity_sites
    assert not any(coverage[site] for site in identity_sites)
