"""Gates for the figure pipeline.

A figure is a claim about a graph, so the drawing must come from the certificate
and must be checked against it.  Two things are gated: that a drawing of a small
certificate really is plane, and that the barycentric collapse at higher orders
is *detected* rather than silently producing a wrong picture.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import draw

HERE = Path(__file__).resolve().parent
DRAWABLE = (46, 47, 48, 49, 50)
COLLAPSED = (67, 110)


def _rings(order: int):
    return draw.rings_of(HERE / "certificates" / "targets" / f"TARGET_{order}.json")


@pytest.mark.parametrize("order", DRAWABLE)
def test_small_certificates_draw_without_crossings(order):
    rings = _rings(order)
    position = draw.tutte(rings)
    assert draw.no_crossings(rings, position)
    assert draw.min_separation(position) > 1e-6


@pytest.mark.parametrize("order", COLLAPSED)
def test_large_certificates_are_reported_as_collapsed_not_drawn(order):
    """Control: the pipeline must not present a degenerate drawing as a figure.

    The crossings at these orders are floating-point artefacts of the
    barycentric solution, not properties of the graph, so the gate asserts the
    diagnosis -- collapsed separation -- rather than the crossing count.
    """

    rings = _rings(order)
    position = draw.tutte(rings)
    assert draw.min_separation(position) < 1e-7
    assert not draw.no_crossings(rings, position)


def test_crossing_test_detects_a_deliberately_broken_drawing():
    """Control: `no_crossings` must be able to fail.

    Swapping two vertices' positions in a plane drawing forces crossings unless
    the test is inert.
    """

    rings = _rings(46)
    position = draw.tutte(rings)
    assert draw.no_crossings(rings, position)
    a, b = sorted(rings)[0], sorted(rings)[len(rings) // 2]
    position[a], position[b] = position[b], position[a]
    assert not draw.no_crossings(rings, position)


@pytest.mark.parametrize("order", DRAWABLE)
def test_drawing_uses_every_vertex_and_edge_of_the_certificate(order):
    """A figure that quietly omits an edge is worse than no figure."""

    rings = _rings(order)
    position = draw.tutte(rings)
    assert set(position) == set(rings)
    svg = draw.to_svg(rings, position)
    assert svg.count("<line") == len(draw.edges_of(rings))
    assert svg.count("<circle") == len(rings)
    tikz = draw.to_tikz(rings, position)
    assert tikz.count("\\draw") == len(draw.edges_of(rings))
    assert tikz.count("\\node") == len(rings)


@pytest.mark.parametrize("order", DRAWABLE)
def test_committed_figures_match_a_fresh_render(order):
    """The checked-in figures must be reproducible from the certificates."""

    rings = _rings(order)
    position = draw.tutte(rings)
    for suffix, render in ((".svg", draw.to_svg), (".tex", draw.to_tikz)):
        committed = HERE / "figures" / f"TARGET_{order}{suffix}"
        assert committed.read_text() == render(rings, position), committed


def test_outer_face_is_a_real_facial_walk():
    rings = _rings(46)
    boundary = draw.outer_face(rings)
    assert boundary in draw.face_cycles(rings)
    assert len(set(boundary)) == len(boundary)


def test_tutte_refuses_a_boundary_that_repeats_a_vertex():
    rings = _rings(46)
    with pytest.raises(ValueError):
        draw.tutte(rings, boundary=[1, 2, 1])
