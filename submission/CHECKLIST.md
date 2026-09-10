# Submission checklist — BAMS

> **SUBMITTED 2026-09-10 12:14:03 UTC.** Submission **ID 21117**, Bulletin of
> the Australian Mathematical Society, section Articles. Verified against the
> journal's own API: `dateSubmitted` set, `submissionProgress` 0, status
> *Queued*, and the queue row moved from *Incomplete* to *Submission*. No editor
> assigned yet. Expect a decision *"often within a month of receipt"*.
> Author dashboard:
> `https://journal.austms.org.au/ojs/index.php/Bulletin/authorDashboard/submission/21117`

Tick before pressing submit. Sources for every requirement are in
[`../paper/README_bams.md`](../paper/README_bams.md).

**Step-by-step walkthrough, including registration:**
[`SUBMISSION_STEPS.md`](SUBMISSION_STEPS.md).
**Field-by-field values:** [`FORM_FIELDS.md`](FORM_FIELDS.md).
This file is the gate list.

## The journal's own five-step form

- [x] Registered at `journal.austms.org.au` as **both reader and author**
- [x] Submission is a **PDF** (`paper/apg101.pdf`, 11 pp., the last being the class's address page) — LaTeX source is
      wanted on acceptance or before review, not now
- [x] Confirmed: original work, not published, not under consideration elsewhere
- [x] Confirmed: AI use is acknowledged and described (disclosure section, end of the manuscript)
- [x] Cover letter pasted from [`COVER_LETTER.md`](COVER_LETTER.md)
- [x] Green Open Access selected — **no fee**

## Metadata to enter in the system (not just in the PDF)

- [x] Author name and **ORCID 0009-0005-0419-4070** entered in the submission form
- [x] Keywords entered in the form
- [x] MSC codes entered under **Subjects** (primary 05C10, secondary 05C30)

## The Submission Preparation Checklist, in the site's own words

Read off the live site 2026-09-09. These are declarations in your name.

- [x] "The article is an original work, has not been published before, and is
      not currently under consideration for publication in another journal" —
      true; the Zenodo deposit is a preprint, which green OA expressly permits
- [x] "This submission is **not** a revision of an earlier submission which is
      still under consideration" — true
- [x] "The authors listed on the paper each contributed to the production of
      the work" — sole author; no AI system is an author
- [x] "The authors are aware of and agree to the policy ... freely accessible
      to the public five years after publication" — your decision
- [x] "The article contains no defamatory or unlawful statements and does not
      infringe the right of any third party"
- [x] "Where necessary to reproduce copyright material, written permission has
      been obtained" — not applicable; nothing is reproduced, and the two
      quoted phrases from the source paper are short and attributed
- [x] "Any use of an artificial intelligence tool ... is appropriately
      acknowledged and described" — the disclosure section names the systems,
      the period and the nature of the assistance
- [x] "the submitted document is in Adobe pdf format" — true

## What must be true of the file

- [x] Built with the AustMS `baustms` class — **10 pages of content**, inside the
      stated preference for papers to be "relatively short"
- [x] Abstract **149 words** — under both the 150 in the class template and
      the 200 on the submissions page
- [x] MSC 2020: primary `05C10`; secondary `05C30`
- [x] Keywords present
- [x] References alphabetical by first author, cited numerically
- [x] Affiliation line reads as you want it — currently *"Independent
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
- [x] Zenodo refreshed to **v1.0.6**, DOI `10.5281/zenodo.22682657`, minted
      2026-09-10 after a failed first attempt (see below). Concept DOI
      `10.5281/zenodo.22269200`, which the manuscript cites, resolves to it.
      Verified inside the archived bytes: `paper/apg101.pdf` in the deposit is
      byte-identical to the submitted PDF, SHA-256
      `25ec25c2…c0d8ba44`, and the description no longer says "unconditional".
- [ ] **The deposit's `submission/COVER_LETTER.md` is three commits stale.**
      Tag `v1.0.6` sits at `dd29640`; the compliance-claim removal landed later
      at `75566e5`. The paper is unaffected. Fold into the next release, or cut
      a v1.0.7 if you want the archive clean now.
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
