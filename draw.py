#!/usr/bin/env python3
"""Straight-line drawings of certificates, for figures.

A paper about plane graphs needs pictures, and a picture drawn by hand is a
second source of truth that can disagree with the certificate.  These drawings
are computed from the rotation system alone, so a figure cannot show a different
graph from the one that was verified.

The embedding is Tutte's: fix one face as a convex polygon and put every other
vertex at the barycentre of its neighbours.  For a 3-connected plane graph
Tutte's theorem guarantees a straight-line drawing with no crossings and the
chosen face outermost.

**These certificates defeat that in floating point, and the reason is not
connectivity.**  They are capped unrollings of a long periodic strip, so the
barycentric solution crushes the interior toward the middle exponentially in the
order.  Measured minimum vertex separation:

    TARGET_46    n=46    2.3e-03    0 crossings
    TARGET_50    n=50    7.8e-06    0 crossings
    TARGET_56    n=56    3.3e-07    1 crossing
    TARGET_67    n=67    3.8e-08   27 crossings
    TARGET_110   n=110   5.0e-12  544 crossings

Crossings appear exactly when the separation falls through double precision.
They are an artefact of the arithmetic, not of the graph: Tutte's theorem still
holds, and the exact solution has no crossings.

Crossings therefore say nothing about connectivity, which is worth stating
because Tutte's theorem is about 3-connected graphs and the reflex is to blame
its hypothesis.  The counterexample of `certificates/counterexamples/` is a
`(3,4,5)`-APG on 46 vertices with a separating pair -- **not** 3-connected --
and it draws with no crossings at all, at a separation of `6.4e-03`, wider than
any 3-connected certificate of comparable order.  An earlier version of this
docstring attributed the crossings to graphs failing 3-connectivity and named
`TARGET_46` as the failing one; `TARGET_46` is in fact 3-connected, and the two
order-46 graphs had been conflated.

Practical consequence: Tutte drawings are usable as figures up to roughly order
50 and are useless above it, where they should be replaced by a schematic of the
cap-strip-cap decomposition rather than a faithful embedding.  `min_separation`
reports the collapse and `main` refuses to write a figure that has silently
degenerated.

Pure standard library, deliberately: the drawing path must not add a dependency
to an artifact whose whole verification story is that it needs none.

    python3 draw.py certificates/targets/TARGET_46.json figure.svg
    python3 draw.py certificates/targets/TARGET_46.json figure.tex --tikz
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from certificate_tools import cycles_from_degrees

import bridge_lemma as bl


def rings_of(path: Path) -> dict[int, list[int]]:
    data = json.loads(Path(path).read_text())
    return {row["id"]: list(row["clockwise"]) for row in data["vertices"]}


def face_cycles(rings: dict[int, list[int]]) -> list[list[int]]:
    """Facial walks as vertex sequences, in the order phi visits them."""

    degrees, alpha = bl.alpha_from_rotation(rings)
    order = sorted(rings, key=lambda v: (len(rings[v]), v))
    cycles, vertex_of, _, sigma_inverse = cycles_from_degrees(degrees)
    phi = [sigma_inverse[alpha[dart]] for dart in range(len(alpha))]
    seen, walks = set(), []
    for dart in range(len(alpha)):
        if dart in seen:
            continue
        walk, cursor = [], dart
        while cursor not in seen:
            seen.add(cursor)
            walk.append(order[vertex_of[cursor]])
            cursor = phi[cursor]
        walks.append(walk)
    return walks


def outer_face(rings: dict[int, list[int]]) -> list[int]:
    """A face to send to infinity: the largest one with no repeated vertex.

    A facial walk that repeats a vertex cannot be drawn as a simple polygon, so
    it is not a usable outer boundary.  Preferring the largest of the rest keeps
    the interior from being crushed against the boundary.
    """

    simple = [walk for walk in face_cycles(rings) if len(set(walk)) == len(walk)]
    if not simple:
        raise ValueError("no facial walk is a simple cycle; cannot choose an outer face")
    return max(simple, key=len)


def tutte(rings: dict[int, list[int]], boundary: list[int] | None = None,
          iterations: int = 20000, tolerance: float = 1e-10) -> dict[int, tuple[float, float]]:
    """Barycentric positions, boundary on a regular polygon.

    Gauss-Seidel rather than a matrix solve, to stay inside the standard
    library.  The system is weakly diagonally dominant and irreducible once the
    boundary is pinned, so the iteration converges; `iterations` is a safety
    stop, not the expected cost.
    """

    boundary = boundary or outer_face(rings)
    if len(set(boundary)) != len(boundary):
        raise ValueError("the boundary walk repeats a vertex")
    position: dict[int, tuple[float, float]] = {}
    count = len(boundary)
    for index, vertex in enumerate(boundary):
        angle = 2.0 * math.pi * index / count
        position[vertex] = (math.cos(angle), math.sin(angle))
    interior = [vertex for vertex in rings if vertex not in position]
    for vertex in interior:
        position[vertex] = (0.0, 0.0)
    pinned = set(boundary)
    for _ in range(iterations):
        shift = 0.0
        for vertex in interior:
            neighbours = rings[vertex]
            x = sum(position[n][0] for n in neighbours) / len(neighbours)
            y = sum(position[n][1] for n in neighbours) / len(neighbours)
            shift = max(shift, abs(x - position[vertex][0]), abs(y - position[vertex][1]))
            position[vertex] = (x, y)
        if shift < tolerance:
            break
    assert pinned == set(boundary)
    return position


def edges_of(rings: dict[int, list[int]]) -> list[tuple[int, int]]:
    return sorted({(min(u, v), max(u, v)) for u in rings for v in rings[u]})


def _crosses(p, q, r, s) -> bool:
    """Do open segments pq and rs meet, sharing no endpoint?"""

    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    d1, d2 = side(r, s, p), side(r, s, q)
    d3, d4 = side(p, q, r), side(p, q, s)
    if ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0)):
        return True
    eps = 1e-12
    for a, b, c in ((r, s, p), (r, s, q), (p, q, r), (p, q, s)):
        if abs(side(a, b, c)) < eps and \
           min(a[0], b[0]) - eps <= c[0] <= max(a[0], b[0]) + eps and \
           min(a[1], b[1]) - eps <= c[1] <= max(a[1], b[1]) + eps:
            return True
    return False


def crossings(rings, position) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Every pair of edges that meet away from a shared endpoint."""

    edges = edges_of(rings)
    found = []
    for i, (a, b) in enumerate(edges):
        for c, d in edges[i + 1:]:
            if {a, b} & {c, d}:
                continue
            if _crosses(position[a], position[b], position[c], position[d]):
                found.append(((a, b), (c, d)))
    return found


def no_crossings(rings, position) -> bool:
    return not crossings(rings, position)


def min_separation(position) -> float:
    """Closest pair of vertices, the direct measure of barycentric collapse.

    Below roughly `1e-7` the drawing is past what double precision can keep
    apart and any crossing count from it is noise.
    """

    points = list(position.values())
    return min(
        math.hypot(points[i][0] - points[j][0], points[i][1] - points[j][1])
        for i in range(len(points))
        for j in range(i + 1, len(points))
    )


def to_svg(rings, position, size: int = 720, margin: int = 24,
           radius: float = 3.0) -> str:
    """Vertices coloured by degree, since degree alternation is the subject."""

    xs = [p[0] for p in position.values()]
    ys = [p[1] for p in position.values()]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) or 1.0
    scale = (size - 2 * margin) / span

    def place(vertex):
        x, y = position[vertex]
        return (margin + (x - min(xs)) * scale, margin + (max(ys) - y) * scale)

    tints = {3: "#1b6ca8", 4: "#c9821f", 5: "#8b2f5f"}
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'width="{size}" height="{size}">',
        f'<rect width="{size}" height="{size}" fill="#ffffff"/>',
        '<g stroke="#33383d" stroke-width="1.1" stroke-linecap="round">',
    ]
    for u, v in edges_of(rings):
        (x1, y1), (x2, y2) = place(u), place(v)
        parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}"/>')
    parts.append("</g><g>")
    for vertex in sorted(rings):
        x, y = place(vertex)
        tint = tints.get(len(rings[vertex]), "#444444")
        parts.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="{radius}" fill="{tint}" '
            f'stroke="#ffffff" stroke-width="0.8"><title>vertex {vertex}, '
            f'degree {len(rings[vertex])}</title></circle>'
        )
    parts.append("</g></svg>")
    return "\n".join(parts)


def to_tikz(rings, position, scale: float = 5.0) -> str:
    styles = {3: "apgthree", 4: "apgfour", 5: "apgfive"}
    lines = [
        "% requires \\usepackage{tikz}",
        "\\begin{tikzpicture}[",
        "  apgthree/.style={circle,fill=black,inner sep=1.1pt},",
        "  apgfour/.style={circle,fill=black!55,inner sep=1.1pt},",
        "  apgfive/.style={circle,draw=black,fill=white,inner sep=1.0pt},",
        "  apgother/.style={circle,draw=black,fill=white,inner sep=1.0pt}]",
    ]
    for vertex in sorted(rings):
        x, y = position[vertex]
        style = styles.get(len(rings[vertex]), "apgother")
        lines.append(f"  \\node[{style}] (v{vertex}) at ({x * scale:.4f},{y * scale:.4f}) {{}};")
    for u, v in edges_of(rings):
        lines.append(f"  \\draw (v{u}) -- (v{v});")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("certificate", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--tikz", action="store_true", help="emit TikZ instead of SVG")
    parser.add_argument("--allow-crossings", action="store_true",
                        help="write the figure even if the drawing is not plane")
    args = parser.parse_args()
    rings = rings_of(args.certificate)
    position = tutte(rings)
    bad = crossings(rings, position)
    gap = min_separation(position)
    if bad and not args.allow_crossings:
        raise SystemExit(
            f"{len(bad)} crossing(s), with minimum vertex separation {gap:.1e}. "
            f"At this order the barycentric solution has collapsed below double "
            f"precision and the drawing is an artefact, not the graph. Use a "
            f"schematic instead, or --allow-crossings to write it anyway."
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        to_tikz(rings, position) if args.tikz else to_svg(rings, position)
    )
    print(f"{args.output}: {len(rings)} vertices, {len(bad)} crossing(s), min separation {gap:.1e}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
