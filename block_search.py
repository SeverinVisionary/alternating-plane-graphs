#!/usr/bin/env python3
"""Hard-walled CNF search for a strict two-socket block.

The wall is enforced from a parent process because pysat's CaDiCaL binding has
no ``solve_limited``: an in-process timer cannot interrupt it, and a budget
checked only between ``solve()`` calls lets one long call run past it.  That
distinction matters for the recorded disposition -- ``INCOMPLETE`` here means
the wall clock ran out, never that the solver reported anything.

A raw model is a CANDIDATE ONLY.  It must pass blocks.validate_block here,
and a validated block still needs the nine-closure / two-verifier promotion
boundary before any claim.  A timeout is INCOMPLETE.  Solver unsat is
ENCODING_UNSAT: a statement about this encoding at this profile, never a
nonexistence theorem.
"""
import sys, time, json, pathlib, collections, multiprocessing

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import exact_map_cnf as cnf
import blocks
from pysat.solvers import Cadical195

def worker(clauses, outbox, inbox):
    s = Cadical195(bootstrap_with=clauses)
    try:
        while True:
            if s.solve() is False:
                outbox.put(("unsat", None)); return
            outbox.put(("model", s.get_model()))
            b = inbox.get()
            if b is None: return
            s.add_clause(b)
    finally:
        s.delete()

def run(order, r, budget, t0=True):
    d, f = cnf.block_profile(order, r)
    t = time.time()
    enc = cnf.ClosedMapCNF(d, f, open_block=True, require_t0=t0)
    build = time.time()-t
    print(f"block({order},{r}) t0={t0}: build {build:.1f}s {enc.statistics()}", flush=True)
    ctx = multiprocessing.get_context("fork")
    out, inp = ctx.Queue(), ctx.Queue()
    proc = ctx.Process(target=worker, args=(enc.clauses, out, inp)); proc.start()
    started = time.time(); models = 0; reasons = collections.Counter(); disp = "INCOMPLETE"
    try:
        while True:
            left = budget - (time.time()-started)
            if left <= 0: break
            try: kind, payload = out.get(timeout=left)
            except Exception: break
            if kind == "unsat":
                disp = "ENCODING_UNSAT"; break
            models += 1
            alpha = enc.alpha_from_model(set(payload))
            rot_json = cnf.dump_rotation(d, alpha)
            try:
                sockets = blocks.validate_block(blocks.rotation_from_certificate(rot_json))
                p = pathlib.Path(__file__).resolve().parent / 'results' / 'blocks' / f'CANDIDATE_{order}_{r}.json'
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(json.dumps(rot_json, indent=2, sort_keys=True))
                disp = "STRICT_BLOCK_CANDIDATE"
                print(f"  *** block({order},{r}): STRICT BLOCK CANDIDATE at model #{models} -> {p}", flush=True)
                print(f"      sockets: {sockets}", flush=True)
                break
            except blocks.BlockError as err:
                reasons[str(err)[:60]] += 1
                inp.put(enc.blocking_clause(alpha))
            if models % 200 == 0:
                print(f"  block({order},{r}): {models} candidates rejected ({time.time()-started:.0f}s) top={reasons.most_common(2)}", flush=True)
    finally:
        elapsed = time.time()-started
        if proc.is_alive(): proc.terminate()
        proc.join(timeout=10)
    print(f"block({order},{r}) t0={t0} -> {disp} after {elapsed:.0f}s, {models} raw models examined; "
          f"reasons={reasons.most_common(4)}", flush=True)
    return {"order":order,"r":r,"t0":t0,"disposition":disp,"seconds":round(elapsed,1),
            "raw_models":models,"clauses":len(enc.clauses),
            "rejection_reasons":dict(reasons),"nonexistence_claimed":False}

if __name__ == "__main__":
    budget = float(sys.argv[1]); out = []
    for spec in sys.argv[2:]:
        o, r = spec.split(","); out.append(run(int(o), int(r), budget))
        record = {"tool": "block_search.py", "budget_seconds": budget,
                  "note": "positive-witness engine; a raw model is a candidate only and "
                          "still needs the nine-closure/two-verifier promotion boundary. "
                          "INCOMPLETE means the wall clock ran out; ENCODING_UNSAT is a "
                          "statement about this encoding at this profile, never nonexistence.",
                  "results": out, "nonexistence_claimed": False}
        pathlib.Path(sys.argv[0]).resolve().parent.joinpath(
            'results', 'logs', 'block_search_20260901.json').write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n")
