# Disclosure of AI use

This work was produced with substantial assistance from large language models.
This file states the extent of that assistance, because it was not incidental
and because most venues now require it to be declared.

**No AI system is an author of this work, and none is credited as a
contributor.** That is the near-universal position of publishers and of COPE,
and it is also the right one: an author must be able to take responsibility for
the content, and a model cannot. Responsibility for every claim in this
repository rests with the named author.

## What was AI-assisted

Nearly all of it. Being specific is more useful than a general caveat:

* **The code.** Every module here -- the three verifiers, the splice
  construction, the connectivity and coverage tooling, the search lanes, the
  figure pipeline, the format and manifest tooling -- was written in sessions
  with an AI coding agent.
* **The certificates.** The 26 Conjecture 10.2 witnesses, the surgery witnesses
  at orders 37 and 38, and the order-46 counterexample were found by search
  programs written the same way, and in some cases located by an AI agent
  directly.
* **The proofs.** The arguments in `CONJECTURE_10_1.md`, `bridge_lemma.py` and
  `PUMPING_LEMMA_STATUS.md` were developed in the same sessions. In particular
  **the argument that removes the (C2) hypothesis from Conjecture 10.1 -- the
  step that makes that result unconditional -- was supplied by an AI reviewer**,
  not by the author, and was then verified independently before being adopted.
* **The prose.** These documents and the manuscript in `paper/` were drafted
  with the same assistance.

## What AI review changed

Independent AI reviewers were used adversarially throughout, instructed to break
the arguments rather than confirm them. They found errors that had been missed,
including three claims stated in this repository that were **false and had to be
withdrawn**. Those retractions are recorded at the files that made them and
collected in [`REVIEW.md`](REVIEW.md). A fourth error -- a certificate
misidentified as not 3-connected -- was also found in review and corrected.

This is disclosed rather than buried because it cuts both ways: the assistance
introduced errors as well as catching them.

## What is not taken on trust

The mathematics does not rest on any model's say-so.

* Every graph asserted here is an explicit rotation system, and every property
  claimed of it is recomputed on each run by three independently written
  decision procedures. See [`ARTIFACT.md`](ARTIFACT.md).
* The proofs in Sections 3 to 5 of the manuscript are ordinary mathematics and
  can be checked by a reader with no computer.
* Where a result rests on computation, the computation is named: the two finite
  hypotheses of the capping lemma, and the certificates themselves.
* Claims made by a reviewer were re-derived before being adopted. The (C2)
  closure was re-checked here by exhaustive search over degrees to 39 and face
  sizes to 59 in exact rational arithmetic before it was written up.
* One piece of reviewer evidence that was **not** reproduced -- a sweep over
  randomly generated bridged maps -- is labelled as testimony rather than as a
  gate, in [`REVIEW.md`](REVIEW.md).

## Tools

| model | role |
| --- | --- |
| Claude Opus 5 | primary agent: code, proofs, documents, manuscript |
| Claude Fable 5.1 | adversarial review; supplied the (C2) removal |
| ChatGPT (Pro tier) | independent proof review |
| Codex `gpt-5.6-terra`, `gpt-5.6-sol` | independent code and proof review |
| DeepSeek `v4-pro`, `v4-flash` | independent proof review |

Reviewer identities are not carried through the rest of the repository, which
attributes findings rather than reviewers; this table is the disclosure.

## The standard this aims at

Verifiability rather than provenance. A reader who distrusts every word of this
disclosure can still run `make verify`, read the proofs, and check the
certificates with third-party software via
[`export_planar_code.py`](export_planar_code.py). That is the point of shipping
the artifact rather than only the claims.
