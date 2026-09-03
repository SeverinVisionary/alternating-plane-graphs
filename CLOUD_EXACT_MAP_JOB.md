# CLOUD JOB - exact rotation-permutation lanes

This is the next compute specification after checkpoint
`bd507ca5`. Run it only in a user-launched
isolated Linux cloud session. The development machine is for editing,
replay, and sub-second checks only.

## Step 0: hard environment gate

Before installing a solver or starting a search, retain:

```sh
python3 --version
pwd
git status --short --branch
git rev-parse HEAD
```

STOP if `pwd` shows a macOS path such as `/Users/...`: this job must not run on
the development machine.  Stop as well if the checkout is dirty or
`HEAD` is not the dispatch commit. Record solver versions, CPU,
memory, UTC start/end, and the exact command in `results/logs/`.

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


## Lane A: direct closed order 46

Enumerate all three algebraically admissible profiles

```text
r = 16, 17, 18
v3=f3=r,  v4=f4=46-2r+4,  v5=f5=r-4,
E=90, F=46.
```

Use a fixed labelled dart pool of `2E=180` darts. A candidate consists of a
fixed cyclic slot order at each vertex, a fixed-point-free dart involution
`alpha`, and the induced face permutation `phi` (one consistent local-turn
convention). Encode, exactly rather than heuristically:

- the degree and face multiplicities above;
- symmetric simple adjacency (no loops or parallel edges);
- face-cycle lengths and distinct boundary vertices;
- `V-E+F=2` and graph transitivity;
- unequal endpoint degrees on every edge;
- unequal sizes on the two faces incident with every edge; and
- the complete `{3,4,5}` vertex/face alternation and histogram identities.

The first positive certificate at order 46 is the priority. An UNSAT result is
admissible only when the encoding and its label/canonicalization coverage are
audited and the solver emits a reproducible proof or complete model count; a
timeout or a restricted encoding is only search evidence.

## Lane B: direct open block `(b,r)=(27,12)`

The exact two-socket profile implied by capping is:

```text
vertices: degree 2 = 6, degree 3 = 8, degree 4 = 5, degree 5 = 8
faces:    size 3 = 8, size 4 = 5, size 5 = 8, size 6 = 2
E=48, F=23, V-E+F=2, darts=96.
```

Mark two of the face cycles as sockets. Each socket must be a simple
alternating `C6` with three degree-2 whites, every socket edge must border a
pentagon, and all remaining edge/vertex/face alternation conditions are exact.
Require the predicted `r=12` seam object (the homogeneous `C4`/two-separator
signature) when that invariant is part of the selected model; otherwise record
the omission and do not call the lane exhaustive for the structural branch.

## Solver/model requirements

The implementation may use CP-SAT, Z3, or an equivalent exact finite-domain
solver installed in the cloud session. The model must expose the dart
permutation or an equivalent rotation system; a graph-only SAT model is not a
plane-map certificate. Every emitted model is normalized and checked in fresh
processes by both:

```sh
python3 verify.py <certificate.json>
python3 verify_darts.py <certificate.json>
```

The committed `exact_map_postprocess.py` is the required boundary for a
positive model. It serializes the candidate, invokes both commands above in
fresh processes, and writes their exact stdout/stderr and hashes into a
replayable audit record. For an open block, it first runs the strict
`blocks.validate_block` validator, then enumerates all nine cap-hub choices and
runs both closed-APG checkers on every closure. Do not promote a near model,
solver `unknown`, or a partial enumeration to existence or nonexistence.

The solver accepts `--random-seed` and `--threads`; record every shard's values
and keep `--threads 1` for the deterministic baseline. Each JSON record also
contains the exact assertion count and Z3 statistics. A longer positive-search
pilot may use 900 seconds per order-46 profile and 600 seconds for the block
profile; these are search budgets, not completeness or UNSAT claims.

The default encoder omits the explicit bounded reachability expansion. This is
sound for positive search because it only enlarges the model class: the fixed
dart counts force `V-E+F=2`, but that Euler value does not by itself exclude a
disconnected map with positive-genus components. Every candidate therefore
still requires the independent connectivity/sphere verifier, and no absence
claim may use this over-approximation. `--explicit-connectivity` retains the
old expansion only as a diagnostic comparison. The block lane also fixes the
six degree-2 whites to the two socket faces and applies representation-only
relabelling symmetries; the postprocessor remains mandatory.

Example postprocessing commands (run only in the isolated cloud checkout):

```sh
python3 exact_map_postprocess.py \
  results/logs/exact_lane_a_r16.json \
  --output results/logs/exact_lane_a_r16_postprocess.json
python3 exact_map_postprocess.py \
  results/logs/exact_lane_b_27_r12.json \
  --output results/logs/exact_lane_b_27_r12_postprocess.json
```

## Required result disposition

Write a separate JSON record for each `(lane, parameter, seed/model)` with the
literal disposition `CERTIFIED`, `INCOMPLETE`, or `BLOCKED`. A `CERTIFIED`
positive result contains the normalized rotation certificate and both checker
outputs. A failed or timed-out run lists the exact unresolved profile and
constraints actually searched. Commit and push each lane separately before
starting the next expensive lane.

## When you are done — archive yourself

A standing project rule.  Verbatim, and this is
the last thing you do:

> WHEN YOU ARE DONE, ARCHIVE YOURSELF. After your final report is written and
> everything is committed and pushed, call `archive_session` with
> `session_id: "self"`. That stops the session and releases its sandbox; the
> transcript stays readable in the Archived list. Do this as your LAST action,
> after the report — never before it, and never while work is still running.
> If the tool is unavailable or refuses (it normally asks for a confirmation
> that nobody is present to give), say so explicitly in your final report, so
> the session can be cleaned up by hand.
