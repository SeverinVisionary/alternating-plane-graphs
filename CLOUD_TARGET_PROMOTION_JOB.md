# CLOUD JOB — source-bound all-26 Boolean-block promotion

This is the only cloud job allowed to turn a certified Boolean cap-motif triple
into a `(3,4,5)`-APG target count. It is not a solver search. Run it only after
the prior cap-motif job has retained `CERTIFIED` artifacts for `(28,12)`,
`(29,12)`, and `(31,12)`. A raw candidate, `unknown`, `unsat`, partial
postprocess, or arbitrary strict block is not an eligible input.

The dispatch supplies two immutable attachments:

1. Exact Git bundle with SHA-256, ref, commit, and tree hash.
2. `apg-boolean-cap-handoff-v1.tar.gz` with SHA-256. It must unpack to
   `handoff-input.json` plus exactly the nine input artifacts named by
   `promotion_handoff_input.template.json`. Do not auto-discover files.

## Step 0 — hard environment and source gate

Before reading source or extracting input, retain this output and hard-stop on
a macOS path or a missing command:

```sh
set -eu
python3 --version
pwd
date -u +%FT%TZ
case "$(pwd)" in /Users/*) exit 99;; esac
command -v python3 >/dev/null || exit 99
command -v git >/dev/null || exit 99
command -v sha256sum >/dev/null || exit 99
command -v tar >/dev/null || exit 99
command -v cmp >/dev/null || exit 99
command -v find >/dev/null || exit 99
command -v sort >/dev/null || exit 99
command -v xargs >/dev/null || exit 99
```

STOP if `pwd` shows a macOS path such as `/Users/...`: this job must not run on
the development machine.

The dispatch must set literal values; never replace them with a nearby commit
or a branch tip:

```sh
SOURCE_BUNDLE=/work/input/<source-bundle>
SOURCE_SHA256=<dispatch SHA-256>
SOURCE_COMMIT=<dispatch full commit>
SOURCE_TREE=<dispatch full tree>
HANDOFF_ARCHIVE=/work/input/apg-boolean-cap-handoff-v1.tar.gz
HANDOFF_SHA256=<dispatch SHA-256>
WORK_ROOT=/work/apg-target-promotion
```

Verify, clone, and extract only after the source gate:

```sh
printf '%s  %s\n' "$SOURCE_SHA256" "$SOURCE_BUNDLE" | sha256sum -c -
printf '%s  %s\n' "$HANDOFF_SHA256" "$HANDOFF_ARCHIVE" | sha256sum -c -
git bundle verify "$SOURCE_BUNDLE"
test ! -e "$WORK_ROOT" || exit 98
mkdir -p "$WORK_ROOT"
git clone "$SOURCE_BUNDLE" "$WORK_ROOT/source"
cd "$WORK_ROOT/source"
git checkout --detach "$SOURCE_COMMIT"
test "$(git rev-parse HEAD)" = "$SOURCE_COMMIT"
test "$(git rev-parse HEAD^{tree})" = "$SOURCE_TREE"
test -z "$(git status --porcelain)"
git fsck
mkdir "$WORK_ROOT/handoff"
tar -xzf "$HANDOFF_ARCHIVE" -C "$WORK_ROOT/handoff"
test -f "$WORK_ROOT/handoff/handoff-input.json"
cmp -s "$WORK_ROOT/handoff/handoff-input.json" \
  promotion_handoff_input.template.json
python3 - "$WORK_ROOT/handoff/dispatch_metadata.json" \
  "$SOURCE_SHA256" "$SOURCE_COMMIT" "$SOURCE_TREE" "$HANDOFF_SHA256" <<'PY'
import json
import sys
from pathlib import Path

Path(sys.argv[1]).write_text(
    json.dumps(
        {
            "format": "apg-target-promotion-dispatch-v1",
            "source_bundle_sha256": sys.argv[2],
            "source_commit": sys.argv[3],
            "source_tree": sys.argv[4],
            "handoff_archive_sha256": sys.argv[5],
        },
        indent=2,
        sort_keys=True,
    ) + "\n",
    encoding="utf-8",
)
PY
```

## Step 1 — mandatory source-bound strict-block gate

The gate rehashes each raw Boolean/postprocess/opened artifact, reopens the raw
marked caps itself, validates all strict/t/r/nine-closure fields, runs both
fresh raw closed-map verifiers, and exports the committed A--D controls in the
same canonical rotation format:

```sh
cd "$WORK_ROOT/source"
python3 promotion_handoff_gate.py \
  "$WORK_ROOT/handoff/handoff-input.json" \
  --output "$WORK_ROOT/handoff/handoff-ledger.json"
```

Its only eligible result is:

```text
format = apg-boolean-block-handoff-v1
disposition = ELIGIBLE
block_input_eligible = true
target_certificate_exists = false
nonexistence_claimed = false
blocks = exactly 28,29,31
published_blocks = exactly 21,22,23,24
```

On any other result, retain the data and report `INCOMPLETE`; do not compose,
do not create `MANIFEST_COMPLETE`, and do not make an existence or
nonexistence claim about a target order.

## Step 2 — deterministic all-26 promotion

Do not pass `--representations`: that is bounded-control mode, and a
caller-supplied map covering the 26 frozen targets is rejected. This command
rehashes/binds all seven blocks to the ledger, rechecks all strict blocks and
their nine closures, exhaustively tries reflection/socket/cyclic gluing
choices, records a replay trace and profile/t budget for every target, and
runs both final APG verifiers.

```sh
PROMOTION_DIR="$WORK_ROOT/handoff/promotion"
python3 compose_target_witnesses.py \
  --handoff-audit "$WORK_ROOT/handoff/handoff-ledger.json" \
  --block "21=$WORK_ROOT/handoff/published_blocks/strict_block_21.json" \
  --block "22=$WORK_ROOT/handoff/published_blocks/strict_block_22.json" \
  --block "23=$WORK_ROOT/handoff/published_blocks/strict_block_23.json" \
  --block "24=$WORK_ROOT/handoff/published_blocks/strict_block_24.json" \
  --block "28=$WORK_ROOT/handoff/inputs/28/opened_block.json" \
  --block "29=$WORK_ROOT/handoff/inputs/29/opened_block.json" \
  --block "31=$WORK_ROOT/handoff/inputs/31/opened_block.json" \
  --output-dir "$PROMOTION_DIR"
```

The expected intermediate disposition is
`PROMOTED_PENDING_SEPARATE_FINAL_AUDIT`, not a completion claim.

## Step 3 — separate exact-26 final audit

Only the committed final auditor may write `MANIFEST_COMPLETE`. It rejects a
stale marker, arbitrary output path, partial/extra target list, nonportable
source ledger, mismatched source-handoff copy, a non-replaying trace/profile,
or any fresh verifier failure. It rechecks every saved block closure and every
final target with both independent checkers.

```sh
python3 finalize_target_promotion.py \
  "$PROMOTION_DIR"
test -f "$PROMOTION_DIR/MANIFEST_COMPLETE"
python3 - "$PROMOTION_DIR" <<'PY'
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
audit = json.loads((root / "final_audit.json").read_text())
expected = [*range(46, 57), *range(67, 75), *range(88, 93), 109, 110]
assert manifest["disposition"] == "PROMOTED_PENDING_SEPARATE_FINAL_AUDIT"
assert manifest["target_orders"] == expected
assert audit["disposition"] == "CERTIFIED_26_TARGETS"
assert audit["target_certificate_count"] == 26
assert [entry["order"] for entry in audit["target_audits"]] == expected
assert all(entry["passed"] for entry in audit["target_audits"])
print("COMPLETE: 26/26 independently verified")
PY
```

If any command fails, report literally `INCOMPLETE: k/26 independently
verified`, list every unresolved order/lane disposition, and never interpret a
failure as nonexistence.

## Step 4 — archive and checkpoint

Retain the full `$WORK_ROOT/handoff` tree: a successful promotion package
contains a self-contained `source_handoff/` copy of the ledger plus raw,
postprocess, and opened artifacts; strict-block/closure certificates; final
certificates; saved/fresh checker evidence; `manifest.json`; `final_audit.json`;
`dispatch_metadata.json`; and, only on success, `MANIFEST_COMPLETE`.

```sh
(
  cd "$WORK_ROOT/handoff"
  find . -type f -print | LC_ALL=C sort | xargs sha256sum > SHA256SUMS
)
tar -czf "$WORK_ROOT/apg-target-promotion-result.tar.gz" -C "$WORK_ROOT" handoff
sha256sum "$WORK_ROOT/apg-target-promotion-result.tar.gz"
```

If the cloud task has authenticated GitHub write access, import the durable
result package to the exact branch, commit it as a separate checkpoint, and
push. Otherwise return the archive and SHA-256 unchanged for an authenticated
local import. A cloud-local file alone never closes Conjecture 10.2.

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
