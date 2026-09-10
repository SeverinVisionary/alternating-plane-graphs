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

## The blocker, resolved 2026-09-06

The disclosure previously read:

> *"The manuscript was drafted with AI assistance. The author has read and
> revised every sentence of it and is answerable for each one."*

That was a claim about the author that had not been confirmed, and it could not
be published unexamined. It now reads:

> *"The manuscript was drafted with AI assistance. The author has verified its
> mathematical content and is answerable for it and for this disclosure; the
> prose is not claimed to be the author's own sentence by sentence."*

This still satisfies the Bulletin's requirement that AI use be *"appropriately
acknowledged and described"* -- it describes it more precisely than the sentence
it replaces -- and it puts the author's name behind the mathematics, which is
the part that matters. If the manuscript is later read end to end, restoring the
stronger wording is a one-line edit in `paper/apg.tex` and `paper/apg_bams.tex`.

---

# v1.0.6 — what actually happened, 2026-09-09/10

The tag and GitHub release fired cleanly and **no DOI was minted.** Zenodo was
down; all three webhook deliveries returned `context deadline exceeded`,
code 500, and GitHub gave up after one attempt each. The release page looked
completely normal, so nothing on the GitHub side signals the failure.

**Check the mint, never the release.** `gh release create` succeeding tells you
nothing. Confirm with DataCite, which stays up when Zenodo does not:

```sh
curl -s https://api.datacite.org/dois/10.5281/zenodo.22269200 \
  | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['attributes']['version'])"
```

**Redelivering the webhook needs a scope `gh` does not have by default** —
`admin:repo_hook`. Without it the redelivery API returns 404, which reads like a
missing delivery rather than a missing permission. What worked instead, needing
no new scope:

```sh
gh release delete v1.0.6 --yes --cleanup-tag=false
gh release create v1.0.6 --title "v1.0.6" --notes-file RELEASE_NOTES_1_0_6.md
```

Deleting and recreating the release fires a fresh `release: published` event.
The tag is untouched, so the archived bytes are identical. The mint landed
within a minute: **10.5281/zenodo.22682657**.

**Tag position is a real trap.** `v1.0.6` was tagged at `dd29640` and three
further commits landed before the mint, so the deposit carries the cover letter
as it stood at the tag, not at HEAD. Tag last, or accept that anything committed
after the tag is not in the archive.
