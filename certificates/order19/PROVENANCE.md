# Order 19: the boundary case of Conjecture 10.3

> **The `.plc` bytes referred to below are not in this repository.** No licence
> statement was found at their source, so they are not redistributed; each graph
> is re-expressed in this repository's own `apg-plane-rotation-v1` format, and
> the digest of every original is kept in
> [`../UPSTREAM_PROVENANCE.json`](../UPSTREAM_PROVENANCE.json). Byte-level checks
> described here skip unless the corpus is restored alongside this tree. See
> [`../../NOTICE.md`](../../NOTICE.md).

Conjecture 10.3 asks for a 3-connected alternating plane graph on every order
from 19 up. Order 19 is the one order that **cannot** be settled from the
`(3,4,5)` subclass: the paper's exhaustive search reports no `(3,4,5)`-APG on 18
or 19 vertices at all, so a witness there has to be a general APG in the sense
of Definition 2.1.

House of Graphs' exhaustive census counts **5** alternating plane graphs on 19
vertices, and Althofer's public table holds exactly five 19-vertex files. All
five are here.

| file | SHA-256 of upstream bytes |
| --- | --- |
| `upstream/03_19-19.plc` | `53ea76e1213006a654705d40d65216a8a1abe890ee6a8972be5009ca1c567f71` |
| `upstream/04_19-19.plc` | `78ba792a5652186957daa375f27c4ce8065426e0efbe381b6d823ef7088ff096` |
| `upstream/05_19-19.plc` | `5bcab5163959cb5580e28afaaa6a53a39018fe596443407649a31a9ce2bab94a` |
| `upstream/06_19-19.plc` | `58c2242f9836fbb23eacc2b014ff66c9725b62eb07d1ad6b7054313c3d51b346` |
| `upstream/07_19-19.plc` | `ce0a31662fde63e3f11b7bccc9045ef398e8e131b52dab6669081f7608df26eb` |

Source: `https://www.althofer.de/apg/apgs/<name>` — the same corpus as
[`../census_sources/`](../census_sources/PROVENANCE.md) and
[`../known/`](../known/PROVENANCE.md). **The redirect matters:** that host issues
a 301 to `althofer.de`, so a fetch without `-L` silently stores a 107-byte HTML
redirect page whose hash looks like a provenance mismatch. That happened once
here before the files were fetched correctly.

`ORDER19_*.json` are decoded from those bytes by
[`import_planar_code.py`](../../import_planar_code.py), independently of the
2026-09-01 an independent reviewer that first found them; the two decodings agree up to
isomorphism of rotation systems.

## What is checked here

* All five are alternating plane graphs — `general_apg.is_apg` accepts each.
* **None is a `(3,4,5)`-APG** — each has a degree-6 vertex or a 6-face, so
  `verify.py`, `verify_darts.py` and `fast_apg_check` all reject them. That is
  correct behaviour and consistent with the paper's exhaustive search.
* **All five are 3-connected**, by brute force over all pairs, with
  `separating_pairs_on_faces` empty.
* The five are pairwise non-isomorphic as plane maps.

So Conjecture 10.3 holds at `n = 19`. One witness would have sufficed; there are
five.

## The one thing taken on trust

That these five are *all* the alternating plane graphs on 19 vertices is the
paper's exhaustive-search claim and the House of Graphs census, not re-derived
here. **For the positive answer it does not matter** — a single 3-connected
witness settles the order. It would only matter for a refutation.
