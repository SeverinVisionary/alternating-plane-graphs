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

The abstract is written to **148 words** to satisfy both. The compiled variant
runs to **12 pages**, which is exactly the journal's stated ceiling ("the paper
should be relatively short (say, no more than 12 pages)"), so any addition needs
a matching cut.
