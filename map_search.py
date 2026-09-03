#!/usr/bin/env python3
"""Deterministic-seed full combinatorial-map search for two-socket APG blocks.

The state is an orientable rotation system represented by a fixed vertex
permutation and a mutable fixed-point-free dart involution.  Moves are exact
two-edge switches.  Invalid abstract graphs are rejected; face and socket
conditions are optimized but a success is serialized only after the independent
block validator accepts the full map.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import platform
import random
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import block_tools as bt


@dataclass
class FixedMap:
    cycles: list[list[int]]
    sigma_inverse: list[int]
    dart_vertex: list[int]
    vertex_degree: list[int]


@dataclass
class SearchStats:
    seed: int
    order: int
    initial_switches: int = 0
    graph_valid_mode: bool = False
    steps: int = 0
    graph_rejections: int = 0
    accepted: int = 0
    improvements: int = 0
    zero_score_states: int = 0
    zero_score_validation_rejections: int = 0
    initial_score: int = -1
    best_score: int = -1
    initial_components: dict[str, int] = field(default_factory=dict)
    current_components: dict[str, int] = field(default_factory=dict)
    best_components: dict[str, int] = field(default_factory=dict)
    elapsed_seconds: float = 0.0


def rotation_to_map(rotation: dict[int, list[int]]) -> tuple[FixedMap, list[int]]:
    vertices = sorted(rotation)
    dense = {vertex: index for index, vertex in enumerate(vertices)}
    cycles: list[list[int]] = []
    dart_vertex: list[int] = []
    lookup: dict[tuple[int, int], int] = {}
    for vertex in vertices:
        cycle: list[int] = []
        for neighbor in rotation[vertex]:
            dart = len(dart_vertex)
            cycle.append(dart)
            dart_vertex.append(dense[vertex])
            lookup[(dense[vertex], dense[neighbor])] = dart
        cycles.append(cycle)
    alpha = [-1] * len(dart_vertex)
    for (u, v), dart in lookup.items():
        alpha[dart] = lookup[(v, u)]
    sigma_inverse = [-1] * len(dart_vertex)
    for cycle in cycles:
        for index, dart in enumerate(cycle):
            sigma_inverse[dart] = cycle[(index - 1) % len(cycle)]
    fixed = FixedMap(
        cycles=cycles,
        sigma_inverse=sigma_inverse,
        dart_vertex=dart_vertex,
        vertex_degree=[len(cycle) for cycle in cycles],
    )
    return fixed, alpha


def add_degree4_vertex(
    fixed: FixedMap, alpha: list[int], rng: random.Random
) -> tuple[FixedMap, list[int]]:
    edge_darts = [dart for dart, mate in enumerate(alpha) if dart < mate]
    eligible: list[tuple[int, int]] = []
    for first_index, first in enumerate(edge_darts):
        first_mate = alpha[first]
        first_vertices = {
            fixed.dart_vertex[first], fixed.dart_vertex[first_mate]
        }
        if any(fixed.vertex_degree[v] not in {3, 5} for v in first_vertices):
            continue
        for second in edge_darts[first_index + 1 :]:
            second_mate = alpha[second]
            endpoints = [
                fixed.dart_vertex[first],
                fixed.dart_vertex[first_mate],
                fixed.dart_vertex[second],
                fixed.dart_vertex[second_mate],
            ]
            if len(set(endpoints)) != 4 or any(
                fixed.vertex_degree[v] not in {3, 5} for v in endpoints
            ):
                continue
            eligible.append((first, second))
    if not eligible:
        raise bt.BlockError("no eligible pair of edges for degree-4 insertion")
    new_darts = list(range(len(alpha), len(alpha) + 4))
    new_vertex = len(fixed.cycles)
    cycle = list(new_darts)
    sigma_inverse = [*fixed.sigma_inverse, -1, -1, -1, -1]
    for index, dart in enumerate(cycle):
        sigma_inverse[dart] = cycle[(index - 1) % 4]
    new_fixed = FixedMap(
        cycles=[*fixed.cycles, cycle],
        sigma_inverse=sigma_inverse,
        dart_vertex=[*fixed.dart_vertex, *([new_vertex] * 4)],
        vertex_degree=[*fixed.vertex_degree, 4],
    )
    candidates: list[tuple[int, list[int]]] = []
    for first, second in eligible:
        old_darts = [first, alpha[first], second, alpha[second]]
        for ordered_old in itertools.permutations(old_darts):
            new_alpha = [*alpha, -1, -1, -1, -1]
            for old, new in zip(ordered_old, new_darts):
                new_alpha[old] = new
                new_alpha[new] = old
            candidates.append((score(new_fixed, new_alpha), new_alpha))
    candidates.sort(key=lambda item: item[0])
    cutoff = candidates[0][0] + 80
    shortlist = [candidate for candidate in candidates if candidate[0] <= cutoff]
    return new_fixed, list(rng.choice(shortlist)[1])


def grow_from_block(
    block: dict[str, object], target_order: int, rng: random.Random
) -> tuple[FixedMap, list[int]]:
    rotation = bt._rotation_from_rows(block["vertices"])
    fixed, alpha = rotation_to_map(rotation)
    while len(fixed.cycles) < target_order:
        fixed, alpha = add_degree4_vertex(fixed, alpha, rng)
    if len(fixed.cycles) != target_order:
        raise bt.BlockError("base block is larger than target")
    return fixed, alpha


def retarget_from_block(
    block: dict[str, object], target_order: int, r_value: int, rng: random.Random
) -> tuple[FixedMap, list[int]]:
    """Retype a nearby block profile and rematch only the freed/new darts."""

    original_rotation = bt._rotation_from_rows(block["vertices"])
    original_fixed, original_alpha = rotation_to_map(original_rotation)
    if target_order < len(original_fixed.cycles):
        raise bt.BlockError("retarget order is smaller than base block")
    desired_counts = {
        2: 6,
        3: r_value - 4,
        4: target_order - 2 * r_value + 2,
        5: r_value - 4,
    }
    if min(desired_counts.values()) < 0 or sum(desired_counts.values()) != target_order:
        raise bt.BlockError("invalid target block degree profile")
    white_vertices = [
        v for v, degree in enumerate(original_fixed.vertex_degree) if degree == 2
    ]
    black_vertices = [
        v for v, degree in enumerate(original_fixed.vertex_degree) if degree != 2
    ]
    if len(white_vertices) != 6:
        raise bt.BlockError("base block does not have six whites")
    old_degrees = sorted(original_fixed.vertex_degree[v] for v in black_vertices)
    target_black = {degree: desired_counts[degree] for degree in (3, 4, 5)}
    allocations: list[tuple[int, tuple[int, int, int]]] = []
    for count3 in range(target_black[3] + 1):
        for count4 in range(target_black[4] + 1):
            count5 = len(black_vertices) - count3 - count4
            if count5 < 0 or count5 > target_black[5]:
                continue
            assigned = [3] * count3 + [4] * count4 + [5] * count5
            cost = sum(abs(old - new) for old, new in zip(old_degrees, assigned))
            allocations.append((cost, (count3, count4, count5)))
    if not allocations:
        raise bt.BlockError("cannot allocate target degrees to base vertices")
    best_cost = min(cost for cost, _ in allocations)
    count3, count4, count5 = rng.choice(
        [counts for cost, counts in allocations if cost == best_cost]
    )
    assigned_degrees = [3] * count3 + [4] * count4 + [5] * count5
    ordered_black = sorted(
        black_vertices, key=lambda v: (original_fixed.vertex_degree[v], rng.random())
    )
    target_for_old = {
        vertex: degree for vertex, degree in zip(ordered_black, assigned_degrees)
    }
    for vertex in white_vertices:
        target_for_old[vertex] = 2
    new_degrees = (
        [3] * (target_black[3] - count3)
        + [4] * (target_black[4] - count4)
        + [5] * (target_black[5] - count5)
    )
    rng.shuffle(new_degrees)

    kept_old_darts: set[int] = set()
    cycle_sources: list[list[int | None]] = []
    for vertex, old_cycle in enumerate(original_fixed.cycles):
        wanted = target_for_old[vertex]
        start = rng.randrange(len(old_cycle))
        rotated = old_cycle[start:] + old_cycle[:start]
        kept = rotated[: min(len(rotated), wanted)]
        kept_old_darts.update(kept)
        cycle_sources.append([*kept, *([None] * (wanted - len(kept)))])
    cycle_sources.extend([[None] * degree for degree in new_degrees])

    source_to_new: dict[int, int] = {}
    cycles: list[list[int]] = []
    dart_vertex: list[int] = []
    for vertex, source_cycle in enumerate(cycle_sources):
        cycle: list[int] = []
        for source in source_cycle:
            dart = len(dart_vertex)
            cycle.append(dart)
            dart_vertex.append(vertex)
            if source is not None:
                source_to_new[source] = dart
        cycles.append(cycle)
    alpha = [-1] * len(dart_vertex)
    for old_dart, new_dart in source_to_new.items():
        old_mate = original_alpha[old_dart]
        if old_mate in source_to_new:
            alpha[new_dart] = source_to_new[old_mate]
    free = [dart for dart, mate in enumerate(alpha) if mate < 0]
    rng.shuffle(free)
    for left, right in zip(free[::2], free[1::2]):
        alpha[left] = right
        alpha[right] = left
    sigma_inverse = [-1] * len(dart_vertex)
    for cycle in cycles:
        for index, dart in enumerate(cycle):
            sigma_inverse[dart] = cycle[(index - 1) % len(cycle)]
    fixed = FixedMap(
        cycles=cycles,
        sigma_inverse=sigma_inverse,
        dart_vertex=dart_vertex,
        vertex_degree=[len(cycle) for cycle in cycles],
    )
    return fixed, alpha


def _abstract_graph_ok(fixed: FixedMap, alpha: list[int]) -> bool:
    edges: set[tuple[int, int]] = set()
    adjacency = [set() for _ in fixed.cycles]
    for dart, mate in enumerate(alpha):
        if dart > mate:
            continue
        u, v = fixed.dart_vertex[dart], fixed.dart_vertex[mate]
        if u == v:
            return False
        du, dv = fixed.vertex_degree[u], fixed.vertex_degree[v]
        if du == 2 or dv == 2:
            if sorted((du, dv)) != [2, 5]:
                return False
        elif du == dv:
            return False
        edge = (min(u, v), max(u, v))
        if edge in edges:
            return False
        edges.add(edge)
        adjacency[u].add(v)
        adjacency[v].add(u)
    reached: set[int] = set()
    stack = [0]
    while stack:
        vertex = stack.pop()
        if vertex in reached:
            continue
        reached.add(vertex)
        stack.extend(adjacency[vertex] - reached)
    return len(reached) == len(fixed.cycles)


def _abstract_graph_penalty(fixed: FixedMap, alpha: list[int]) -> int:
    edges: Counter[tuple[int, int]] = Counter()
    adjacency = [set() for _ in fixed.cycles]
    penalty = 0
    for dart, mate in enumerate(alpha):
        if dart > mate:
            continue
        u, v = fixed.dart_vertex[dart], fixed.dart_vertex[mate]
        if u == v:
            penalty += 2
            continue
        du, dv = fixed.vertex_degree[u], fixed.vertex_degree[v]
        if du == 2 or dv == 2:
            if sorted((du, dv)) != [2, 5]:
                penalty += 1
        elif du == dv:
            penalty += 1
        edge = (min(u, v), max(u, v))
        edges[edge] += 1
        adjacency[u].add(v)
        adjacency[v].add(u)
    penalty += sum(count - 1 for count in edges.values() if count > 1)
    unseen = set(range(len(fixed.cycles)))
    components = 0
    while unseen:
        components += 1
        stack = [next(iter(unseen))]
        while stack:
            vertex = stack.pop()
            if vertex not in unseen:
                continue
            unseen.remove(vertex)
            stack.extend(adjacency[vertex] & unseen)
    penalty += 2 * (components - 1)
    return penalty


def _faces(fixed: FixedMap, alpha: list[int]) -> tuple[list[list[int]], list[int]]:
    face_of = [-1] * len(alpha)
    faces: list[list[int]] = []
    for start in range(len(alpha)):
        if face_of[start] >= 0:
            continue
        face_id = len(faces)
        cycle: list[int] = []
        dart = start
        while face_of[dart] < 0:
            face_of[dart] = face_id
            cycle.append(dart)
            dart = fixed.sigma_inverse[alpha[dart]]
        if dart != start:
            raise bt.BlockError("face permutation merged into an old orbit")
        faces.append(cycle)
    return faces, face_of


def score_breakdown(fixed: FixedMap, alpha: list[int]) -> dict[str, int]:
    """Return deterministic weighted score components and their exact total."""

    faces, face_of = _faces(fixed, alpha)
    lengths = [len(face) for face in faces]
    actual = Counter(lengths)
    vertex_counts = Counter(fixed.vertex_degree)
    target = Counter(
        {3: vertex_counts[3], 4: vertex_counts[4], 5: vertex_counts[5], 6: 2}
    )
    distribution = sum(
        abs(actual[size] - target[size]) for size in set(actual) | set(target)
    )
    face_distribution = 40 * distribution
    abstract_graph = 80 * _abstract_graph_penalty(fixed, alpha)

    equal_faces = 0
    for dart, mate in enumerate(alpha):
        if dart < mate and (
            face_of[dart] == face_of[mate]
            or lengths[face_of[dart]] == lengths[face_of[mate]]
        ):
            equal_faces += 1
    equal_face = 20 * equal_faces

    white_penalty = 0
    for vertex, cycle in enumerate(fixed.cycles):
        if fixed.vertex_degree[vertex] != 2:
            continue
        incident = sorted(lengths[face_of[dart]] for dart in cycle)
        white_penalty += sum(abs(a - b) for a, b in zip(incident, [5, 6]))
        if incident != [5, 6]:
            white_penalty += 2
    white = 30 * white_penalty

    hex_penalty = 0
    for face in faces:
        if len(face) != 6:
            continue
        degrees = [fixed.vertex_degree[fixed.dart_vertex[dart]] for dart in face]
        if Counter(degrees) != Counter({2: 3, 5: 3}):
            hex_penalty += sum(degree not in {2, 5} for degree in degrees) + 3
        hex_penalty += sum(
            degrees[index] == degrees[(index + 1) % 6] for index in range(6)
        )
    hex_component = 30 * hex_penalty
    components = {
        "face_distribution": face_distribution,
        "abstract_graph": abstract_graph,
        "equal_face": equal_face,
        "white": white,
        "hex": hex_component,
    }
    return {**components, "total": sum(components.values())}


def score(fixed: FixedMap, alpha: list[int]) -> int:
    return score_breakdown(fixed, alpha)["total"]


def switch_move(
    fixed: FixedMap, alpha: list[int], rng: random.Random
) -> list[int] | None:
    edges = [dart for dart, mate in enumerate(alpha) if dart < mate]
    first, second = rng.sample(edges, 2)
    first_mate, second_mate = alpha[first], alpha[second]
    if rng.randrange(2):
        pairs = ((first, second), (first_mate, second_mate))
    else:
        pairs = ((first, second_mate), (first_mate, second))
    candidate = list(alpha)
    for left, right in pairs:
        candidate[left] = right
        candidate[right] = left
    return candidate


def rotation_from_state(fixed: FixedMap, alpha: list[int]) -> dict[int, list[int]]:
    rotation: dict[int, list[int]] = {}
    for vertex, cycle in enumerate(fixed.cycles, start=1):
        rotation[vertex] = bt._normalize(
            fixed.dart_vertex[alpha[dart]] + 1 for dart in cycle
        )
    return rotation


def run_search(
    base_block: dict[str, object],
    *,
    order: int,
    r_value: int | None,
    seed: int,
    steps: int,
    initial_switches: int = 0,
    graph_valid: bool = False,
) -> tuple[dict[str, object] | None, SearchStats, dict[str, object]]:
    started = time.monotonic()
    rng = random.Random(seed)
    if r_value is None:
        fixed, current = grow_from_block(base_block, order, rng)
    else:
        fixed, current = retarget_from_block(base_block, order, r_value, rng)
    if initial_switches < 0:
        raise bt.BlockError("initial_switches must be nonnegative")
    for _ in range(initial_switches):
        perturbed = switch_move(fixed, current, rng)
        if perturbed is None:
            raise bt.BlockError("initial switch perturbation failed")
        current = perturbed
    current_breakdown = score_breakdown(fixed, current)
    current_score = current_breakdown["total"]
    best = list(current)
    best_score = current_score
    best_breakdown = dict(current_breakdown)
    stats = SearchStats(
        seed=seed,
        order=order,
        initial_switches=initial_switches,
        graph_valid_mode=graph_valid,
        initial_score=current_score,
        best_score=best_score,
        initial_components=dict(current_breakdown),
        current_components=dict(current_breakdown),
        best_components=dict(best_breakdown),
    )
    success: dict[str, object] | None = None

    def validate_zero_score_state(
        state: list[int], *, step: int
    ) -> dict[str, object] | None:
        stats.zero_score_states += 1
        rotation = rotation_from_state(fixed, state)
        try:
            return bt.block_from_rotation(
                rotation,
                provenance={
                    "method": "dart-involution-anneal",
                    "order": order,
                    "seed": seed,
                    "step": step,
                    "initial_switches": initial_switches,
                    "graph_valid_mode": graph_valid,
                },
            )
        except bt.BlockError:
            stats.zero_score_validation_rejections += 1
            return None

    if current_score == 0:
        success = validate_zero_score_state(current, step=0)
    for step in range(steps):
        if success is not None:
            break
        stats.steps = step + 1
        candidate = switch_move(fixed, current, rng)
        if candidate is None:
            stats.graph_rejections += 1
            continue
        if graph_valid and not _abstract_graph_ok(fixed, candidate):
            stats.graph_rejections += 1
            continue
        candidate_breakdown = score_breakdown(fixed, candidate)
        candidate_score = candidate_breakdown["total"]
        fraction = step / max(1, steps - 1)
        temperature = 200.0 * (0.5 / 200.0) ** fraction
        difference = candidate_score - current_score
        if difference <= 0 or rng.random() < math.exp(-difference / temperature):
            current = candidate
            current_score = candidate_score
            current_breakdown = candidate_breakdown
            stats.accepted += 1
        if candidate_score < best_score:
            best = list(candidate)
            best_score = candidate_score
            best_breakdown = dict(candidate_breakdown)
            stats.best_score = best_score
            stats.best_components = dict(best_breakdown)
            stats.improvements += 1
        # A zero score encodes the cheap necessary predicates, not the complete
        # block contract.  Validate every such state: the first zero may have a
        # repeated facial vertex or another condition rejected by block_tools.
        if candidate_score == 0:
            success = validate_zero_score_state(candidate, step=step + 1)
            if success is not None:
                best = list(candidate)
                best_score = 0
                best_breakdown = dict(candidate_breakdown)
                stats.best_score = 0
                stats.best_components = dict(best_breakdown)
                break
    stats.current_components = dict(current_breakdown)
    stats.best_components = dict(best_breakdown)
    stats.elapsed_seconds = time.monotonic() - started
    best_payload = {
        "alpha": best,
        "best_score": best_score,
        "cycles": fixed.cycles,
        "dart_vertex": fixed.dart_vertex,
        "sigma_inverse": fixed.sigma_inverse,
        "vertex_degree": fixed.vertex_degree,
    }
    return success, stats, best_payload


def main() -> int:
    if platform.system() == "Darwin":
        raise SystemExit("map_search.py is cloud-only; refusing to run on Darwin")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--order", required=True, type=int)
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--r", dest="r_value", type=int)
    parser.add_argument("--steps", type=int, default=500_000)
    parser.add_argument("--initial-switches", type=int, default=0)
    parser.add_argument("--graph-valid", action="store_true")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    args = parser.parse_args()
    block = bt.load_json(args.base)
    success, stats, best = run_search(
        block,
        order=args.order,
        r_value=args.r_value,
        seed=args.seed,
        steps=args.steps,
        initial_switches=args.initial_switches,
        graph_valid=args.graph_valid,
    )
    args.log.parent.mkdir(parents=True, exist_ok=True)
    args.log.write_text(
        json.dumps(
            {
                "base": str(args.base),
                "best_state": best,
                "replay": (
                    f"python3 map_search.py --base {args.base} --order {args.order} "
                    f"{'--r ' + str(args.r_value) + ' ' if args.r_value is not None else ''}"
                    f"{'--initial-switches ' + str(args.initial_switches) + ' ' if args.initial_switches else ''}"
                    f"{'--graph-valid ' if args.graph_valid else ''}"
                    f"--seed {args.seed} --steps {args.steps} --output {args.output} "
                    f"--log {args.log}"
                ),
                "stats": stats.__dict__,
                "success": success is not None,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if success is None:
        print(
            f"MISS order={args.order} seed={args.seed} steps={stats.steps} "
            f"best_score={stats.best_score} elapsed={stats.elapsed_seconds:.3f}s"
        )
        return 2
    bt.write_json(args.output, success)
    print(
        f"SUCCESS order={args.order} seed={args.seed} step={stats.steps} "
        f"elapsed={stats.elapsed_seconds:.3f}s output={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
