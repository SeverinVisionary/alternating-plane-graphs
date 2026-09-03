# Cap-construction working set, archived 2026-09-01

The certificates in [`../../certificates/targets/`](../../certificates/targets/)
are the deliverable and are independently checkable without anything in here.
This directory preserves the code and intermediate data that *produced* them,
so the construction can be re-derived rather than only re-checked.

**Provenance and status.** Written during an independent review,
archived here verbatim. It is **not** held to this repository's coding gates,
has no test suite of its own here, and nothing in the repository imports it.
Treat it as an archived working set, not as maintained code.

- `code/` — the searcher and assembly scripts. `capsearch.py` is the
  alternating disk-filling search; `genstrip.py` enumerates unrollings;
  `cutlib.py` and `interface.py` derive meridian cuts and cap interfaces;
  `assemble2.py` and `finish_targets.py` build the closed maps;
  `closure_run.py` is the exhaustive closure argument for the uncappable
  `(1,0)` unrolling; `control*.py` are its validation controls.
- `HITV_2_3_*.pkl` — the cap fillings found on the `(2,3)` unrolling, pickled.
- `MANIFEST.txt` — the reviewer's own SHA-256 manifest of the certificates, kept for
  cross-checking against `certificates/targets/SHA256SUMS`, which was generated
  here independently.

**What is load-bearing and what is not.** Correctness of the 26 certificates
rests entirely on `verify.py` and `verify_darts.py` plus the recomputed
identities in `test_target_certificates.py`. Nothing in this directory is
trusted by that chain. If the code here were wrong, the certificates would
still stand or fall on the verifiers alone.


## The `.pkl` files

The 32 `HITV_2_3_*.pkl` files are Python pickles, protocol 4. **Pickle is an
execute-on-load format**, so treat any pickle from any source with suspicion.
These were audited with `pickletools.dis`: they contain no `GLOBAL`,
`STACK_GLOBAL`, `REDUCE`, `BUILD`, `NEWOBJ` or `INST` opcode -- only tuples,
lists, integers and strings -- so a restricted `Unpickler` whose `find_class`
refuses every request loads them successfully. Load them that way, or not at
all; nothing in the settled results depends on them.
