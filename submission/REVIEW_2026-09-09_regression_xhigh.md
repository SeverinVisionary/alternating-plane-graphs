A — caption regressions

Figure 1 caption is still false. It says the exterior face occupies “three corners,” two at the white vertex. The exterior boundary walk has eight corner occurrences total; only two are at the white cut vertex. The three 8 labels are three placements of the face-size label, not three corners. This directly conflicts with the corrected body statement that the white vertex has four corners, with the exterior occupying two. 

apg101(3) +1


Fix: “the unbounded face is labelled three times in the drawing, including in both corners it occupies at the white vertex…”

Table 1’s new caption misstates the dependency. “The two-valued hypothesis … forces” the 7/12 bound and the opposite-side values to be distinct/even is not true by itself. The body correctly uses alternation to make adjacent values distinct, bipartiteness/parity to make the opposite side even, and bridgelessness in the face case. 

apg101(3) +1


Fix: replace “the two-valued hypothesis … forces” by “under the alternating hypotheses, the two-valued side …; bipartiteness/parity and alternation then make…”

Figure 4’s new traversal arrows are geometrically wrong. u=(0,0) and w=(2.5,0), but the arrows meant to depict W
A
	​

,W
C
	​

 are arcs starting at (-0.30,-0.90) and (3.80,0.90) and are not based at u,w. Thus the arrows do not visually form the continuous W
A
	​

,a,W
C
	​

,a traversal claimed by the caption. 

apg101(3)


Fix: make each W-arrow start/end at the corresponding bridge endpoint, or remove those arrows.

B — handhold regression

Lemma 3.1’s “signed excess” caveat contains a false claim. “2 … is … not a bound on any [positive excess]” is false. In the lemma’s simple loop-free setting, degu,degw≥1 and every facial walk has size at least 2, so

c(a)≤1+1+
2
1
	​

+
2
1
	​

=3,x(a)≤2.

Equality occurs for K
2
	​

. The point you want is only that ∑x(a)=2 by itself gives no useful per-edge control and is not the sum of the positive parts. 

apg101(3)

C — new Figure 5

Terminology/caption regression: the defined term is “positive-eligible”, but both the new 1/24-units handhold and Figure 5 silently shorten it to “eligible.” More importantly, “Parity forces u to lie on exactly one bridge” suppresses the crucial second premise: parity gives 1 or 3; the fact that the positive-eligible edge itself is a non-bridge rules out 3. 

apg101(3) +1


Fix: use “positive-eligible” everywhere and say “Parity, together with the incident non-bridge edge, forces…”

Minor drawing defect in Figure 5: the dashed arrows described as assignments “to b” terminate at (1.15,±0.52), while b lies on y=0; visually they point into empty space rather than to the bridge. 

apg101(3)

NO-GO — shortest blocking list: Figure 1 false corner caption; Lemma 3.1 false “not a bound” sentence; Table 1 caption’s false dependency claim; Figure 4 traversal arrows not actually forming the claimed traversal.
