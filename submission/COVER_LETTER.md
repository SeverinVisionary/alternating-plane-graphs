# Cover letter — Bulletin of the Australian Mathematical Society

> Paste into "Comments for the Editor", or attach. The submission file is
> `paper/apg101.pdf`.

---

Dear Editors,

I submit **"No alternating plane graph has exactly two vertex degrees, or
exactly two face sizes"** for consideration in the Bulletin. It is seven pages.

A plane graph is *alternating* if adjacent vertices have different degrees,
adjacent faces have different sizes, and every vertex and every face has size at
least three. Althöfer, Haugland, Scherer, Schneider and Van Cleemput introduced
them (*Ars Math. Contemp.* **8** (2015) 337–363) and closed that paper with four
open problems. This note settles the first: no such graph has exactly two
distinct vertex degrees, and none has exactly two distinct face sizes.

The proof is short. Assign each edge the sum of the reciprocals of its two
endpoint degrees and its two incident face sizes. Summing over edges returns the
number of vertices plus the number of faces, so Euler's formula says the excess
above one, totalled over all edges, is exactly two — some edge must exceed the
budget. Alternation then caps every edge at one, in both halves, by the same
inequality with vertices and faces exchanged.

The engine is the source paper's own. Its §9.1 bounds the face count of a weaker
class by exactly this sum, and that derivation never uses the hypothesis it is
stated under; its §3.2 attacks the class of this conjecture with different
machinery that never bounds the face count. Connecting the two is the
contribution. That the argument is short is the point of interest, not a
weakness — but it does mean the value of the note lies in the connection, and I
would welcome a referee's judgement on whether that connection is already known.

The result is unconditional. Definition 2.1 of the source paper does not say how
face size is read at a bridge; the paper rules bridges out a few lines later by
asserting 2-edge-connectivity. Section 5 shows the conclusion holds under the
permissive reading too, so the theorem does not depend on which reading is taken.

**Disclosure.** Large language models were used materially in this work,
including the step that makes the result unconditional, and Section 1 describes
that use. AI review also found and forced the correction of errors in earlier
drafts. No AI system is an author. I confirm this satisfies the Bulletin's
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
