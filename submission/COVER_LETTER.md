# Cover letter — Bulletin of the Australian Mathematical Society

> Paste as the "Comments for the Editor" field, or attach. Replace the bracketed
> line if you add an affiliation.

---

Dear Editors,

I submit **"Three conjectures on alternating plane graphs"** for consideration in
the Bulletin.

Althöfer, Haugland, Scherer, Schneider and Van Cleemput introduced alternating
plane graphs — plane graphs in which adjacent vertices differ in degree and
adjacent faces differ in size — and closed their 2015 paper in this area (*Ars
Math. Contemp.* **8**, 337–363) with four open problems. This paper settles two
of them and makes partial progress on a third.

The central result is **Conjecture 10.1**: there is no alternating plane graph
with exactly two distinct vertex degrees, and none with exactly two distinct
face sizes. The proof is short. A single per-edge identity — the reciprocals of
the two endpoint degrees and the two incident face sizes, summed over edges,
gives the vertex and face counts — turns Euler's formula into the statement that
some edge must have "excess" above 1. Alternation then caps every edge at
exactly 1, in both halves, by the same inequality with vertices and faces
exchanged. The argument is the source paper's own machinery from its Section 9,
which it applied only to a weaker class; the connection to the strong class
appears not to have been made.

The result is unconditional. The 2015 paper's Definition 2.1 does not say how
face size is read at a bridge; the paper rules bridges out a few lines later by
asserting 2-edge-connectivity. Section 5 shows the conclusion holds under the
permissive reading too, so the theorem does not depend on which reading is
taken.

**Conjecture 10.2** — a (3,4,5)-alternating plane graph at every order n ≥ 20 —
is settled by explicit certificates at the 26 orders the source paper left open,
together with a periodic capping lemma reaching order 48 and every n ≥ 50.

For **Conjecture 10.3** the paper is deliberately narrow: it certifies 54 orders
by explicit witness and states plainly that the tail above 56 is open. An
earlier version of this manuscript claimed the full conjecture; the induction
carrying 3-connectivity through the periodic family did not survive scrutiny and
was withdrawn, with the defects set out in a remark. The fourth problem is
untouched.

**Artifact.** Every graph asserted is supplied as an explicit rotation system,
archived on Zenodo under the concept DOI 10.5281/zenodo.22269200. No file
records the claim that a graph *is* an alternating plane graph: degrees, faces,
face sizes, connectivity and both alternation conditions are recomputed on each
run by four separately written decision procedures. Referees are welcome to
check any certificate independently; they export to `planar_code` for `plantri`
or House of Graphs.

**Disclosure.** Large language models were used materially in this work,
including the step that makes Theorem 3.1 unconditional, and the disclosure in
Section 1 describes the use task by task. No AI system is an author. I confirm
this satisfies the Bulletin's requirement that such use be acknowledged and
described.

The manuscript is 12 pages, has not been published elsewhere, and is not under
consideration by another journal. A preprint is publicly available in the
artifact repository; I understand the Bulletin's Green Open Access policy
permits this, and I am submitting on the Green route.

[I am an independent researcher, unaffiliated. ORCID 0009-0005-0419-4070.]

Yours sincerely,
Hanyu Yang
