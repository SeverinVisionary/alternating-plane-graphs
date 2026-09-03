# Complete socket normal form for the Boolean block encoder

This note justifies the `canonical=True` symmetry reduction in
`exact_map_bool_sat.py` for an **open strict Section-8 block**.  It is a
labelling convention for positive search only.  It neither removes a
geometric block nor changes the postprocessor requirement that every positive
model pass the strict block validator, all nine caps, and both independent
closed-map checkers.

## Socket normal-form lemma

Let a strict two-socket block be presented by a labelled rotation system.  Its
two socket faces are alternating six-cycles.  By the strict interface and the
port-cycle theorem, their boundary vertices can be written as two disjoint
cycles

```text
w0 - b0 - w1 - b1 - w2 - b2 - w0,
w3 - b3 - w4 - b4 - w5 - b5 - w3,
```

where the `wi` are all six degree-two whites and the `bi` are six distinct
degree-five port vertices.  (The white sets are disjoint by the block
contract; the degree-five sets are disjoint because the two port `C6`
components are distinct.)

Relabel the white vertices as `0,...,5` in this order and relabel the six port
degree-five vertices as the first six vertices in the degree-five label class,
again in this order.  Relabel all remaining vertices arbitrarily within their
degree classes.  Finally, cyclically rotate each local neighbour list so that
the listed socket edges occupy the desired dart slots.  Neither operation
changes the combinatorial map: vertex relabelling is an isomorphism and a
cyclic rotation of one local list is the same rotation order with a different
chosen first dart.

For each socket, let `wi` mean the first dart at its white and let `bi` mean
the first dart at its degree-five vertex.  The following six unordered dart
matches force its facial walk in the `phi = sigma^-1 alpha` convention:

```text
(w0, b0), (b0+4, w1), (w1+1, b1),
(b1+4, w2), (w2+1, b2), (b2+4, w0+1).
```

Tracing `phi` gives exactly

```text
w0, b0+4, w1+1, b1+4, w2+1, b2+4,
```

and then returns to `w0`.  Thus the matches merely select the two existing
hexagons; face-period constraints identify them as the two length-six faces.
The twelve matches for both sockets are therefore satisfiable after this
normalization for every strict block.

The other endpoint of every forced matching pair is the dart across a socket
edge.  Strictness makes the opposite face a pentagon, so the normal form also
fixes twelve face labels: the twelve dart positions on the two cycles have
length six and their twelve opposite darts have length five.  These labels are
logical consequences of the same normal form, not an additional search
restriction.  The encoder asserts them directly so that generic face-period
propagation does not need to rediscover them.

## Executable positive control

`boolean_socket_canonical.py` computes these index pairs with no solver
dependency.  `test_exact_map_bool_contract.py` relabels each published A21,
B22, C23, and D24 block—and each reflected embedding—using only the two
permitted representation operations above.  It reconstructs the dart
involution and face successor, then checks all twelve required matches and
both exact length-six socket cycles.  This is a positive coverage test for the
normal-form lemma; it does not infer that any new block exists.

The next immutable cloud bundle must additionally run the fixed A21 control
with the real Boolean encoder constraints enabled:

```sh
python3 exact_map_bool_sat.py \
  --known-block results/blocks/A21.json --canonicalize-known-block \
  --timeout-s 120 --threads 1 --output results/logs/bool_known_A21_canonical.json
```

This dynamically applies the same representation-only relabelling, pins the
resulting dart involution, and leaves `canonical=True`.  A `sat`/`CANDIDATE`
record then exercises the complete normal form end-to-end before it is used in
another target search.  The exact control and strictly serial primary target
commands are frozen in
[`CLOUD_BOOL_SOCKET_CANONICAL_JOB.md`](CLOUD_BOOL_SOCKET_CANONICAL_JOB.md).
