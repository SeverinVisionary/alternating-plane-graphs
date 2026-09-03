import collections
from strip_lib import EDGES, ROT, OMEGA, DEG
from fractions import Fraction

# quotient darts 0..11, sigma from ROT, alpha pairs
sigma = {}
for v, cyc in ROT.items():
    for i, d in enumerate(cyc):
        sigma[d] = cyc[(i+1) % len(cyc)]
alpha = {2*e: 2*e+1 for e in range(6)} | {2*e+1: 2*e for e in range(6)}
sinv = {v:k for k,v in sigma.items()}
phi = {d: sinv[alpha[d]] for d in range(12)}
# faces as dart cycles
seen, faces = set(), []
for d in range(12):
    if d in seen: continue
    walk, c = [], d
    while c not in seen:
        seen.add(c); walk.append(c); c = phi[c]
    faces.append(walk)
print("faces (dart walks):", faces)

# dart displacement in omega: dart 2e (at first endpoint, pointing to second) = +omega[e]; dart 2e+1 = -omega[e]
def wdisp(d, w):
    e, side = d//2, d%2
    return w[e] if side == 0 else -w[e]

for f in faces:
    print("face", f, "omega-sum", sum(wdisp(d, OMEGA) for d in f))

# solve for tau: integer vector with each face sum 0, independent of omega mod coboundaries.
# unknowns tau[0..5]; constraints: for each face, sum_{darts} sign*tau[e] = 0
import itertools
import numpy as np
A = []
for f in faces:
    row = [0]*6
    for d in f:
        e, side = d//2, d%2
        row[e] += (1 if side==0 else -1)
    A.append(row)
A = np.array(A)
print("face constraint matrix:\n", A)
# nullspace over rationals
from sympy import Matrix
M = Matrix(A)
ns = M.nullspace()
print("nullspace dim:", len(ns))
for v in ns: print(v.T)
