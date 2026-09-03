# CLOUD JOB - Boolean exact-map pilot

This is a bounded positive-search pilot for the 26 unresolved orders.  Run it
only in a user-launched isolated Linux cloud session from the exact Git bundle
attached to the task.  The development machine is for editing and replay,
not solver execution.

## Step 0: source and environment gate

Before reading a repository file, installing a solver, or running tests, retain
`python3 --version`, `pwd`, and `git status --short --branch`.  Hard-stop if
`pwd` shows a macOS path such as `/Users/...` -- this job must not run on the
development machine -- and on a dirty checkout, a bundle/ref/commit/tree mismatch, failed
`git fsck`, or any revision substituted for the advertised bundle ref.  Record
the bundle SHA-256, exact `HEAD` and tree, Python/Z3 versions, CPU/memory, UTC
start/end, and every command line.

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


## Encoding

Run `exact_map_bool_sat.py`.  Its Boolean variables form a perfect matching of
the fixed dart pool, so every selected edge has unequal endpoint degrees and no
loop.  One-hot target vertices enforce simple adjacency.  The induced
`phi=sigma^{-1}alpha` permutation is represented without nested arrays; dart
face lengths, exact periods, face-size counts, simple facial boundaries, and
opposite-face inequalities are all checked in the model.  The block lane also
forces the six degree-2 whites onto the two length-6 sockets, alternates each
socket, and requires the opposite face of every socket edge to be a pentagon.

Connectivity is intentionally omitted as a positive-search over-approximation;
the committed postprocessor and both independent verifiers remain mandatory.
No `unsat`, `unknown`, timeout, or absent model is a nonexistence claim.

## Known-map encoding gate

Before target shards, pin the Boolean matching to the published order-20
certificate and run:

```sh
python3 exact_map_bool_sat.py \
  --known-certificate certificates/known/order20.json \
  --timeout-s 120 --threads 1 \
  --output results/logs/bool_known_order20.json
```

The result must be `CANDIDATE`/`sat`; independently run both verifiers on the
published certificate.  A failed or non-sat known-map gate stops the job before
any target computation.

The closed control does not exercise the degree-2 socket clauses, so it must
be followed by a pinned strict-block control.  This must be `CANDIDATE`/`sat`,
then pass the normal strict validator, all nine cap-hub closures, both
independent verifiers, and the embedded structural audit before target shards:

```sh
python3 exact_map_bool_sat.py \
  --known-block results/blocks/A21.json \
  --require-t0 --timeout-s 120 --threads 1 \
  --output results/logs/bool_known_A21_block.json
python3 exact_map_postprocess.py \
  results/logs/bool_known_A21_block.json \
  --expected-order 21 \
  --expected-block-t 0 \
  --output results/logs/bool_known_A21_block_postprocess.json
```

On any non-sat or non-`CERTIFIED` strict-block control, stop before target
shards.  This detects an encoding that accepts closed APGs while inadvertently
excluding every valid two-hexagon opening.

## Bounded target shards

After the known-map gate, run exactly these six one-thread, seed-0 commands
**strictly serially**.  Wait for each command's shell exit, raw JSON (if any),
and any required candidate postprocessing before starting the next command.
`--threads 1` limits Z3's internal worker count; it does not make several
Python/Z3 processes safe to run at once under the cloud memory limit.  Do not
background a command or use a parallel runner.  If a process is killed or
writes no raw JSON, retain its stdout/stderr and record `INCOMPLETE`; do not
retry that profile inside this job.

`SECTION8_PORT_THEOREM.md` proves that the former `(25,10)` shard is
inconsistent with the two strict port cycles, so it is replaced by the only
finite-use order-25 branch `(25,11)`.  It is deliberately *not* passed
`--require-t0`: a valid finite-use candidate must instead retain its audited
`t=1` value and later pass the finite composition budget.

The remaining five shards are explicitly portable `t=0` branches.  The
Boolean constraint requires every degree-5 vertex to have exactly two
pentagonal incidences; this is a positive-search restriction for reusable
blocks, never an absence claim about other strict profiles.  Together,
`(28,12)`, `(29,12)`, and `(31,12)` are the primary all-target covering triple;
`(27,12)` and `(34,13)` are independent structural/coverage hedges.
`block_arithmetic.boolean_primary_t0_target_representations()` freezes the
conditional order-and-`t` arithmetic for that triple; it becomes usable only
after all corresponding positive certificates pass this job's gates.

```sh
python3 exact_map_bool_sat.py \
  --lane block --block-order 25 --r 11 --timeout-s 600 --threads 1 --random-seed 0 \
  --output results/logs/bool_lane_b_25_r11_finite_seed0.json
python3 exact_map_bool_sat.py \
  --lane block --block-order 27 --r 12 --require-t0 --timeout-s 600 --threads 1 --random-seed 0 \
  --output results/logs/bool_lane_b_27_r12_t0_seed0.json
python3 exact_map_bool_sat.py \
  --lane block --block-order 28 --r 12 --require-t0 --timeout-s 600 --threads 1 --random-seed 0 \
  --output results/logs/bool_lane_b_28_r12_t0_seed0.json
python3 exact_map_bool_sat.py \
  --lane block --block-order 29 --r 12 --require-t0 --timeout-s 600 --threads 1 --random-seed 0 \
  --output results/logs/bool_lane_b_29_r12_t0_seed0.json
python3 exact_map_bool_sat.py \
  --lane block --block-order 31 --r 12 --require-t0 --timeout-s 600 --threads 1 --random-seed 0 \
  --output results/logs/bool_lane_b_31_r12_t0_seed0.json
python3 exact_map_bool_sat.py \
  --lane block --block-order 34 --r 13 --require-t0 --timeout-s 600 --threads 1 --random-seed 0 \
  --output results/logs/bool_lane_b_34_r13_t0_seed0.json
```

Keep raw JSON, stdout/stderr, exact commands, and a SHA-256 manifest.  For
every target record with `disposition=CANDIDATE`, run
`exact_map_postprocess.py` in a fresh process.  A closed candidate needs both
`verify.py` and `verify_darts.py`; a block candidate additionally needs strict
block validation, all nine cap-hub closures, and both checkers on every
closure.  Its embedded structural audit must also be preserved.  For the
`(25,11)` finite lane, it must show `t=1` in all closures before any later
composition; for each `--require-t0` lane, it must show `t=0` in all closures
or the encoding/port theorem is `BLOCKED`.  This audit does not replace either
independent verifier or turn a candidate into a nonexistence claim.  Preserve
all postprocess output.  Only a candidate passing the certificate checks is
`CERTIFIED`; all other records are `INCOMPLETE` or `BLOCKED`.

Pass `--expected-block-t 1` when postprocessing a `(25,11)` candidate and
`--expected-block-t 0` for every `--require-t0` candidate.  The postprocessor
checks the requested value in all nine closures; a mismatch blocks that search
branch even if the underlying closed caps are otherwise valid APGs.

Do not run additional shards or infer coverage beyond these six profiles.

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
