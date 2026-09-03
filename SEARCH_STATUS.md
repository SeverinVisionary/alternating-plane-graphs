# APG search status and embedding semantics

The historical two-edge annealing and bounded beam logs used `graph-valid` to
mean only that the mutable alpha state passed the abstract graph gate: it was
simple and connected and satisfied the search's vertex-degree adjacency
constraints. That gate did **not** test the Euler characteristic of the induced
rotation system.

In particular, the six order-26 score-470 parents recorded in
`results/logs/order26_near_open_radius5.json` and reused by the first annealing
and three-edge target checkpoints are abstract-valid but are not plane maps.
For each, `V - E + F = 0`; they are orientable genus-one maps. Historical logs
are preserved verbatim and must be read with that narrower terminology.

For all new work in this target:

- **abstract-valid** means the existing exact abstract graph gate passes;
- **spherical** or **plane-valid** means the abstract graph gate passes and the
  fixed rotation/alpha state has exact Euler characteristic `V - E + F = 2`.

The six score-800 states produced by the complete order-26 k3 expansion in
`results/logs/order26_three_edge_all_triples.json` are the first plane-valid
frontier obtained from this family. Every subsequent candidate is rejected
before scoring unless it is both abstract-valid and plane-valid.

The plane-valid order-26 k3 family is closed after radius 4. Its complete
64-parent radius-4 expansion exhausted 7,772,160 exact transitions, found no
score-zero witness, and did not improve below the radius-3 minimum of 510. This
is a bounded-family stopping statement, not a nonexistence claim.

## Four-edge calibration evidence correction

The historical file `results/logs/D24_four_edge_full_tests.txt` is preserved
verbatim, but its reported **127 tests must not be cited as a committed-tree
suite**. It came from a dirty cloud workspace and included three tests absent
from checkpoint `ab81937c`:

- `MapSearchTests.test_mixed_span_mode_recovers_fixed_positive_D24`;
- `NearOpeningRematchTests.test_exact_order26_k4_lane_is_frozen`;
- `NearOpeningRematchTests.test_perfect_matching_count`.

A clean isolated checkout of exact `ab81937c515ab16d8227db3ae10615266654b22a`
collects and passes **124/124** tests. The D24 k4 calibration was replayed there
to temporary outputs: the state and recovered certificate are byte-identical,
and the selected pairs, scan counts, all 60 inverse outcomes, D24 hash, and both
closure hashes replay exactly. See `results/logs/D24_four_edge_clean_audit.json`.
This corrects provenance only; it is not a new mathematical result.

The localized order-26 exact k4 support job is complete. Its frozen input is all
56 plane-valid score-510 radius-4 states; each has a 12-edge support consisting
of six equal-face edges together with the eight edges incident to four bad
degree-2 white vertices. The run exhausted all 1,663,200 rematchings. The plane
gate left 1,792 raw and 1,484 distinct states; no score-zero state occurred and
the minimum remained 510. This closes only this localized k4 family and is not
a nonexistence result.

## Historical near-opening topology audit

The historical order-26, dual-order-26, order-30, order-33, and order-34 k4 and
two-edge radius logs used an abstract-map gate only. Exact replay of all 1,024
serialized frontier states confirms their alpha hashes, scores, and abstract
validity, but none has Euler characteristic 2. Their Euler characteristics are
0 or -2. Consequently these logs remain valid only as bounded searches in
abstract fixed-rotation map space. They are not plane-valid frontiers and do
not support any nonexistence claim. The historical files are preserved
verbatim; `results/logs/historical_near_open_topology_audit.json` records the
complete per-file and minimum-score Euler-characteristic histograms.

The next covering-triple lane is staged from five exact plane-embedded but
abstract-invalid near openings at block orders 26, 29, and 33. Each has exactly
two frozen mandatory abstract-defect edges. Order-29b's two defects are
disjoint; no shared-vertex or k3-obstruction claim is made for that seed. The
stage includes a complete mandatory-k3 family (1,968 future attempts) followed
by a separate complete mandatory-k4 family (359,700 future attempts), totaling
361,668. No target rematching from either family has been executed by the stage
checkpoint, and the staged seeds are not witnesses.

The five staged mandatory-defect families have now been run completely. The
mandatory-k3 lane exhausted 1,968 rematchings and every candidate failed the
abstract graph gate. The mandatory-k4 lane exhausted 359,700 rematchings;
358,458 failed the abstract graph gate and 1,242 were abstract-valid but failed
the exact Euler-sphere gate. Thus neither lane produced a plane-valid state to
score, and no score-zero block certificate occurred. This closes only these
five frozen mandatory-defect k3/k4 families. It is a bounded search result, not
a nonexistence claim, and it does not authorize k5, composition, or another
seed family.

The exact five-edge deranged-rematching primitive is now independently
calibrated on D24. It enumerates exactly 544 matchings of ten selected darts
that retain none of five current edges. From a frozen plane-valid positive
score-490 perturbation, the complete 544-candidate inverse family has exactly
one plane-valid score-zero member: the original D24 block, verified by both
block validators, both closers, and the final certificate verifier.

A mandatory-defect k5 target is staged, but **not executed**, for the same five
frozen order-26/order-29/order-33 near openings. Every selected set consists of
the two mandatory defect edges and every unordered triple of the full remaining
edge set, without filtering. The frozen future budget is 96,544 selections and
52,519,936 rematchings. This is a pre-compute protocol only; it adds no target
search result and makes no nonexistence claim.

Before any target use, the k5 result validator was hardened to reconcile every
per-seed/global counter, replay every serialized frontier alpha on its exact
fixed map through the abstract and Euler-sphere gates, reproduce scores and
rotations, enforce exact namespaces/histograms/frontier identities, and replay
every certificate through both validators, both closers, and the final
verifier. The target remains staged and unexecuted.

The five frozen mandatory-defect k5 families have now been run completely.
The exact run exhausted all 96,544 selected five-edge sets and all 52,519,936
deranged rematchings. Four distinct plane-valid states survived the gates, at
scores 760, 780, 800, and 1620; none had score zero and no block certificate
was produced. This closes only this exact five-seed mandatory-k5 family. It is
a bounded search result, not a nonexistence claim, and does not authorize k6,
another seed family, or composition.

## Structural invariant audit checkpoint (2026-08-29)

The next step is now implemented as a lightweight, exact audit rather than a
new blind cloud enumeration. `structural_audit.py` independently reconstructs
the closed rotation systems for all 3x3 choices of socket hubs and computes the
corner matrix `P`, the joint edge-type matrix `X`, the t=0 core matrix `Y`, the
degree-5/pentagon incidence graph `H55`, and the two cap motifs. The serialized
evidence is in
`results/logs/structural_audit_known_blocks.json`; the exploratory professor
memo and its review session metadata are preserved beside it.

Known-answer controls pass for A21, B22, C23, and D24: all 36 closures are
spherical, have `t_vertex=t_face=0`, match the exact `P` and `X` formulae, and
have the expected `Y`; each has two H55 components of six nodes, and every cap
is a degree-4 hub joined to two degree-3 leaves. All 16 ordered A--D gluings
also pass the independent t-additivity check and produce four six-node H55
components. The regression suite is `test_structural_audit.py` (3 tests).

This is a control result, not yet a theorem about all compatible blocks. In
particular, the proposed port-cycle argument and the conditional r=11
exclusion remain unauthorised as search-pruning rules until their topological
hypotheses are proved independently. No 549,982-attempt survivor expansion or
k6 run is authorised by this checkpoint.

## Public-source structural census checkpoint (2026-08-29)

The nineteen planar-code inputs named by the alternative-order opening-scan
manifest are now frozen under `certificates/census_sources/`. Their bytes all
match the recorded SHA-256 values. `source_census.py` independently verifies
all 19 closed rotation systems, recomputes their exact `(r,t,H55)` signatures,
and exhausts their legal disjoint closure-fan pairs.

All 19 sources pass the spherical APG verifier, and every one has zero strict
Section-8 openings. The source signatures are not homogeneous: the public
order-26/27/28 examples have r=11 branches, several order-29--32 examples have
r=12, order-32--35 examples include r=13, and order-36 examples have r=14;
t ranges from 1 to 4. This is useful source-ranking evidence, not a theorem
about compatible blocks or about the unresolved target orders.

The replay artifact is
`results/logs/source_structural_census.json`, with a regression gate in
`test_source_census.py`. No new cloud compute was used for this census, and no
source score or bounded miss is being promoted to nonexistence.

## review checkpoint (2026-08-30)

The linked the independent review/an independent reviewer review identified three concrete completeness gaps in
the first structural pass, and they are now addressed in the reference lane:

- `blocks.close_block_variants` exposes every successful 3x3 hub choice while
  preserving the historical smallest-white `close_block` replay; reflected
  rotations and reflected opening scans are available through
  `mirror_block`, `compose_blocks_variants`, and `opening_scan_with_mirror`.
- `verify.py` now rejects a repeated vertex in any reconstructed facial walk
  explicitly, rather than relying on a later adjacency consequence.
- `validate_relaxed_block` and `relaxed_opening_scan` implement a documented
  necessary-condition over-approximation: socket whites may meet degree 3 or
  5 and socket hexagons may border triangles or pentagons, with the gluing and
  face-alternation role checks applied exactly. The 19-source census reports
  zero relaxed openings in both orientations, but this is only source-corpus
  evidence and not a claim that the relaxed class is empty.
- `verify_darts.py` is now a second standalone checker. It reconstructs faces
  from the opposite dart-permutation turn, has no imports from `verify.py`,
  `blocks.py`, or search code, and passes the positive and mutation controls in
  `test_verify_darts.py`.

The same review recommends a genuinely third-party dart-permutation checker
and an exact SAT/CP lane (including a direct order-46 target) before spending
more k-edge rematching budget. Those remain planned cloud work; no k6 or SAT
job has been run from the shared host.

## Fixed proof-review adjudication (2026-08-30)

The follow-up independent review audit is archived in
`results/logs/professor_pro_fixed_audit_20260830.md`. The CLI request asked for
ultra-high fixed-proof review, but the backend actually recorded `tier=Pro` and
`effort=pro`; it is therefore recorded as a Pro review and is not silently
counted as an ultra-high run.

Its sharpened mathematical disposition is:

- Under the strict Section-8 interface, each socket gives a distinct isolated
  `C6` component of the degree-5/pentagon incidence graph `H55`; this does not
  require `t=0`.
- At `r=11`, the two port cycles force `H55 = C6 + C6 + K2`, hence `t=1`.
- Standard fresh-copy gluing and capping preserve the incidence graph and make
  `t` additive. A block admitting a valid fivefold fresh-copy composition (or
  unbounded multiplicity) must therefore have `t=0` and cannot be an `r=11`
  block.

This is a proof target for the exact implementation interface, not yet a
search-wide pruning theorem: the bridge from the repository's accepted
objects to the formal strict interface, and compatibility of every future
socket type, still needs a code-level certificate or a complete enumeration.

The next cloud dispatch is frozen in `CLOUD_EXACT_MAP_JOB.md`: direct closed
order 46 for all `r=16,17,18`, followed by an exact `(b,r)=(27,12)` open-block
lane. Both `verify.py` and the standalone `verify_darts.py` are mandatory on
every positive model; no solver or SAT/CP compute has been run on the shared
host.

## Cloud dispatch status (2026-08-30)

The native cloud task reached an isolated Linux x86_64 worker and passed the
non-Darwin gate, but the first access attempts were blocked before computation.
The authenticated clone had no credentials; a retry through the public codeload
and GitHub API endpoints returned HTTP 404 for the pinned commit. No different
revision was substituted and no certificate or UNSAT claim was made. The exact
attempt report is `results/logs/cloud_exact_map_dispatch_20260830_blocked.json`.
A follow-up access audit found no attachment/shared-data mount, GitHub CLI, SSH
key, credential helper, or token. The complete Git bundle advertising the pinned
commit was then attached to the same cloud task and its resume prompt sent. The
cloud worker verified the bundle digest, transfer ref, exact HEAD/tree, fsck, and
clean tree before starting its bounded exact encoding.

## Exact cloud pilot result checkpoint (2026-08-30)

The attached-bundle retry completed the requested bounded pilot on the isolated
Linux worker. The machine-readable record is
`results/logs/exact_cloud_1259a7ce_summary.json` (SHA-256
`73f03b6595b60e678741788c9ff040df6cc733dbeeee0200f6ab657bd85f2b38`), and the
imported encoder is `exact_map_sat.py` (SHA-256
`a993b939256977c608e33446087da8f91d9b286a2bdd17756c1bb03b3541f11a`). The
bundle, exact commit/tree, Linux gate, and clean checkout were reverified; the
known-answer gate passed 48 tests with 79 subtests.

Lane A covered all three required order-46 profiles. Z3 returned `unknown` for
`r=16` (128.981 s), `r=17` (129.820 s), and `r=18` (129.170 s); each is
`INCOMPLETE`, not UNSAT. Lane B covered the exact `(b,r)=(27,12)` two-socket
profile and returned `unknown` after 122.237 s (`INCOMPLETE`). No positive model
was emitted, so no certificate, dual-verifier replay, or cap-hub closure was
available. The imported Lane-B encoding does not include the predicted
homogeneous `C4`/two-separator seam invariant; therefore this is a bounded pilot
and not an exhaustive structural-branch search. The literal overall result is
`INCOMPLETE: 0/26 independently verified`; no nonexistence or UNSAT claim is
made.

The cloud task also exposed the four original per-profile JSON records. They
are archived verbatim under `results/logs/exact_lane_a_r16.json`,
`exact_lane_a_r17.json`, `exact_lane_a_r18.json`, and
`exact_lane_b_27_r12.json`; their SHA-256 values are recorded in the summary
and match the cloud-reported bytes.

## Exact-map re-dispatch access gate (2026-08-30)

The longer pilot was prepared from commit `7deedb35` (tree
`39d8ff2b`) with solver diagnostics and mandatory candidate postprocessing.
The Chrome file-chooser upload of its exact bundle was blocked by the
extension's `Allow access to file URLs` setting, so the cloud task was asked to
fetch the public branch over HTTPS instead. The isolated Linux worker passed
its platform gate but GitHub returned
`fatal: could not read Username for 'https://github.com': terminal prompts
disabled`; it hard-stopped before reading the repository or starting a solver.
The attempt is recorded in
`results/logs/cloud_exact_map_dispatch_20260830_next.json`. No revision was
substituted, and no new order, SAT, UNSAT, or nonexistence claim follows.

## Exact-map certificate-boundary checkpoint (2026-08-30)

The pilot's static review identified a second gate that must be complete before
any SAT model is treated as a witness. `exact_map_postprocess.py` now provides
that boundary. It serializes a candidate, invokes `verify.py` and the standalone
`verify_darts.py` in fresh processes, and records exact commands, stdout/stderr,
and artifact hashes. For a two-socket candidate it additionally runs the strict
`blocks.validate_block` validator, enumerates the complete 3x3 cap-hub set, and
checks every closure with both verifiers. A non-candidate, failed check, or
partial closure set remains `INCOMPLETE`.

The regression controls use the published order-20 APG and A21 block: both
independent checkers pass the closed control, and all nine A21 closures pass.
The focused postprocessor/verifier gate is 19 tests. This is a validation and
replay improvement only; it adds no target-order certificate and no
nonexistence claim.

The remaining completeness work before a fresh long run is explicit: define
and encode the homogeneous C4/two-separator seam invariant with positive and
negative controls; add a relabelling lemma and known-map satisfiability tests
for the fixed dart-slot representation; account for deterministic symmetry
shards; and reserve any absence claim for a proof-producing backend. The next
cloud dispatch must run the postprocessor on every positive model before
reporting `CERTIFIED`.

## Exact-map encoding reduction checkpoint (2026-08-30)

The next pilot uses the same finite-domain model with two positive-search
reductions. First, the explicit `V-1`-round reachability expansion is disabled
by default. The prescribed profiles force `V-E+F=2`, but that Euler value does
not by itself exclude a disconnected map with positive-genus components; the
reduced model is therefore an intentional over-approximation. Every candidate
still requires the independent connectivity/sphere verifier, and no absence
claim may use this relaxation. The old expansion remains available only via
`--explicit-connectivity` for a diagnostic comparison. Second, the block lane
requires all six degree-2 whites to lie on the two marked sockets and fixes a
socket/face/dart labelling convention; these are necessary properties of every
strict Section-8 block and remain independently checked by the postprocessor.

The local syntax and regression gate is 24 tests. No solver was run on the
shared Mac and no target certificate or nonexistence claim has been added. The
next cloud job must record the new assertion counts and retain
`INCOMPLETE` for all `unknown`/timeout outcomes.

## Long-pilot artifact preservation checkpoint (2026-08-30)

The exact-bundle Linux pilot's complete 63-entry artifact set is now preserved
under `results/logs/long_pilot_20260830/`. The downloaded archive is
`results/logs/apg-exact-bundle-pilot-artifacts-20260830.tar.gz`, 7,447 bytes,
SHA-256 `84963668eecf772e280b2df9ebc4f7d4e543ea9002a07bb33a2eb724d0eb8834`.
The extracted `manifest.json` has SHA-256
`5e5b03048ccfe778968ef016ba5394d307c4b816d2adab19a421aa01ec25ffa3`; every
listed file's byte count and digest match that manifest. `source_gate.json`
records the exact bundle, commit/tree, Linux gate, fsck, and clean checkout.

All 11 shards are solver `unknown`/`INCOMPLETE`; no positive model was emitted,
so the postprocessor records are necessarily non-candidate dispositions. This
checkpoint preserves evidence only and does not add a target certificate or an
absence claim.

## Exact-map metadata-preserving redispatch (2026-08-30)

The exact mbox series was attached successfully after the Chrome file-URL
permission was enabled. The cloud worker is now running from the baseline
bundle plus that series; it must verify the seven commit hashes and final tree
before any solver starts. The dispatch record is
`results/logs/cloud_exact_map_dispatch_20260830_next.json`, and the attached
mbox digest is recorded there. Until the session returns source-gate and
postprocessing records, the target count remains `0/26` independently verified.

## Exact target-bundle redispatch (2026-08-30)

The metadata-preserving mbox was accepted by the cloud worker and reproduced the
dispatch tree, but every replayed commit object had a different hash; the session
therefore hard-stopped before tests or solver work. To remove replay-dependent
metadata from the source gate, a complete Git bundle containing the exact target
objects was attached to the same isolated cloud task. The bundle is
`<source-bundle>`, SHA-256
`6bcfa9bcd92a3c8ba59e1a69b8a4e1608187e107be3475ce0ce00d2a8d0d1ea7`, and
advertises `refs/heads/apg-345-target` at
`7deedb353ca80d5de61d4bf999310809feea3e4d` with tree
`39d8ff2bbf71eff7b6fe0d3a005464cb4eb835d6`. The worker must verify the bundle,
exact commit/tree, and a clean checkout before reading the job spec or running
any solver. Target coverage remains `0/26` until raw outputs pass the mandatory
postprocessor and independent verifiers.

## Reduced exact-map pilot artifact checkpoint (2026-08-30)

The reduced-encoder pilot was run from the exact bundle for commit
`e44699b2780a269537df71a861c247444d10be4e` (tree
`490812444803e3e326f7d61ccaac9a67e2af40a4`). The Linux source gate passed,
including bundle SHA-256, complete-history verification, fsck, and a clean
checkout; the known-answer suite passed `56` tests and `87` subtests.

The four requested one-thread, seed-0 shards produced no candidate. Lane B
`(27,12)` returned solver `unsat` in the reduced, representation-restricted
model after `0.43` seconds (`1905` assertions); this is bounded search evidence
only and remains `INCOMPLETE`, not a nonexistence result. Lane A closed
`r=16,17,18` each ran for the full 300-second budget and returned `unknown`
with `3205, 3206, 3207` assertions respectively; each remains `INCOMPLETE`.
No verifier or closure run was applicable because no positive model was
emitted.

The complete 29-entry raw audit set is preserved under
`results/logs/reduced_pilot_20260830/`; its archive is
`results/logs/apg-reduced-e44699b2-pilot-artifacts-20260830.tar.gz` (4,197
bytes, SHA-256
`829e94f494e18275987e0d375f0a44ea7a6d19637256569dd33c6df4d994216d`). The
manifest has SHA-256
`57816b204b84701dd94c2076713d422245d6992a9dee91fa8d9e3f6d78c86fa4`, and
all listed sizes and digests were rechecked locally. Target coverage remains
`0/26`.

## Boolean exact-map pilot preparation checkpoint (2026-08-30)

The next solver method is committed in `exact_map_bool_sat.py` at
`1f5687cc`. It replaces the nested Z3-array involution with Boolean matching
variables, one-hot target vertices, exact `phi` face periods, and explicit
degree/face edge-incidence cardinalities. A pinned order-20 certificate gate
is required before the target shards. The cloud specification is
`CLOUD_BOOL_MAP_JOB.md`; its exact bundle is source-pinned to the commit and
will be attached only after the operator unlocks the authenticated Work
browser. No local Z3 run has been performed.

The Boolean profile helper is now parameterized by `(order,r)` and records the
actual block order in solver output; postprocessing uses that field when
checking closures. The first targeted proposed branches are `(25,10)`,
`(29,12)`, and `(34,13)`, followed by the three direct order-46 profiles.
These branches are search triage only and do not assert that other `r` values
are impossible.

## Boolean strict-block representation repair (2026-08-30)

Before the Boolean pilot was dispatched, its open-block clauses were audited
against the published A21 strict block.  The audit found two independent
overconstraints in the original Boolean encoding: it put both darts of each
degree-2 socket white on hexagons (where a genuine white has one hexagonal and
one pentagonal incidence), and it failed to subtract the twelve forced
degree-2--degree-5 stubs before solving the residual degree-3/4/5 edge-count
equations.  Either defect would make a valid strict block spuriously
unreachable, so no result from the earlier unrun Boolean block configuration is
admissible evidence.

Commit `f5d42448` corrects both constraints and adds a published A21 geometry
regression control.  The cloud job now has two mandatory SAT controls before
any target shard: the pinned order-20 closed map and a pinned A21 open block.
The latter must then pass strict block validation, every one of the nine
cap-hub closures, both independent verifiers, and retained structural H55/t
audit data.  The structural audit is diagnostic rather than a new pruning
condition.  The local focused gate passed 28 tests; no Z3 solver was run on
the shared host, no target order was searched, and coverage remains `0/26`.

## Strict-port theorem and Boolean branch correction (2026-08-30)

The fixed-proof audit's remaining implementation bridge is now recorded in
`SECTION8_PORT_THEOREM.md`.  The accepted strict block interface enforces
simple socket and pentagonal facial walks, two disjoint degree-2/5 socket
cycles, and strict pentagonal socket neighbours; the companion fresh-copy
composition operation preserves that interface.  Those facts give two distinct
isolated `C6` components in the
degree-5/pentagon incidence graph `H55`.

Consequently, a capped `r=10` strict block has its entire `H55` consumed by
the two ports and therefore forces `t=0`; the exact core count at `(b,r)=(25,10)`
then has `beta = 7r - 2b - 22 = -2`.  That profile is impossible by a direct
count, so the unrun Boolean `(25,10)` shard has been removed.  This does not
discard the finite-use `(25,11)` branch: its two port cycles instead force
`H55 = C6 + C6 + K2` and `t=1`.

The Boolean encoder now has opt-in `--require-t0`, which constrains every
degree-5 vertex to exactly two pentagonal incidences and first rejects any
profile failing the strict-portable core gate.  The scheduled cloud work is
therefore `(25,11)` as a finite-use lane plus portable `t=0` lanes
`(27,12)`, `(28,12)`, `(29,12)`, `(31,12)`, and `(34,13)`.  The new finite
composition helper records that a positive-t block may be used only when the
summed target-chain budget is at most four; it must not be silently treated as
freely repeatable.  The postprocessor now turns a requested block-t branch
into a nine-closure gate (`--expected-block-t`); `--require-t0` solver records
implicitly require zero. It also reconstructs the degree-three count from
every candidate/closure and rejects a solver record whose claimed `r` profile
does not match. The focused syntax/regression gate passed **42 tests**; no
local Z3 solver ran and target coverage remains `0/26`.

Cross-model review was attempted before this checkpoint: an independent reviewer
`an independent reviewer` max and `an independent reviewer` xhigh legs both encountered the local
model-cache schema failure and produced no final verdict, while the fresh an independent reviewer
CLI leg returned a tooling execution error. None is counted as an approval; the
checkpoint relies on the recorded focused local gates and the mandatory cloud
known-answer controls.

## Live Boolean control gate and path-boundary repair (2026-08-30)

The isolated cloud worker accepted the exact `4ab6dcb1` bundle only after the
Linux, bundle SHA, explicit remote-ref checkout, commit/tree, clean-worktree,
and `git fsck` gates. Its order-20 Boolean control was `sat` and passed both
independent verifiers. The pinned A21 strict-block control was likewise `sat`,
passed the explicit `t=0` gate, strict validation, all nine cap closures, and
both verifiers.

That control exposed a non-mathematical boundary defect: a normal repo-root
postprocessor invocation stored relative candidate paths, while its verifier
subprocesses deliberately use the module directory as their working directory.
The first run therefore reported only file-not-found closure failures. The
cloud worker reran the same already-written A21 record with absolute artifact
paths and obtained `CERTIFIED`; no target result was promoted from the failed
path invocation. `exact_map_postprocess.py` now resolves both input and output
paths at its boundary, and a repo-root CLI regression test reproduces the
former failure mode and requires all nine closures to certify. The active
already-dispatched bundle predates that repair, so its worker must retain the
absolute-path workaround for any candidate; the next bundle includes the fix.

## Boolean pilot artifact audit and serial recovery boundary (2026-08-30)

The completed Boolean pilot archive is now independently preserved by its
source and artifact hashes in
`results/logs/boolean_cloud_pilot_4ab6dcb1_audit.json`. Its 64-entry manifest
was locally rehashed entry-by-entry. The source gate names exact bundle
`03ae525d18d4a426ea230d7a4ce009d9abc9bdf610eab325cb4d4afc950e26af`, commit
`4ab6dcb160704aa869268d738a7b700d3da0afa5`, and tree
`1671856be18ee636538a1c99242a94e1cab8557d`; it records an isolated Linux
worker, clean checkout, `git fsck`, Python 3.12.13, and Z3 5.1.0.

The known order-20 control passed both independent checkers. The A21 strict
control is `CERTIFIED`: strict validation, the requested `r=10`/`t=0` gates,
all nine cap-hub closures, and both independent checkers on every closure pass.
The archived absolute-path result was independently replayed with the repaired
postprocessor, so the former relative-path failure is not being mistaken for a
mathematical failure.

No target profile produced a certificate. `(25,11)`, `(27,12)`, `(28,12)`,
and `(29,12)` each ran their full bounded budget and returned Z3 `unknown`,
therefore `INCOMPLETE`. `(31,12)` and `(34,13)` were killed before raw JSON
was written; their retained stderr records only `Killed`. The pilot worker had
started target processes concurrently despite each command specifying
`--threads 1`; that option constrains solver threads, not process memory. This
is a resource block, not an UNSAT result or any absence statement. The exact
target count remains `0/26` independently verified.

`CLOUD_BOOL_RECOVERY_JOB.md` narrows the next source-gated cloud task to those
two missing-record profiles only. It replays the closed and strict-block
controls, requires relative-path postprocessing to exercise the repaired
boundary, then runs `(31,12)` to completion before `(34,13)` begins. It must
retain per-process resource output and may not retry a killed/unknown profile
inside the same task. The recovery job has no authority to promote any
incomplete result to nonexistence or to launch additional profiles.

## Serial recovery utility block and portable-runner repair (2026-08-30)

The first serial recovery used exact commit
`71369575d83b87207f8203adfbe86c26099ec870` (tree
`6bac17ae49b411675296f47d7a9d0fd33f609c35`) and passed its Linux/bundle/fsck/
clean-tree gate. Its order-20 and A21 controls passed again; the latter was
`CERTIFIED` with all nine closures, both checkers, and `r=10`, `t=0` gates.
The 38-entry artifact archive and its manifest were independently rehashed;
their SHA-256 values and the literal `BLOCKED` target disposition are frozen in
`results/logs/boolean_cloud_serial_recovery_71369575_audit.json`.

Neither target solver launched. The cloud image lacked `/usr/bin/time`, which
the first recovery specification used as a hard command prefix; `(31,12)` and
`(34,13)` each exited 127 before Python/Z3 started and wrote no raw target
JSON. They were nevertheless attempted in the required serial order. This is
an execution-wrapper defect only, not a timeout, UNSAT result, witness, or
nonexistence statement.

The next recovery bundle replaces that external utility assumption with
`cloud_resource_runner.py`. The committed wrapper streams the child command's
stdout/stderr unchanged and writes portable child exit/resource metadata even
on a missing executable or signal exit. Its focused success and child-failure
tests are required before the same two profiles are retried, still one process
at a time and with no authority to add profiles or seeds.

## Portable serial Boolean recovery audit (2026-08-30)

The repaired recovery bundle at exact commit
`d69d3863c10284af77c026cc9f07f2d18fc91bb4` (tree
`8b7be28a5a1e9fcba9267a648a1af20d3fd00fff`) passed its isolated-Linux,
bundle/ref, complete-history, fsck, and clean-checkout gates. Its archive
`apg-boolean-d69d3863-recovery-artifacts.tar.gz` has SHA-256
`c4f8956ce48265e0898a8b0f35d43f7c56415c18b3b0bf0dcecfd788af127fd2`; its
42-entry manifest has SHA-256
`fbae199437c59143a1c62b605428a6cd9a0285ad23faf5b4ea7eefdd80542483`, and
every listed artifact was rehashed locally.

The order-20 known map passed both independent verifiers. The A21 strict
control again reached `CERTIFIED`: strict validation, the `r=10`/`t=0` gates,
all nine cap-hub closures, and both independent checkers on every closure
pass. The strict intermediate correctly has degree-two socket whites and so
is not itself a closed APG certificate; an independent local strict validator
accepted it while the two closed-map verifiers accepted all nine closures.

The serial target processes each ran one thread for the full 600-second solver
budget and exited normally with retained resource metadata: `(31,12)` returned
`unknown` after 600.004 seconds and `(34,13)` returned `unknown` after 600.105
seconds. Neither emitted a candidate, so neither was postprocessed and neither
has a certificate. Both dispositions are `INCOMPLETE`; no UNSAT,
nonexistence, or solved-order claim is made. The machine-readable checkpoint is
`results/logs/boolean_cloud_serial_recovery_d69d3863_audit.json`.

## Complete socket normal-form checkpoint (2026-08-30)

The Boolean strict-block symmetry reduction is now strengthened from one
arbitrary pair to a complete representation normal form for both mandatory
socket hexagons. `BOOLEAN_SOCKET_CANONICALIZATION.md` proves that relabelling
within degree classes and rotating local dart lists preserve the rotation
system while putting all twelve socket matches in fixed slots.
`boolean_socket_canonical.py` executes that normalisation without a solver
dependency. The local contract exhausts A21/B22/C23/D24 and their mirrors,
checks every forced dart pair and each induced hexagonal `phi` cycle, and
exercises the exact fixed-slot profile used by the CLI control.

The new `--canonicalize-known-block` switch makes the A21 known control use
the same normal form with `canonical=true`, while retaining the old
non-canonical control for comparison. Its future cloud prerequisite and the
strictly serial `(28,12),(29,12),(31,12)` primary coverage batch are frozen in
`CLOUD_BOOL_SOCKET_CANONICAL_JOB.md`. This is a new source-pinned positive
search encoding, not an inference from the older one-pair `unknown` records.

The normal-form propagation now also asserts the resulting 24 exact face
labels before generic face-period propagation: the two determined socket
`phi` cycles are length six and the twelve darts opposite their edges are
length five.  The latter fact uses strict pentagonal socket neighbours, not a
new pruning hypothesis. The contract checks every published A21/B22/C23/D24
block and its mirror against independently traced facial periods; fresh
two independent read-only reviews found no material
restriction or target-profile misclassification. This remains a solver
reduction only: it adds no APG or strict-block certificate and target coverage
remains `0/26` pending the newly source-pinned cloud batch.

## Closed cap-motif Boolean route (2026-08-30)

The strict open-block encoding now has an independent closed-map formulation
from the professor strategy memo. A strict Section 8 block, once capped, is a
closed APG with two disjoint marked degree-4-to-(degree-3, degree-3) fans;
deleting those four edges restores its two sockets. The Boolean route fixes
only those four labelled fan edges after a degree-class relabelling. It does
not assume their face geometry, so a positive closed model must first pass both
closed-APG verifiers and then reopen through `blocks.open_cap_fans` to the
strict validator, structural audit, and all-nine-closure checker boundary.

`BOOLEAN_CAP_MOTIF_NORMALIZATION.md` records the normal-form proof and
`CLOUD_BOOL_CAP_MOTIF_JOB.md` freezes a source-gated, strictly serial portable
`(28,12),(29,12),(31,12)` `t=0` batch. The A21 known control is dynamically
capped, relabelled, pinned in the same normal form, then required to reopen and
certify all nine closures. Local tests exercise every A21 closure, all
published A21--D24 blocks and mirrors, the positive postprocessor boundary,
and target-profile label arithmetic. This is a second search encoding and has
not yet produced a target/block certificate; coverage remains `0/26`.

The local checkpoint gate passed 52 primary tests, 9 independent dart/block
tests, `py_compile`, and `git diff --check`. A read-only an independent reviewer review
found one P2 provenance defect: an unmarked closed record could name
`require_t0` and bypass the reopening/nine-closure branch. The boundary now
rejects that malformed record and has a negative regression test. The parallel
an independent review returned `Execution error` without a verdict, so
it is recorded as a tooling blocker rather than an approval. The immutable
cloud A21 cap control remains the required first solver proof before any target
profile runs.

## Source-bound all-26 promotion gate checkpoint (2026-08-30)

The closed-cap Boolean route now has a complete fail-closed promotion path for
a future positive `(28,12),(29,12),(31,12)` triple. The postprocessor exports
`opened_block.json` only after it is `CERTIFIED`; it no longer leaves a reusable
open block on a later `t`, `r`, or nine-closure failure. The source handoff
gate then binds the raw Boolean certificate, raw/post/opened SHA-256 values,
marked cap reopening, strict Section-8 validation, portable `t=0`, and fresh
dual raw checks, and materializes canonical A--D controls.

The deterministic composer requires the eligible ledger for the frozen 26
target mode, rechecks every supplied source, explores all reflection/socket/
cyclic gluings with a replay trace, records the predicted histogram and
additive `t` budget, and leaves only
`PROMOTED_PENDING_SEPARATE_FINAL_AUDIT`. A separate final auditor replays the
durable source-handoff copy, all strict block closures, and all final targets
through both verifiers before—and only before—writing `MANIFEST_COMPLETE`.
`CLOUD_TARGET_PROMOTION_JOB.md` specifies the isolated-Linux, exact-bundle,
hash-bound dispatch and archive protocol.

This is a major executable certificate-promotion checkpoint, not a
construction result. No cloud Boolean target profile was run for this new
route, no portable 28/29/31 block has been certified, no target certificate was
added, and target coverage remains **0/26 independently verified**. No
nonexistence claim is made.

The final adversarial source-evidence audit also found and closed a JSON
ambiguity defect: ordinary decoders keep the last duplicate object member, so
an ambiguous raw certificate could otherwise be normalized before its fresh
checks. The cap postprocessor, source handoff, composer, finalizer, and both
independent APG checkers now reject duplicate object members (including nested
rotation lists) and non-standard JSON numeric constants before accepting any
certificate or provenance object. Regression controls cover duplicate raw
`certificate` and `clockwise` keys and both standalone verifier CLIs.
The review disposition, findings, local checks, and explicitly non-counting
external-panel blockers are retained in
`results/logs/promotion_gate_review_20260830.md`.

## Full marked-cap interface gate (2026-08-31)

The portable closed-cap Boolean lane now requires the complete necessary
degree-five neighbourhood pattern of each marked cap, rather than only its two
hub--leaf edges. If a strict socket with degree-five boundary vertices
`b0,b1,b2` is capped at one white hub, the hub and two leaves have degree-five
neighbourhoods `{b0,b2}`, `{b0,b1}`, and `{b1,b2}`. Thus each has exactly two
degree-five neighbours, every pair has exactly one common one, and no
degree-five vertex meets all three. These predicates are now imposed directly
in `exact_map_bool_sat.py`; they remain only a necessary graph interface, with
facial reopening delegated to the independent postprocessor.

The pure-Python control validates this interface across all 72 published
closures (A21--D24, both orientations, all nine cap-hub choices). The cloud
job requires the emitted `require_cap_interface=true` marker for its pinned
A21 control and every target candidate. Three independent review legs found
no correctness defect; the review record is
`results/logs/cap_interface_review_20260831.md`.
This is a stronger exact-search revision, not a block certificate or a target
construction: no new target profile has run and the verified target count is
still 0/26.

## Marked-cap facial interface gate (2026-08-31)

The portable closed-cap Boolean lane now also requires the facial consequence
of the two cap chords: each chord has one triangular and one quadrilateral
side, and the quadrilateral sides lie on the same 4-face. The solver states
this in its own dart convention, `phi = sigma^-1 alpha`: the two matched dart
pairs have face lengths `{3,4}`, and their selected length-four darts meet
within `phi^1`, `phi^2`, or `phi^3`. This is a necessary reduction only; it
does not replace the closed-map check, reopening, strict-block validation,
structural audit, or all-nine-closure boundary.

The regression family contains every published A21--D24 block, both
orientations, and all nine cap choices: 72 closures / 144 marked caps. It now
checks both the independent vertex-face description and the exact Boolean
dart convention. The cloud job rejects stale outputs unless they carry
`require_cap_facets=true`.

## Cap-facial Boolean cloud checkpoint (2026-08-31)

The stronger encoding has now run in an isolated Linux an independent reviewer Cloud checkout at
source commit `5048157a686fe2422582b5f041f0f1c1ed1ccab5` (tree
`7159563eddfe7036bb3aacb0600076bbc19fd825`). The complete, checksummed run
bundle is
[`results/archives/bool_cap_motif_5048157a686f.tar.gz`](results/logs/bool_cap_motif_5048157a686f/),
with the unpacked manifest and command log under
[`results/logs/bool_cap_motif_5048157a686f/`](results/logs/bool_cap_motif_5048157a686f/).

Both mandatory positive controls passed: order 20 was SAT/CANDIDATE and passed
both independent APG verifiers; the dynamically capped A21 control was
SAT/CANDIDATE, then postprocessed to CERTIFIED, including cap opening, all nine
closures, and its `t=0` and `r` gates. The local checkpoint independently
rechecked the SHA-256 manifest and archive, replayed both order-20 verifiers,
replayed both verifiers for the A21 candidate and all nine closures, and
reproduced the A21 postprocessor result from the raw Boolean record.

The three serial one-thread, seed-zero, 600-second target profiles `(28,12)`,
`(29,12)`, and `(31,12)` each returned Z3 `unknown` and the recorded
disposition `INCOMPLETE`; none produced a candidate eligible for postprocessing.
Consequently there is no strict-block certificate, target certificate, promotion
handoff, or nonexistence assertion from this run. It establishes a
replayable, cloud-validated strength checkpoint for the cap-facial lane, not a
new APG construction: target coverage remains **0/26 independently verified**.

The review panel, source dispositions, and local gate are retained in
`results/logs/cap_facial_interface_review_20260831.md`
and the Cloud report gives the exact raw hashes and resource records in
[`results/logs/bool_cap_motif_5048157a686f/RUN_REPORT.md`](results/logs/bool_cap_motif_5048157a686f/RUN_REPORT.md).

## Complete socket-normal-form Boolean cloud checkpoint (2026-08-31)

An independent, proof-backed exact encoding has also now run in isolated an independent reviewer
Cloud.  It fixes both socket normal forms (all twelve socket dart matches, their
two length-six face cycles, and the twelve opposite pentagon darts), rather
than searching the marked cap fans used by the preceding checkpoint.  The
worker started clean on commit `1c406a43e8e201d2f000b0210ecf70e8e7be9455`
and tree `4ff0fb7c7775bf3647a7c4ec08364c5f053737f0`, passed `git fsck`, and
ran its targets strictly serially, with one Z3 thread and seed zero.  Its full
artifact archive is
[`results/bool_socket_normal_form_1c406a43e8e2.tar.gz`](results/logs/bool_socket_normal_form_1c406a43e8e2/)
(SHA-256 `b7c48dab154eec55ea8351f51ad352c376c1ff85effa716d26071304b391d0ad`)
and its manifest is under
[`results/logs/bool_socket_normal_form_1c406a43e8e2/`](results/logs/bool_socket_normal_form_1c406a43e8e2/).

The order-20 closed control was SAT/CANDIDATE and passed both independent APG
verifiers.  The canonicalized A21 socket-normal-form control was SAT/CANDIDATE
and postprocessed to `CERTIFIED`: its opened candidate passed strict block
validation, all nine closed A21 closures passed both independent APG verifiers,
and its `t=0` and `r=10` gates passed.  Local intake rechecked the complete
manifest in its recorded relative-path directory, tested the archive, replayed
both order-20 verifiers and all eighteen A21 closure verifier invocations, and
re-ran the A21 postprocessor with matching candidate and closure hashes.  The
opened A21 candidate is intentionally not fed directly to closed-APG verifiers:
its degree-two socket whites make it a strict block, while the nine capped
closures are the APG certificates.

The three required portable profiles `(28,12)`, `(29,12)`, and `(31,12)` each
ran for 642--649 solver seconds, exited normally, and returned Z3 `unknown`
with disposition `INCOMPLETE`; no raw candidate existed, so no target
postprocessor, strict block certificate, or promotion handoff ran.  This is a
second independent cloud-validated negative-search *checkpoint*, not a proof
of nonexistence and not a construction.  The all-26 target coverage remains
**0/26 independently verified**.  The exact dispositions and resource records
are in
[`results/logs/bool_socket_normal_form_1c406a43e8e2/RUN_REPORT.md`](results/logs/bool_socket_normal_form_1c406a43e8e2/RUN_REPORT.md).

## Direct-open Boolean provenance checkpoint (2026-08-31)

The residual-`H55` `r=13` lane emits strict Section-8 blocks directly, so it
cannot use the closed-cap promotion handoff. `direct_block_handoff_gate.py`
now defines the separate fail-closed boundary for a future direct `(31,13)`
candidate. Its input binds the exact source commit and tree plus only the raw
Boolean and postprocess records. The gate canonicalizes and validates the raw
strict block, requires the `r=13` 2-regular (but non-`C4`) Boolean marker,
checks the raw/postprocess digest binding and all `t=0`/`r` gates, recreates
the complete 3x3 closure grid, compares every recreated closure digest with
the postprocessor, and runs both independent APG verifiers freshly on all nine
closures. It then writes a portable strict-block ledger with no target or
nonexistence claim.

The dynamic A21 direct-block control, source/tree and path rejection controls,
raw/postprocess tampering controls, and a cap-provenance spoof control pass.
`CLOUD_BOOL_R13_RESIDUAL_H55_JOB.md` conditionally invokes this gate only after
a certified order-31 postprocessor result. The existing all-26 composer still
accepts only the distinct closed-cap ledger, so this is a source-certificate
boundary and a prepared next construction path—not a target promotion or a
construction result. Target coverage remains **0/26 independently verified**.
The requested fresh Terra/max read-only review was blocked before a verdict by
its read-only macOS temporary-cache failure; this is recorded, without treating
it as approval, in
`results/logs/direct_open_handoff_review_20260831.md`.

## Residual-`H55` `r=12` Cloud checkpoint (2026-08-31)

The source-pinned residual-`H55 = C4` Boolean batch is complete on an isolated
Linux worker. Its source commit was
`baa349135fc965f150460994bbb48ab8bec4707c` with tree
`57858f688bd168e0cb0476ff12fee7a6ec0bc85b`; both were independently resolved
locally. The retained archive
[`results/bool_r12_residual_h55_baa349135fc9.tar.gz`](results/logs/bool_r12_residual_h55_baa349135fc9/)
is readable, and the sidecar manifest validates all 51 retained artifacts.

The order-20 control passed both independent APG verifiers. The canonical A21
direct-block control postprocessed to `CERTIFIED`; local replay reproduced its
postprocess gates and byte-identical candidate plus all nine closure
certificates, and freshly reran both verifiers for every closure. The three
strictly serial one-thread target profiles `(28,12)`, `(29,12)`, and `(31,12)`
each ran for the configured 600-second timeout and returned Z3 `unknown` with
raw disposition `INCOMPLETE`. Their records carry the required canonical,
portable `t=0`, and residual-`C4` marker. No target emitted a candidate, so no
block postprocessor, source handoff, promotion, target certificate, or
nonexistence assertion exists. The executable local disposition is
[`r12_intake_audit.json`](results/logs/bool_r12_residual_h55_baa349135fc9/r12_intake_audit.json):
`VALIDATED_INCOMPLETE`, `block_certificate_count=0`, and
`nonexistence_claimed=false`.

## Solver-core diagnosis and route pricing (2026-08-31)

Nine target-profile runs across three successive structural strengthenings all
returned Z3 `unknown` / `INCOMPLETE` at their 600-649 second bounds, with the
controls passing each time. Identical dispositions at identical bounds across
three *different* encodings point at what the three share rather than at the
structure any one of them added.

Measured locally on an isolated Linux worker: they share an arithmetic core.
`exact_map_bool_sat.py` is Boolean only in its matching layer; `phi`,
`face_length`, the `phi_powers` chain and the `vertex_at` rows are `z3.Int`
values defined by `Sum(If(...))` over every dart. At block `(31,12)` with
`t=0` that is 784 integer variables, 51 056 assertions and 344 442 distinct AST
nodes, and 25.9 seconds of the budget spent building the formula before the
search starts. The full table is in
[`SOLVER_CORE_DIAGNOSIS.md`](SOLVER_CORE_DIAGNOSIS.md); it replays with
`python3 measure_encoding_cost.py` and its record is
[`results/logs/solver_core_diagnosis_20260831.json`](results/logs/solver_core_diagnosis_20260831.json).

Two consequences, neither of which is a construction or a nonexistence claim:

- The recorded `(28,12)`, `(29,12)` and `(31,12)` timeouts are evidence about
  the encoding that ran them, not about those profiles. Re-running the same
  lane with a larger budget is not indicated.
- `exact_map_cnf.py` states the closed-map lane with no arithmetic at all:
  `phi(d) = t` *is* the matching literal `m[d, sigma(t)]`, faces are Boolean
  labels, and the single-orbit-per-face-class property is derived from the
  exclusion of loops and parallel edges rather than bought with a power chain.
  It also imposes the forced edge-class counts `e34`, `e35`, `e45`, which the
  profile determines by a nonsingular 3x3 system. Its predicted-object gate
  runs across parameters, not at one point: all 23 published `(3,4,5)`-APGs
  held here -- the four known fixtures at orders 17, 20 and 42 plus the 19
  frozen census sources at orders 26-36, spanning `r = 8` to `r = 14` -- are
  models of the encoding after re-embedding. The label normal form keeps them,
  and the four fixtures round-trip through both independent verifiers.

  The two-swap mutation control is recorded as it came out rather than as a
  pass: all 205 rewirings of the order-20 map are rejected by both verifiers
  and by the encoding, so the control agreed only on the negative side and its
  load-bearing branch -- a valid APG the encoding wrongly rejects -- never
  executed. The 23-fixture gate carries the positive direction.

The CNF lane is a **checkpoint, not a replacement**: CaDiCaL found no witness
at `(17,8)`, `(18,8)`, `(19,9)` or `(20,9)` inside 240 seconds each, at orders
where witnesses are published and the encoding provably admits them. The
binding constraint is the `n3! n4! n5!` vertex-relabelling symmetry, and the
partial lex-leader break written for it is **off by default and ungated** --
an earlier draft of it was not a valid lex-leader condition, and the corrected
version has no control exhibiting a published APG relabelled to satisfy it.
`unsat` from this encoding is recorded as `ENCODING_UNSAT` and is a statement
about the encoding at that profile.

The exhaustive-generation route is now priced and closed. The 2015 authors'
generator (`github.com/nvcleemp/alternating`, a plantri 4.5 plugin) builds and
runs here; with an exact `{3,4,5}` degree-excess pruning bound added it clears
order 12 in 1.58 s and order 13 in 21.44 s, and exceeds 600 s at order 14.
plantri's `-p` mode enumerates triangulations and deletes edges, so its base
cost grows like `(256/27)^n` and the pruning acts only below that enumeration.
Order 46 is some `10^32` times the order-13 cost: unreachable for a structural
reason rather than a compute budget. The order-17 positive control did not
finish, so that lane carries no passing positive control and its counts are not
census results.

Target coverage remains **0/26 independently verified**.

## Pure-CNF lane: first witness, gated symmetry break, block lane encodable (2026-08-31)

Follow-up to the solver-core diagnosis above. Four changes, all gated, none of
them a target construction. Target coverage remains **0/26 independently
verified**.

**1. Three forced constraints turned the lane from silent to productive.**
The three faces at a degree-3 vertex have sizes exactly `{3,4,5}` (distinct
faces, pairwise adjacent, so pairwise different sizes); a triangular face has
vertex degrees exactly `{3,4,5}` (its vertices are pairwise adjacent, so
alternation makes their degrees differ); and the corner counts `c[3][k] = r`
and `c[L][3] = r` follow. Each is implied by the per-edge constraints and each
is decisive. Order 17 went from `INCOMPLETE` at 240 s to **CERTIFIED in 4.2 s**
with a rotation system that passes both independent verifiers -- the first
witness this lane has emitted at any order.

**2. The vertex lex-leader break is now gated, and is a measured net loss.**
`lex_leader_relabelling` sorts a map by adjacent same-degree transpositions;
each swap strictly increases the flattened adjacency matrix, so it terminates,
and it terminates at a labelling the encoder accepts. All 23 published APGs
reach such a representative, still pass both verifiers there, and are still
models under the break. That is the executable control the break was missing.
It nonetheless stays **off by default**: on satisfiable instances it costs
more than it saves (order 17: 99 s with it against 4.2 s without), which is the
usual asymmetry between refutation and finding one witness.

**3. The block lane is encodable in CNF for the first time.** A size-six label
class could be two triangular orbits instead of one hexagon, so hexagonal darts
now carry a position in `Z/6` with `pos(phi(d)) = pos(d) + 1`; an orbit of
length `L` returning to its start forces `L = 0 mod 6`, so `L >= 6`, and a
six-dart class containing it *is* that orbit. The forced edge-class counts
generalise with it: with socket whites adjacent only to pentagon corners the
four unknowns `e25, e34, e35, e45` are determined, and at block `(21,10)` they
are `12, 6, 12, 6`. Gate: the published strict blocks **A21, B22, C23 and D24
are all models**. The profiles that have been timing out -- `(28,12)`,
`(29,12)`, `(31,12)` -- are therefore now expressible in CNF. No block search
has been run on them; this is an encoding result, not a search result.

**4. The mutation control now bites.** Two-swap rewirings were the wrong move:
all 205 are invalid, so the control only agreed on the negative side and its
load-bearing branch never fired. Three-edge deranged rematchings do reach other
genuine APGs; twelve of them pass both independent verifiers, and every one is
still a model, and still a model under the vertex normal form after
relabelling.

**Where the frontier sits.** A ladder at 240 s per profile, up to four `r` per
order, certifies order 17 in 4.2 s and finds **no witness at any of orders 20,
22, 24, 26, 28, 30, 33, 36**; the run was stopped by its outer wall during
order 40. The record is
[`results/logs/cnf_scaling_ladder_20260831.json`](results/logs/cnf_scaling_ladder_20260831.json).

The wall is sharp rather than gradual, and it is not that witnesses are
scarce: order 26 at `r = 11` is a profile where the frozen census holds a
published witness, and 240 s does not find one. Formula size is not the
constraint -- closed `(46,18)`, the smallest target profile, is 775 102
variables and 3 664 506 clauses built in 6.3 s. The constraint is the
`n3! n4! n5!` relabelling orbit, which grows from `1.2 x 10^8` at order 17 to
`3.1 x 10^10` at order 20.

One asymmetry worth carrying forward: `ENCODING_UNSAT` is decided at order 30
in 105 s while satisfiable profiles at order 20 are undecided at 240 s. The
refuted profiles are the cheap boundary cases on *either* side of the
undecided interior -- at order 20 both `r = 7` and `r = 10` refute in about
4 s while `r = 8, 9` do not -- so this is not yet evidence that interior
profiles refute, but it is the first measured support for the refutation lane
scaling differently from witness search. (An earlier revision of this section
said the refutations were all at extreme low `r`; `(20,10)` is the
counterexample.)

## Route calibration: quotient route killed, R4 narrowed (2026-09-01)

The external an independent reviewer could not be dispatched -- this session holds
no credentials for it -- so
[`REVIEW.md`](REVIEW.md)
was staged at the time; it has since run, and nothing here counts toward a milestone gate
under the project rules section 9. What was done instead is a local literature and
computation pass over the answerable parts of that brief, recorded in
[`results/logs/route_calibration_20260901.md`](results/logs/route_calibration_20260901.md).

**The symmetric-quotient route is killed by measurement.**
`automorphism_census.py` enumerates the map automorphism group of every
published `(3,4,5)`-APG held here: **21 of 23 are rigid**, the only two with a
nontrivial automorphism are the order-17 maps, and every map at orders 26-42 is
asymmetric. Imposing a `C2` would search a class the record suggests is empty
exactly where witnesses are needed. The corpus is 23 maps, not the 88 House of
Graphs records and not a census, so this is a strong prior rather than a
theorem.

Rigidity also explains the previously unexplained 24x cost of the vertex
lex-leader break on satisfiable instances: with `|Aut| = 1` each isomorphism
class contributes a full `n3! n4! n5!` orbit of labelled solutions, so breaking
the labelling symmetry removes solutions in the same proportion as search
space. Density is unchanged and only overhead remains. Symmetry breaking here
can pay only on the refutation side.

**The canonical-construction route narrows to SAT-modulo-symmetries.**
Brinkmann's homomorphism-principle map generator (arXiv:2408.16512) generates
rotation systems with a prescribed degree sequence at millions per second and
needs no isomorphism rejection on rigid graphs, but its author states it is not
useful for genus 0, and its own embedding count `(1/2) prod (deg(i)-1)!` is
astronomical at the order-46 profile. SMS (Kirchweger-Szeider) is the right
technology, to be prototyped against the measured order-17/order-20 pair before
it is built out.

Two existing positions were independently corroborated. Jooken's 2025
computer-assisted graph theory survey (arXiv:2508.20825) lists alternating plane
graphs among its generators and cites the 2015 paper with no closure of
Conjecture 10.2 -- the prior-art gate is unchanged. And the survey's own worked
example settles a Schmeichel-Hakimi case by generating planar triangulations and
deleting **one** edge, where our targets need `n - 4 = 42`, which is precisely
why the plantri route prices out at `10^32`.

Target coverage remains **0/26 independently verified**.

## An increment-3 periodic strip, verified (2026-09-01)

An independent review leg (one independent reviewer -- **not** another,
which is staged at the time; since run; see
`results/logs/the review record`
for what that does and does not count for) proposed a reduction that makes the
self-composable-strip question finite, and an object satisfying it. The object
is re-derived and re-checked here in
[`periodic_strip.py`](periodic_strip.py), written from the quotient certificate
rather than from the reviewer's code.

**The reduction.** A strip that composes with itself indefinitely is an
infinite periodic alternating map on the cylinder; the translation acts freely,
so the quotient is a map on the **torus** with `c` vertices, `c` being the
increment. The leg reports `c = 1, 2, 4, 5` impossible (the first two by
counting, the others by exhaustive enumeration of 6 912 and 207 360 rotation
systems) and `c = 3` realised uniquely up to relabelling, orientation and
mirror. Only the `c = 3` object is re-verified here.

**Verified locally.** The quotient has `V = 3, E = 6, F = 3`, so
`V - E + F = 0`; degrees and face sizes are exactly `{3,4,5}`; no edge joins
equal degrees, none separates equal face sizes, and no face lies on both sides
of an edge. Lifting 25 periods gives a simple map with 67 complete interior
faces of sizes `23 x 3`, `22 x 4`, `22 x 5`, with **zero** faces outside
`{3,4,5}`, **zero** faces repeating a vertex, **zero** interior edges
separating equal-size faces and **zero** joining equal degrees.

The counting closes exactly: a period adds one vertex and one face of each
size, so `n` rises by 3 and `r` by 1, keeping `v5 = r - 4` and
`v4 = n - 2r + 4` consistent. The degree-5 orbit carries exactly two pentagonal
incidences, so the strip is `t`-neutral and pumping never consumes the
`t <= 4` composition budget.

**It closes no target order.** Using it needs a closed APG containing a
matching seam cycle to cut open and insert periods into, and no such witness is
known. The leg scanned 444 canonical two-sided seam signatures of length
`<= 9`, both mirror forms, against all 23 published APGs held here and found no
match; that negative is the reviewer's measurement and is not re-run here. What the
strip changes is the shape of the remaining problem: three seam-bearing
witnesses below order 46, one per residue class mod 3, would close **all 26
targets** and reprove the paper's Theorem 8.1 -- instead of 26 searches, or
even three block searches.

## Block lane: socket interface ported, and it hits the same wall (2026-09-01)

`exact_map_cnf.py` now carries the socket interface and the `t = 0` branch,
ported from `exact_map_bool_sat` and keeping its correction that a degree-2
white lies on exactly *one* hexagon. Gates: all four published strict blocks
A21-D24 are models with the socket interface and with `t = 0` (so all four are
portable), and every three-edge deranged rematching of A21 that the alternation
rules admit as an encoding is rejected -- 84 of 400 sampled were encodable and
all 84 were refused, while A21 itself passes.

The search itself found nothing. All four open profiles were run under
[`block_search.py`](block_search.py) at a 1 150 s hard wall each, with every
raw model destined for `blocks.validate_block` before it could be called a
candidate:

| profile | clauses | raw models | disposition |
| --- | --- | --- | --- |
| `(25,11)`, `t=0` | 435 982 | **0** | `INCOMPLETE` |
| `(28,12)`, `t=0` | 631 648 | **0** | `INCOMPLETE` |
| `(29,12)`, `t=0` | 705 569 | **0** | `INCOMPLETE` |
| `(31,12)`, `t=0` | 873 391 | **0** | `INCOMPLETE` |

Record: [`results/logs/block_search_20260901.json`](results/logs/block_search_20260901.json).

Not one profile returned a single model before its wall, so the candidate
validator never ran and no rejection reasons were collected. The block lane
hits the same labelled-search wall as the closed lane. **This says nothing
about whether a block exists at these profiles** -- it is a statement about the
wall clock, and it is what the solver-core diagnosis predicts.

Target coverage remains **0/26 independently verified**.

## The cap interface: constant in the number of periods (2026-09-01)

[`strip_patch.py`](strip_patch.py) cuts a finite cylinder out of the verified
strip and reports exactly what a cap would have to supply. The measurement
that matters:

| periods `m` | vertices | interior | boundary vertices | edges owed to caps |
| --- | --- | --- | --- | --- |
| 4 | 12 | 5 | **7** | **14** |
| 6 | 18 | 11 | **7** | **14** |
| 10 | 30 | 23 | **7** | **14** |
| 20 | 60 | 53 | **7** | **14** |

**The interface does not grow with `m`.** A straight cut leaves the same seven
deficient vertices owing the same fourteen edges however long the cylinder is,
seven at each end. That is what separates this route from every search tried so
far: the cap problem is a fixed, small problem, and solving it once yields a
closed APG for *every* `m`, not one witness.

The profile arithmetic closes with no constraint on `m`. If the two caps
contribute `a3, a4, a5` vertices of each degree then `v_d = a_d + m`, so
`v3 - v5 = 4` forces

```text
a3 - a5 = 4
```

and `v4 = n - 2r + 4` then follows automatically -- `cap_arithmetic` asserts
that identity rather than assuming it. The 26 targets split `6 / 10 / 10`
across residues mod 3, so **three cap pairs, one per residue, would close every
open order**; `test_strip_patch.py` checks that cover exactly.

This is an interface derivation, not a construction. No cap is known, a patch
is not an APG, and both verifiers correctly reject one. Coverage remains
**0/26 independently verified**.

## 26/26 target certificates, verified (2026-09-01)

Every open order of Conjecture 10.2 -- `46-56, 67-74, 88-92, 109, 110` -- now
has an explicit plane rotation system in
[`certificates/targets/`](certificates/targets/), with a SHA-256 manifest.

**Construction.** Cap a periodic strip. The `c = 3` alternating torus quotient
verified in [`periodic_strip.py`](periodic_strip.py) admits many unrollings,
not one; the primitive class is free. The `(1,0)` unrolling this repository had
encoded is **uncappable as far as the committed evidence goes** -- an
exhaustive alternating disk-filling search closes all 16 short-meridian
interfaces with zero solutions (the searcher is archived and ungated, caps at
5,000,000 nodes and reports `NOT CONCLUSIVE` on abort, and no terminal run
report is committed: strong negative result, not a theorem), which also
explains retroactively why no published APG contains such a seam. A `(2,3)`
unrolling of the *same* quotient is cappable at both ends, and
`capM + t periods + capP` reaches every target order. (The `t` range was
first recorded here as 2 to 22; measured off the certificates it is 5-19,
2-23 and 5-26 by residue class -- see the decomposition section below.)

**Verification, four independent ways.** Discovery was an independent review
leg's (`results/logs/the review record`);
correctness rests only on checks run here.

1. `verify.py`, fresh process, `--expect-order`: **26/26**.
2. `verify_darts.py`, fresh process: **26/26**. The two are genuinely
   independent -- neither imports the other or any shared module, both import
   stdlib only, and they trace faces in opposite dart-permutation directions.
3. A third implementation, the `_fast_apg_filter` written earlier for the
   mutation control and never derived from either verifier: **26/26**.
4. Profile identities recomputed from the rotation systems rather than read
   from any verifier's output: `v3 - v5 = 4`, `v4 = n - 2r + 4`, `E = 2n - 2`,
   `F = n`, `V - E + F = 2` at every order.

All 26 are distinct by SHA-256 and by graph signature.
[`test_target_certificates.py`](test_target_certificates.py) freezes this as 115
gates, including a **negative control**: transposing two neighbours in one
rotation -- preserving the graph and every degree, changing only the embedding
-- is rejected, so the verifiers are testing facial structure and not degree
sequences.

**What this is not, yet.** It is not a novelty claim. the project rule on prior art
requires a fresh prior-art poll, and preferably author / House-of-Graphs
reconciliation, immediately before any public claim; the standing audit is
dated 2026-08-30. The residual technical risks are pre-existing and
program-level: a fault shared by both verifiers, or a mismatch between the
certificate contract and Definition 2.1 -- the latter narrowed by the theorem
that minimum degree 3 with all faces at most 5 forces 2-connectivity and simple
facial walks, subject to confirming the paper's face-size convention against a
PDF no worker here can fetch.

**Target coverage: 26/26 accepted by both independent verifiers**, pending the
prior-art re-poll.

## Prior-art gate closed; Definition 2.1 resolved (2026-09-01)

The operator dispatched [`PRIOR_ART.md`](PRIOR_ART.md)
verbatim in an independent reviewer with browsing, reaching the five primary-source domains this
worker's network access proxy refuses. Full answer archived at
[`results/logs/prior_art_poll_20260901.md`](results/logs/prior_art_poll_20260901.md);
reconciliation in [`PRIOR_ART.md`](PRIOR_ART.md).

**Verdict, quoted:** "none of the 26 exceptional orders has a publicly verified
settlement that I could find." The order list returned is character-for-character
the target set `T`.

**It did not fall into the trap.** The poll states explicitly that Althofer's
"for all numbers of vertices from 19 on" is the *general* APG class and does not
settle the `(3,4,5)` restriction. That conflation is the exact failure Section 0
exists to prevent, and it did not occur.

**Two legs, now cross-checked.** This poll independently re-derived the
2026-08-29/30 findings -- Althofer's page last updated 2014-12-01, the generator
repository's last `master` commit 2013-11-07 with no graph deposit, the House of
Graphs census stopping at 19 with counts `2, 0, 5`, and forward citations
limited to Wen-Gabrys-Musial 2023 and Jooken 2025, neither closing anything. It
went further on the author pages; the earlier audits went further on the
citation indexes (Google Scholar, Crossref, OpenAlex, Semantic Scholar were all
blocked in the poll's browser) and on the House of Graphs enquiry API. Between
them the coverage is complete but for the items listed below.

**One re-verification gap, not a conflict.** The 2026-08-29 audit read
`althofer.de/apg/table.html`; the poll could not fetch it. One leg checked and
found nothing at a target order, the other could not re-check. Nothing asserts a
target-order entry exists.

**A near-miss worth recording.** House of Graphs lists rows at orders 48, 50, 51
and 55 -- four numbers inside `T`. They are **weak** alternating plane graphs
with degrees 2 and `k`; degree 2 is forbidden by Definition 2.1 outright. Anyone
re-running this gate will meet them.

**Definition 2.1 risk retired, and unconditionally.** The poll reports the paper
contains **no explicit statement** of the boundary-walk convention for face
size. That no longer matters. Both verifiers compute face size as facial-walk
length ([`verify.py:203`](verify.py), [`verify_darts.py:189`](verify_darts.py))
*and* reject any face repeating a vertex ([`verify.py:208`](verify.py),
[`verify_darts.py:193`](verify_darts.py)), so every face of every certificate is
a simple cycle -- on which walk length, distinct edges, distinct vertices and
"sides" are the same integer. The certificates satisfy Definition 2.1 under
every reading of "size". The extra condition can only shrink the class, which is
safe for an existence claim; the convention would only bite on a nonexistence
claim, and none is made at any order in `T`. This supersedes the hedge at the
end of the previous section, which made the point conditional on a PDF nobody
here could fetch.

**What is still outstanding.** The poll's model identifier and mode
(the recorded tier) were not pasted back, so cite it as "an operator-dispatched
browsing poll, 2026-08-31" rather than as a `Pro` leg until they arrive. The
House of Graphs **user-upload** database was not exhaustively searched. No
author correspondence has been sent. The Section 9 milestone reviews -- HEAVY
`code-review-panel` and a professor-mode an independent reviewer review of the *mathematics*, as
distinct from this record poll -- had not run at the time of writing.

**Target coverage: 26/26 accepted by both independent verifiers, with the
public-record gate discharged on the evidence.**

## Session archive and gate re-run (2026-09-01)

The full gate suite was re-run after the prior-art reconciliation:
**110 passed in 639.82 s** (`test_target_certificates.py`,
`test_strip_patch.py`, `test_exact_map_cnf.py`). Documentation-only change; no
code was touched.

The session that produced the certificates is archived as a decision record at
`results/logs/session_20260901_context_archive.md`
— start and end state, why each route was taken or dropped with a pointer to
where each result lives, a **correction ledger naming what caught each of ten
errors**, which review legs were dispatched to whom, and the open threads. It
restates no load-bearing number; where it and a primary file disagree, the
primary file wins.

Two things in it are worth surfacing here because they generalise beyond this
target. **Three different structural encodings failing identically is evidence
about the shared core, not about the encodings** — measuring the formula before
adding to it was the highest-value hour of the session. And **a search that
cannot find a witness you already hold is diagnostic**: order 26 at `r = 11` is
the fact that ended the direct-search route and sent the work to the quotient
reduction.

## The period/cap decomposition, read off the certificates (2026-09-01)

[`pumping_family.py`](pumping_family.py) tests the structure claim -- each
target is `capM + t periods + capP` -- against the finished certificates, using
nothing but the committed rotation systems: no generator, no cap file, no strip
code. Each vertex gets a local signature (its degree plus the cyclic sequence of
its neighbours' degrees, canonical under rotation and reflection); the degree-5
period signature `(3,4,3,4,4)` counts periods, and the *cap remainder* is what
is left after removing `t` copies of the three period signatures.

The claim survives, in a sharper form than it was stated:

| residue mod 3 | cap remainder | orders | `t` |
| --- | --- | --- | --- |
| 0 | **33 vertices**, one class | 48, 51, 54, 69, 72, 90 | 5-19 |
| 1 | **40 vertices**, two classes | 46 alone; 49-109 | 2; 3-23 |
| 2 | **32 vertices**, one class | 47-110 | 5-26 |

`n = 3t + cap` holds exactly at all 26 orders and `t` rises by exactly `dn/3`
within each class, so residues 0 and 2 are each a single cap pair pumped, and
the "three cap pairs, one per residue" description is confirmed from the
witnesses rather than from the construction.

**Order 46 is a boundary case, and it is the interesting one.** It is the
`t = 2` member of residue 1, its cap remainder has the same *size* as the other
nine, and it differs from them in exactly three degree-4 signature counts:
`(3,5,3,5)` 8 vs 9, `(3,5,5,5)` 6 vs 4, `(5,5,5,5)` 0 vs 1. At the minimum
period count the two caps are close enough to change each other's local
structure.

That is a constraint on the pumping lemma nobody had written down. The lemma
"cap + t periods + cap is a (3,4,5)-APG for all t >= t0" cannot be proved from
an interface argument alone at `t = 2`, because there the interface is not the
only thing the two caps see. Either the lemma starts at `t >= 3` -- leaving
order 46 as a separate verified instance -- or its proof has to handle cap-cap
contact. Nothing here is evidence against order 46: both verifiers accept it.
It says where the general proof has to do work.

Two corrections fall out. The measured `t` ranges are 5-19, 2-23 and 5-26, not
the "t from 2 to 22" recorded above; and the period count cannot be read from
the degree-3 or degree-4 period signatures, which also occur inside caps -- only
the degree-5 one is exclusive.

[`test_pumping_family.py`](test_pumping_family.py): 11 gates, including the
`t = 2` split pinned exactly and a negative control requiring the decomposition
to change under a single re-embedding transposition.

## Milestone panel: one CRITICAL, two HIGHs, and what they cost (2026-09-01)

The §13 reviews ran. Full record and dispositions in
[`REVIEW.md`](REVIEW.md); the three completed archives are
under `results/logs/`. The mathematics came through untouched — two legs
re-derived all 26 certificates with their own reconstructions, one of them an
exact-rational Tutte embedding that certified zero edge crossings, i.e.
planarity without Euler's formula. What did not come through was several of the
claims made *about* that mathematics.

**The prior-art gate is open, not closed.** The poll that closed it came back
without the model identifier and the recorded tier, and its own dispatch prompt says
such a run "does not count toward the gate". Three documents said it was closed
anyway. The evidence stands; the status does not, and the PR is back in draft.

**The definition-of-done gate could not detect the deletion of any APG
condition.** A leg removed each condition from each verifier in turn — the
alternation gates, Euler, connectivity, loops, parallel edges — and the gate
stayed green in all thirteen cases, because its only negative control is a
rotation transposition and Euler alone rejects that.
[`verifier_mutations.py`](verifier_mutations.py) now measures this by mutating
every `_fail` site and running a corpus of broken certificates through each
mutant; [`test_verifier_mutations.py`](test_verifier_mutations.py) requires
every clause of Definition 2.1/3.1 to have a control and freezes the sites that
still lack one.

**The two verifiers are not independent evidence, and this file said they
were.** `verify.py` turns to the predecessor dart, `verify_darts.py` to the
successor; the face partitions are identical up to reversing every face, so
they cannot disagree on any input. Verified here at all 26 orders and now
asserted as a gate. Three implementations catch three coding errors; none
catches a shared misreading of Definition 2.1.

**"Theorem 3.2" is unsourced.** Both verifiers and both search encodings impose
`v_i = f_i`, `v5 = v3-4`, `E = 2n-2`, `F = n`, citing a theorem with no quote,
page or proof anywhere in this repository. A leg derived `v3 = f3` and
`(v3-v5)+(f3-f5) = 8` and could not derive `v5 = f5`. The risk is over-strict,
so the witnesses are safe — but every "0 models found" in this repository is a
statement about a possibly proper subclass of Definition 3.1. The mutation
harness sharpens it: those six checks cannot be given a negative control unless
Theorem 3.2 is false.

**Narrowed the same day.** [`THEOREM_3_2_STATUS.md`](THEOREM_3_2_STATUS.md)
proves `v3 = f3` and then derives, from counting and Euler alone,
`v4 - f4 = 5k`, `f5 - v5 = 4k` and `v5 = v3 - 4 - 2k` for one integer `k`. The
whole imposed block is exactly `k = 0`, so what is unsourced is a single
integer, not six identities -- and `v5 ≡ v3 (mod 2)` holds unconditionally,
which already refutes the panel's candidate counterexample `v5 = r-3, f5 = r-5`
(it needs `k = -1/2`). All 30 committed objects have `k = 0`;
[`test_profile_identities.py`](test_profile_identities.py) checks the
derivation and the assumption separately, and labels the second as an
assumption. **Still open, still one page of the PDF.**

Also corrected: the third checker is now a real gate rather than a claim
([`fast_apg_check.py`](fast_apg_check.py), 26/26 with its own tamper control);
"provably uncappable" is now "uncappable as far as the committed evidence
goes"; the manifest test requires exactly the 26 target names; the cloud briefs
carry an executable macOS abort again rather than prose; and the target-set
test reads the frozen statement out of `PRIOR_ART.md` instead of restating its
own literal.

## The independent review: two things we wrote down are false (2026-09-01)

Verdict: **major revision, bordering on rejection of the proof architecture —
and the conjecture is settled anyway.** Both halves matter, and they are
separable. Archive: the review record;
dispositions in [`REVIEW.md`](REVIEW.md).

**Settled.** The leg confirms that witnesses at the 26 orders close the
conjecture: `[20,45] ∪ [46,56] ∪ [57,66] ∪ [67,74] ∪ [75,87] ∪ [88,92] ∪
[93,108] ∪ {109,110} ∪ [111,∞) = [20,∞)`, no gap, and the provenance of a
witness is irrelevant once the certificate is valid. It reconstructed order 46
itself and found a simple connected spherical `(3,4,5)`-APG — the fourth
independent confirmation, from a fourth toolchain.

**False as written, 1: the reduction.** "A self-composable strip quotients to a
torus" needs an orientation-preserving *cellular* translation. Freeness alone
gives `τ(θ,s) = (-θ, s+1)`, whose quotient is a **Klein bottle**. The converse,
which is the direction actually used, needs `ω` to satisfy the facial cocycle
equations, primitivity of the induced `H_1(T²;Z) → Z`, and a simple lift — an
offset assignment is none of these by itself.

The committed object survives this: [`unrolling_class.py`](unrolling_class.py)
computes all three facial voltage sums as zero and checks that parallel
quotient edges lift to distinct offsets. What was wrong was the argument, not
the `ω`.

**False as written, 2: the coverage arithmetic.** One fixed cap pair gives
`n(t) = A + 3t`, so `t ∈ [2,22]` spans 60 — but `109-46 = 110-47 = 63`. Three
cap pairs with `t = 2..22` cannot cover `T`. This is the same defect the
decomposition section above found empirically hours earlier from the opposite
direction: the measured ranges are 5-19, **2-23**, **5-26**, spans of 63. The
construction is right; the recorded range was wrong.

**The labels name nothing.** `(1,0)` and `(2,3)` are not classes until a
homology basis is fixed. In the normal form `(p, p-q, 0, 0, q, 0)` the
committed `ω` is `(p,q) = (-2,-1)` — while `(1,0)` is `(1,1,0,0,0,0)`, whose
lift has `e0` parallel to `e1` and is therefore not simple. `periodic_strip.py`
calls the committed object "the `(1,0)` unrolling". Until the basis is written
down, **the uncappability claim — which is stated about "the `(1,0)`
unrolling" — is not reproducible**, and neither is the certificates' stated
provenance. [`test_unrolling_class.py`](test_unrolling_class.py) pins all of
this.

**The pumping lemma now has a statement.** A bounded-collar capping lemma:
fixed caps, an integer `q` bounding the collars in which any incidence changes,
every open facial trace paired and completed inside its collar with final
length in `{3,4,5}`, alternation across every seam edge, no loop or parallel
edge — then the composite is a `(3,4,5)`-APG **for all `t ≥ 2q+1`**. The leg's
two countermodels show why the constant interface deficit is not enough: a band
whose longitudinal face grows with `t`, and two strands exchanged each period
so fixed caps work for even `t` and fail for odd `t`. Our own `t = 2` anomaly
at order 46 is exactly `t < 2q+1`.

**And what an uncappability proof needs**: interface completeness up to a
stated equivalence, a finiteness theorem (a fixed boundary admits fillings with
arbitrarily many interior vertices, so a depth bound proves nothing),
exhaustive branching, and every pruning rule proved extension-preserving. The
leg also observes the negative result is logically unnecessary for the
conjecture.

**Novelty**: classical machinery — cyclic covers, voltage graphs, derived
embeddings — with the novelty in the objects. Its phrasing is better than ours:
"standard cyclic-cover machinery applied to obtain new problem-specific APG
constructions and explicit witnesses."

## The gate closes: source read first-party, sweep run from this host (2026-09-01)

The network restriction that shaped every prior-art round here does not
apply on the development machine. All five previously refused domains answer, so
the whole gate was re-run first-party rather than relayed.

**The paper.** Read directly from the UGent deposit
(`sha256 e1c72804…52884cf`). Definition 2.1, Definition 3.1, Theorem 8.1,
Conjecture 10.2 and the open-order sentence are now quoted verbatim in
[`PRIOR_ART.md`](PRIOR_ART.md). The open set is `[46,56] ∪ [67,74] ∪ [88,92] ∪
{109,110}` — character for character the target set.

**Theorem 3.2 is real, and its proof is the step we were missing.** p. 340:
*"If `G` is a (3,4,5)-alternating plane graph, then `v3 = f3`, `v4 = f4` and
`v5 = f5`."* Our own derivation had reached the paper's five-case table exactly
— `k ∈ {-2,-1,0,1,2}` in the parametrisation above — and the paper closes it by
counting (5,5)-combinations two ways to get `a5 - b5 = 2(v5 - f5)` with `a5`,
`b5` non-negative and bounded, which survives only at `k = 0`. So the profile
block both verifiers impose is the paper's theorem, and every "0 models found"
here is about the full class of Definition 3.1.
[`THEOREM_3_2_STATUS.md`](THEOREM_3_2_STATUS.md).

**The sweep.** Althöfer's maintained table parsed by column — 88 rows, orders
4-44, **empty** intersection with the targets, and the numbers that look like
target orders in a flat text scan are its *index* column, which is the §0 trap
met and cleared. DataCite: **0 results** for `"alternating plane graph"`.
Crossref: 1 citing work. OpenAlex: 1. Semantic Scholar: 2, the second being
Jooken's 2025 survey, neither settling an order. `nvcleemp/alternating`: last
pushed 2013-11-07. Author pages: last updated 2014-12-01 and 2013-09-13.

**Not covered, and said plainly.** Google Scholar (bot-gated, queried by no leg
in any round), the House of Graphs user-upload database (its search API returns
`401` without credentials), and author correspondence.

**And the settlement itself is now a gate.**
[`test_conjecture_coverage.py`](test_conjecture_coverage.py) takes the paper's
own stated coverage — heuristic `[20,42]`, Section 8's
`[21,24] ∪ [39,45] ∪ [57,66] ∪ [75,87] ∪ [93,108]`, Theorem 8.1's `n ≥ 111` —
checks that it leaves exactly the 26 orders, that the certificates are exactly
those 26, and that the union is `[20, ∞)` with no gap, with a control that
removing any one certificate reopens its order.

## Which cover class the certificates are actually built from (2026-09-01)

The independent review's objection -- that `(1,0)` and `(2,3)` name nothing without a
homology basis -- is answered by measurement rather than by finding the basis.

Cover classes are invisible at radius 1: `omega` changes which *copy* of a
vertex an edge reaches, never which type, so degrees and neighbour degrees are
identical in every class of the same quotient. What differs is which closed
walks in the quotient lift to cycles. Counting simple cycles of length 3-6
through a vertex reads that difference off directly, and it separates the
candidates cleanly.

[`certificate_unrolling.py`](certificate_unrolling.py) applies it to all 26:

| | `(1, -1)` | `(-2, -1)` |
| --- | --- | --- |
| order 74 | 25 interior vertices | **0** |
| order 92 | 43 | **0** |
| order 110 | 61 | **0** |
| orders 46, 47, 49 (`t` = 2, 5, 3) | 0 | 0 |

Every certificate of order >= 48 contains vertices with the deep-interior
profile of the **`(1, -1)`** cover, growing linearly with the period count, and
**none** contains a vertex of the `(-2, -1)` cover -- which is the class
`periodic_strip.py` commits and labels "the `(1,0)` unrolling". The three small
orders contain neither, because at `t = 2, 5, 3` a ball of radius 3 still
reaches a cap: the same boundary effect the decomposition section sees at
`t = 2`.

So in the canonical coordinates:

```text
the strip inside the certificates   (p,q) = ( 1, -1)   omega = ( 1,  2, 0,  0, -1,  0)
the strip in periodic_strip.py      (p,q) = (-2, -1)   omega = (-2, -1, 0, -1, -2, -1)
```

The repository's story survives -- one class caps, a different one does not --
and its labels named neither. **The uncappability result concerns `(-2, -1)`**,
and that is now a checkable statement.
[`test_certificate_unrolling.py`](test_certificate_unrolling.py): 55 gates,
including a control that the invariant can tell the two classes apart at all.

## The bounded collar, measured on the certificates (2026-09-01)

[`PUMPING_LEMMA_STATUS.md`](PUMPING_LEMMA_STATUS.md) carries the lemma the
independent review wrote and what is still missing from it. The measurement:
[`strip_alignment.py`](strip_alignment.py) grows a map isomorphism from the
`(1,-1)` cover into each certificate, then prunes it to the part where every
cover edge is a certificate edge, so "strip image" means what it says. What is
left over is constant inside each residue class — **27** at every residue-0
order, **42** at residue 1 from order 67, **29** at residue 2 from order 53 —
and `n = 3t + complement` holds exactly. Every additional period is absorbed by
the strip; the caps do not move.

That is hypothesis 3 of the lemma, the bounded collar, measured on the finished
objects instead of inferred from a cut of the strip. Below each threshold the
complement is smaller and irregular, because the strip is too short for the
alignment to reach a deep interior: `t = 2` at order 46 again, from a third
direction.

Still missing, and named in the status file: the caps as explicit patches with
boundary words, an implementation of the splice (the certificates' `ω` has an
edge of offset 2, so the interface spans two periods), and the value of `q`.
[`test_strip_alignment.py`](test_strip_alignment.py): 50 gates, including a
control that the alignment really is a map isomorphism onto its image and a
note that alignment *size* is a weak class discriminator — the cycle profile is
the sharp one.

## Uncappability: the specification, and one route closed (2026-09-01)

[`UNCAPPABILITY_SPEC.md`](UNCAPPABILITY_SPEC.md) writes down what the claim
would need — interface completeness, finiteness, complete branching,
extension-preserving pruning — and settles one of them negatively.

**The easy finiteness route does not exist.** If every vertex type admissible in
a `(3,4,5)`-APG were positively curved, Gauss-Bonnet would bound a disk cap's
interior and a depth-limited search would be a proof.
[`curvature.py`](curvature.py) enumerates all **54** admissible types:
**36 are negatively curved**, **none is flat**, and the range is `-4/15` to
`+17/60`. A cap can absorb unbounded negative curvature, so requirement 2 must
be met by boundary-state saturation or a checkable UNSAT certificate. Anyone
re-running the search with a larger node cap should read that first.

**What Gauss-Bonnet does give**: `Σ k(v) = 2` with every term `≤ 17/60` forces
at least 8 positively curved vertices in any `(3,4,5)`-APG. Both hold at all 26
certificates in exact rational arithmetic, computed from the rotation system
with no code shared with either verifier — an independent structural check
falling out of the analysis.

**And the claim is about a different object than it names.** The class it
concerns is `(-2,-1)`; a rewrite has to re-run the search against that, since
"the `(1,0)` unrolling" names neither it nor the certificates' class.
