# Submission checklist — BAMS

Tick before pressing submit. Sources for every requirement are in
[`../paper/README_bams.md`](../paper/README_bams.md).

## The journal's own five-step form

- [ ] Registered at `journal.austms.org.au` as **both reader and author**
- [ ] Submission is a **PDF** (`paper/apg101.pdf`, 11 pp., the last being the class's address page) — LaTeX source is
      wanted on acceptance or before review, not now
- [ ] Confirmed: original work, not published, not under consideration elsewhere
- [ ] Confirmed: AI use is acknowledged and described (disclosure section, end of the manuscript)
- [ ] Cover letter pasted from [`COVER_LETTER.md`](COVER_LETTER.md)
- [ ] Green Open Access selected — **no fee**

## Metadata to enter in the system (not just in the PDF)

- [ ] Author name and **ORCID 0009-0005-0419-4070** entered in the submission form
- [ ] Keywords entered in the form
- [ ] MSC codes entered in the form (primary 05C10, secondary 05C30)

## Attestations the form asks for

- [ ] Not a replacement for an earlier submission still under consideration
- [ ] Authorship is complete and appropriate — sole author, no omitted contributor
- [ ] Five-year public-access policy accepted
- [ ] Third-party rights, permissions and acknowledgements addressed (none apply:
      no figure, table or quotation is reproduced from another source; the two
      quoted phrases from the source paper are short and attributed)
- [ ] Competing interests: none to declare — confirm this is still true

## What must be true of the file

- [x] Built with the AustMS `baustms` class — **10 pages of content**, inside the
      stated preference for papers to be "relatively short"
- [x] Abstract **149 words** — under both the 150 in the class template and
      the 200 on the submissions page
- [x] MSC 2020: primary `05C10`; secondary `05C30`
- [x] Keywords present
- [x] References alphabetical by first author, cited numerically
- [ ] Affiliation line reads as you want it — currently *"Independent
      researcher, California, USA"*; add a city or leave as is

## Things to settle first

- [x] **Read `paper/apg101.pdf` end to end** — done by the author 2026-09-09.
- [x] **Confirmed by the author 2026-09-09**, the sentence printed in the
      disclosure: *"The author re-derived every argument independently."* This
      is the one line in the note a referee cannot check and the author can, and
      it now stands on the author's own confirmation rather than on drafting.
- [x] **Scope decided 2026-09-09: Conjecture 10.1 alone**, as `paper/apg101.tex`.
      Conjectures 10.2 and 10.3 go to a separate manuscript for another venue,
      after the capping lemma's deletion direction and window claim are
      repaired — see `REVIEW.md`, "Not yet acted on".
- [ ] **Consider contacting the original authors** before submitting. They are
      the only people who would know of an unpublished settlement, and the
      artifact re-expresses graphs from their corpus. See
      [`../PRIOR_ART.md`](../PRIOR_ART.md).
- [x] Zenodo is current at v1.0.5, DOI 10.5281/zenodo.22669418, verified
      against the archived bytes.
- [x] **Diffed `apg101.tex` against `apg.tex` and `apg_bams.tex`, 2026-09-09.**
      Drift found, this time in the other direction: the three review passes had
      corrected `apg101.tex` and left the archival versions carrying the false
      "those corners are non-consecutive" sentence and the "unconditional"
      framing the Pro review rejected. Both ported; `ARTIFACT.md`, `ZENODO.md`,
      `docs/index.html` and `.zenodo.json` carried the same overclaim and are
      corrected too. **The Zenodo deposit at v1.0.5 predates all of this and is
      now behind** — the note's computational-support paragraph cites the
      concept DOI, so refresh the deposit before or at submission.

## What you are told to expect

*"Editorial decisions on acceptance or otherwise are taken quickly, often within
a month of receipt."* The bar is *"new and interesting results"* with exposition
*"in publishable form, without revision"* — that second clause is the real risk
here. The author has now read the note end to end and confirmed the
re-derivation, but no *other* mathematician has read the proof: the teach-back
review of `RESEARCH_GUIDELINES.md` §8 is satisfied only in its
responsible-author form, not by an independent reader.
