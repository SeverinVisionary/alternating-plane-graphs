Referee assessment

I find no gap in the two nonexistence arguments under the manuscript’s boundary-walk convention for face size. In particular, the bridge-face estimate, parity argument, assignment of positive edges to bridges, and final inequality withstand scrutiny. The qualifications “incident with a non-bridge edge” and “at most one degree-3 endpoint of a bridge” are essential and are correctly handled. 

apg101

I would nevertheless revise before submission. Several ancillary assertions need correction, and the exposition does not yet cleanly distinguish the short proof of the published conjecture from the substantially longer bridge-relaxed extension.

The specific disproportion feared in your prompt is not the principal problem here: the hardest charging step already receives substantial explanation. The larger problems are misplaced emphasis, repeated defensive commentary, inaccurate statements of scope and source correspondence, and the absence of a genuinely worked example.

I read all 468 source lines. Locations below are physical lines of apg101.tex, with \documentclass as line 1; the citation viewer uses different numbering. Counts below concern source prose, not printed page area. I checked the relevant passages of the 2015 paper, but did not review any machine-verification artifacts or assess the compiled page breaks.

Correctness and unjustified assertions — address these first

These six items are the correctness-related portion of the revision list.

C1. The abstract conflates two different conventions and overstates the mechanism

Location: lines 31–37.
Severity: BLOCKING for a referee — scope of the claimed result.

There are two separate issues.

First, “the conclusion holds either way” follows a statement about face size at a bridge. Read naturally, this claims independence from the definition of face size. That is not what the paper proves: boundary-walk length remains fixed throughout. What changes is whether face alternation includes self-adjacency across a bridge.

Second, “alternation caps every edge at one” needs the two-valued hypothesis and the resulting parity restriction. It is not a consequence of alternation alone. Nor is pointwise nonpositive excess the mechanism of the bridge-relaxed two-face-size proof, which explicitly allows positive edges. 

apg101 +1

Execute: Replace the pointwise assertion with:

In either of the two excluded configurations, parity and alternation force this sum to be at most one on every edge.

Replace the final sentence with:

With face size still counted by boundary-walk length, we also prove the result when face alternation is required only between distinct adjacent faces; this extension uses an additional charging argument.

Delete “unconditional.” The original definition already excludes bridges; the extension enlarges that class rather than resolving an ambiguity in the published bridge convention. 
AMC Journal

C2. Two equation correspondences are inaccurate

Location: lines 107–110 and 221–225.
Severity: SIGNIFICANT — source accuracy, not failure of the proof.

Equation (9.5) is the face bound f≤5e/12; it contains no 1/2 to replace. The degree-2 contribution appears in (9.8) and the combined inequality (9.9). Also, (9.2) is the incidence identity rf
r
	​

=∑
s
	​

e
r,s
	​

, not literally the displayed global formula attributed to it in the manuscript. 
AMC Journal

Execute:

At lines 107–110, replace “both assert” with “use the face-incidence count underlying”; do not present the global formula as the literal content of both numbered equations.

At line 221, replace the sentence with:

This combines the face bound (9.5) of [1] with the corresponding vertex count, replacing the degree-2 contribution in (9.8)–(9.9) by 1/d
1
	​

≤1/3.

The current claims are here. 

apg101 +1

C3. The calibration paragraph draws an inference that its next paragraph correctly disclaims

Location: lines 266–272.
Severity: SIGNIFICANT.

Matching the threshold does not establish that the contradiction is “not on an over-count.” Your following paragraph supplies exactly the reason: an invalidly stronger face bound can reproduce the same cutoff. Thus the first paragraph’s “So” is logically too strong. 

apg101

Execute: Replace lines 266–272 with:

This comparison illustrates where the minimum-degree-three hypothesis enters. Agreement of the exclusion threshold is not an independent verification of the face bound.

The worked example proposed below gives a substantially better check: it actually attains f=5e/12, so it detects the particular invalid strengthening you discuss.

C4. The statement about obtaining a lower bound on B has the inequality direction wrong

Location: lines 425–426.
Severity: SIGNIFICANT.

Your estimates give

2≤
24
P
	​

−
6
B
	​

,

equivalently

P≥4B+48orB≤
4
P
	​

−12.

Without another relation between P and B, this does not provide a standalone lower bound on B. 

apg101

Execute: Replace the offending clause with:

Without a bound relating the number of positive edges to the number of bridges, the local estimates give no contradiction.

C5. The sensitivity calculation does not state the hypothesis it actually varies

Location: lines 430–433.
Severity: SIGNIFICANT — an unjustified counterfactual calculation, not a gap in the actual 8-bound proof.

The advertised coefficients require a common lower bound on every bridge’s incident face, as well as on the larger face size used at non-bridge edges. Merely writing s
2
	​

≥7 does not state the first requirement.

There is another subtlety: under a hypothetical bound 7, the exact 3−4 classification need not follow from the local estimates. The tuple of endpoint degrees and face sizes

(3,5;3,7)

has charge 106/105>1. The weaker conclusion “a positive edge has a degree-3 endpoint” survives and is sufficient.

For a uniform lower bound q on bridge-face lengths and on s
2
	​

, the calculation is

2(
q
1
	​

−
12
1
	​

)+(
q
2
	​

−
12
5
	​

)=
q
4
	​

−
12
7
	​

.

This gives your three coefficients at q=8,7,6, respectively. 

apg101

Execute: My preferred edit is to delete this sensitivity discussion. Retain only the useful observation that P≤4B would already suffice. If retained, state the uniform hypothesis explicitly and use the formula above; do not claim the 3−4 classification persists.

C6. The general charge lemma needs a small domain repair

Location: lines 150–171; related convention at lines 100–105.
Severity: SIGNIFICANT for the literal lemma statement; no application is affected.

“No isolated vertex” does not explicitly exclude the empty graph. Under the usual convention that its plane complement is one face, the empty graph gives 0

=v+f=1. The disconnected generality also requires the size of a face to include all its boundary components, whereas the convention speaks of one boundary walk. If loops are allowed in the lemma’s broader graph class, “an end of exactly d edges” must instead count end incidences. 

apg101 +1

Execute: Restrict the lemma to what the paper uses:

Let G be a finite, connected, simple plane graph with at least one edge.

Then state ∑
a
	​

c(a)=v+f=e+2 directly. Remove the disconnectedness aside at lines 254–258. Alternatively, retain the generality only after explicitly repairing all three conventions.

Part A — checkable readability rubric

These are proposed editorial acceptance tests for this note, not official numerical BAMS requirements. A numerical proportion is diagnostic; it cannot compensate for an omitted implication.

L1. Orientation
Criterion	Pass threshold	Current verdict and evidence
1. Exact claim and limits	The abstract distinguishes the published definition, the bridge-relaxed extension, and the fixed meaning of face size. No stronger reading is suggested.	FAIL. Lines 31–37 conflate the latter two issues; C1 applies. 

apg101


2. Nearest prior result	One paragraph identifies the previous surviving cases and explains precisely what additional observation excludes them.	FAIL. Lines 57–63 give the numerical order bounds but do not explain their respective degree cases; “only” obscures the prior structural reduction. 

apg101


3. Natural failed approach	Before the main proof, display or explain one insufficient bound and the hypothesis that strengthens it.	FAIL. The manuscript never presents the basic 7/6>1 obstruction to using alternation alone. The ingredients appear only during the successful proof. 

apg101


4. Mechanism in advance	Within roughly 100 words, explain “two values ⇒ parity on the other side ⇒7/12+5/12=1.”	FAIL. The abstract previews the charge identity but omits the parity mechanism that makes the estimate work. 

apg101


5. Main result versus extension	A reader finishing the introduction can identify which argument settles the original conjecture and which proves a stronger variant.	FAIL. This distinction becomes explicit only in the preliminaries; the introduction instead diverts into an AI disclosure containing future proof references. 

apg101 +1

L2. Argument
Criterion	Pass threshold	Current verdict and evidence
6. Defined on first use	Zero unexplained nonstandard symbols or terminology essential to the current paragraph.	FAIL. Clear first-use problems include V, e, the f
s
	​

 family, and (C2); “darts” is also unexplained. Locations: lines 62, 68, 109–110, 313. 

apg101 +2


7. Standard-definition proof is complete	Both halves explain the parity implication and the distinct-4,6 bound; no unlicensed appeal to duality.	PASS. Sections 4.1–4.2 do this, including the corner-based treatment of cut vertices. 

apg101 +1


8. Charging proof is complete	Every positive edge has a well-defined unique destination; each destination has a proved capacity; the final sum uses a genuine partition.	PASS. Lines 386–415 establish all three. 

apg101


9. Lemma roles are announced	Every substantive lemma has a preceding sentence saying what it will accomplish. Immediate corollaries are exempt.	PASS. The identity and parity lemmas both have useful previews. 

apg101 +1


10. Difficulty is signalled before the hard step	The reader is told in advance which local-to-global implication is the bottleneck.	PASS for the extension. Lines 293–302 preview the unique-bridge assignment and capacity. The stronger phrase “the substance” comes later, but the mechanism is not concealed. 

apg101


11. Proportionate explanation	For this proof, the assignment/capacity step receives at least 30% of the bridge-proof prose; the elementary double-count proof remains one short paragraph, at most about 80 prose words.	PASS. Step 2 receives approximately 48% of the bridge-proof prose. The double-count proof is short. 

apg101 +1


12. Forward dependencies	Zero undefined prerequisites in a proof; future-result previews in an introduction are allowed. Definitions used in orientation should be available immediately.	PASS for proof dependencies; FAIL for orientation. The mathematical proofs proceed backwards through established material. But (C2) appears at line 68 and is defined at line 124, while the disclosure points from line 71 to a theorem at line 335. 

apg101 +1


13. Repetition has a purpose	A historical argument occurs once; a proof is not repeated after a direct citation would suffice. A short preview is allowed.	FAIL. The introduction and post-4.1 remark repeat the same historical comparison; the B=0 case repeats Section 4.2. 

apg101 +2


14. Worked example	Before the first substantial application, one specified graph has its relevant counts and charge calculation worked out.	FAIL. The calibration compares thresholds, not a graph. The two later graph constructions do not calculate the charge identity. 

apg101 +1


15. Nearby nonexample	A small example identifies exactly which tempting conclusion fails and which hypothesis is missing; its diagnostic quantities are shown.	FAIL on adequacy, not presence. The pendant-triangle example is well chosen but unworked; the bridged-APG construction is too elaborate to serve as the first diagnostic example. 

apg101 +1

L3. Audit trail
Criterion	Pass threshold	Current verdict and evidence
16. Exact source correspondence	Every attributed numbered equation says what the manuscript claims it says.	FAIL. C2 identifies two corrections. 

apg101 +1


17. Inherited versus contributed material	The paper identifies the inherited counting idea and distinguishes its present application and additional bridge argument.	PASS in intent. This distinction is present, although its equation-level accuracy and placement need improvement. 

apg101


18. Human-checkable proof	No theorem conclusion depends on an absent computation, classifier, search, or certificate.	PASS. The final contradiction is derived from explicit combinatorial arguments and rational inequalities. 

apg101


19. Responsibility and AI contribution	Material AI assistance, including any proposed proof idea, is disclosed without transferring responsibility.	PASS. The disclosure is unusually explicit. Its placement and revision-history content are the problems, not concealment. 

apg101


20. Machine-verification boundary	Any claimed machine verification states what was checked, what assumptions were trusted, and whether checking is logically necessary.	FAIL for the project-level L3 standard described in your prompt. The attachment supplies no such account. This is not a gap in the written proof, and the manuscript itself should not be accused of claiming a formal certificate it does not claim. 

apg101

Release test: Have one graph theorist unfamiliar with APGs spend at most 90 minutes reading the revised note and the pinned source passages. Without contacting the author, they should be able to explain both 7/12+5/12 estimates, reconstruct the bridge-face bound, justify the assignment capacity, and distinguish the two definitions. This test is currently untested, not passed by my assertion.

The actual disproportion audit

Using TeXcount’s prose counts, excluding mathematical expressions:

Portion	Approximate prose words
Preliminaries, lines 78–141	458
Entire per-edge-identity section	158
Standard-definition theorem section, excluding calibration	409
Bridge proof, lines 340–422	526
Its Step 0	114
Its Step 1	81
Its Step 2	250
Its Step 3	31
AI disclosure	118
Calibration	90
Final sensitivity remark	99

Thus Step 2 is not underexplained: 250/526≈48%. Step 0 also deserves its explanation; the facial-walk splice and exclusion of a length-two facial boundary are not details to erase.

The disproportion lies elsewhere. The preliminaries are longer than the entire standard-definition theorem section, and much of that space is interpretative defence rather than orientation. Historical comparison, draft-error history, threshold calibration, and parameter sensitivity collectively distract from a short argument. The revision should transfer space from those passages to one explicit failed bound, one worked graph, and a clear statement of the extension’s role. 

apg101 +2

Part B — remaining improvements

C1–C6 above are part of this list. The items below give the remaining changes, including structural moves. They are intended to be executed together.

Orientation and overall structure
B1. Correct the abstract’s definition wording

Location: lines 25–27.
Severity: POLISH.

“Every vertex and every face has size” assigns a face-size term to vertices.

Execute: Write “every vertex has degree at least three and every face has size at least three.” Include “finite, simple, connected” either here or in a clearly stated standing convention immediately before the formal definition. 

apg101

B2. State the nearest prior result accurately and explain the gain

Location: lines 57–63.
Severity: SIGNIFICANT.

The reader is given the numbers 25 and 56 without the surviving degree sets to which they belong. The source reduces the possibilities to {3,4} and {3,5}, respectively. 
AMC Journal

Execute: Replace the “obtaining only” comparison by a neutral account of those two cases, then say that the face-incidence bound excludes both. Remove “The proof is short” as the paragraph’s opening: it announces an evaluation rather than the mathematical advance.

A useful concluding sentence is:

Consequently every alternating plane graph has at least three distinct vertex degrees and at least three distinct face sizes.

This makes the significance immediately legible.

B3. Show why the natural first charge estimate fails

Location: after the historical paragraph, before the present AI subsection.
Severity: SIGNIFICANT.

The reader currently sees the successful fractions without first seeing what must be improved. 

apg101

Execute: Add the following short explanation:

Alternation alone gives at most 1/3+1/4 from each of the vertex and face sides, hence only c(a)≤7/6, which does not contradict Euler’s formula. The two-valued hypothesis supplies the missing parity restriction: on the opposite side, the two distinct values must be even and therefore at least 4 and 6. This improves one contribution to 5/12, giving c(a)≤1.

This is the principal missing orientation paragraph.

B4. Give one explicit dependency map

Location: end of the introduction; revise section order accordingly.
Severity: SIGNIFICANT.

The necessary map is currently distributed across the abstract, the convention discussion, and the Section 5 preview. 

apg101 +2

Execute: Use this order:

Definitions → edge identity and parity lemma → original conjecture → bridge-face lemma → bridge-relaxed two-degree case → bridge-relaxed two-face-size charging proof.

State in the introduction that the last three components prove an additional extension, not prerequisites for settling the published conjecture. Moving the parity lemma is specified in B12; extracting the bridge-face lemma is specified in B20.

B5. Stop using “weak” for two different relaxations

Location: lines 58, 130–131, 262–265, and throughout Section 5.
Severity: SIGNIFICANT.

The paper’s “weak alternating plane graphs” allow degree 2; your “weak reading” instead permits bridges while retaining minimum degree 3. These are independent changes. 

apg101 +1

Execute: Reserve weak alternating plane graph for the source’s term. Use bridge-relaxed alternating plane graph for your variant. Rename Section 5 “The bridge-relaxed extension.” Replace “weak 2,k class” by “weak alternating plane graphs with vertex degrees 2 and k.”

B6. Repair the first-use notation and standing assumptions

Location: lines 62, 68, 80–105, 109–110, 151–153, 305–319.
Severity: SIGNIFICANT.

This is a collection of small interruptions that cumulatively increase rereading. 

apg101 +1

Execute:

State finiteness explicitly in the standing assumptions.

Replace the introductory V≥25, V≥56 by “order at least 25 and 56”; retain v,e,f for counts later.

Remove (C2) from the early disclosure, using “the bridge-relaxed extension.”

Either define f
s
	​

 and e before the source formula or, preferably, replace that formula with the concise verbal source correspondence in C2.

Use u,w for vertices in the parity lemma, avoiding reuse of v, already a vertex count.

B7. Make the face-size convention concrete rather than defensive

Location: lines 100–115.
Severity: SIGNIFICANT.

The convention is important, but its current discussion spends more effort defending an interpretation than helping the reader use it. The phrase “repeats a vertex” also benefits from excluding the obligatory return to the starting vertex. 

apg101

Execute: Retain the operational definition and the bridge’s contribution of two. Replace the abstract warning about distinct vertices with this diagnostic example:

Two quadrilaterals sharing exactly one vertex have an exterior boundary walk of length 8, although only 7 distinct vertices occur on that boundary. Thus bipartiteness forces even boundary-walk length, not an even number of distinct boundary vertices.

Label this an illustration of the convention, not an APG example. Keep a short, corrected source note immediately attached to the convention; do not move the qualification to an appendix.

B8. State the published bridge convention once, without staging an ambiguity

Location: lines 118–139.
Severity: SIGNIFICANT.

The passage first presents two readings as available, then explains that the source explicitly chooses one, then defends studying the other. That is unnecessary suspense. 

apg101

Execute: Start with:

In the original definition, opposite face occurrences across an edge must have different sizes; hence bridges are excluded.

Then define the bridge-relaxed variant in a separate sentence. Define face adjacency through opposite sides of an edge, so adjacency at a vertex is not confused with adjacency along an edge. Remove “we simply decline to rely on it.”

B9. Move and shorten the AI disclosure without weakening it

Location: lines 65–76.
Severity: SIGNIFICANT.

The disclosure interrupts the first mathematical orientation and sends the reader to undefined notation and a distant proof step. The history of corrected draft errors is not part of the proof’s audit trail. 

apg101

Execute: Move it to an endmatter subsection before the bibliography. Retain all three substantive facts: material assistance with exploration/review/drafting; AI proposal of the bridge-extension idea; independent author checking and responsibility. Delete the inventory of earlier errors and “sentence by sentence.”

Approximately 60–90 words should suffice before any separate computational-support statement. This is relocation, not concealment; the journal expressly requires material AI use to be acknowledged and described. 
AustMS Journal

Counting tools, examples, and the original theorem
B10. Remove the dangling introduction to the identity

Location: line 141 and lines 147–148.
Severity: POLISH.

“We shall use the following” is separated from the following result by a section heading and then another introduction. 

apg101

Execute: Delete line 141. Use one introduction:

We isolate the face-incidence count used in [1, §9.1] and combine it with the analogous vertex count.

Do not attribute the exact combined lemma to the source unless you identify where that exact statement appears.

B11. Insert a worked graph that also explains the minimum-degree hypothesis

Location: after the edge identity and excess definition, before the main theorem.
Severity: SIGNIFICANT.

This is the highest-value addition. Neither the calibration nor the later examples presently works through the invariant. 

apg101

Execute: Use this graph and calculation:

Start with a triangle and replace each side by two internally disjoint paths of length two, drawn together along that side. The resulting simple plane graph has 9 vertices, 12 edges and 5 faces: three quadrilaterals and two hexagons. Every edge joins degrees 2 and 4, and separates face sizes 4 and 6. Thus

c(a)=
2
1
	​

+
4
1
	​

+
4
1
	​

+
6
1
	​

=
6
7
	​

,
a
∑
	​

(c(a)−1)=12⋅
6
1
	​

=2.

It satisfies both alternation conditions but is not an APG because its minimum degree is two.

This simultaneously provides a worked example, a nearby nonexample to dropping minimum degree three, and an equality case for

f=
12
5
	​

e.

Consequently it rules out any universally stronger coefficient 5/12−ε, unlike merely reproducing the threshold in the current calibration. A small schematic is optional; the construction and counts must remain explicit.

B12. Prove the corner-parity argument once

Location: lines 237–247 and 304–320.
Severity: SIGNIFICANT.

The same rotation argument appears in a special case and then again in general form. Its importance warrants a lemma, not two near-repetitions. 

apg101 +1

Execute: Move the general parity lemma and its proof into Section 3, after the identity/example. Rename that section “Edge charge and local parity.”

In its proof, replace “Walk the darts” by “List the incident edges in cyclic order,” under the simple-graph convention. Preserve the explanation using corner occurrences, not a list of distinct incident faces.

In Section 4.2, replace the repeated rotation proof by an application of the lemma with zero bridges. Retain one sentence emphasizing that this avoids any assumption that facial boundaries or vertex-face incidences are distinct.

B13. Work the pendant-triangle nonexample through the parity formula

Location: lines 322–328, moved with the parity lemma.
Severity: SIGNIFICANT.

The example is good, but the surrounding comparison with “the classical Eulerian criterion” is more elaborate than the example’s calculation. 

apg101

Execute: Give the four degrees 3,2,2,1, the corresponding bridge-incidence counts 1,0,0,1, and the differences 2,2,2,0. Say explicitly:

This illustrates the parity lemma, not the APG definition: vertices of degree one and two are present.

Replace the discussion of “strictly weaker” and “the only one it supplies” with the simple conclusion that the lemma controls degree minus bridge incidence, not degree itself.

B14. Explain the obstruction to using the dual, rather than only naming a hypothesis

Location: lines 192–196.
Severity: POLISH.

The warning is correct and worth retaining, but a nonspecialist may not recall why three-edge-connectivity appears. 

apg101

Execute: Add a short explanation that a two-edge cut can produce parallel edges in the dual, so the dual need not remain in the simple-graph class. Then say the proof instead exchanges the local counting arguments.

Do not replace the corner argument by “the other half follows by duality.”

B15. Make the theorem proof a single navigable proof

Location: lines 188–252.
Severity: POLISH.

The theorem is followed by prose, subsections, and two manual \qed endings rather than one visibly delimited proof. 

apg101 +2

Execute: Use one proof environment with two labelled cases, “Two vertex degrees” and “Two face sizes,” and one final end-of-proof mark. State 3≤d
1
	​

<d
2
	​

 and 3≤s
1
	​

<s
2
	​

 when introducing them.

Keep both cases: their symmetry is helpful, but the source-to-target parity implications are different enough that neither should be suppressed.

B16. Delete the repeated historical remark after the first case

Location: lines 220–226.
Severity: POLISH.

It repeats the introduction nearly point for point and interrupts the two halves of one theorem. 

apg101

Execute: Move the corrected equation correspondence from C2 into the introduction or a short source note after the complete theorem; delete the remaining repetition. Remove “The two sections were not connected,” which is rhetorically stronger than necessary to describe your contribution.

B17. Remove the disconnectedness aside

Location: lines 254–258.
Severity: POLISH, implementing C6.

It opens a generality the theorem does not need and that requires a slightly different boundary convention. 

apg101

Execute: Delete it after restricting the identity lemma. Connectedness should be stated once as an assumption, not repeatedly defended.

B18. Replace threshold “calibration” with a short mathematical comparison

Location: lines 260–272.
Severity: SIGNIFICANT.

A separate subsection promises more evidential value than this comparison provides. It also uses the ambiguous “weak 2,k” notation. 

apg101

Execute: Reduce it to a short remark, preferably adjacent to B11’s example:

c(a)≤
2
1
	​

+
k
1
	​

+
12
5
	​

=
12
11
	​

+
k
1
	​

.

State that this estimate alone excludes k≥12, whereas k=11 requires the source’s separate argument. Explicitly take k≥3. Apply C3’s limitation sentence and delete the invented 1/1000 perturbation.

The bridge-relaxed extension
B19. State nonexistence as the extension’s result, not “bridgelessness within the class”

Location: lines 276–302 and 335–338.
Severity: SIGNIFICANT.

The section alternates between proving nonexistence and describing vacuous bridgelessness of the nonexistent class. The title and theorem label further encourage the latter reading. 

apg101 +1

Execute: State directly that both nonexistence conclusions remain true for the bridge-relaxed definition. Remove “In particular no such graph has a bridge” and “What is proved here is bridgelessness within the two-face-size class.”

In the preview, replace “The lemma attaches every positive edge” by “The parity lemma, together with the degree-three restriction on positive edges, gives a unique bridge to which each positive edge is assigned.”

B20. Promote Step 0 to a lemma with the conclusion actually used

Location: lines 345–359; reused at lines 441–442.
Severity: SIGNIFICANT.

The heading announces only s
2
	​

≥8, while later arguments need the stronger conclusion that every bridge’s incident face has length at least eight. The proof establishes that stronger statement; it should be its advertised output. 

apg101 +1

Execute: Put a lemma at the beginning of Section 5:

In a finite connected simple plane graph of minimum degree at least three, every face incident with a bridge has boundary-walk length at least eight.

Move the proof there. Keep the splice

∣F∣=∣W
A
	​

∣+∣W
C
	​

∣+2.

Keep a complete justification for excluding length two. It can be shortened by observing that both components after bridge deletion have minimum degree at least two, but do not replace it with an unexplained assertion that their facial boundaries are cycles.

B21. Put the easy bridge-relaxed two-degree case before the charging theorem

Location: move lines 436–455 to immediately after the new bridge-face lemma.
Severity: SIGNIFICANT.

The current proposition depends on a step buried inside the preceding theorem and repeats much of Section 4.1. 

apg101

Execute: After the new lemma, give the proposition using just: the bipartiteness observation from Section 4.1; charge at most 1 for non-bridges; charge at most 5/6 for bridges; contradiction. This makes the remaining two-face-size case unmistakably the difficult extension.

B22. Relocate and complete the bridged-APG construction

Location: lines 282–291.
Severity: SIGNIFICANT.

This is a useful scope nonexample, but it currently precedes the extension’s mechanism and assumes a suitable exterior attachment vertex without saying how it is obtained. 

apg101

Execute: Move it to a remark after the extension. Specify three copies of a concrete seed, such as Schneider-17 in the source’s Figure 2. 
AMC Journal
 Choose a degree-5 vertex in each and redraw with an incident face exterior. Join the same selected vertex of the middle copy to the selected vertices of the other two.

Retain the degree check 7,6,6, and replace “at least 13” by the transparent calculation

∣F
new
	​

∣=∣F
1
	​

∣+∣F
2
	​

∣+∣F
3
	​

∣+4≥13.

Conclude that bridge-relaxed APGs in general need not be bridgeless. Do not make the reader verify this larger construction before learning the charging mechanism.

B23. Make the local-estimate cases visually parallel and expose the bridge-face hypothesis

Location: lines 362–377.
Severity: SIGNIFICANT.

The cases are correct, but the bridge line appears to use only the preceding s
2
	​

≥8, and the degree-5 comment is not established by the three displayed cases alone. 

apg101

Execute: Introduce the cases with both facts:

Every bridge-face has size at least eight, and s
2
	​

≥8. Every non-bridge separates an s
1
	​

-face from an s
2
	​

-face.

Present three compact rows: bridge; non-bridge with both degrees at least four; non-bridge incident with degree three. Give the charge sum and excess bound in parallel columns or aligned lines.

Delete the degree-5 concluding sentence. It is unnecessary and currently anticipates a further estimate.

B24. Delete the unnecessary exact 3−4 classification

Location: lines 380–384; corresponding preview at lines 297–299.
Severity: SIGNIFICANT.

The charging proof needs a unique degree-3 endpoint, not proof that the other endpoint has degree four. The extra classification adds an unused implication and the distracting decimal fraction 12.8/24. 

apg101

Execute: Delete lines 380–384 except the Step 2 heading. In the preview, replace “non-bridge 3−4 edges” with “non-bridge edges incident with a degree-3 vertex.” Start Step 2 directly with the positive edge and its unique degree-3 endpoint.

This also makes the optional weaker-bound discussion less fragile, as C5 explains.

B25. Preserve the assignment proof, but consolidate its repeated qualification

Location: lines 386–405.
Severity: SIGNIFICANT.

This is the genuine bottleneck and already one of the manuscript’s strongest passages. Its only excess is repeating the same conditional qualification after it has been established. 

apg101

Execute: Preserve, explicitly, these four implications:

A positive edge is non-bridge and has a unique degree-3 endpoint.

At that endpoint, parity and the presence of a non-bridge edge force exactly one bridge.

Therefore the assignment is defined and single-valued.

A bridge has at most one degree-3 endpoint, with at most two other incident edges.

Compress lines 394–397 to:

The non-bridge incidence is essential: a degree-3 vertex with three incident bridges would receive no such assignment.

Do not replace the proof by “charge each positive edge to a nearby bridge.” “Nearby” would erase exactly the work the referee must check.

B26. Name the final summation step and label the reusable identities

Location: lines 159–164, 182–184, 408–415.
Severity: POLISH.

“Step 3” has no descriptive title, and the two identities most likely to be cited during checking are unnumbered. 

apg101 +1

Execute: Title it “Step 3: summing the excesses.” Number the global identity ∑x(a)=2 and the final bridge inequality. Define P and B before the displayed summation and retain the explicit partition into positive edges, bridges, and remaining edges.

Do not add explanatory prose to the final arithmetic: its present length is appropriate.

B27. Dispose of the bridgeless case at the start

Location: lines 341–342 and 418–421; corollary at lines 330–333.
Severity: POLISH.

The end of the proof re-proves the already established bridgeless case. 

apg101

Execute: Begin:

If G has no bridge, it satisfies the original definition and is excluded by Theorem 4.1. Thus assume B≥1.

Delete the repeated final case. The even-degree corollary can then be removed as a separately numbered result: the moved parity lemma already provides its content, and no remaining argument needs that corollary.

B28. Retain only the useful slack observation

Location: lines 424–434.
Severity: SIGNIFICANT, implementing C4–C5.

The remark begins with a valuable explanation but develops into a sensitivity analysis longer than its contribution warrants. 

apg101

Execute: Reduce it to:

The essential point is the bound relating positive edges to bridges. Even the weaker estimate P≤4B would give total excess at most zero; the sharper bound P≤2B supplies a negative margin.

Delete the remaining parameter discussion from the note. Preserve any desired sensitivity calculations in working notes, not as a qualification needed to understand the theorem.

Audit trail and final polish
B29. Replace defensive or metaphor-heavy phrases with mathematical descriptions

Location: lines 35–36, 57, 63, 138–139, 147–148, 225, 269–272, 425–433.
Severity: POLISH.

“Engine,” “budget,” “tether,” “closes nothing,” “emphatically,” and repeated assertions that the source did not connect its sections make the note sound partly like a response to earlier reviews. 

apg101 +2

Execute: Use “face-incidence count,” “bound,” “assignment,” and “does not yield a contradiction.” Keep standard “charge” and “excess.” Keep explicit difficulty signals, especially:

The essential step is to bound the number of positive edges assigned to each bridge.

The aim is not to make the proof sound effortless.

B30. Add a precise computational-support statement, not a claim of unspecified verification

Location: new endmatter paragraph beside the relocated AI disclosure.
Severity: SIGNIFICANT for the requested L3 standard; not a mathematical prerequisite.

The submitted source does not explain the machine verification mentioned in your context. 

apg101

Execute: State which of the following actually occurred: exact-arithmetic checks, tests on explicit embeddings, finite-case enumeration, or proof-assistant verification. Identify the checked claims and distinguish checks of examples from universal arguments.

If checks were advisory, say that the theorem’s proof is the self-contained argument in the note and does not depend on computation. A repository is then supplementary, not something the referee must execute. If making a reproducibility claim, provide a fixed version, an entry command, expected output, and relevant representation assumptions—particularly whether face size counts boundary incidences. Do not call testing “formal verification,” and do not invent missing records.

B31. Perform a final source-to-PDF release check after the restructuring

Location: entire source, especially moved labels, theorem numbering, and endmatter.
Severity: POLISH.

The proposed moves affect cross-references and proof boundaries; I have not assessed the compiled layout.

Execute: Compile with the journal class until cross-references stabilize. Check for undefined references, duplicated proof-ending marks, orphaned case headings, and a page break separating the assignment rule from its capacity argument. Keep each short example with its calculation.

The existing abstract is approximately 146 prose words, below the journal’s 200-word maximum; keep the revised abstract within that limit and free of numbered internal references. 
AustMS Journal

Final disposition

Preserve the mathematics of the charge identity, the corner-parity argument, the bridge-face splice, and the unique-assignment/capacity proof. These are not passages that need to be made reassuringly shorter at the expense of their assumptions.

The revised note should let the reader see two distinct achievements: a short parity-and-incidence proof of the original conjecture, followed by a genuinely harder bridge-relaxed extension. The largest gains will come from correcting the scope statements, replacing repeated defence with explicit orientation, deleting the unused 3−4 classification and sensitivity detour, and adding the nine-vertex worked example. The result should be shorter overall while making the actual mathematical work more—not less—visible.
