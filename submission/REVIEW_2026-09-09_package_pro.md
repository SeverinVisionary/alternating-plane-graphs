1. Regressions

I found no dangling TeX references, missing proof dependencies, or justification that disappeared between the main theorem and the extension. There are, however, two false explanatory sentences and one small descriptive inconsistency:

apg101.tex:214–217, immediately before the parity lemma: “those corners are non-consecutive, so the alternation below is undisturbed.” This needs qualification: across a bridge, consecutive corners belong to the same face. The lemma’s proof handles this correctly; its introduction does not. Delete that clause or restrict it to crossings of non-bridge edges. 

apg101(1)

apg101.tex:237–243, the triangle-with-pendant-edge example: “although no vertex has even degree.” The listed degrees are 3,2,2,1, so two vertices have even degree. Change this to “although not every vertex has even degree.” 

apg101(1)

Introduction roadmap: “the two conventions that the source paper leaves implicit” conflicts with the later, correct statement that the source explicitly excludes bridges. Remove “that the source paper leaves implicit.” 

apg101(1) +1

None of these breaks the proofs.

2. New correctness defects

Apart from the explanatory errors above, I found no new mathematical defect. All four highlighted claims pass.

Nine-vertex example. The construction has three degree-4 vertices, six degree-2 vertices, twelve edges, three quadrilateral faces and two hexagonal faces. Every edge separates a quadrilateral from a hexagon, so its face contribution is 5/12, while its full charge is 7/6. Thus f=5=(5/12)e and total excess is 2. This genuinely establishes sharpness of the uniform face bound on the relevant weak class—not existence in the minimum-degree-3 class. 

apg101(1)

General bridge-face lemma. Correct without alternation. After deleting the bridge, both components actually have minimum degree at least 2, stronger than the stated intermediate bound of 1. Their exposed facial walks cannot have length 1 or 2 in a connected simple graph of that kind. Consequently the joined face has length at least 3+3+2=8. No deleted alternating-graph assumption is needed. 

apg101(1)

Bridgeless bridge-relaxed implies original definition. Correct: in a connected plane graph, an edge has the same face on both sides precisely when it is a bridge. With no bridges, requiring alternation between distinct adjacent faces imposes the original condition on every edge. 

apg101(1) +1

Three-copy construction. Correct. Crucially, the new bridges have endpoint degrees 6 and 7, not equal degrees. The chosen vertices’ original neighbours remain degree 3 or 4; interior faces remain size 3, 4 or 5; and the merged exterior has size at least 13. Both alternation requirements therefore survive where required. 

apg101(1)

I also checked the extension’s central assignment: uniqueness of the degree-3 endpoint and its unique incident bridge justify P≤2B; the final excess inequality follows. 

apg101(1)

3. Cover letter

The claimed contribution and separation between the original conjecture and the bridge-relaxed extension match the manuscript. Two accuracy/compliance adjustments remain.

At lines 28–30, “bounds the face count … by exactly this sum” should identify the face-incidence component of the four-term charge. Likewise, “never uses the hypothesis it is stated under” is too sweeping: the estimate uses bipartiteness and face alternation; it does not require degree 2 specifically. A narrow clarification is sufficient. 

COVER_LETTER

 
AMC Journal

The AI disclosure is substantively candid but not yet complete against Cambridge’s published guidance. It describes exploration, review, drafting and the origin of the extension, but identifies no tools or versions. The guidance asks for names and versions, dates and access information to the extent reasonably possible, and a description of use. Add the actual recoverable details; do not invent missing version information. The cover letter’s categorical “I confirm this satisfies…” should be removed or deferred until that is done. 

apg101(1)

 

COVER_LETTER

 
Cambridge University Press

Editorial tone: I would remove “not a weakness” and the invitation to determine whether the connection is already known. They risk sounding defensive or uncertain about prior-art diligence. It is fair for an editor to scrutinise originality and mathematical interest; brevity itself, independent status, or disclosed AI use is not a mathematical defect. Keep the factual attribution and disclosure. 

COVER_LETTER

The preprint/Green-access position is consistent with the journal’s published policy. 
AustMS Journal

4. Checklist

Add the following actual submission requirements, not merely manuscript-format checks:

Submission metadata: author name and ORCID, keywords, and MSC codes must be entered in the submission system. Having the latter two in the PDF, and the ORCID in the letter, is not the same check. 

CHECKLIST

 
AustMS Journal

Remaining compulsory attestations: this is not a replacement submission for an earlier submission still under consideration; authorship is complete and appropriate; the five-year public-access policy is accepted; and third-party rights, permissions and acknowledgements have been addressed where applicable. Also check for any potential competing interests requiring disclosure. 
AustMS Journal
+1

Author-verification check: explicitly confirm the sentence already printed—“The author re-derived every argument independently”—rather than treating an end-to-end PDF read as sufficient evidence for that stronger statement. Retain it only if accurate. 

CHECKLIST

 

apg101(1)

I found no listed journal requirement for the external human teach-back test. It remains a separate quality safeguard.

5. Go / no-go

NO-GO for the unchanged package; GO after a small correction pass and the author’s final line-by-line check. I found no proof-level reason to postpone submission.

Must fix before submitting:

Correct the two parity explanations and the “implicit conventions” sentence.

Make the cover-letter attribution precise, complete the AI disclosure, and ensure its author-verification claim is true.

Complete the missing submission checks, rebuild, and inspect the actual submission PDF.

Would improve it: remove the defensive cover-letter wording, give the otherwise unspecified “public repository” a stable locator in the computational-support paragraph, and perform the already proposed independent human teach-back. This model review does not satisfy that last test. 

apg101(1)

The final PDF’s rendering and the checklist’s archived-byte assertion were not verified in this pass.
