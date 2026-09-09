# Copy-paste sheet for the BAMS OJS form

Everything the five-step form asks for, in the order it asks. Values are taken
from the manuscript, not retyped from memory. Where a field is an attestation,
it is left as a question for you, because only you can answer it truthfully.

Site: `journal.austms.org.au`. Register as **both reader and author** — one
account, both roles ticked, or the submission option never appears.

---

## Step 1 — Start

| Field | Value |
| --- | --- |
| Section | Articles |
| Language | English |

**Attestations. Read each; they are your declarations, not formalities.**

- [ ] The submission has not been previously published, nor is it before another
      journal. **True** as of 2026-09-09: the note has never been submitted
      anywhere. The Zenodo deposit is a preprint/artifact, which the Bulletin's
      green route expressly permits — see `../paper/README_bams.md`.
- [ ] The submission file is a PDF. **True** — `../paper/apg101.pdf`.
- [ ] Where available, URLs for the references have been provided. **True** —
      six of the seven carry a DOI or are books.
- [ ] The text adheres to the stylistic requirements in Author Guidelines.
      **True** — AustMS `baustms` class.
- [ ] Not a replacement for an earlier submission still under consideration.
      **True.**
- [ ] Authorship complete and appropriate. **Sole author.** No AI system is an
      author; the assistance is described in the manuscript's disclosure.
- [ ] No defamatory or unlawful statements, no third-party rights infringed.
      **True** as far as I can establish — nothing is reproduced.
- [ ] Written permission for copyright material. **Not applicable.**
- [ ] AI tool use acknowledged and described. **True** — the disclosure section
      names the systems, the period and the nature of the assistance.
- [ ] Five-year public-access policy accepted. **Your decision.**

The site's list has no competing-interests item; an earlier draft of this sheet
invented one.

**Comments for the Editor**: paste `COVER_LETTER.md` whole, minus its markdown
heading and the blockquote at the top.

## Step 2 — Upload

| | |
| --- | --- |
| File | `paper/apg101.pdf` |
| Component | Article Text |

LaTeX source is wanted on acceptance or before review — **not now**. Do not
upload `apg101.tex` at this step.

## Step 3 — Metadata

**Title** (copy exactly, including the comma):

    No alternating plane graph has exactly two vertex degrees, or exactly two face sizes

**Abstract** (148 words — inside both the 150 of the class template and the 200
of the submissions page):

    A plane graph is alternating if every vertex has degree at least three,
    every face has size at least three, adjacent vertices have different degrees
    and adjacent faces have different sizes. Althofer, Haugland, Scherer,
    Schneider and Van Cleemput introduced these graphs and conjectured that none
    has exactly two degrees, and none exactly two face sizes. We prove both, by
    one per-edge inequality applied twice with the roles of vertices and faces
    exchanged. Summing the reciprocals of the two endpoint degrees and the two
    incident face sizes over all edges returns the number of vertices plus the
    number of faces; parity and alternation then force that sum to be at most
    one on every edge, while Euler's formula forces some edge past one. We also
    prove both statements when face alternation is required only between
    distinct adjacent faces, so that bridges are admitted; that extension uses a
    charging argument.

If the field is plain text, "Althofer" without the umlaut is safer than a
mangled entity; if it accepts Unicode, use **Althöfer**.

**Author**

| Field | Value |
| --- | --- |
| Given name | Hanyu |
| Family name | Yang |
| Affiliation | Independent researcher, California, USA |
| Country | United States |
| ORCID | `0009-0005-0419-4070` |
| E-mail | the address on your account |

**Keywords** — enter one at a time; the widget usually needs Enter between them:

    alternating plane graph
    plane graph
    discharging
    Euler's formula

**MSC 2020**

| | |
| --- | --- |
| Primary | `05C10` |
| Secondary | `05C30` |

The archival manuscript also carries `68R10`; this note does not, because
nothing in it is computational.

**Open Access**: select **Green**. No fee. Gold is USD 3,655 and buys immediate
Cambridge Core access — not needed, and the green route already permits the
Zenodo deposit.

## Step 4 — Confirmation

Nothing to enter. Check the file list shows exactly one PDF.

## Step 5 — Next steps

Note the submission ID it gives you here, and record it in `CHECKLIST.md`.

---

## Before you press submit

- The deposit is at **v1.0.6**, DOI minted 2026-09-09, which is the first
  version containing this note and the first without the withdrawn
  "unconditional" wording. The manuscript's computational-support paragraph
  cites the concept DOI `10.5281/zenodo.22269200`, which resolves to it.
- Expect a decision **often within a month**. The bar is *"new and interesting
  results"* with exposition *"in publishable form, without revision"*.
- The standing risk is unchanged and is not a formatting matter: **no
  mathematician other than you has read the proof.**
