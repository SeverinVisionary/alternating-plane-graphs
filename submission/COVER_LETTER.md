# Cover letter — Bulletin of the Australian Mathematical Society

> Paste into "Comments for the Editor", or attach. The submission file is
> `paper/apg101.pdf`.

---

Dear Editors,

I submit **"No alternating plane graph has exactly two vertex degrees, or
exactly two face sizes"** for consideration in the Bulletin. It is ten pages of content; the PDF runs to eleven, the last being the author-address page the AustMS class emits.

A plane graph is *alternating* if every vertex has degree at least three, every
face has size at least three, adjacent vertices have different degrees, and
adjacent faces have different sizes. Althöfer, Haugland, Scherer, Schneider and Van Cleemput introduced
them (*Ars Math. Contemp.* **8** (2015) 337–363) and closed that paper with four
open problems. This note settles the first: no such graph has exactly two
distinct vertex degrees, and none has exactly two distinct face sizes.

The proof is short. Assign each edge the sum of the reciprocals of its two
endpoint degrees and its two incident face sizes. Summing over edges returns the
number of vertices plus the number of faces, so Euler's formula says the excess
above one, totalled over all edges, is exactly two — some edge must exceed the
budget. In either of the two excluded configurations, parity and alternation
force that sum to be at most one on every edge — the same inequality in both
halves, with vertices and faces exchanged.

The counting is the source paper's own. Its §9.1 bounds the face count of a
weaker class by the face-incidence half of this four-term charge, and that
derivation uses bipartiteness and face alternation but not the degree 2 it is
stated under; its §3.2 attacks the class of this conjecture with different
machinery that never bounds the face count. Combining the face-incidence count
with the analogous count over vertices is the contribution.

Section 5 adds an extension rather than a repair. The source paper's definition
excludes bridges, as it states on p. 339. With face size still counted by
boundary-walk length, Section 5 proves both nonexistence statements again under
the weaker requirement that face alternation hold only between *distinct*
adjacent faces, so that bridges are admitted. That argument is the longer and
harder half of the note, and its bottleneck — a bound on how many
positive-excess edges can be assigned to each bridge — is identified as such.

**Disclosure.** Large language models were used materially in this work,
including the idea behind the Section 5 extension, and a disclosure section at
the end of the manuscript describes that use. No AI system is an author. I confirm this satisfies the Bulletin's
requirement that such use be acknowledged and described.

This note has not been published elsewhere and is not under consideration by
another journal. A preprint and a machine-checkable artifact are publicly
deposited (concept DOI 10.5281/zenodo.22269200); I understand the Bulletin's
Green Open Access policy permits this, and I am submitting on the Green route.

For completeness: two further conjectures from the same source paper are treated
in a separate manuscript, which I may submit elsewhere in due course. It shares
no result with this note.

I am an independent researcher, unaffiliated. ORCID 0009-0005-0419-4070.

Yours sincerely,
Hanyu Yang
