# CLOUD JOB — Boolean exact-map serial recovery

This job is a narrow recovery of two profiles whose first Boolean pilot was
killed before a raw solver record was written. It runs only in a
user-launched, isolated Linux cloud session from the exact Git bundle attached
to the task. It is not a license to rerun the first four target profiles,
search another profile, infer nonexistence, or use the development machine.

The dispatch message, not this file, supplies the immutable bundle SHA-256,
advertised ref, commit, and tree for this particular recovery bundle. Before
reading repository files, installing a solver, or running tests, record
`python3 --version`, `pwd`, `git status --short --branch`, Z3 version,
CPU/memory, UTC start/end, the bundle digest, and every command line. Hard-stop
if `pwd` shows a macOS path such as `/Users/...` -- this job must not run on the
development machine -- and on a dirty worktree, bundle/ref/commit/tree mismatch, failed
complete-history `git bundle verify`, or failed `git fsck`.

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


## Non-negotiable serial rule

There may be exactly one Python/Z3 target process at a time. `--threads 1`
limits Z3 worker threads only; it does **not** allow two one-thread solver
processes to share the session's memory safely. Do not background a command,
use `xargs -P`, a job runner, or start `(34,13)` until `(31,12)` has exited and
any candidate postprocessing has ended. Run each target through the committed
`cloud_resource_runner.py` wrapper: it writes portable per-child resource and
exit metadata even when GNU `/usr/bin/time` is unavailable. Preserve that JSON,
stdout, stderr, raw JSON, and shell exit status for each profile.

Set a run directory below the target module while running from the repository
root; keep it relative so the repaired postprocessor boundary is exercised:

```sh
set -eu
RECOVERY_REV=$(git rev-parse --short=12 HEAD)
LOG_DIR="results/logs/bool_recovery_${RECOVERY_REV}"
mkdir -p "$LOG_DIR"
```

## Mandatory controls

Run the closed published map first. It must produce a `CANDIDATE`/`sat` raw
record, then the published certificate must pass both independent verifiers.

```sh
python3 exact_map_bool_sat.py \
  --known-certificate certificates/known/order20.json \
  --timeout-s 120 --threads 1 \
  --output "$LOG_DIR/bool_known_order20.json"
python3 verify.py \
  certificates/known/order20.json --expect-order 20
python3 verify_darts.py \
  certificates/known/order20.json --expect-order 20
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat"' \
  "$LOG_DIR/bool_known_order20.json"
```

Then replay the strict A21 control. The postprocessor invocation deliberately
uses repo-root-relative paths: it must be `CERTIFIED` with nine closures and
the requested `r=10`, `t=0` values. Any failed/non-sat/non-certified control
is a hard stop before target computation.

```sh
python3 exact_map_bool_sat.py \
  --known-block results/blocks/A21.json \
  --require-t0 --timeout-s 120 --threads 1 \
  --output "$LOG_DIR/bool_known_A21_block.json"
python3 exact_map_postprocess.py \
  "$LOG_DIR/bool_known_A21_block.json" \
  --expected-order 21 --expected-block-t 0 \
  --output "$LOG_DIR/bool_known_A21_block_postprocess.json"
jq -e '.disposition == "CERTIFIED" and .closure_count == 9 and
       .r_gate.passed and .block_t_gate.passed and
       ([.closures[].passed] | all)' \
  "$LOG_DIR/bool_known_A21_block_postprocess.json"
```

## Target recovery

Run these commands in this exact order, serially. Do not use `set -e` around
the solver itself: a cloud OOM kill must be retained as a bounded block instead
of preventing collection of the other profile. The next command may begin only
after the preceding solver process has exited and its exit status has been
written to the named text file.

```sh
set +e
python3 cloud_resource_runner.py \
  --metadata "$LOG_DIR/bool_lane_b_31_r12_t0_seed0.resources.json" -- \
  python3 exact_map_bool_sat.py \
  --lane block --block-order 31 --r 12 --require-t0 \
  --timeout-s 600 --threads 1 --random-seed 0 \
  --output "$LOG_DIR/bool_lane_b_31_r12_t0_seed0.json" \
  >"$LOG_DIR/bool_lane_b_31_r12_t0_seed0.stdout" \
  2>"$LOG_DIR/bool_lane_b_31_r12_t0_seed0.stderr"
status_31=$?
set -e
printf '%s\n' "$status_31" > "$LOG_DIR/bool_lane_b_31_r12_t0_seed0.exit_status"
```

If that record exists and has `disposition=CANDIDATE`, postprocess it before
the next target. A candidate is usable only if the result is `CERTIFIED` with
all nine closures passing the `r=12`, `t=0` gates; otherwise retain the output
as `INCOMPLETE`/`BLOCKED` and continue. If the raw record is absent, record
that it was absent and retain the exit status/stderr; do not synthesize a
solver result or retry it.

```sh
if test -s "$LOG_DIR/bool_lane_b_31_r12_t0_seed0.json" && \
   jq -e '.disposition == "CANDIDATE"' "$LOG_DIR/bool_lane_b_31_r12_t0_seed0.json"; then
  set +e
  python3 exact_map_postprocess.py \
    "$LOG_DIR/bool_lane_b_31_r12_t0_seed0.json" \
    --expected-order 31 --expected-block-t 0 \
    --output "$LOG_DIR/bool_lane_b_31_r12_t0_seed0_postprocess.json"
  post_status_31=$?
  set -e
  printf '%s\n' "$post_status_31" > "$LOG_DIR/bool_lane_b_31_r12_t0_seed0_postprocess.exit_status"
fi
```

Only then run `(34,13)` under the same one-process rule:

```sh
set +e
python3 cloud_resource_runner.py \
  --metadata "$LOG_DIR/bool_lane_b_34_r13_t0_seed0.resources.json" -- \
  python3 exact_map_bool_sat.py \
  --lane block --block-order 34 --r 13 --require-t0 \
  --timeout-s 600 --threads 1 --random-seed 0 \
  --output "$LOG_DIR/bool_lane_b_34_r13_t0_seed0.json" \
  >"$LOG_DIR/bool_lane_b_34_r13_t0_seed0.stdout" \
  2>"$LOG_DIR/bool_lane_b_34_r13_t0_seed0.stderr"
status_34=$?
set -e
printf '%s\n' "$status_34" > "$LOG_DIR/bool_lane_b_34_r13_t0_seed0.exit_status"

if test -s "$LOG_DIR/bool_lane_b_34_r13_t0_seed0.json" && \
   jq -e '.disposition == "CANDIDATE"' "$LOG_DIR/bool_lane_b_34_r13_t0_seed0.json"; then
  set +e
  python3 exact_map_postprocess.py \
    "$LOG_DIR/bool_lane_b_34_r13_t0_seed0.json" \
    --expected-order 34 --expected-block-t 0 \
    --output "$LOG_DIR/bool_lane_b_34_r13_t0_seed0_postprocess.json"
  post_status_34=$?
  set -e
  printf '%s\n' "$post_status_34" > "$LOG_DIR/bool_lane_b_34_r13_t0_seed0_postprocess.exit_status"
fi
```

Write a machine-readable disposition for **both** profiles. A raw `unknown`,
timeout, failed postprocessor, non-candidate, kill, or missing raw JSON is
`INCOMPLETE` or `BLOCKED`. A raw Z3 `unsat` must be preserved verbatim only
alongside an `INCOMPLETE` disposition; it is never nonexistence. For any
certified candidate retain the candidate, postprocessor record, all nine
closures, every verifier stdout/stderr, and its structural audit. End by
making a SHA-256 manifest of every retained file and report no result beyond
these two profiles.

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
