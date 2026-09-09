Overall judgment

Keep five figures and two tables—but replace the present Figure 5 with a picture of the assignment proving P≤2B. The current allocation gives a figure to the final construction remark but none to the step the manuscript identifies as its bottleneck. 

apg101(2) +1

The numerical checks pass. The two fully drawn graphs have the stated degrees, facial walks and incidences, and both tables have correct arithmetic. Figure 3’s caption contains a false sentence. Figure 5’s construction is correct in the prose, but its drawing obscures the crucial identification of the central vertex.

I read the complete source and rendered all seven floats separately. The baustms class was unavailable, so I have checked the actual TikZ drawings and table contents, but not their final placement in the production-class PDF. The page-count assessment below is therefore an estimate.

Part 1 — Figures and tables
Figure 1 — The two quadrilaterals

Verdict: retain. ADD — make the repeated occurrence visible.

Correctness. The drawing has seven vertices and eight edges. The white cut vertex has degree four; the other six vertices have degree two. The facial boundary lengths are 4,4,8. The exterior walk visits the cut vertex twice within one circuit, giving eight vertex occurrences but seven distinct vertices. The two bounded quadrilateral faces meet only at that vertex and are not adjacent through an edge. Everything stated about the drawing is correct. 

apg101(2)

Value. This earns its space. It addresses an actual source of mistakes, rather than illustrating familiar terminology. It also supplies a concrete instance for the later distinction between corners and distinct incident faces.

Placement and caption. Its source position, immediately after the boundary-walk convention, is right. The caption already defines what is being counted, but it should explicitly identify this as a convention example rather than an alternating plane graph.

Recommended change. Put two small traversal arrows through the two exterior corners at the white vertex, or mark those two corners with the same exterior-face symbol. A fully numbered eight-step walk would be more clutter than help.

Replace the caption’s final sentence with:

“The numbers indicate face sizes; the exterior walk encounters the white vertex twice. This is a convention example, not an alternating plane graph.”

REJECT — an additional boundary-walk paragraph. The picture and the existing 8-versus-7 sentence already explain the distinction. More prose would repeat the lesson rather than strengthen it.

Figure 2 — The worked weak alternating graph

Verdict: retain. ADD — clarify the caption’s calibration role.

Correctness. I checked the drawing’s facial walks, not just its appearance. There are three degree-four vertices and six degree-two vertices, twelve edges, three quadrilateral faces, and two hexagonal faces. Every edge has endpoint degrees 2,4 and incident face sizes 4,6. Thus

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

Also v+f=9+5=14=e+2, and f/e=5/12. The exterior hexagon and the three quadrilateral labels occupy the correct regions. 

apg101(2) +1

Value. This is the strongest existing figure. It simultaneously demonstrates the charge identity, shows why the minimum-degree hypothesis matters, and calibrates the face bound. It should not be sacrificed for page count.

Placement and caption. Keep it beside Example ex:worked, preferably on the same page as the displayed calculation. Its caption is nearly standalone, but merely saying “white ones degree 2” makes the reader reconstruct why that matters.

Replace the degree-description sentence with:

“Filled vertices have degree 4; white vertices have degree 2, violating the minimum-degree-three requirement for an alternating plane graph.”

For the final calculation, print the four reciprocals rather than only c(a)=7/6. That makes the caption independently useful.

CONSIDER — highlight one representative edge; lean against. A slightly heavier edge could connect the four surrounding quantities to the calculation, but the drawing is already clean. Do not add four explanatory arrows: the adjacent worked example supplies those explanations.

Figure 3 — Corner occurrences

Verdict: ADD — essential caption correction; turn the bare fan into a parity illustration.

Correctness. The indexing is right: in the displayed cyclic order, F
i−1
	​

 and F
i
	​

 are the two sides of a
i
	​

, with indices modulo five. The false statement is the caption’s conclusion:

“At a cut vertex one face may occupy several of these corners, but never two consecutive ones.”

Consecutive occurrences of the same face occur precisely across a bridge. This contradicts the immediately preceding caption sentence and the correct explanation in the proof. 

apg101(2) +1

The minimal repair is:

“A face may occupy several corners at a cut vertex; two consecutive corners belong to the same face precisely when their separating edge is a bridge.”

The five spokes are not themselves an error: the current picture does not assert a proper two-colouring of its corner occurrences. But that is also its weakness.

Value. As drawn, it teaches the notation, not the parity argument. It can do both within essentially the same footprint.

Recommended change. Keep the five-spoke arrangement, mark a
1
	​

 as the unique bridge, and mark the corner colours cyclically as 0,1,0,1,0. Indicate F
5
	​

=F
1
	​

 across a
1
	​

. The other four edges are non-bridges and produce four colour changes.

Keep face-occurrence labels separate from colour labels: two nonconsecutive occurrences with colour 0 need not be occurrences of the same face.

A replacement caption could read:

“Corner occurrences at a vertex u, with indices modulo five: F
i−1
	​

 and F
i
	​

 lie on opposite sides of a
i
	​

. In the illustrated local configuration, a
1
	​

 is the only bridge and F
5
	​

=F
1
	​

; the two face colours change across the other four edges, illustrating that degu−∣{bridges at u}∣=4 is even.”

Placement. Keep it with the parity lemma. It should not float away from the cyclic-list proof: that proof is where the colour-change annotations earn their space.

Figure 4 — The face carrying a bridge

Verdict: CONSIDER — retain after improving the schematic; I lean toward retention.

Correctness. The decomposition

∣F∣=∣W
A
	​

∣+∣W
C
	​

∣+2

is right. Under the lemma’s hypotheses—connected, simple, plane, minimum degree at least three—both component-side walks have length at least three, giving 8. 

apg101(2)

However, the drawing is a component schematic, not a literal graph drawing. Its circles do not exhibit the degrees, the internal edges, or the lengths of W
A
	​

,W
C
	​

. Read literally as graph edges, each circle would look like a loop at its attachment vertex. The caption should prevent that reading.

Value. The potentially valuable information is the walk decomposition, not the fact that a bridge joins two components. At present the latter is drawn, while the former is mostly left to the caption.

Recommended change. Make the component outlines visually schematic and add traversal arrows: around W
A
	​

, along one side of a, around W
C
	​

, and back along the other side of a. The two arrows alongside the bridge represent two traversals, not parallel graph edges. Do not make W
A
	​

,W
C
	​

 look as though they are necessarily simple cycles.

Suggested caption:

“The outlines represent the components A,C of G−a, with internal edges omitted. The face carrying a=uw follows the component-side facial walks W
A
	​

,W
C
	​

 and traverses a once in each direction, giving ∣F∣=∣W
A
	​

∣+∣W
C
	​

∣+2. In the simple minimum-degree-three setting of the lemma, both walks have length at least three, so ∣F∣≥8.”

Placement. Move the float’s source location into the lemma’s discussion, after A,C,W
A
	​

,W
C
	​

 have been introduced. Currently the picture precedes even the lemma statement and asks the caption to introduce all four objects. 

apg101(2)

REJECT — replacing the schematic with two elaborate component drawings. Their internal combinatorics are irrelevant to the universal decomposition. Directional annotations give more explanatory value for less space.

Figure 5 — Three joined copies

Verdict: ADD — cut this figure and use its space for the assignment diagram. Retain the construction remark.

Correctness. The prose construction has the right arithmetic:

(degz
1
	​

,degz
2
	​

,degz
3
	​

)=(6,7,6),∣F
ext
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

The two bridges must attach to one and the same degree-five vertex in H
2
	​

. 

apg101(2)

The graphic instead draws two separate attachment points labelled z
2
	​

. Its caption explicitly tells the reader to identify them, so I would not call the prose construction false. Nevertheless, this is a poor visual convention here: the identification is exactly what produces degree seven and makes the new bridge endpoints have different degrees. A literal two-attachment-vertex construction would instead produce degree-six vertices at both ends of each new bridge and fail degree alternation. 

apg101(2)

Value. The remark earns its space because it prevents an overreading of the extension. The current figure adds little to that remark and makes its only delicate incidence harder to see.

Placement and caption. It appears before the remark that introduces the construction. That is not disastrous, but it further increases the caption’s explanatory burden.

CONSIDER — a corrected retained version; lean against. Draw one z
2
	​

, preferably at the top of the central component outline, with both bridges leaving the same exterior corner. Label the resulting degrees 6,7,6. Never duplicate this vertex for “legibility.”

My preferred action remains deletion. Remove the corresponding (Figure~\ref{fig:bridged}) from the remark so the cut does not leave a broken reference.

Table 1 — The two reciprocal budgets

Verdict: retain. ADD — make the mechanism, not just the bounds, explicit in the caption.

Correctness. Both rows are right:

3
1
	​

+
4
1
	​

=
12
7
	​

,
4
1
	​

+
6
1
	​

=
12
5
	​

,
12
7
	​

+
12
5
	​

=1.

The vertex and face contributions are exchanged correctly. These are upper bounds; the table does not require the displayed extremal values to be the only values present in the graph. 

apg101(2)

Value. Keep it. It lets the referee compare the two cases without mentally aligning two proof paragraphs. That is more useful than another picture of an edge.

Placement. Its source position before the proof is right: it functions as a map of the argument.

Caption. The current phrase “forces parity on the other side, which bounds it by 5/12” compresses away one essential ingredient: parity and distinctness together give 4,6, not parity alone.

Suggested replacement:

“Bounds for the endpoint-degree and incident-face contributions to c(a), their sum, at an edge a=uw with incident faces F
−
,F
+
. The two-valued hypothesis forces even values on the opposite side; alternation then gives the bound 5/12, versus 7/12 on the first side.”

ADD — related precision fix in the introduction. Replace “on the other side the two values are even” with “the two values encountered at each edge on the other side are distinct and even.” The current wording can suggest that the opposite side also has exactly two values, which is not the hypothesis. 

apg101(2)

Table 2 — The three edge cases

Verdict: retain. ADD — label the second column as an upper bound and distinguish eligibility from positivity.

Correctness. Every entry checks:

bridge
non-bridge, both endpoint degrees≥4
non-bridge, degree-three endpoint
	​

c(a)≤
5/6
109/120
25/24
	​

x(a)≤
−1/6
−11/120
1/24.
	​

	​


The use of 1/5 in the middle row is justified by distinct endpoint degrees. The final row permits positive excess but does not establish it. 

apg101(2)

Value. This earns its space. It isolates routine arithmetic so Step 2 can concentrate on the assignment.

Placement. Correct: after obtaining s
2
	​

≥8, before defining P. Keep it visibly attached to Step 1.

Recommended changes. Rename “vertex side + face side” to “upper-bounding reciprocal sum.” Otherwise that column can look like a statement of actual contributions rather than worst-case substitutions.

Suggested caption:

“Upper bounds for the four-term reciprocal edge charge c(a) and its excess x(a)=c(a)−1. Endpoint degrees are distinct and at least three; a bridge has one face of size at least eight on both sides, while a non-bridge separates faces of sizes s
1
	​

≥3 and s
2
	​

≥8. The last row permits, but does not assert, positive excess.”

Also delete the duplicated introduction “Three cases: Table … records the three resulting cases.” One sentence is enough. 

apg101(2)

What is genuinely missing

ADD — the assignment/capacity diagram, replacing current Figure 5.

Put it in Step 2, adjacent to the paragraph beginning “Now fix a bridge b.” Depict a bridge b=uw, a degree-three endpoint u, and its two remaining incident edges a
1
	​

,a
2
	​

, both marked non-bridges. Show dashed assignment arrows a
1
	​

↦b, a
2
	​

↦b. Label the other endpoint degw

=3, with its other incidences omitted. This displays both the local origin of the assignment and the reason a bridge cannot receive another two edges through its opposite endpoint. 

apg101(2)

Use this caption:

“Assignment at the degree-three endpoint u of an eligible edge. Parity forces a unique incident bridge b=uw, leaving two non-bridge edges to assign to b; degree alternation excludes a second degree-three endpoint at w. Dashed arrows denote assignments, not graph edges.”

This is a local configuration under the hypothetical counterexample assumptions, not a claimed example of a complete two-face-size graph.

The other missing visual information can be supplied by improving existing figures: colour changes in Figure 3 and traversal directions in Figure 4. No sixth figure is needed.

Part 2 — Metaphors and concrete handholds

I would use four inline handholds, predominantly as replacements rather than additions.

ADD 1 — Reciprocal charge and the total excess, in one accounting explanation

Location: replace the proof of Lemma lem:identity, currently beginning “A vertex of degree d …”. 

apg101(2)

“Distribute one unit from each vertex equally over its incident edges, and one unit from each face equally over its boundary side occurrences; the amount received by a is c(a). Thus the edges receive v+f units in all, and subtracting one per edge leaves v+f−e=2.”

This explains why those particular reciprocals appear and why the baseline is one per edge. It remains valid for bridges because the face unit is distributed over side occurrences, not distinct edges.

The honesty boundary matters: 2 is the total signed excess, not the total positive excess and not an upper bound on positive contributions. Also, this is a reframing of the incidence count, not a new redistribution step in the main proof.

ADD 2 — Corners as occurrences rather than faces

Location: in the paragraph before Figure fig:corners, replace the sentence beginning “Stating it over the corners at a vertex …”. 

apg101(2)

“A corner is a sector between consecutive edges at a vertex: there are degu corner occurrences even when fewer distinct faces meet u. In Figure 1, the cut vertex has four corners but only three incident faces, since the exterior face occupies two corners.”

This uses the paper’s own earlier example and supplies a concrete count. It is preferable to metaphors involving rooms, wedges of cake, or repeated “visits,” each of which would need translation back into incidence language.

ADD 3 — What bridge relaxation costs

Location: replace the paragraph in §5 beginning “The relaxation introduces exactly one new difficulty …”. 

apg101(2)

“Across a bridge, the original estimates lose distinct face sizes and can also lose even endpoint degrees. The large-face lemma controls the bridge’s own excess; the harder assignment in Step 2 controls the potentially positive non-bridge edges.”

This is more accurate than identifying only the failure of Case 2. Case 1 also loses its distinct-face-size estimate on bridges, which is why the bridge-face lemma is used in Proposition prop:twoY-weak. 

apg101(2)

What the relaxation buys is already stated clearly: a stronger theorem covering a larger class. No further metaphor is needed for that benefit.

ADD 4 — Why the bridge deficit pays for its assignments

Location: immediately after “Hence P≤2B,” before Step 3. 

apg101(2)

“In units of 1/24, the upper bounds are +1 per eligible edge and −4 per bridge, so even two assigned edges leave each bridge’s group with upper bound −2.”

This makes “expensive” precise and fixes the possible sign confusion: a large bridge face produces a smaller reciprocal contribution, hence a negative excess.

Crucially, put it after the capacity argument. Before that argument it would suggest that sufficient compensation is automatic. It is not. Also call these upper bounds in units of 1/24; actual edge charges need not be integer multiples of 1/24.

Concepts for which I would not add another metaphor
Concept	Ranked decision
Boundary-walk length versus distinct vertices	REJECT additional prose. Figure 1, with its repeated exterior occurrence marked, already gives the right concrete handhold.
Why the number of colour changes is even	REJECT a separate metaphor. “The cyclic list closes up, so the number of changes is even” is already the clearest statement. Improve Figure 3 rather than paraphrasing that sentence. 

apg101(2)


Why a bridge face has length at least eight	REJECT another analogy. The decomposition W
A
	​

,a,W
C
	​

,a
−1
, shown by traversal arrows, is the explanation. It must remain clear that the two lower bounds of three use the lemma’s graph hypotheses.
Positive-eligible versus actually positive	ADD the Table 2 caption clarification; REJECT a second inline explanation. “Permits, but does not assert, positive excess” is sufficient. Retain the term eligible throughout the assignment discussion.
The assignment being defined and single-valued	ADD the missing diagram; REJECT “routing,” “matching,” or other imported vocabulary. The existing proof correctly establishes a unique degree-three endpoint and a unique bridge there. Do not replace those checks with a slogan. 

apg101(2)


Why the capacity is two rather than four	ADD the opposite-endpoint label in the diagram; REJECT another paragraph. The obstruction is exactly degree alternation at the ends of the bridge. The existing remark correctly explains that four would already suffice for contradiction. 

apg101(2)


Exchanging vertex and face arguments without formally taking the dual	REJECT a metaphor or dual-graph figure. The existing sentence about a two-edge cut producing parallel dual edges is precise and appropriate for the intended referee. 

apg101(2)


The extremal numbers 3,4 and 4,6	ADD the introduction/Table 1 precision fixes above; REJECT a numerical aside. The reader needs to know that these are bounding pairs, not the complete value sets.

CONSIDER — an actual ordinary alternating plane graph near the definition; I lean against. There is an orientation gap: the two fully drawn examples are not ordinary alternating plane graphs, and the actual examples in the final remark are represented only by component outlines. Nevertheless, a fully legible Schneider-17 drawing would demand substantial space without removing a difficulty in either proof. Figure 2’s carefully identified near-example is the better use of space in this note.

Part 3 — Page count and readability trade
Recommended package: approximately the same ten pages

The proposed main revision is largely length-neutral:

Change	Length effect	Readability effect
Replace current Figure 5 with the assignment diagram	Approximately neutral: one float replaces one float	Moves visual attention to the proof’s bottleneck
Annotate Figures 1, 3 and 4 within their existing footprints	Little change apart from captions	Makes occurrences, colour changes and double traversal visible
Use the four inline handholds	Mostly replacement text; one short new sentence after P≤2B	Explains the accounting and bridge deficit without duplicating the proof
Clarify the two table captions	A few additional lines	Separates hypotheses, upper bounds and actual positivity
Retain the final construction remark but remove its figure reference	Saves a little prose	Preserves the extension’s scope without the misleading drawing convention

My working target is still ten pages. I would not promise nine, and I have not measured the revised pagination in baustms. An extra page caused by float movement would call for repacking or removing optional material, not smaller text or compressed diagrams.

CONSIDER — shorten the historical paragraph in the introduction; I lean toward doing so if space is needed. The paragraph on Lebesgue, Kotzig, discharging and light configurations is legitimate context, but its individual historical statements do not prepare the reader for a proof step. It can be shortened while preserving appropriate citations. By contrast, retain the precise explanation of how the argument relates to AHSSV §9.1: that is directly relevant attribution and orientation. 

apg101(2)

REJECT — adding a separate reciprocal-charge schematic, a budget bar chart, a full ordinary-APG plate, and the assignment figure on top of all five current figures. That would increase the visual inventory without a corresponding reduction in difficulty.

Would I submit at that length?

Yes, on the visual and expository grounds assessed here, I would submit the corrected, approximately ten-page version. The Bulletin’s current description prefers relatively short papers and says papers longer than twelve pages are not usually accepted; ten pages is within that preference, though that is not by itself an argument for keeping unnecessary material. 
Cambridge University Press

The important trade is not “more illustrations versus fewer pages.” It is less explanation of things the referee already understands, and a better illustration of the one incidence argument they must actually check. Fix Figure 3, remove Figure 5’s duplicated-vertex convention, and give Step 2 the visual space it deserves.
