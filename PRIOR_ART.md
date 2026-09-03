# PRIOR ART - (3,4,5)-alternating plane graphs, Conjecture 10.2

Repo gate artifact. The public sources listed below were checked through
2026-08-30 before any search or certificate code was written and before any
compute was dispatched.

## Literal admission decision

**ADMIT FOR EXPLORATORY CLOUD COMPUTE.** The 26-order frontier below remains
unresolved in the public record. No published theorem, public graph deposit,
author-hosted update, code repository, or forward citation found in this audit
contains a `(3,4,5)`-alternating plane graph at any target order.

This is a negative public-record audit, not proof that no private or unpublished
construction exists. No author correspondence was sent. A public closure claim
therefore requires a fresh source poll and, preferably, author/House-of-Graphs
reconciliation after candidate witnesses exist.

## Independent refresh (2026-08-30)

The public-record gate was independently refreshed after the first audit. The
live [House of Graphs alternating-plane-graphs meta-directory](https://houseofgraphs.org/meta-directory/alternating-plane-graphs)
and its public text-enquiry API returned exactly 88 records for the full phrase
`alternating plane graph`, all at orders 17 through 44; its intersection with
the 26 target orders is empty. The shorter `apg` query returned those same 88
records plus one unrelated order-16 graph. This is evidence about public
deposits, not a claim that House of Graphs is a complete census at larger
orders.

The current [Van Cleemput academic page](https://nvcleemp.be/academic/) still
lists the 2015 APG paper, old generator, and HoG corpus but no later APG
construction. The public [generator repository](https://github.com/nvcleemp/alternating)
has no target-order graph deposit; its default branch's last commit is dated
2013-11-07. Crossref, OpenAlex, COCI, Semantic Scholar, arXiv, and DBLP exact
title/DOI searches returned only the original work, an unrelated 2023 citation,
and the 2025 computer-assisted graph-theory survey, which cites the 2015 APG
paper but supplies no closure or target-order witness.

Accordingly the supportable statement is: **no published or publicly deposited
construction closing any target order was located in the 2026-08-30 audit.**
This does not prove the conjecture is unresolved by the whole mathematical
community: unindexed, differently named, private, or unpublished work remains
possible. Before any novelty claim, obtain a current existence-vector response
from the authors or House-of-Graphs maintainers.

## First-party prior-art sweep, 2026-09-01 — the gate closes on this, not on the poll

Every source below was fetched from the development machine in this session,
not relayed. The network restriction that forced the earlier poll does not
apply here: all five previously refused domains answer. This supersedes the
unprovenanced poll as the basis for the §0 gate; the poll remains archived and
is now corroboration rather than the record.

| source | queried | result |
| --- | --- | --- |
| **The paper itself** (UGent deposit) | 2026-09-01, `sha256 e1c72804…52884cf` | Definition 2.1/3.1, Theorem 3.2, Theorem 8.1 and Conjecture 10.2 read directly; the open set is `[46,56] ∪ [67,74] ∪ [88,92] ∪ {109,110}`, character for character our `T`. Quotes in the section above. |
| **Althöfer, `alternating-plane-graphs.html`** | 2026-09-01 | "Latest Update: December 01, 2014". No later construction. |
| **Althöfer, `alternating-planar-graphs.html`** | 2026-09-01 | "Latest Update: September 13, 2013". Board-game page; unrelated to the restricted class. |
| **Althöfer, `apg/table.html`** — the maintained table | 2026-09-01 | **88 entries, orders 4-44, intersection with `T` empty.** Parsed by column: `Index \| Order \| Faces \| Group \| Dual \| Author \| degree counts \| face counts`. The last row is index 88 at order 44. |
| **DataCite** (`api.datacite.org`, `"alternating plane graph"`) | 2026-09-01 | **0 results.** No DOI deposit anywhere in the DataCite graph. |
| **Crossref** (DOI `10.26493/1855-3974.584.09a`) | 2026-09-01 | Record confirmed, published 2015-05-29, `is-referenced-by-count: 1`. |
| **OpenAlex** (`cites:W1798145357`) | 2026-09-01 | 1 citing work: *Review and Assessment of Digital Twin-Oriented Social Network Simulators*, 2023 — unrelated. |
| **Semantic Scholar** (by DOI) | 2026-09-01 | `citationCount: 2` — the 2023 work above and *Computer-assisted graph theory: a survey*, 2025. Neither closes an order. |
| **`github.com/nvcleemp/alternating`** (the generator) | 2026-09-01 | `pushed_at 2013-11-07`, default branch `master`. No target-order deposit. |

**The one re-verification gap from the previous round is closed.** The
2026-08-30 audit read `althofer.de/apg/table.html` and the operator poll could
not fetch it. It has now been read here and parsed by column, and the numbers
that looked like target orders in a flat text scan are the table's **index**
column: rows 46-88 exist, orders 46-110 do not. That is exactly the trap §0
warns about, met and cleared.

### What is still not covered

Honest, and unchanged by this sweep:

- **Google Scholar** — queried by no leg, here or before. Bot-gated.
- **The House of Graphs user-upload database.** The meta-directory page is
  client-rendered and the search API returns `401 Unauthorized` without
  credentials, so it was not re-read first-party in this session. Two earlier
  legs on separate infrastructure did read it and agree: 88 records at orders
  17-44, empty intersection with `T`, plus **weak** alternating plane graphs
  (degrees 2 and `k`) at orders 48, 50, 51 and 55 — degree 2 is forbidden by
  Definition 2.1, so those are not witnesses. Anyone re-running this gate will
  meet those four numbers and must not mistake them.
- **Author correspondence.** Not sent. This is the difference between "not
  found in the public record" and "confirmed new", and `PRIOR_ART.md` has
  always said it is preferred before a public claim.

### Disposition

**The §0 gate is closed on first-party evidence** as of 2026-09-01: the record
is established with URLs, retrieval dates, a file hash and verbatim quotes; the
maintained author table and the DOI-repository sweep both return nothing at any
target order; and the citation graph holds two citing works, neither of which
settles anything. This is a negative public-record audit, not a proof that no
private or unindexed construction exists — the standard caveat, and the reason
the author email still matters.

## First-party source read, 2026-09-01

Every statement in the next section was previously transcribed from a session's
report. The PDF has now been fetched and read directly from this host, so the
quotes below are first-party.

| field | value |
| --- | --- |
| source | <https://backoffice.biblio.ugent.be/download/6921573/6921591> (UGent deposit of the AMC article) |
| retrieved | 2026-09-01 |
| `sha256` | `e1c72804d769a81c336638f118714338488a42f472fc087d1b492841852884cf` |
| size | 433 752 bytes |
| extraction | `pdftotext -layout` |

**Definition 2.1** (p. 339), verbatim:

> A plane graph is called an *alternating plane graph*, when the following
> conditions are fulfilled:
> - There are no adjacent vertices with the same degree.
> - There are no adjacent faces with the same size.
> - Each vertex has degree at least 3.
> - Each face has size at least 3.
>
> Note that the exterior face is also considered to be a face and also needs to
> satisfy the conditions above.

**Definition 3.1** (p. 339), verbatim:

> An alternating plane graph is called an `(x1, ..., xn)`-alternating plane
> graph if all vertices have degree `x1, ..., x_{n-1}` or `xn` and all faces
> have `x1, ..., x_{n-1}` or `xn` **sides**.

So face size is measured in **sides**, and the certificate contract's rejection
of facial walks that repeat a vertex is consistent with it: on this class every
face is a simple cycle, where sides, edges, vertices and walk length coincide.
The paper also treats APGs as **simple**: immediately after Definition 2.1 it
argues that the dual of a 2-edge-connected but not 3-edge-connected APG "is not
a simple graph, and therefore the dual is not an alternating plane graph", and
it notes that an APG is always at least 2-edge-connected.

**Theorem 3.2** (p. 340), verbatim, with a complete proof there:

> If `G` is a (3, 4, 5)-alternating plane graph, then `v3 = f3`, `v4 = f4` and
> `v5 = f5`.

The proof reaches `v5 = f5 = v3 - 4`; see
[`THEOREM_3_2_STATUS.md`](THEOREM_3_2_STATUS.md), which also records that the
derivation done here before the paper was read reproduces the proof's own
five-case table, and that the step it was missing is the (5,5)-combination
count.

**Theorem 8.1** (p. 356), verbatim:

> For any `n >= 111` there exists a (3,4,5)-alternating plane graph on `n`
> vertices.

with the construction `18a + 19b + 20c + 21d + 3` and the remark that the
Frobenius number of `18, 19, 20, 21` is 107.

**The open orders and Conjecture 10.2** (p. 362), verbatim:

> The exhaustive search showed that there are no (3,4,5)-alternating plane
> graphs on less than 17 vertices and on 18 and 19 vertices. The heuristic
> search found (3,4,5)-alternating plane graphs on all numbers of vertices from
> 20 to 42. In Section 8 we showed that (3,4,5)-alternating plane graphs exist
> on all numbers of vertices starting from 111, but the same construction can
> also construct (3,4,5)-alternating plane graphs on `n` vertices for
> `n ∈ [21, ..., 24] ∪ [39, ..., 45] ∪ [57, ..., 66] ∪ [75, ..., 87] ∪
> [93, ..., 108]`. This means that we do not know whether there exists a
> (3,4,5)-alternating plane graph on `n` vertices for
> `n ∈ [46, ..., 56] ∪ [67, ..., 74] ∪ [88, ..., 92] ∪ {109, 110}`.
>
> **Conjecture 10.2.** For all `n >= 20` there exist (3,4,5)-alternating plane
> graphs on `n` vertices.

That open set is the target set `T`, character for character.
[`test_conjecture_coverage.py`](test_conjecture_coverage.py) checks that the
paper's stated coverage leaves exactly those 26 orders and that the
certificates plus the paper close `[20, ∞)` with no gap.

## Frozen statement and terminology

Primary source:

- I. Althofer, J. K. Haugland, K. Scherer, F. Schneider, and N. Van
  Cleemput, *Alternating plane graphs*, Ars Mathematica Contemporanea 8(2)
  (2015), 337-363, DOI
  [10.26493/1855-3974.584.09a](https://doi.org/10.26493/1855-3974.584.09a).
  Published 2015-05-29; PDF read directly on 2026-08-29 from the
  [journal](https://amc-journal.eu/index.php/amc/article/view/584/798) and
  independently from the [UGent repository](https://backoffice.biblio.ugent.be/download/6921573/6921591).

Definition 2.1 requires a particular plane embedding in which adjacent vertices
have different degrees, adjacent faces have different sizes, every vertex has
degree at least 3, and every face (including the exterior face) has size at least
3. Definition 3.1 adds that both the vertex degrees and face sizes belong to the
specified set. Here that set is exactly `{3,4,5}`.

The target is the paper's Conjecture 10.2 (p. 362), quoted verbatim:

> "For all n ≥ 20 there exist (3,4,5)-alternating plane graphs on n vertices."

The positive-certificate gate is one explicit plane rotation system satisfying
that definition for every order in

```text
T = {46,47,48,49,50,51,52,53,54,55,56,
     67,68,69,70,71,72,73,74,
     88,89,90,91,92,
     109,110}.
```

The set has `11 + 8 + 5 + 2 = 26` orders. A partial witness set is progress,
not a solution of this target.

## Published 2015 frontier

The paper reports the following coverage:

| source within the paper | established orders |
| --- | --- |
| heuristic search, Section 6/10 | every order 20 through 42 |
| block construction, Section 8 | 21-24, 39-45, 57-66, 75-87, 93-108 |
| Theorem 8.1 | every order at least 111 |

Theorem 8.1 (p. 356), verbatim:

> "For any n ≥ 111 there exists a (3,4,5)-alternating plane graph on n vertices."

Its construction combines blocks of orders 21, 22, 23, and 24, identifying
three vertices at each join. The final order is

```text
18a + 19b + 20c + 21d + 3,
```

and the proof uses the Frobenius number 107 of `18,19,20,21`.

Section 10 then says the authors "do not know whether there exists" a target
graph at the four intervals making up `T`, immediately before stating
Conjecture 10.2. This is the source of the 26-order claim; it is not inferred
from a filename or recomputed record.

## Maintained and author-hosted sources

All sources in this section were retrieved again on 2026-08-29.

### House of Graphs

- The current [Alternating plane graphs meta-directory](https://houseofgraphs.org/meta-directory/alternating-plane-graphs)
  defines the same general APG class and links the 2015 paper and public
  generator. Its exhaustive table stops at order 19 with counts `2, 0, 5` for
  orders `17,18,19`. It says: "The numbers were independently verified."
- A live House of Graphs text search for `apg` returned 89 records. Extraction
  of all six result pages found 88 paper APG records (HoG ids 19338 through
  19512) at orders 17 through 44, plus one unrelated order-16 "Almost Planar
  Cap Graph" whose text also matches `apg`. No order in `T` occurs.
- The meta-directory is a complete small-order census; the 88 public records
  are selected graphs constructed for the paper. These scopes are different
  and neither is a hidden target-order collection.

### Authors' pages and corpus

- Ingo Althofer's [APG status page](https://althofer.de/alternating-plane-graphs.html)
  states "Latest Update: December 01, 2014." Its linked
  [machine-readable table](https://althofer.de/apg/table.html) contains 88
  selected planar-code examples, with maximum order 44. It has no target-order
  record and is an archive, not a current status assertion.
- Nico Van Cleemput's current [academic page](https://nvcleemp.be/academic/)
  lists publications through 2026. For APGs it lists only the 2015 paper, the
  old generator, and House of Graphs corpus. It says the programs reproduce
  the paper's results and that its graphs are in the HoG APG section. No later
  APG paper, result, software, or graph collection appears.
- The public [`nvcleemp/alternating`](https://github.com/nvcleemp/alternating)
  repository describes itself as "Generation and study of alternating planar
  graphs (and related animals)." GitHub's API reports creation on 2013-09-26,
  last push on 2013-11-07, and repository-metadata update on 2020-09-10. Its
  master tree contains generator/filter source and scripts, but no graph files
  at target orders and no post-paper result. The only other branch was abandoned
  in July 2013 because it gave no speed-up.

## Forward-citation and post-2015 audit

### Citation indexes

The DOI and exact title were checked in Crossref, OpenAlex, Semantic Scholar,
OpenCitations COCI, DBLP, and ordinary web search on 2026-08-29.

- [OpenAlex work W1798145357](https://openalex.org/W1798145357), updated
  2026-08-25, reports one citing work: a 2023 digital-twin/social-network
  simulator review. Its citation is unrelated to APG construction or status.
- [Semantic Scholar](https://www.semanticscholar.org/paper/d286fb9a63a926e12827d9bf9b9c3eb496ab3a19)
  reports that same work plus Jorik Jooken's 2025 survey below.
- [OpenCitations COCI](https://opencitations.net/index/coci/api/v1/citations/10.26493/1855-3974.584.09a)
  returns only the unrelated 2023 citation.
- Crossref exact-title/DOI search finds the 2015 paper and no later APG work.
  DBLP author/title searches likewise expose only the 2015 record.

The index disagreement is coverage, not a mathematical contradiction: Semantic
Scholar indexes the 2025 arXiv survey citation while OpenAlex and COCI currently
do not.

### 2025 survey

J. Jooken, [*Computer-assisted graph theory: a survey*](https://arxiv.org/abs/2508.20825),
submitted 2025-08-28, was read directly. Its generator/census table lists
"Alternating plane graphs" as a planar, degree-sequence-based class and cites
only the 2015 paper. It supplies no later construction, order vector, or closure
claim. This is useful corroboration that the public generator lineage had not
advanced by 2025, but it is not itself a maintained conjecture table.

### Direct searches

Exact searches were run for the title, DOI, `Conjecture 10.2`,
`(3,4,5)-alternating plane graph`, the author set, and the four target intervals.
GitHub code search for the exact conjecture and APG phrase returned no files.
No post-2015 paper, preprint, thesis, talk, repository, graph file, or status page
with a target-order witness was found.

Negative search results are supporting evidence only. The stronger evidence is
the current author bibliography plus a complete extraction of the live public
HoG APG deposits.

## Apparent contradictions resolved

1. **General APGs versus `(3,4,5)` APGs.** The abstract and Theorem 7.1 cover
   general alternating plane graphs from order 19. The gluing construction can
   create degrees/faces outside `{3,4,5}`. It does not settle Conjecture 10.2.
2. **3-edge-connected versus 3-connected.** Theorem 7.1 says
   3-edge-connected. Conjecture 10.3 asks for 3-vertex-connected graphs. These
   are different properties; neither changes the present target.
3. **HoG census versus HoG deposits.** The meta-directory's complete exhaustive
   census ends at 19. The searchable paper corpus contains selected examples
   through 44. Neither source asserts nonexistence above its enumerated range.
4. **Citation counts.** OpenAlex/COCI find one citation and Semantic Scholar
   finds two. The extra item is the 2025 survey; neither citation contains an
   APG witness or closure result.
5. **GitHub issue provenance.** The supplied issue-comment anchor currently
   returns 404 and the issue comments API is empty. The rerank text is now in
   issue #115's body. Its target list matches the primary paper exactly, so the
   deleted comment is not used as mathematical evidence.

## Known-answer and falsification requirements after this gate

The verifier/search package must keep these claims separate:

- Positive verifier controls: independently downloaded Schneider-17 and
  Ghent-17, plus published `(3,4,5)` witnesses at more than one other order.
- Negative verifier controls: deterministic certificate mutations that break,
  one at a time, rotation consistency, simplicity/connectivity, vertex-degree
  range, face-size range, vertex alternation, and face alternation.
- Search calibration: reproducing a known order-20/42 witness checks the search
  path. It does not prove completeness.
- The published absence at orders 18 and 19 is a generator-completeness claim,
  not an ordinary witness-verifier test. Reproducing it requires a separately
  costed exhaustive cloud run and explicit completeness accounting.

## Residual risk and re-poll rule

Not verified:

- private graph files or unpublished heuristic runs held by the authors;
- unindexed correspondence, talks, or deposits without APG terminology;
- House of Graphs records not tagged or described with `apg`.

These gaps do not reveal a public priority conflict, so exploratory compute is
admitted. They do constrain claim wording. Before publishing or submitting a
closure result, repeat the DOI/title/citation searches, the full HoG order
inventory, the authors' pages, and the public generator history. Then ask the
authors/HoG maintainers to reconcile any new 26-order witness vector before
claiming priority.

Approved interim wording:

> "In a public-record audit through 29 August 2026, we found no published or
> publicly deposited construction for the 26 orders left open in the 2015
> paper. This is an audit result, not a claim about private work."

## Partial re-poll, 2026-09-01 — **the gate is NOT closed**

> **Superseded the same day.** Kept as the record of what a container-bound
> worker could and could not reach. The first-party sweep at the top of this
> file reached every source named below as unreachable, and closes the gate.

Triggered by the 26 target certificates now in `certificates/targets/`. Section
0 requires a fresh poll immediately before any public claim. **This poll is
incomplete and does not discharge that requirement.**

**What could be checked.** Web search only. Queries for the conjecture, its
authors, and the target orders surfaced the 2015 paper, the AMC journal record,
Van Cleemput's academic page, Althöfer's alternating-plane-graphs pages, the
dblp record, and Jooken's 2025 computer-assisted graph theory survey
(arXiv:2508.20825, which cites the 2015 paper and closes nothing). No result
described a construction at any target order, and no post-2015 work on the
`(3,4,5)` restriction surfaced at all.

**What could NOT be checked, and this is the blocking part.** The primary
sources Section 0 insists on are unreachable from this session: `althofer.de`,
`houseofgraphs.org`, `amc-journal.eu` and `biblio.ugent.be` are all refused by
the network access proxy, for both `WebFetch` and `curl`. So the *maintained
tables and author status pages* — which Section 0 says outrank papers — were
not read. Neither was the 2015 PDF itself.

**A distinction worth stating explicitly, because conflating it is exactly the
error Section 0 exists to prevent.** Search summaries of Althöfer's pages say
alternating plane graphs "exist for all cardinalities from 19 on". That is the
**general** APG statement — no restriction on degrees or face sizes — and it is
*not* Conjecture 10.2, which is about the `(3,4,5)` restriction where both
vertex degrees and face sizes lie in `{3,4,5}`. The two smallest general APGs
have 17 vertices; the `(3,4,5)` case is strictly harder and is the one with the
26 open orders. A reader skimming the general result could easily conclude the
question was settled long ago. It is not the same question.

**Required before any public claim**, unchanged from the original audit and now
load-bearing:

1. Read the live House of Graphs alternating-plane-graphs meta-directory and
   Van Cleemput's and Althöfer's maintained pages directly, from a host with
   network access.
2. Obtain a current existence-vector response from the authors or the House of
   Graphs maintainers for the 26 orders.
3. Confirm the 2015 paper's face-size convention from the PDF — the walk-length
   convention is what the `F = n` identity implies, and the certificate
   contract depends on it.

Until those are done the supportable statement is only: **26 certificates exist
and pass two independent verifiers here; whether they are new is unestablished.**

> **Superseded.** The partial re-poll above was completed by the operator-
> dispatched poll recorded in the next section, which reached every primary
> source this session could not.

## Operator poll, 2026-09-01 — strong evidence, and the gate is still open

> **Superseded the same day.** This poll's missing provenance line is what kept
> the gate open, and the review panel was right to call that a CRITICAL. It no
> longer decides anything: the gate now rests on the first-party sweep at the
> top of this file, and this poll is corroboration. Its evidence agrees with
> the sweep on every point that could be compared.

Dispatched by the operator with [`PRIOR_ART.md`](PRIOR_ART.md)
verbatim, in an independent reviewer with browsing. Retrieval dates in the answer are
2026-08-31. Archived in full at
[`results/logs/prior_art_poll_20260901.md`](results/logs/prior_art_poll_20260901.md).

**Verdict returned**, quoting the answer:

> "Public-record verdict as of August 31, 2026: none of the 26 exceptional
> orders has a publicly verified settlement that I could find."

The order list it returns is character-for-character the repo's target set `T`.
The answer states its own scope correctly: "a **public-record conclusion**, not
proof that no private or unindexed graph exists."

### The gate is not closed, and calling it closed was the error

*Corrected 2026-09-01 after the review panel raised it as the run's only
CRITICAL. The previous version of this section said the gate was "discharged on
the substance" with provenance as a bookkeeping gap. That reading is not
available to us: the rule is ours and it is unconditional.*

The dispatch prompt requires the model identifier and mode (the recorded tier) to be
recorded **"or the run does not count toward the gate"**. Neither was pasted
back. So:

- The **evidence** is real, and it reaches the maintained tables and author
  pages that Section 0 says outrank papers — which no worker here can fetch.
  Nothing below is retracted.
- The **gate is open**. A poll that does not count toward the gate does not
  close it, and no amount of quality in its content changes that; the whole
  point of the provenance requirement is that it is checkable by someone who
  was not there.
- Cite this poll as "an operator-dispatched browsing poll, 2026-08-31", never
  as a `Pro`-tier independent review, and make **no novelty claim** until the
  identifier and mode arrive.

The cost of getting this wrong is exactly the failure Section 0 exists to
prevent, and this repository has paid it once already (`B(4,7) >= 42`, written
up as an improvement on a 27-year-old published bound).

### Reconciliation against the 2026-08-29 and 2026-08-30 audits

Agreement, independently re-derived by a different agent on different infrastructure:

| fact | this poll | earlier audits |
| --- | --- | --- |
| Althöfer `alternating-plane-graphs.html` last update | "Latest Update: December 01, 2014" | same string |
| `nvcleemp/alternating` last `master` commit | 2013-11-07 | 2013-11-07 |
| that repo contains no graph deposit at any target order | confirmed, 15-file tree enumerated | confirmed |
| Van Cleemput academic page lists no post-2015 APG work | confirmed | confirmed |
| HoG exhaustive APG census stops at 19, counts `2, 0, 5` | confirmed | confirmed |
| forward citations = Wen–Gabrys–Musial 2023 and Jooken 2025 | confirmed; neither closes anything | confirmed |
| general "from 19 on" result is *not* Conjecture 10.2 | confirmed explicitly | confirmed |

**Where this poll is stronger.** It read Althöfer's second page
(`alternating-planar-graphs.html`, "Latest Update: September 13, 2013"), which
earlier audits had not, and it read the House of Graphs meta-directory and the
author pages directly rather than through this session's blocked proxy.

**Where this poll is weaker, and the earlier audits cover it.** Google Scholar,
Crossref, OpenAlex and Semantic Scholar were all blocked in the poll's browsing
environment. The 2026-08-29 audit did reach
[OpenAlex W1798145357](https://openalex.org/W1798145357), Semantic Scholar and
OpenCitations COCI directly, and the 2026-08-30 refresh queried the House of
Graphs public text-enquiry API, extracting all 88 APG records (orders 17-44,
empty intersection with `T`).

**What neither leg covered** (added 2026-09-01, panel finding): **Google
Scholar** was reached by neither, so no citation index with its coverage has
been queried. The poll records no retrieval for `biblio.ugent.be` or
`api.datacite.org` either, and describes its own citing-work list as a
*verified lower bound*, not an exhaustive one. The union of the two legs is
therefore wide but not complete, and the earlier claim that they "cover every
index either one missed" was wrong. A settlement visible only through Google
Scholar, an institutional deposit or a DataCite DOI would still be missed.

### The one genuine discrepancy

The 2026-08-29 audit records reading
[`https://althofer.de/apg/table.html`](https://althofer.de/apg/table.html) and
finding 88 planar-code examples of maximum order 44. This poll reports that the
same URL "produced a redirect/fetch failure" and could not be inspected.

This is a **re-verification gap, not a mathematical conflict**: one leg read the
table and found nothing at a target order, the other could not reach it to
check. Nothing asserts a target-order entry exists. The table is in any case
described by its own parent page as supporting the *unrestricted* all-orders
construction, so it is not a maintained status table for Conjecture 10.2.

### A near-miss that a future auditor will hit

The House of Graphs meta-directory carries a second, larger table with rows at
orders **48, 50, 51 and 55** — four numbers inside `T`. Those rows are
**weak alternating plane graphs with degrees 2 and `k`**. They are not
`(3,4,5)`-APGs, they permit degree 2 which Definition 2.1 forbids outright, and
they settle nothing. Anyone re-running this gate will meet those four numbers
and must not mistake them for witnesses. Recorded here because the poll caught
it and the earlier audits did not mention it.

### Definition 2.1, and the face-size convention — resolved

The poll quotes Definition 2.1 as far as fair use allows:

> "There are no adjacent vertices with the same degree. There are no adjacent
> faces with the same size. Each vertex has degree at least 3."

plus, paraphrased, that every face has size at least three and that the exterior
face counts as a face and obeys the same conditions. Connectedness is **not** a
listed bullet; the paper instead derives that every APG is at least
2-edge-connected, since edge-connectivity one would give a face adjacent to
itself. House of Graphs states "simple, connected plane graph" outright.

On the question the certificate contract depended on — whether face size is the
length of the boundary **walk**, counting an edge twice when the walk traverses
it twice — the poll's answer is a clean negative:

> "No explicit statement of that convention was found in the paper."

**This retires the risk anyway, and unconditionally.** Both verifiers here
compute a face's size as the length of its facial walk
([`verify.py:203`](verify.py), [`verify_darts.py:189`](verify_darts.py)) **and**
separately reject any face whose walk repeats a vertex
([`verify.py:208`](verify.py), [`verify_darts.py:193`](verify_darts.py)). So on
every certificate in `certificates/targets/`, each face is a simple cycle. On a
simple cycle the walk length, the number of distinct edges, the number of
distinct vertices, and the number of "sides" are the *same integer*. Whichever
convention the paper intends, it assigns our faces the same sizes, so the
alternation condition it imposes is the identical check. The certificates
satisfy Definition 2.1 under every reading of "size".

Two consequences worth stating plainly:

1. The extra no-repeated-vertex condition can only **shrink** the class. A
   certificate that passes here is an APG under the paper's definition; the
   converse is not claimed and is not needed.
2. The convention would matter for a **nonexistence** claim, where a stricter
   contract could miss a witness. No nonexistence claim is made at any order in
   `T`. (The separate machine result that the `(1,0)` unrolling is uncappable is
   a statement about that seam, not about any order.)

Item 2 of the handoff is therefore closed. Connectedness is checked explicitly
by both verifiers, so the paper's 2-edge-connectivity remark is satisfied a
fortiori.

### What remains unverified after this poll

Carried forward, unchanged in substance:

- The **House of Graphs user-upload database** was not exhaustively searched by
  the poll (JavaScript/POST interface). The 2026-08-30 text-enquiry API sweep is
  the best evidence here and returned no target order, but it queried by
  description text, so an untagged user upload remains conceivable.
- **No author correspondence has been sent.** This is still the difference
  between "not found in the public record" and "confirmed new", and it is
  handoff item 3.
- Private, unpublished or differently-named work remains possible, as with any
  negative audit.
- `althofer.de/apg/table.html` was read once (2026-08-29) and not re-reached.

### Approved claim wording, updated

Superseded by the first-party sweep. The wording that matches the evidence as
of 2026-09-01 is:

> "In a first-party public-record audit on 1 September 2026 — the 2015 paper
> read directly, Althöfer's maintained table parsed by column, DataCite,
> Crossref, OpenAlex, Semantic Scholar and the authors' generator repository
> all queried — we found no published or publicly deposited
> (3,4,5)-alternating plane graph at any of the 26 orders left open in that
> paper. Google Scholar and the House of Graphs user-upload database were not
> queried, and the authors have not been contacted, so this is an audit result
> and not a claim about private or unindexed work."

