# Submitting to the Bulletin of the Australian Mathematical Society

Written 2026-09-09 for `paper/apg101.pdf` in `~/alternating-plane-graphs`.

**What is verified and what is not.** The registration form fields, the
submission preparation checklist, and the author guidelines below were read off
the live site on 2026-09-09 and are quoted from it. The step-by-step *ordering*
of the five-step wizard is the standard OJS 3 flow; the wizard itself sits
behind a login, so I could not walk it. Where I am describing the standard flow
rather than something I read, it says so.

---

## Before you open the browser

Have these to hand:

| | |
| --- | --- |
| The file | `~/alternating-plane-graphs/paper/apg101.pdf` — 11 pages, the last being the class's address page |
| Cover letter | `~/alternating-plane-graphs/submission/COVER_LETTER.md` |
| Field values | `~/alternating-plane-graphs/submission/FORM_FIELDS.md` |
| ORCID | `0009-0005-0419-4070` |

Do **not** upload the `.tex`. LaTeX source is wanted on acceptance, or before
peer review — not at submission.

---

## Part 1 — Register

1. Go to **https://journal.austms.org.au/ojs/index.php/Bulletin/user/register**

2. Fill the **Profile** section:

   - **Given Name** (required): `Hanyu`
   - **Family Name**: `Yang`
   - **Affiliation** (required): `Independent researcher, California, USA`
   - **Country** (required): `United States`

3. Fill the **Login** section:

   - **Email** (required): your address
   - **Username** (required): your choice
   - **Password** / **Repeat password** (required): your choice

   Pick these yourself and type them yourself. I have not generated or stored
   any of them.

4. Checkboxes, exactly as the form words them:

   - "Yes, I agree to have my data collected and stored according to the privacy
     statement" — **required to proceed.**
   - "Yes, I would like to be notified of new publications and announcements" —
     optional.
   - "Yes, I would like to be contacted with requests to review submissions to
     this journal" — optional. Ticking it opens a **Reviewing interests** text
     field. Leaving it unticked is fine and does not affect your submission.

5. Press **Register**.

6. **Check your roles before going further.** The Author Guidelines say you must
   be registered "as both *readers* and *authors*". The registration form has no
   role selector, so this install grants those by default — but verify, because
   without the Author role the "Make a Submission" link never appears:

   - Click your name, top right → **View Profile** → **Roles** tab
   - **Reader** and **Author** should both be ticked. Tick Author if it is not.
   - Save.

   If Author cannot be ticked there, e-mail the editorial office and ask for the
   role; do not try to work around it.

---

## Part 2 — Start the submission

7. Go to **https://journal.austms.org.au/ojs/index.php/Bulletin/submissions** or
   click **Make a Submission** from the journal home page.

### Step 1 of 5 — Start

8. **Section**: `Articles`. **Language**: `English`.

9. **Submission Preparation Checklist.** These are the site's exact words, with
   what I know about each. They are declarations in your name — read them, do
   not just clear them.

   - *"The article is an original work, has not been published before, and is
     not currently under consideration for publication in another journal"* —
     **true.** The note has never been submitted anywhere. The Zenodo deposit is
     a preprint/artifact, which the Bulletin's green route expressly permits
     ("preprint/submitted version may be made available by the author at any
     time").
   - *"This submission is **not** a revision of an earlier submission which is
     still under consideration"* — **true.**
   - *"The authors listed on the paper each contributed to the production of the
     work"* — **true**, sole author. No AI system is listed as an author.
   - *"The authors are aware of and agree to the policy ... freely accessible to
     the public five years after publication"* — **your decision.** This is the
     standard AMPAI policy and the reason the green route is free.
   - *"The article contains no defamatory or unlawful statements and does not
     infringe the right of any third party"* — **true** as far as I can
     establish. The note reproduces no figure, table or dataset from another
     source; it quotes two short attributed phrases from the source paper, which
     is fair quotation.
   - *"Where necessary to reproduce copyright material, written permission has
     been obtained"* — **not applicable**; nothing is reproduced. (The
     `baustms.cls` class file is the AustMS's own and is not redistributed by
     this project.)
   - *"Any use of an artificial intelligence tool to generate text or images or
     analyse data for the submission is appropriately acknowledged and
     described"* — **true.** The manuscript's *Disclosure of AI use* section, at
     the end before the bibliography, names the systems, the period of use
     (February–September 2026) and the nature of the assistance, including that
     the Section 5 extension was proposed by an AI reviewer.
   - *"the submitted document is in Adobe pdf format"* — **true.**

10. **Comments for the Editor**: paste **`submission/COVER_LETTER_PLAINTEXT.txt`**
    whole. Do **not** paste the `.md` — the field is a rich-text editor, so the
    markdown `**bold**` markers survive as literal asterisks and the file's hard
    line wraps become `<br>` mid-sentence.

11. Continue.

### Step 2 of 5 — Upload Submission

12. Upload `~/alternating-plane-graphs/paper/apg101.pdf`.

13. Set the file's **component** to **Article Text**.

14. Continue. Confirm the list shows exactly one PDF and nothing else.

### Step 3 of 5 — Enter Metadata

15. **Title** — copy exactly, comma included:

        No alternating plane graph has exactly two vertex degrees, or exactly two face sizes

16. **Abstract** — 148 words, inside the stated 200. The text is in
    `FORM_FIELDS.md`; paste it as one paragraph. If the field is plain text,
    write `Althofer` rather than risk a mangled `Althöfer`.

17. **Contributors** — you should already be listed. Confirm the affiliation
    reads `Independent researcher, California, USA` and **add the ORCID
    `0009-0005-0419-4070`** if the field is empty. The checklist explicitly asks
    for "*all* authors, with their ORCID".

18. **Keywords** — enter one at a time, pressing Enter after each:

        alternating plane graph
        plane graph
        discharging
        Euler's formula

19. **Subjects** (this is where MSC goes — the checklist calls them "Subjects"):

        05C10
        05C30

    `05C10` is the single primary the guidelines ask for; `05C30` is the
    secondary. Do not add `68R10` — the archival manuscript carries it, this
    note has no computational content.

20. **Open Access**, if the form offers a choice: select **Green**. It costs
    nothing. Gold is USD 3,655 and buys immediate Cambridge Core access, which
    you do not need — green already permits the Zenodo deposit.

### Step 4 of 5 — Confirmation

21. Review, then **Finish Submission**. Confirm when it asks.

### Step 5 of 5 — Next Steps

22. Record the submission ID it shows you. Put it in
    `~/alternating-plane-graphs/submission/CHECKLIST.md` so there is one place
    that knows.

---

## Afterwards

- Expect a decision **"often within a month of receipt"**. The bar is *"new and
  interesting results"* with exposition *"in publishable form, without
  revision"*.
- Keep `paper/apg101.tex` unchanged from here on. If they accept, they will ask
  for the source, and it must be the source of the PDF they read.
- One risk is not addressed by anything above: **no mathematician other than
  you has read the proof.** If a referee asks for changes, that is the likeliest
  reason.
