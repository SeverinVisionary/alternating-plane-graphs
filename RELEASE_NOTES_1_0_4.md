**Two independent reviews of the Conjecture 10.1 proof found three false
statements. None is fatal; one of them mattered.**

Both reviews were run at Extra High and verified against the live
conversations. They were given the whole of §2–§5 and opposite stances — one
told to assume the proof is wrong and find where, the other to assume it sound
and say what a referee would still refuse to sign off on. **Neither could break
it.** Both would accept it as a correct proof of Conjecture 10.1 after the
corrections below, and neither could exhibit a `2,Y`- or `X,2`-alternating plane
graph. They converged independently on the same weakest point.

### Step 0 of the bridge argument had a false justification

It read: *"A simple connected plane graph on at least three vertices has every
facial walk of length at least 3: a walk of length 2 requires parallel edges and
one of length 1 a loop."*

A facial walk of length 2 can also be **a single bridge traversed twice** — `K2`
is the example — and that case was never disposed of. The conclusion survives:
for two darts alone to form a facial orbit, both endpoints have degree 1,
forcing the component to be `K2`, which `deg_A(u) >= 2` excludes. But the reason
given did not cover it, and Step 0's `s_2 >= 8` feeds every numerical estimate
in the bridge argument. The case is now written out.

### Two further false statements, neither load-bearing

* **The Eulerian remark.** It claimed the parity lemma is *"the classical fact
  that a plane graph is face 2-colourable if and only if it is Eulerian,
  restated so that bridges are permitted"*. A triangle with a pendant edge has
  its two faces properly coloured once self-adjacency across the bridge is
  ignored, and is not Eulerian. The lemma is strictly weaker than the classical
  criterion, not a restatement of it. It was commentary, used nowhere.
* **Convention (C1)** said a facial walk repeats a vertex *"if and only if the
  graph is not 2-connected"*. That is false per face: two triangles sharing a cut
  vertex have two faces repeating nothing and an outer face that repeats. The
  true statement quantifies over all faces.

Also: *"the outer walk of A"* is replaced by *"the facial boundary walk of A
incident with the corner formerly occupied by a"* — in a fixed embedding that
face need not be the unbounded one.

### What did not change

Both reviews confirmed (C1) is the only theorem-level external vulnerability and
neither found new reason to doubt it. One noted independently that the 2015
paper's own Lemma 9.2 proof — *"since the graph is bipartite, all f_j for j odd
are 0"* — is false under a distinct-vertices reading, which is further evidence
**for** (C1). Full account in `REVIEW.md`.
