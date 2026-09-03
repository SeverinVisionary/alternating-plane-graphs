#!/usr/bin/env python3
"""Arithmetic filters for strict Section-8 two-socket block profiles.

The functions here deliberately distinguish two notions that are easy to
conflate:

* ``strict_port_forced_t`` records consequences of the two mandatory socket
  ports alone.  It does not assume a block may be used indefinitely.
* ``t0_profile_is_feasible`` records only the raw ``t=0`` core count.
  ``strict_portable_t0_profile_is_feasible`` additionally applies the two-port
  theorem and is the requested search restriction for repeatable Section-8
  composition, not a nonexistence assertion about one-off strict blocks.

``r`` is always the degree-three count after capping the two sockets, and
``order`` is the order before or after capping (capping changes no vertices).
"""

from __future__ import annotations


def t0_core_parameters(order: int, r: int) -> tuple[int, int, int]:
    """Return ``(beta, gamma, epsilon)`` for a capped ``t=0`` block.

    Removing the twelve socket-boundary and four cap edges leaves the joint
    degree/face edge matrix whose three independent nonnegative entries are

    ``beta = 7r - 2order - 22``,
    ``gamma = 2order - 6r + 18``, and
    ``epsilon = 2order - 4r - 2``.
    """

    return (
        7 * r - 2 * order - 22,
        2 * order - 6 * r + 18,
        2 * order - 4 * r - 2,
    )


def t0_core_matrix(order: int, r: int) -> list[list[int]]:
    """Return the exact ``t=0`` core joint-edge matrix."""

    beta, gamma, epsilon = t0_core_parameters(order, r)
    return [
        [gamma, beta, gamma],
        [beta, gamma, beta],
        [gamma, beta, epsilon],
    ]


def t0_profile_is_feasible(order: int, r: int) -> bool:
    """Whether the raw ``t=0`` core branch passes its arithmetic gate.

    This deliberately does not apply the two-port theorem.  It is the legacy
    algebraic branch table used by ``structural_audit.py``; a strict two-socket
    block needs the stronger :func:`strict_portable_t0_profile_is_feasible`.
    """

    if order < 4 or r < 4 or order - 2 * r + 4 < 0:
        return False
    return min(t0_core_parameters(order, r)) >= 0


def t0_branches(order: int) -> tuple[dict[str, object], ...]:
    """List all algebraically feasible raw ``t=0`` branches at ``order``."""

    rows: list[dict[str, object]] = []
    for r in range(order + 1):
        if not t0_profile_is_feasible(order, r):
            continue
        beta, gamma, epsilon = t0_core_parameters(order, r)
        rows.append(
            {
                "r": r,
                "beta": beta,
                "gamma": gamma,
                "epsilon": epsilon,
                "Y": t0_core_matrix(order, r),
            }
        )
    return tuple(rows)


def strict_port_forced_t(r: int) -> int | None:
    """Return the ``t`` value forced solely by two strict socket ports.

    Every strict socket contributes a distinct isolated six-cycle to the
    degree-5/pentagon incidence graph.  Thus ``r=10`` consumes every node and
    forces ``t=0``; at ``r=11`` precisely one degree-5 vertex and pentagon
    remain, forcing a single incidence edge and ``t=1``.  Other profiles have
    a larger residual incidence graph, so the port argument alone does not
    determine ``t``.
    """

    if r == 10:
        return 0
    if r == 11:
        return 1
    return None


def strict_portable_t0_residual_h55_cycle_size(r: int) -> int | None:
    """Return a residual ``H55`` cycle forced on the portable branch.

    At capped ``r=12``, the two isolated port ``C6`` components consume six
    degree-five vertices and six pentagons from each of two size-eight parts.
    On the strict portable ``t=0`` branch every remaining degree-five vertex
    has two pentagonal incidences, so the two residual vertices and two
    residual pentagons form ``K(2,2) = C4``.  This is a propagation fact for
    the strict canonical interface, not a completeness or nonexistence rule
    for arbitrary APGs.
    """

    return 4 if r == 12 else None


def strict_portable_t0_residual_h55_is_2regular(r: int) -> bool:
    """Whether the residual strict-port ``H55`` is forced 2-regular.

    On the strict portable ``t=0`` branch, each degree-five vertex has
    exactly two pentagonal incidences.  The two port cycles are isolated, so
    at ``r >= 12`` the remaining ``r - 10`` degree-five vertices contribute
    exactly ``2(r - 10)`` residual incidences.  Every residual pentagon has
    at least one degree-five vertex (a proper coloring of its 5-cycle cannot
    omit degree five) and at most two (those positions are independent).
    The incidence total therefore makes every residual pentagon degree two
    as well.  Thus the residual simple bipartite incidence graph is
    2-regular.  At ``r=12`` its two vertices on each side give the ``C4``
    reported by :func:`strict_portable_t0_residual_h55_cycle_size`.

    This is a propagation fact for the strict canonical portable interface;
    it says nothing about arbitrary APGs or finite-use branches.
    """

    return r >= 12


def strict_portable_t0_profile_is_feasible(order: int, r: int) -> bool:
    """Whether a strict two-socket block can lie on the portable ``t=0`` lane.

    In addition to the core counts, this applies the exact port consequence at
    ``r=10`` and ``r=11``.  In particular, an algebraically feasible ``r=11``
    row is excluded because the two strict socket ports force ``t=1`` there.
    """

    forced_t = strict_port_forced_t(r)
    return t0_profile_is_feasible(order, r) and forced_t in (None, 0)


def strict_portable_t0_branches(order: int) -> tuple[dict[str, object], ...]:
    """List portable strict-block ``t=0`` profiles at ``order``."""

    return tuple(
        row for row in t0_branches(order)
        if strict_portable_t0_profile_is_feasible(order, int(row["r"]))
    )
