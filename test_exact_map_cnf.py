"""Gates for the pure-CNF closed-map encoding.

The load-bearing tests here are the *predicted-object* gate and the mutation
control (the project rule on predicted-object gates): a published (3,4,5)-APG must be a model of the
encoding, and a rewiring of it that the independent verifiers accept must
still be a model.  A recovery-only gate ("the encoding accepts something")
would pass through a silently weakened constraint set.
"""
from __future__ import annotations

import itertools
import json
import platform
import subprocess
import sys
from pathlib import Path

import pytest

Cadical195 = pytest.importorskip(
    "pysat.solvers", reason="python-sat is an optional dependency; see requirements-optional.txt"
).Cadical195

import exact_map_cnf as cnf
from fast_apg_check import is_apg as _fast_apg_filter

HERE = Path(__file__).resolve().parent
KNOWN = HERE / "certificates" / "known"


def _is_model(degrees, faces, alpha, **kwargs) -> bool:
    encoding = cnf.ClosedMapCNF(degrees, faces, fixed_alpha=alpha, **kwargs)
    solver = Cadical195(bootstrap_with=encoding.clauses)
    try:
        return bool(solver.solve())
    finally:
        solver.delete()


def _verifiers_accept(rotation, order, tmp_path) -> bool:
    path = tmp_path / f"candidate_{order}.json"
    path.write_text(json.dumps(rotation, indent=2, sort_keys=True) + "\n")
    reports = cnf.run_verifiers(path, order)
    return all(report["passed"] for report in reports)


# ------------------------------------------------------------------ profiles


@pytest.mark.parametrize("order,r", [(20, 9), (17, 8), (28, 12), (46, 18)])
def test_closed_profile_matches_the_forced_identities(order: int, r: int) -> None:
    degrees, faces = cnf.closed_profile(order, r)
    assert degrees == faces
    assert len(degrees) == order
    assert degrees.count(3) == r
    assert degrees.count(5) == r - 4
    assert degrees.count(4) == order - 2 * r + 4
    # E = 2n - 2 and F = n are consequences, not inputs.
    assert sum(degrees) == 2 * (2 * order - 2)
    assert len(faces) == order


def test_closed_profile_rejects_impossible_parameters() -> None:
    with pytest.raises(ValueError):
        cnf.closed_profile(20, 3)
    with pytest.raises(ValueError):
        cnf.closed_profile(20, 13)


def test_feasible_r_values_are_exactly_the_admissible_ones() -> None:
    for r in cnf.feasible_r_values(46):
        cnf.closed_profile(46, r)
    assert cnf.feasible_r_values(46) == list(range(4, 26))


# ---------------------------------------------------- the one-orbit argument


def test_label_classes_are_single_orbits_only_below_size_six() -> None:
    assert cnf.prove_label_class_is_one_orbit(5, 3)
    # A hexagonal face could be two triangular orbits sharing a label, so the
    # open-block lane may not reuse this module without an orbit constraint.
    assert not cnf.prove_label_class_is_one_orbit(6, 3)


def test_a_size_six_face_is_refused_rather_than_silently_encoded() -> None:
    degrees = [3] * 8 + [4] * 6 + [5] * 4
    # 68 darts; the sizes below consume all of them, so the size-six face is
    # what the encoder must object to.
    faces = [3] * 9 + [4] * 5 + [5] * 3 + [6]
    assert sum(faces) == sum(degrees)
    with pytest.raises(ValueError, match="explicit orbit constraint"):
        cnf.ClosedMapCNF(degrees, faces)


# --------------------------------------------------- forced edge-class counts


def test_degree_edge_counts_are_determined_by_the_profile() -> None:
    degrees, faces = cnf.closed_profile(20, 9)
    encoding = cnf.ClosedMapCNF(degrees, faces)
    counts = encoding.degree_edge_counts()
    assert counts == {(3, 4): 13, (3, 5): 14, (4, 5): 11}
    assert sum(counts.values()) == 2 * 20 - 2


@pytest.mark.parametrize("order,r", [(20, 9), (26, 11), (46, 18)])
def test_degree_edge_counts_solve_their_own_linear_system(order: int, r: int) -> None:
    degrees, faces = cnf.closed_profile(order, r)
    counts = cnf.ClosedMapCNF(degrees, faces).degree_edge_counts()
    for size in (3, 4, 5):
        incident = sum(count for key, count in counts.items() if size in key)
        assert incident == size * degrees.count(size)


# ----------------------------------------------------- predicted-object gate


def test_the_published_order_20_apg_is_a_model() -> None:
    degrees, alpha = cnf.alpha_from_certificate(KNOWN / "order20.json")
    profile_degrees, faces = cnf.closed_profile(len(degrees), degrees.count(3))
    assert degrees == profile_degrees
    assert _is_model(degrees, faces, alpha)


def test_the_face_label_normal_form_keeps_the_published_map() -> None:
    """The label ordering is a representation convention, not a restriction."""

    degrees, alpha = cnf.alpha_from_certificate(KNOWN / "order20.json")
    _, faces = cnf.closed_profile(len(degrees), degrees.count(3))
    assert _is_model(degrees, faces, alpha, break_face_symmetry=False)
    assert _is_model(degrees, faces, alpha, break_face_symmetry=True)


def test_re_embedding_a_published_certificate_round_trips(tmp_path: Path) -> None:
    for name in ("order20.json", "schneider17.json", "ghent17.json", "order42.json"):
        degrees, alpha = cnf.alpha_from_certificate(KNOWN / name)
        rotation = cnf.dump_rotation(degrees, alpha)
        assert _verifiers_accept(rotation, len(degrees), tmp_path)


# --------------------------------------------------------- mutation control


def _two_swap(alpha: list[int], first: int, second: int) -> list[int] | None:
    """Rewire two edges of ``alpha`` into the other pairing of their darts."""

    mutated = list(alpha)
    a, b = first, alpha[first]
    c, d = second, alpha[second]
    if len({a, b, c, d}) != 4:
        return None
    mutated[a], mutated[c] = c, a
    mutated[b], mutated[d] = d, b
    return mutated


def test_every_published_apg_is_a_model(tmp_path: Path) -> None:
    """The predicted-object gate, across parameters rather than at one point.

    The 19 frozen planar-code census sources span orders 26-36 and ``r`` from
    11 to 14, and the four known fixtures add orders 17, 20 and 42.  A kernel
    calibrated on a single profile passes a one-map gate; it does not pass
    this one (the project rules sections 3 and 4).
    """

    fixtures: list[Path] = sorted(KNOWN.glob("*.json"))
    for source in sorted((HERE / "certificates" / "census_sources").glob("*.plc")):
        target = tmp_path / f"{source.stem}.json"
        subprocess.run(
            [sys.executable, str(HERE / "import_planar_code.py"), str(source), str(target)],
            capture_output=True,
            check=True,
        )
        fixtures.append(target)

    seen_orders: set[int] = set()
    seen_r: set[int] = set()
    for fixture in fixtures:
        degrees, alpha = cnf.alpha_from_certificate(fixture)
        order, r = len(degrees), degrees.count(3)
        profile_degrees, faces = cnf.closed_profile(order, r)
        assert degrees == profile_degrees, f"{fixture.name} is off-profile"
        assert _is_model(degrees, faces, alpha), f"{fixture.name} is not a model"
        seen_orders.add(order)
        seen_r.add(r)

    assert len(fixtures) == 23
    assert seen_orders >= {17, 20, 26, 29, 32, 36, 42}
    assert len(seen_r) >= 4



def _perfect_matchings(darts: list[int]):
    """Every perfect matching of an even-sized dart list."""

    if not darts:
        yield ()
        return
    head, rest = darts[0], darts[1:]
    for index, partner in enumerate(rest):
        remainder = rest[:index] + rest[index + 1 :]
        for tail in _perfect_matchings(remainder):
            yield ((head, partner),) + tail


def _deranged_rematchings(alpha: list[int], edges: tuple[tuple[int, int], ...]):
    """Rematchings of the selected edges' darts that retain none of them.

    This is the move `three_edge_rematch.py` enumerates: of the 15 perfect
    matchings on six darts, 8 share no pair with the original three.
    """

    darts = sorted(dart for edge in edges for dart in edge)
    original = {frozenset(edge) for edge in edges}
    for matching in _perfect_matchings(darts):
        if any(frozenset(pair) in original for pair in matching):
            continue
        mutated = list(alpha)
        for left, right in matching:
            mutated[left] = right
            mutated[right] = left
        yield mutated


def test_rewirings_the_verifiers_accept_are_still_models(tmp_path: Path) -> None:
    """The load-bearing direction: a valid APG the encoding wrongly rejects.

    Two-swap rewirings of a published map are all invalid, so they only
    exercise agreement on the negative side.  Three-edge deranged rematchings
    -- the move the repository's own `three_edge_rematch.py` enumerates -- do
    reach other genuine APGs, and every one of those must still be a model.
    """

    degrees, alpha = cnf.alpha_from_certificate(KNOWN / "order20.json")
    _, faces = cnf.closed_profile(len(degrees), degrees.count(3))
    edges = tuple((d, alpha[d]) for d in range(len(alpha)) if d < alpha[d])

    accepted: list[list[int]] = []
    examined = 0
    for triple in itertools.combinations(edges, 3):
        for mutated in _deranged_rematchings(alpha, triple):
            examined += 1
            if not _fast_apg_filter(degrees, mutated):
                continue
            rotation = cnf.dump_rotation(degrees, mutated)
            if _verifiers_accept(rotation, len(degrees), tmp_path):
                accepted.append(mutated)
        if len(accepted) >= 12:
            break

    assert examined > 1000
    assert accepted, "three-edge rematching produced no verifier-accepted APG"
    for mutated in accepted:
        assert _is_model(degrees, faces, mutated), "encoding rejected a verified APG"
        # The same map must also survive the vertex normal form after
        # relabelling, or the symmetry break would be discarding solutions.
        relabelled = cnf.lex_leader_relabelling(degrees, mutated)
        assert _is_model(degrees, faces, relabelled, break_vertex_symmetry=True)


def test_two_swap_rewirings_agree_on_the_negative_side(tmp_path: Path) -> None:
    """All 205 two-swaps of the order-20 map are rejected by both sides.

    Kept as a recorded fact, not as the positive gate: its load-bearing branch
    never fires, which is why the three-edge test above exists.
    """

    degrees, alpha = cnf.alpha_from_certificate(KNOWN / "order20.json")
    _, faces = cnf.closed_profile(len(degrees), degrees.count(3))
    examined = 0
    accepted_by_verifiers = 0
    for first in range(0, len(alpha), 3):
        for second in range(first + 1, len(alpha), 5):
            mutated = _two_swap(alpha, first, second)
            if mutated is None:
                continue
            examined += 1
            rotation = cnf.dump_rotation(degrees, mutated)
            if _verifiers_accept(rotation, len(degrees), tmp_path):
                accepted_by_verifiers += 1
    assert examined == 205
    assert accepted_by_verifiers == 0


def test_a_rewiring_that_breaks_alternation_is_refused_at_encoding_time() -> None:
    degrees, alpha = cnf.alpha_from_certificate(KNOWN / "order20.json")
    _, faces = cnf.closed_profile(len(degrees), degrees.count(3))
    same_degree = [
        (d, e)
        for d in range(len(alpha))
        for e in range(d + 1, len(alpha))
        if degrees[cnf.cycles_from_degrees(degrees)[1][d]]
        == degrees[cnf.cycles_from_degrees(degrees)[1][e]]
    ]
    assert same_degree
    encoding = cnf.ClosedMapCNF(degrees, faces)
    for d, e in same_degree[:20]:
        assert encoding.pair(d, e) is None


# ------------------------------------------- vertex lex-leader break, gated


def test_every_published_apg_has_a_lex_leader_representative(tmp_path: Path) -> None:
    """The control the vertex symmetry break needs before it may be used.

    Relabelling by adjacent same-degree transpositions strictly increases the
    flattened adjacency matrix, so the walk terminates; it terminates at a
    labelling with no violated transposition.  Requiring that a *published*
    map reaches such a representative -- still accepted by both verifiers, and
    still a model under the break -- is what turns the argument into a gate.
    """

    fixtures: list[Path] = sorted(KNOWN.glob("*.json"))
    for source in sorted((HERE / "certificates" / "census_sources").glob("*.plc")):
        target = tmp_path / f"{source.stem}.json"
        subprocess.run(
            [sys.executable, str(HERE / "import_planar_code.py"), str(source), str(target)],
            capture_output=True,
            check=True,
        )
        fixtures.append(target)
    assert len(fixtures) == 23

    moved = 0
    for fixture in fixtures:
        degrees, alpha = cnf.alpha_from_certificate(fixture)
        if cnf.satisfies_vertex_lex_leader(degrees, alpha) is not None:
            moved += 1
        relabelled = cnf.lex_leader_relabelling(degrees, alpha)
        assert cnf.satisfies_vertex_lex_leader(degrees, relabelled) is None
        _, faces = cnf.closed_profile(len(degrees), degrees.count(3))
        assert _verifiers_accept(cnf.dump_rotation(degrees, relabelled), len(degrees), tmp_path)
        assert _is_model(degrees, faces, relabelled, break_vertex_symmetry=True)
    assert moved > 0, "no fixture needed relabelling, so the gate proved nothing"


def test_relabelling_preserves_the_map_up_to_isomorphism() -> None:
    degrees, alpha = cnf.alpha_from_certificate(KNOWN / "order20.json")
    relabelled = cnf.lex_leader_relabelling(degrees, alpha)
    before = sorted(sorted(row) for row in cnf.adjacency_from_alpha(degrees, alpha))
    after = sorted(sorted(row) for row in cnf.adjacency_from_alpha(degrees, relabelled))
    assert before == after
    assert sorted(relabelled) == sorted(alpha)


# ------------------------------------------------ the open two-socket lane


@pytest.mark.parametrize("name,order,r", [("A21", 21, 10), ("B22", 22, 10), ("C23", 23, 10), ("D24", 24, 10)])
def test_published_strict_blocks_are_models(name: str, order: int, r: int) -> None:
    """Predicted-object gate for the hexagon lane.

    A published two-socket block has exactly the structure the size-six orbit
    constraint is meant to admit, and a class of six darts splitting into two
    triangles is exactly what it is meant to exclude.
    """

    degrees, alpha = cnf.alpha_from_certificate(HERE / "results" / "blocks" / f"{name}.json")
    profile_degrees, faces = cnf.block_profile(order, r)
    assert degrees == profile_degrees
    assert faces.count(6) == 2
    assert _is_model(degrees, faces, alpha, open_block=True)


def test_the_closed_lane_still_refuses_a_hexagon() -> None:
    degrees, faces = cnf.block_profile(21, 10)
    with pytest.raises(ValueError, match="open_block=True"):
        cnf.ClosedMapCNF(degrees, faces)


def test_block_profile_matches_the_repository_constructor() -> None:
    from exact_map_sat import profile_block

    for order, r in ((21, 10), (28, 12), (29, 12), (31, 12)):
        assert cnf.block_profile(order, r) == profile_block(order, r)


def test_edge_class_counts_are_forced_in_the_block_lane() -> None:
    degrees, faces = cnf.block_profile(21, 10)
    counts = cnf.ClosedMapCNF(degrees, faces, open_block=True).degree_edge_counts()
    assert counts == {(2, 5): 12, (3, 4): 6, (3, 5): 12, (4, 5): 6}
    # Socket whites take both their edges to pentagon corners.
    assert counts[(2, 5)] == 2 * degrees.count(2)
    assert sum(counts.values()) == (4 * 21 - 12) // 2


# ---------------------------------------------------- the socket interface


@pytest.mark.parametrize("name,order,r", [("A21", 21, 10), ("B22", 22, 10), ("C23", 23, 10), ("D24", 24, 10)])
def test_published_blocks_survive_the_socket_interface(name: str, order: int, r: int) -> None:
    """Predicted-object gate for the socket constraints and the t=0 branch."""

    degrees, alpha = cnf.alpha_from_certificate(HERE / "results" / "blocks" / f"{name}.json")
    profile_degrees, faces = cnf.block_profile(order, r)
    assert degrees == profile_degrees
    assert _is_model(degrees, faces, alpha, open_block=True)
    # All four published blocks are portable, so t=0 must keep them too.
    assert _is_model(degrees, faces, alpha, open_block=True, require_t0=True)


def test_the_socket_interface_rejects_rematchings_of_a_published_block() -> None:
    """The socket constraints must do real work, not merely be satisfiable.

    Every three-edge deranged rematching of A21 that the alternation rules even
    admit as an encoding must be rejected, while A21 itself is kept.
    """

    degrees, alpha = cnf.alpha_from_certificate(HERE / "results" / "blocks" / "A21.json")
    _, faces = cnf.block_profile(21, 10)
    assert _is_model(degrees, faces, alpha, open_block=True)
    edges = tuple((d, alpha[d]) for d in range(len(alpha)) if d < alpha[d])
    encodable = 0
    for triple in itertools.islice(itertools.combinations(edges, 3), 150):
        for mutated in _deranged_rematchings(alpha, triple):
            try:
                admitted = _is_model(degrees, faces, mutated, open_block=True)
            except ValueError:
                continue  # a white would meet a non-pentagon: excluded outright
            encodable += 1
            assert not admitted, "socket interface admitted a rematched block"
    assert encodable > 20, "the control exercised too few encodable rematchings"


# ------------------------------------------------ the encoder finds witnesses


def test_the_encoder_certifies_an_order_17_witness(tmp_path: Path) -> None:
    """End to end: search, emit, and pass both independent verifiers."""

    record = cnf.search(17, 8, timeout=180.0, certificate_directory=tmp_path)
    assert record["disposition"] == "CERTIFIED", record
    assert record["nonexistence_claimed"] is False
    assert all(report["passed"] for report in record["verifiers"])
    degrees, alpha = cnf.alpha_from_certificate(Path(record["certificate"]))
    assert len(degrees) == 17 and degrees.count(3) == 8


# ------------------------------------------------------------- run mechanics


def test_environment_self_check_refuses_darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    with pytest.raises(SystemExit, match="isolated Linux"):
        cnf.environment_self_check()
    assert cnf.environment_self_check(allow_darwin=True)["system"] == "Darwin"


def test_a_timeout_is_recorded_as_incomplete_and_claims_nothing(tmp_path: Path) -> None:
    record = cnf.search(20, 9, timeout=3.0, certificate_directory=tmp_path)
    assert record["disposition"] in {"INCOMPLETE", "CERTIFIED"}
    assert record["nonexistence_claimed"] is False
    if record["disposition"] == "INCOMPLETE":
        assert record["certificate"] is None


def test_the_cli_records_the_environment(tmp_path: Path) -> None:
    output = tmp_path / "record.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(HERE / "exact_map_cnf.py"),
            "--order",
            "20",
            "--r",
            "9",
            "--timeout",
            "3",
            "--certificates",
            str(tmp_path),
            "--output",
            str(output),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert output.exists(), completed.stderr
    record = json.loads(output.read_text())
    assert record["environment"]["system"] == platform.system()
    assert record["nonexistence_claimed"] is False
