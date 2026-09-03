# CLOUD JOB — complete socket-normal-form primary Boolean search

This is a **new encoding checkpoint**, not a rerun of an inconclusive cloud
job.  It runs the proof-backed complete two-socket normal form committed with
this source: all twelve socket dart matches, the two induced length-six socket
cycles, and their twelve length-five opposite darts are fixed after a
representation isomorphism plus strictness, rather than the earlier
single-pair convention.  The task must
run only in a user-launched, isolated Linux cloud session from an exact Git
bundle supplied by the dispatch message.  It may not use the shared Mac,
change source, add a profile, add a seed, or turn any non-certificate into a
nonexistence claim.

The three target profiles are the portable primary covering triple
`(b,r)=(28,12),(29,12),(31,12)`.  A certified block for each would be enough
to compose witnesses for all 26 target orders, but this job makes no such
claim unless every raw model clears the independent postprocessing boundary.

## Mandatory source and environment gate

Before reading any repository file, test, solver, or job specification:

1. Record `python3 --version`, `pwd`, Z3 version, CPU/memory, UTC start, and
   `git status --short --branch`; hard-stop if `pwd` shows a macOS path such as
   `/Users/...` -- this job must not run on the development machine -- or if the
   tree is dirty.
2. Locate the attached exact bundle and verify the dispatch-supplied SHA-256.
3. Run `git bundle verify`; it must advertise the dispatch-supplied ref and
   commit. Clone it, explicitly check out that commit, verify the supplied
   tree, and run `git fsck`.
4. Hard-stop on any bundle/ref/commit/tree/fsck/source mismatch. Do not
   substitute a nearby revision or an archive with only a matching tree.

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


Run from the repository root after that gate:

```sh
set -eu
NORMAL_FORM_REV=$(git rev-parse --short=12 HEAD)
LOG_DIR="results/logs/bool_socket_normal_form_${NORMAL_FORM_REV}"
mkdir -p "$LOG_DIR"
```

## Mandatory known-answer controls

First prove that the fixed closed-map lane still encodes a known APG exactly.

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

Then run the end-to-end canonicalized A21 control.  It dynamically relabels
the published strict block, preserves its exact dart involution, and requires
`canonical=true`; it is not allowed to fall back to the historical
non-canonical fixed control.  Its strict intermediate is not itself a closed
APG, so certify it only through the mandatory nine caps and both independent
closed-map verifiers in `exact_map_postprocess.py`.

```sh
python3 exact_map_bool_sat.py \
  --known-block results/blocks/A21.json \
  --canonicalize-known-block --require-t0 --timeout-s 120 --threads 1 \
  --output "$LOG_DIR/bool_known_A21_socket_normal_form.json"
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and
       .canonical == true and .control == "published-strict-block-canonicalized"' \
  "$LOG_DIR/bool_known_A21_socket_normal_form.json"
python3 exact_map_postprocess.py \
  "$LOG_DIR/bool_known_A21_socket_normal_form.json" \
  --expected-order 21 --expected-block-t 0 \
  --output "$LOG_DIR/bool_known_A21_socket_normal_form_postprocess.json"
jq -e '.disposition == "CERTIFIED" and .closure_count == 9 and
       .r_gate.passed and .block_t_gate.passed and
       ([.closures[].passed] | all)' \
  "$LOG_DIR/bool_known_A21_socket_normal_form_postprocess.json"
```

Any failed control is a hard stop before a target process starts.

## Strictly serial target execution

There may be exactly one Python/Z3 target process at a time.  `--threads 1`
limits only Z3 threads; it does not permit concurrent solver processes.  The
following helper runs one target to completion, writes its resource and exit
metadata, and conditionally postprocesses only a raw `CANDIDATE`.  A raw
`unknown`, raw `unsat`, missing JSON, process kill, timeout, or failed
postprocessor is retained as `INCOMPLETE`/`BLOCKED`; none is a mathematical
absence statement.

```sh
run_target () {
  target_order="$1"
  target_r="$2"
  target_stem="bool_socket_nf_b_${target_order}_r${target_r}_t0_seed0"

  set +e
  python3 cloud_resource_runner.py \
    --metadata "$LOG_DIR/${target_stem}.resources.json" -- \
    python3 exact_map_bool_sat.py \
    --lane block --block-order "$target_order" --r "$target_r" --require-t0 \
    --timeout-s 600 --threads 1 --random-seed 0 \
    --output "$LOG_DIR/${target_stem}.json" \
    >"$LOG_DIR/${target_stem}.stdout" 2>"$LOG_DIR/${target_stem}.stderr"
  target_status=$?
  set -e
  printf '%s\n' "$target_status" > "$LOG_DIR/${target_stem}.exit_status"

  if test -s "$LOG_DIR/${target_stem}.json" && \
     jq -e '.disposition == "CANDIDATE" and .canonical == true and
            .require_t0 == true' "$LOG_DIR/${target_stem}.json"; then
    set +e
    python3 exact_map_postprocess.py \
      "$LOG_DIR/${target_stem}.json" \
      --expected-order "$target_order" --expected-block-t 0 \
      --output "$LOG_DIR/${target_stem}_postprocess.json"
    post_status=$?
    set -e
    printf '%s\n' "$post_status" > "$LOG_DIR/${target_stem}_postprocess.exit_status"
  fi
}
```

Run these three calls in this exact order.  Do not background them, run a
parallel shell, or begin the next call until the previous call and any
candidate postprocessing have returned.

```sh
run_target 28 12
run_target 29 12
run_target 31 12
```

For each certified candidate, retain its raw record, postprocessor record,
candidate, all nine closures, both verifier stdout/stderr files, and its
structural audit.  At the end, write a machine-readable per-profile
disposition, a SHA-256 manifest for every retained file, and one complete
archive.  The report must state `target_certificate_exists=false` unless a
postprocessor actually emitted `CERTIFIED`; it must state
`nonexistence_claimed=false` unconditionally.

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
