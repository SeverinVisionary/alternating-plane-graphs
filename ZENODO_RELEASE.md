# Staged release: v1.0.3

Everything here is prepared. **Nothing fires until the disclosure sentence in
`paper/apg.tex` is confirmed or struck** — see the last section.

## What this release changes, in one line

A theorem was withdrawn, the gate that hid the gap was repaired, and the deposit
was retitled to match what it actually establishes.

## Pre-flight

```sh
cd ~/alternating-plane-graphs
git status --porcelain            # must be empty
make verify                       # 1295 passed, 13 skipped  (~8 min; ~2h with python-sat)
python3 render_artifact_pdf.py    # regenerates docs/artifact.pdf
(cd paper && tectonic -X compile apg.tex)
```

Then confirm the metadata is the new title and version:

```sh
python3 -c "import json;d=json.load(open('.zenodo.json'));print(d['title']);print(d['version'],d['publication_date'])"
grep -m1 -A1 '^title:' CITATION.cff
```

Expected: *Alternating plane graphs: settling Conjectures 10.1 and 10.2, with
witnesses for 10.3* · `1.0.3` · `2026-09-06`.

## Cut it

```sh
git tag -a v1.0.3 -m "Withdraw the Conjecture 10.3 theorem; repair the coverage gate"
git push origin v1.0.3
gh release create v1.0.3 --title "v1.0.3" --notes-file RELEASE_NOTES_1_0_3.md
```

Zenodo picks the release up through the GitHub integration and mints the version
DOI from `.zenodo.json`. **Do not paste fields into the Zenodo form** — the file
is the source of truth, and hand-editing has diverged from it before.

## After it lands

- [ ] Check the new version DOI resolves and shows the **new title**
- [ ] Confirm the record no longer says Conjecture 10.3 is settled — the live
      1.0.2 record still does, and that is the single most embarrassing thing
      currently public
- [ ] The concept DOI `10.5281/zenodo.22269200` should now resolve to 1.0.3

## The one blocker

`paper/apg.tex`, in the AI disclosure:

> *"The manuscript was drafted with AI assistance. The author has read and
> revised every sentence of it and is answerable for each one."*

This is a claim about the author, not about the mathematics, and it is the only
statement in the deposit that no amount of checking here can make true. Either
read the manuscript end to end and leave it, or replace it with something
narrower — for instance that the author is answerable for the mathematical
content and for this disclosure, without claiming line-by-line revision.

Until that is settled, this release stays staged.
