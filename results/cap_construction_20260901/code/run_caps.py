from capsearch import Search
import collections, sys

# boundary vertices of the cut triangle
X, Y, Z = 'X', 'Y', 'Z'
DEG = {X: 3, Y: 4, Z: 5}
ADJ = {frozenset((X,Y)), frozenset((Y,Z)), frozenset((Z,X))}

def search(name, region, forb, max_new):
    s = Search(region, forb, DEG, ADJ, max_new=max_new)
    sols = s.run()
    print(f"{name} (max_new={max_new}): {len(sols)} fillings, {s.nodes} nodes")
    bysize = collections.Counter(nnew for _,_,nnew in sols)
    print("  by interior-vertex count:", dict(sorted(bysize.items())))
    return sols

# capR: cap replacing the RIGHT side of directed C = x->y->z.
# region traversed with cap on the left: reversed cycle [Z, Y, X]
# forb: edge (Z,Y) -> surviving strip face size 5; (Y,X) -> 3; (X,Z) -> 4
# rems: Z:2, Y:1, X:0
capR_sols = {}
for mn in range(0, 13):
    sols = search("capR", [(Z,2),(Y,1),(X,0)], [5,3,4], mn)
    capR_sols[mn] = sols
print()
capL_sols = {}
for mn in range(0, 13):
    sols = search("capL", [(X,1),(Y,1),(Z,1)], [5,4,5], mn)
    capL_sols[mn] = sols
