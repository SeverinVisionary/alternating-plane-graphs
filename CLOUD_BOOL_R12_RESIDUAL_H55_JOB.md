# CLOUD JOB — canonical `r=12` residual-`H55` Boolean propagation search

This job is a source-bound follow-up to the two inconclusive Boolean batches.
It uses the same strict open-block, complete socket-normal-form encoding, plus
one proved propagation consequence of the portable branch: at capped `r=12`,
the two isolated socket `C6` components and `t=0` leave exactly a residual
`H55 = C4`.  It is not a nonexistence procedure.  It may search only the three
listed portable profiles; no extra seed, profile, symmetry assumption, or
parallel process is authorized.

## Mandatory source and environment gate

Before reading the job, source, tests, or solver, record `python3 --version`,
`pwd`, UTC, Z3 version, CPU/memory, and `git status --short --branch`; hard stop
if `pwd` shows a macOS path such as `/Users/...` -- this job must not run on the
development machine -- or if the initial checkout is dirty.  Verify the dispatch-supplied exact
commit and tree and run `git fsck --full`; hard stop on any mismatch.  This job
runs only in an isolated Linux cloud session, never on the shared Mac.

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


After the gate, create

```sh
set -eu
REV=$(git rev-parse --short=12 HEAD)
LOG_DIR="results/logs/bool_r12_residual_h55_${REV}"
mkdir -p "$LOG_DIR"
```

## Positive controls

Run the standard closed order-20 control and both independent verifiers.

```sh
python3 exact_map_bool_sat.py \
  --known-certificate certificates/known/order20.json \
  --timeout-s 120 --threads 1 --output "$LOG_DIR/bool_known_order20.json"
python3 verify.py \
  certificates/known/order20.json --expect-order 20
python3 verify_darts.py \
  certificates/known/order20.json --expect-order 20
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and
       .require_residual_h55_c4 == false' "$LOG_DIR/bool_known_order20.json"
```

Then require the canonicalized A21 strict-block control to pass ordinary
postprocessing.  A21 has `r=10`, so the new `r=12` propagation must be false
there; this prevents an accidental profile-independent restriction.

```sh
python3 exact_map_bool_sat.py \
  --known-block results/blocks/A21.json \
  --canonicalize-known-block --require-t0 --timeout-s 120 --threads 1 \
  --output "$LOG_DIR/bool_known_A21.json"
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and
       .canonical == true and .require_t0 == true and
       .require_residual_h55_c4 == false' "$LOG_DIR/bool_known_A21.json"
python3 exact_map_postprocess.py \
  "$LOG_DIR/bool_known_A21.json" --expected-order 21 --expected-block-t 0 \
  --output "$LOG_DIR/bool_known_A21_postprocess.json"
jq -e '.disposition == "CERTIFIED" and .closure_count == 9 and
       .block_t_gate.passed and .r_gate.passed and ([.closures[].passed] | all)' \
  "$LOG_DIR/bool_known_A21_postprocess.json"
```

Either control failure is a hard stop.

## Strictly serial target search

Exactly one Python/Z3 process may run at a time.  Every raw `unknown`, `unsat`,
kill, missing JSON, or failed postprocessor is `INCOMPLETE`/`BLOCKED`, not
nonexistence.  Postprocess only a retained raw candidate whose record confirms
the new propagation was enabled.

```sh
run_target () {
  order="$1"
  stem="bool_r12_h55_b_${order}_r12_t0_seed0"
  set +e
  python3 cloud_resource_runner.py \
    --metadata "$LOG_DIR/${stem}.resources.json" -- \
    python3 exact_map_bool_sat.py \
      --lane block --block-order "$order" --r 12 --require-t0 \
      --timeout-s 600 --threads 1 --random-seed 0 --output "$LOG_DIR/${stem}.json" \
    >"$LOG_DIR/${stem}.stdout" 2>"$LOG_DIR/${stem}.stderr"
  status=$?
  set -e
  printf '%s\n' "$status" > "$LOG_DIR/${stem}.exit_status"
  if test -s "$LOG_DIR/${stem}.json" && jq -e \
      '.disposition == "CANDIDATE" and .canonical == true and
       .require_t0 == true and .require_residual_h55_c4 == true' \
      "$LOG_DIR/${stem}.json"; then
    python3 exact_map_postprocess.py \
      "$LOG_DIR/${stem}.json" --expected-order "$order" --expected-block-t 0 \
      --output "$LOG_DIR/${stem}_postprocess.json"
  fi
}

run_target 28
run_target 29
run_target 31
```

Retain commands, source/environment gate, raw records, resource metadata,
candidate postprocess artifacts, all retained closures and verifier outputs, a
relative-path SHA-256 manifest, and one archive.  State
`target_certificate_exists=false` unless a postprocessor emitted `CERTIFIED`,
and state `nonexistence_claimed=false` unconditionally.  Do not dispatch the
all-26 promotion job unless all three postprocessors are `CERTIFIED` and their
source handoff is independently revalidated.

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
