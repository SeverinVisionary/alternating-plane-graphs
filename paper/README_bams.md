# `apg_bams.tex` — the Bulletin of the Australian Mathematical Society variant

Same manuscript as `apg.tex`, with the front matter and theorem environments
ported to the AustMS `baustms` document class. It is kept in step by hand; if
they diverge, `apg.tex` is the source of truth.

**The class file is not redistributed here.** `baustms.cls` is the AustMS's, and
no licence statement was found alongside it, so the same rule applies as to the
graph corpus (see `NOTICE.md`). Fetch it yourself:

    curl -O https://archive.austms.org.au/Publ/Bulletin/baustms.cls
    curl -O https://archive.austms.org.au/Publ/Bulletin/srtnumbered.bst
    TEXINPUTS=".:" tectonic apg_bams.tex

Two things the journal's own materials disagree on, so the stricter governs:

| | submissions page | class template |
| --- | --- | --- |
| abstract limit | 200 words | **150 words** |

The abstract is written to **147 words** to satisfy both (checked 2026-09-06). The compiled variant
ran to **12 pages** when last built, exactly the journal's stated ceiling ("the
paper should be relatively short (say, no more than 12 pages)"). **Rebuilt 2026-09-06 with the
fetched class file: it is now 13 pages**, one over the guidance, because the
Conjecture 10.3 withdrawal added about a page. A cut of roughly one page is
needed before submitting, or the length has to be argued for. Note the author
guidelines state no hard maximum -- the 12 pages is the About page's wording,
*"relatively short (say, no more than 12 pages)"*.

`baustms.cls` and `srtnumbered.bst` are git-ignored here for the same reason
they are not committed: they are the AustMS's. Fetch them with the commands
above before building.

## The submission process, checked 2026-09-06

Sources: the OJS [submissions page][sub] and [about page][about].

| | |
| --- | --- |
| where | OJS at `journal.austms.org.au`; register as *reader and author*, then a 5-step form |
| at submission | **a PDF**. LaTeX source is required on acceptance, or before peer review |
| abstract | **200 words** on the submissions page; the class template says 150. Ours is 147 |
| length | *"relatively short (say, no more than 12 pages)"* — guidance, not a hard limit; the author guidelines state no maximum |
| classification | MSC 2020, one primary plus one or more secondary, and keywords. Present: `05C10` primary; `05C30`, `68R10` secondary |
| decision speed | *"often within a month of receipt"* |
| bar | *"new and interesting results"*, exposition *"in publishable form, without revision"* |
| cost | **none** on the default green route |
| copyright | author retains it, licence to publish granted to AMPAI |
| green OA, what you may post | **preprint/submitted version: "may be made available by the author at any time", licence of the author's choosing** -- so this repository and its DOI are not a conflict. Accepted manuscript: author's own web page on acceptance, a non-commercial repository six months after publication, under CC-BY-NC-ND. Final typeset version: Cambridge Core only, free to all after five years; elsewhere, abstract plus a link |
| gold OA | optional, **USD 3,655** (2026, indexed annually) or covered by an institutional Read and Publish agreement; immediate access on Cambridge Core under a CC licence the author picks |

**Why gold exists, given that green already permits the preprint.** The journal
states it outright: *"The Bulletin's Green Open Access policy does not allow the
use of the Green Open Access self-archiving route to Plan S compliance."* An
author bound by Plan S -- ERC, Wellcome, and many national funders -- therefore
cannot satisfy their mandate on the free route and must either pay or publish
elsewhere. Most who do pay are covered by a library agreement and never see the
invoice. Gold also lifts the six-month repository embargo, releases the typeset
version immediately, and replaces CC-BY-NC-ND with a licence permitting reuse
and text mining.

**None of that applies here.** No funder mandate, no institution, no Plan S
obligation, and the work is already deposited with its own DOI. Green.

**The AI policy is a disclosure requirement, not a bar.** The submission
checklist asks the author to confirm that *"any use of an artificial
intelligence tool to generate text or images or analyse data for the submission
is appropriately acknowledged and described"*. `AI_DISCLOSURE.md` and the
manuscript's disclosure section are written to that standard already.

**No referee suggestions** are requested, and no data-availability policy is
stated; the manuscript carries one anyway.

[sub]: https://journal.austms.org.au/ojs/index.php/Bulletin/about/submissions
[about]: https://journal.austms.org.au/ojs/index.php/Bulletin/about
