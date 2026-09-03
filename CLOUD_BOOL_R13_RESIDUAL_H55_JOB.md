# CLOUD JOB — canonical `r=13` residual-`H55` Boolean propagation search

This is the successor to `CLOUD_BOOL_R12_RESIDUAL_H55_JOB.md`, not a parallel
job. Dispatch it only after that `r=12` task is terminal and its artifacts
have been independently audited and checkpointed. It searches the two
remaining scheduled portable `r=13` profiles, using the proved consequence
that the residual degree-five/pentagon incidence graph is 2-regular. At
`r=13` that residual graph is a `C6`. This is a necessary propagation only,
not a nonexistence procedure.

The raw records in this job are direct open-strict-block records. The existing
all-26 promotion gate accepts only the separate closed-cap provenance format
for `(28,12),(29,12),(31,12)`. Therefore even a `CERTIFIED` result here is a
strict-block certificate, not authorization to start `CLOUD_TARGET_PROMOTION_JOB.md`.
It can be used in target construction only after
`direct_block_handoff_gate.py` validates its raw/postprocess/closure provenance
and a later final promotion extension accepts that distinct route.

## Mandatory source and environment gate

Before reading the job, source, tests, or solver, record `python3 --version`,
`pwd`, UTC, Z3 version, CPU/memory, and `git status --short --branch`; hard stop
if `pwd` shows a macOS path such as `/Users/...` -- this job must not run on the
development machine -- or if the initial checkout is dirty. Verify the dispatch-supplied exact
commit and tree and run `git fsck --full`; hard stop on any mismatch. This job
runs only in an isolated Linux cloud session, never on the shared Mac.

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


After the gate, create

```sh
set -eu
REV=$(git rev-parse --short=12 HEAD)
LOG_DIR="results/logs/bool_r13_residual_h55_${REV}"
mkdir -p "$LOG_DIR"
```

## Positive controls

Run the standard closed order-20 control and both independent verifiers. Its
record must show both residual gates disabled.

```sh
python3 exact_map_bool_sat.py \
  --known-certificate certificates/known/order20.json \
  --timeout-s 120 --threads 1 --output "$LOG_DIR/bool_known_order20.json"
python3 verify.py \
  certificates/known/order20.json --expect-order 20
python3 verify_darts.py \
  certificates/known/order20.json --expect-order 20
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and
       .require_residual_h55_2regular == false and
       .require_residual_h55_c4 == false' "$LOG_DIR/bool_known_order20.json"
```

Then require the canonicalized A21 strict-block control to pass ordinary
postprocessing. A21 has `r=10`, so both residual gates must remain false.

```sh
python3 exact_map_bool_sat.py \
  --known-block results/blocks/A21.json \
  --canonicalize-known-block --require-t0 --timeout-s 120 --threads 1 \
  --output "$LOG_DIR/bool_known_A21.json"
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and
       .canonical == true and .require_t0 == true and
       .require_residual_h55_2regular == false and
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

Exactly one Python/Z3 process may run at a time. Every raw `unknown`, `unsat`,
kill, missing JSON, or failed postprocessor is `INCOMPLETE`/`BLOCKED`, never
nonexistence. The `r=13` targets must record the general 2-regular gate as
true and the `r=12`-specific `C4` flag as false. Postprocess only retained raw
candidates.

```sh
run_target () {
  order="$1"
  stem="bool_r13_h55_b_${order}_r13_t0_seed0"
  set +e
  python3 cloud_resource_runner.py \
    --metadata "$LOG_DIR/${stem}.resources.json" -- \
    python3 exact_map_bool_sat.py \
      --lane block --block-order "$order" --r 13 --require-t0 \
      --timeout-s 600 --threads 1 --random-seed 0 --output "$LOG_DIR/${stem}.json" \
    >"$LOG_DIR/${stem}.stdout" 2>"$LOG_DIR/${stem}.stderr"
  status=$?
  set -e
  printf '%s\n' "$status" > "$LOG_DIR/${stem}.exit_status"
  if test -s "$LOG_DIR/${stem}.json"; then
    jq -r 'if (.canonical == true and .require_t0 == true and
              .require_residual_h55_2regular == true and
              .require_residual_h55_c4 == false)
           then "PASSED" else "FAILED" end' "$LOG_DIR/${stem}.json" \
      > "$LOG_DIR/${stem}.propagation_gate"
  else
    printf '%s\n' 'MISSING' > "$LOG_DIR/${stem}.propagation_gate"
  fi
  if test -s "$LOG_DIR/${stem}.json" && jq -e \
      '.disposition == "CANDIDATE" and .canonical == true and
       .require_t0 == true and .require_residual_h55_2regular == true and
       .require_residual_h55_c4 == false' "$LOG_DIR/${stem}.json"; then
    python3 exact_map_postprocess.py \
      "$LOG_DIR/${stem}.json" --expected-order "$order" --expected-block-t 0 \
      --output "$LOG_DIR/${stem}_postprocess.json"
  fi
}

run_target 31
run_target 34
```

If and only if the order-31 postprocessor is `CERTIFIED`, run the direct-open
source handoff in the same checked-out source tree. This does *not* compose a
target or create `MANIFEST_COMPLETE`: it writes a portable strict-block ledger
whose nine closures are reconstructed and rechecked independently of the
saved cloud checker logs.

```sh
if jq -e '.disposition == "CERTIFIED"' \
  "$LOG_DIR/bool_r13_h55_b_31_r13_t0_seed0_postprocess.json"; then
  python3 - "$LOG_DIR/direct_handoff_31_input.json" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

path = sys.argv[1]
value = {
    "format": "apg-direct-open-block-handoff-input-v1",
    "source": {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "tree": subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], text=True).strip(),
    },
    "profiles": {
        "31": {
            "raw_record": "bool_r13_h55_b_31_r13_t0_seed0.json",
            "postprocess_record": "bool_r13_h55_b_31_r13_t0_seed0_postprocess.json",
        }
    },
}
Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
PY
  python3 direct_block_handoff_gate.py \
    "$LOG_DIR/direct_handoff_31_input.json" \
    --output "$LOG_DIR/direct_handoff_31_ledger.json"
  jq -e '.format == "apg-direct-open-block-handoff-v1" and
         .disposition == "ELIGIBLE" and .block_input_eligible and
         .target_certificate_exists == false and .nonexistence_claimed == false' \
    "$LOG_DIR/direct_handoff_31_ledger.json"
fi
```

Retain commands, source/environment gate, raw records, resource metadata,
candidate postprocess artifacts, all retained closures and verifier outputs, a
relative-path SHA-256 manifest, and one archive. State
`target_certificate_exists=false` unless a postprocessor emitted `CERTIFIED`,
and state `nonexistence_claimed=false` unconditionally. A certified order-31
block requires the direct-open promotion extension described above; an
order-34 block additionally needs an explicit arithmetic coverage audit before
it is used in any target composition.

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
