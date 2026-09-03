# CLOUD JOB — closed cap-motif Boolean search for portable Section 8 blocks

This is an **independent positive-witness encoding**, not a retry or an
interpretation of prior `unknown` records. It searches a closed APG with two
marked `4--(3,3)` cap fans, then the mandatory postprocessor deletes the four
marked edges and recovers a strict two-socket block. Run only in a
user-launched isolated Linux cloud session from the exact Git bundle named in
the dispatch message. Never use the shared Mac, modify source, add profiles or
seeds, or treat `unknown`, raw `unsat`, a kill, or failed reopening as absence.

The primary profiles are `(b,r)=(28,12),(29,12),(31,12)`. A certified block
for each supplies the portable Section 8 triple, but no target claim is allowed
until all closed-map, strict-opening, nine-closure, and `t=0` gates pass.

## Source and environment gate

Before reading repository files, tests, solver, or this job specification:

1. Record `python3 --version`, `pwd`, Z3 version, CPU/memory, UTC start, and
   `git status --short --branch`; hard-stop if `pwd` shows a macOS path such as
   `/Users/...` -- this job must not run on the development machine -- or if the
   tree is dirty.
2. Require the committed job dependencies before any control: `command -v
   python3`, `command -v jq`, and `command -v git`; hard-stop if any is
   missing rather than failing ambiguously under `set -e` later:

```sh
# Executable form of the same stop, so it does not depend on being read.
case "$(pwd)" in /Users/*) echo "macOS path: this job must not run here"; exit 99;; esac
```


   ```sh
   command -v python3 >/dev/null || exit 99
   command -v jq >/dev/null || exit 99
   command -v git >/dev/null || exit 99
   ```
3. Locate the attached exact bundle and verify its dispatch-supplied SHA-256.
4. Run `git bundle verify`; it must advertise the supplied ref and commit.
   Clone it, explicitly check out that commit, verify the supplied tree, and
   run `git fsck`.
5. Hard-stop on any source mismatch. Do not use a nearby revision or a tree-only
   archive.

After that gate, from repo root:

```sh
set -eu
CAP_REV=$(git rev-parse --short=12 HEAD)
LOG_DIR="results/logs/bool_cap_motif_${CAP_REV}"
mkdir -p "$LOG_DIR"
```

## Mandatory controls

First run the standard closed order-20 Boolean control and both independent
verifiers.

```sh
python3 exact_map_bool_sat.py \
  --known-certificate certificates/known/order20.json \
  --timeout-s 120 --threads 1 --output "$LOG_DIR/bool_known_order20.json"
python3 verify.py \
  certificates/known/order20.json --expect-order 20
python3 verify_darts.py \
  certificates/known/order20.json --expect-order 20
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat"' \
  "$LOG_DIR/bool_known_order20.json"
```

Then dynamically cap A21, relabel its marked fans, pin its known matching, and
require the cap reopening/all-nine-closure boundary.

```sh
python3 exact_map_bool_sat.py \
  --known-cap-block results/blocks/A21.json \
  --require-t0 --timeout-s 120 --threads 1 \
  --output "$LOG_DIR/bool_known_A21_cap_motif.json"
jq -e '.disposition == "CANDIDATE" and .z3_result == "sat" and
       .lane == "closed" and .canonical == true and
       .require_cap_fans == true and .require_cap_interface == true and
       .require_cap_facets == true and
       .require_t0 == true and
       .control == "published-strict-block-capped-cap-normalized"' \
  "$LOG_DIR/bool_known_A21_cap_motif.json"
python3 exact_map_postprocess.py \
  "$LOG_DIR/bool_known_A21_cap_motif.json" \
  --expected-order 21 --expected-block-t 0 \
  --output "$LOG_DIR/bool_known_A21_cap_motif_postprocess.json"
jq -e '.disposition == "CERTIFIED" and .cap_opening.passed and
       .closure_count == 9 and .block_t_gate.passed and .r_gate.passed and
       ([.closures[].passed] | all)' \
  "$LOG_DIR/bool_known_A21_cap_motif_postprocess.json"
```

Either control failure is a hard stop before targets.

## Strictly serial target execution

Exactly one Python/Z3 target process may run at a time. `--threads 1` limits
solver threads only; it does not authorize parallel processes. The helper
retains resource metadata and postprocesses only raw candidates. A raw
`unknown`, raw `unsat`, missing JSON, kill, timeout, or failed postprocessor is
`INCOMPLETE`/`BLOCKED`, never a nonexistence conclusion.

```sh
run_target () {
  target_order="$1"
  target_r="$2"
  target_stem="bool_cap_b_${target_order}_r${target_r}_t0_seed0"

  set +e
  python3 cloud_resource_runner.py \
    --metadata "$LOG_DIR/${target_stem}.resources.json" -- \
    python3 exact_map_bool_sat.py \
    --lane closed --closed-order "$target_order" --r "$target_r" \
    --require-cap-fans --require-t0 --timeout-s 600 --threads 1 --random-seed 0 \
    --output "$LOG_DIR/${target_stem}.json" \
    >"$LOG_DIR/${target_stem}.stdout" 2>"$LOG_DIR/${target_stem}.stderr"
  target_status=$?
  set -e
  printf '%s\n' "$target_status" > "$LOG_DIR/${target_stem}.exit_status"

  if test -s "$LOG_DIR/${target_stem}.json" && \
     jq -e '.disposition == "CANDIDATE" and .canonical == true and
            .require_cap_fans == true and .require_cap_interface == true and
            .require_cap_facets == true and
            .require_t0 == true' \
       "$LOG_DIR/${target_stem}.json"; then
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

run_target 28 12
run_target 29 12
run_target 31 12
```

Do not background, use a parallel shell, or begin a profile before the prior
target and its candidate postprocess exit. Retain source/environment data, raw
records, resource metadata, postprocess data, closed candidates, reopened
blocks (`opened_block.json` plus its postprocessor SHA-256 and cap-fan
provenance), all closures, checker stdout/stderr, structural audits, a SHA-256
manifest, and one complete archive. For every profile, state
`block_certificate_exists=true` only if its postprocessor emits `CERTIFIED`;
otherwise state it as false. State `target_certificate_exists=false`
**unconditionally**: this job searches strict blocks, not the 26 final target
APGs. State `nonexistence_claimed=false` unconditionally.

## Required handoff after a positive triple

Do not turn three certified block records into an all-target claim in this
search job. If—and only if—each of `(28,12)`, `(29,12)`, and `(31,12)` has a
retained `CERTIFIED` postprocessor record, launch the separate source-gated
promotion job `CLOUD_TARGET_PROMOTION_JOB.md`. It rechecks each raw/block audit,
uses the exported reopened blocks, composes every one of the 26 exact chains,
and runs both independent APG verifiers on every final certificate. Only that
separate job may report a target-certificate count.

Before handoff, build a portable, hashable artifact directory matching the
committed `promotion_handoff_input.template.json`: copy each target's raw
Boolean record to `inputs/<order>/raw.json`, its `CERTIFIED` postprocess record
to `inputs/<order>/postprocess.json`, and its postprocessor-exported strict
rotation to `inputs/<order>/opened_block.json`; copy the template unchanged as
`handoff-input.json`. Include raw/post/opened SHA-256 values and the source
commit/tree in the cap-job artifact manifest, then archive that directory. The
promotion job verifies every binding again and rejects a partial or hand-edited
archive; never assemble this handoff from an `INCOMPLETE` postprocess.

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
