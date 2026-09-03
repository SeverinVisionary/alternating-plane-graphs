# Prior-art poll — operator-dispatched leg, 2026-09-01

Archive of the prior-art rule re-poll. Dispatched by the operator using
[`PRIOR_ART.md`](../../PRIOR_ART.md) verbatim, because
`althofer.de`, `houseofgraphs.org`, `amc-journal.eu`, `biblio.ugent.be` and
`api.datacite.org` are all refused by this session's network access proxy.

## Provenance

| field | value |
| --- | --- |
| assistant | an independent reviewer (browsing enabled) |
| model identifier | **NOT RECORDED — operator to supply** |
| mode / the recorded tier | **NOT RECORDED — operator to supply** |
| retrieval dates claimed in the answer | 2026-08-31 |
| pasted into this repo | 2026-09-01 |
| prompt used | `PRIOR_ART.md`, unmodified |

⚠️ The dispatch prompt says the model identifier and mode must be recorded "or
the run does not count toward the gate". The pasted answer carries neither.
The **evidence** below is complete and is reconciled into `PRIOR_ART.md`; the
**provenance line** is outstanding. See `PRIOR_ART.md`, section "Operator poll,
2026-09-01", for exactly what that does and does not license.

## Verdict as returned

> **Public-record verdict as of August 31, 2026: none of the 26 exceptional
> orders has a publicly verified settlement that I could find.**

Orders returned as still open — identical to the repo's target set `T`:

```text
46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
67, 68, 69, 70, 71, 72, 73, 74,
88, 89, 90, 91, 92, 109, 110
```

The answer is explicit that this is "a **public-record conclusion**, not proof
that no private or unindexed graph exists."

---

## Response, verbatim

### Verdict

**Public-record verdict as of August 31, 2026: none of the 26 exceptional orders has a publicly verified settlement that I could find.** Accordingly, the following orders should still be treated as open:

```text
46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56,
67, 68, 69, 70, 71, 72, 73, 74,
88, 89, 90, 91, 92, 109, 110
```

The original paper identifies exactly these orders as unknown and then formulates Conjecture 10.2. I found no later restricted construction in the authors' pages, the House of Graphs meta-directory, the authors' GitHub repository, the forward-citing works I could verify, or exact-title/conjecture/order searches. This is a **public-record conclusion**, not proof that no private or unindexed graph exists. In particular, I could not exhaustively query House of Graphs' separate user-upload database. \[1]

#### The unrestricted result is separate

The paper itself makes the distinction immediately after Conjecture 10.2: it first gives the unknown restricted orders and then separately recalls that unrestricted APGs exist for every \(n\geq19\). Thus the unrestricted theorem does **not** settle any of the 26 restricted cases. \[1]

Althöfer's later of the two pages says:

> "for all numbers of vertices from 19 on"

But that sentence concerns general alternating plane graphs. The same page does mention the 3,4,5 restriction elsewhere, but it never says that restricted graphs exist at all orders from 19 onward. \[2]

### Direct source audit

All retrieval dates below are **August 31, 2026**.

#### 1. Ingo Althöfer: `alternating-plane-graphs.html`

URL: `https://althofer.de/alternating-plane-graphs.html`

Stated update:

> "Latest Update: December 01, 2014"

The page describes a construction of unrestricted APGs:

> "for all numbers of vertices from 19 on"

It also discusses 3,4,5-restricted examples and facts such as \(V=F\), but contains no Conjecture 10.2 status table, no announcement of a newly covered exceptional order, and no update later than December 2014 — before the final 2015 publication. \[2]

The linked explicit-construction table is at: `https://althofer.de/apg/table.html`

I could **not** inspect that table: following the link produced a redirect/fetch failure. The surrounding page unambiguously describes it as supporting the unrestricted all-orders-from-19 construction, not as a maintained table of the 26 restricted cases. \[2]

#### 2. Ingo Althöfer: `alternating-planar-graphs.html`

URL: `https://althofer.de/alternating-planar-graphs.html`

Stated update:

> "Latest Update: September 13, 2013"

This is an older version of substantially the same historical page. It records early restricted examples and unrestricted small-order results, but has no Conjecture 10.2 statement and no later settlement announcement. \[3]

There is a minor internal discrepancy between the two Althöfer pages:

* the "plane" page says the Nimczick–Schreiber graph has 25 vertices and 25 faces;
* the "planar" page says 25 vertices and 26 faces;
* both later caption it as having 25 **inner** faces.

The outer face may account for the difference, but that would be an inference, so I leave the discrepancy unresolved. It has no bearing on Conjecture 10.2. \[2]

#### 3. Nico Van Cleemput's academic page

URL: `https://nvcleemp.be/academic/`

No page-level "last updated" date is stated. The publication list includes a 2026 entry, so the page is not simply a 2015 snapshot, although that is not itself an update timestamp. \[4]

For the 2015 paper it says:

> "The graphs constructed in this paper are available in the Alternating Plane Graphs section of the House of Graphs."

It separately points to `nvcleemp/alternating` as the software used to reproduce the paper's results. It gives no open/closed status for Conjecture 10.2 and identifies no graph added after publication at an exceptional order. \[4]

#### 4. House of Graphs meta-directory

URL: `https://houseofgraphs.org/meta-directory/alternating-plane-graphs`

No last-updated date is stated.

The current indexed description calls an APG:

> "a simple, connected plane graph"

The ordinary APG census then lists only orders \(1\) through \(19\): two graphs at 17, none at 18, and five at 19. There is no ordinary-APG row — restricted or unrestricted — for any of the 26 orders. The meta-directory describes its lists as complete graph-class censuses only "up to a given order," so this table should not be read as an all-orders status table. \[5]

The same page contains a larger table with rows such as 48, 50, 51, and 55, but those are explicitly **weak alternating plane graphs with degrees 2 and \(k\)**. They are not (3,4,5)-APGs and do not settle the conjecture. \[5]

Therefore:

* **Within the meta-directory census:** I verified no (3,4,5)-APG at any exceptional order.
* **Within the broader House of Graphs user-upload database:** I could not establish a complete negative. Direct access returned:

> "You need to enable JavaScript to run this app."

The separate graph search uses a JavaScript/POST interface that I could not submit through the available browser. Thus I cannot honestly say that no individual user-uploaded graph exists somewhere outside the meta-directory collection. \[5]

#### 5. `nvcleemp/alternating` GitHub repository

URL: `https://github.com/nvcleemp/alternating`

The repository has two branches, `master` and `combined_fast`. The newest `master` commit is dated **November 7, 2013**, with message:

> "Program to find plane graphs with face-alternating matchings"

The other branch ended on July 16, 2013. Therefore I found no post-2013 commit activity on either branch.

The complete, non-truncated `master` tree contains 15 files: C source files, shell scripts, a makefile, and the bundled `plantri.c`. It contains no graph archive, planar-code data set, certificate, order-indexed construction directory, or later deposit addressing the 26 orders.

### Forward citations

#### Concrete citing records found

ResearchGate displays:

> "Citations (3)"

However, its three records resolve to **two distinct works**, because the 2023 journal article and its arXiv preprint are listed separately. \[6]

**1. Wen, Gabrys and Musial, 2023**

Jiaqi Wen, Bogdan Gabrys and Katarzyna Musial, *Review and Assessment of Digital Twin–Oriented Social Network Simulators*.

URLs: `https://arxiv.org/abs/2305.03234`; DOI `https://doi.org/10.1109/ACCESS.2023.3312129`

The paper's simulator appendix describes the APG repository as:

> "A generator for alternating planar graphs."

This is a software-directory citation. Searches within the full paper found neither "Conjecture 10.2" nor "(3,4,5)," and it reports no new APG construction or order. \[7]

**2. Jooken, 2025**

Jorik Jooken, *Computer-assisted graph theory: a survey*. URL: `https://arxiv.org/abs/2508.20825`

Its table of available graph generators and censuses includes:

> "Alternating plane graphs [3]"

The reference is part of a broad generator/census inventory. The paper does not mention Conjecture 10.2 or the (3,4,5) restriction and reports no newly covered order. \[8]

**Neither of these distinct citing works closes the conjecture or any one of the 26 cases.**

#### Citation-index checks and limitations

| Service | Result on August 31, 2026 |
| --- | --- |
| **Google Scholar** | The target citation request was blocked by the browsing environment; I could not obtain a reliable live count or citing-paper list. This must not be interpreted as zero citations. |
| **Crossref** | The DOI API request could not be opened in this environment, so I could not independently verify a Crossref citation count or citing list. |
| **OpenAlex** | The DOI API request was blocked, and the accessible website required JavaScript. I could not retrieve its live `cited_by` data. |
| **Semantic Scholar** | The target API/page request failed; no reliable live count or list was obtained. |
| **dblp** | The paper's bibliographic record is present, with DOI and "details & citations" links, but dblp did not expose a native complete citing list in the accessible record. Its citation details are delegated to external services such as Crossref/OpenAlex. \[9] |

Consequently, the two distinct citing works above are a **verified lower bound**, not a guaranteed exhaustive list of every citation in Google Scholar or other proprietary indexes.

### Definition 2.1, face size and connectedness

PDF used: `https://amc-journal.eu/index.php/amc/article/view/584/798` — retrieved August 31, 2026.

I cannot reproduce more than 25 words verbatim from the paper here. The maximal exact excerpt from Definition 2.1 is:

> "There are no adjacent vertices with the same degree. There are no adjacent faces with the same size. Each vertex has degree at least 3."

The remaining condition, faithfully paraphrased, requires every face to have size at least three; the following sentence says that the exterior face counts as a face and must satisfy the same conditions. \[1]

#### Is face size explicitly defined as boundary-walk length?

**No explicit statement of that convention was found in the paper.**

The paper uses "size" in Definition 2.1 and later speaks of faces having a specified number of "sides." But full-text searches produced no occurrence defining face size as:

* the length of the boundary walk;
* counting a repeated edge twice;
* or any equivalent explicit convention involving "walk," "boundary," or "twice."

Therefore I cannot verify the requested boundary-walk convention from a stated sentence in this paper. The identity obtained by summing face incidences may strongly indicate the standard convention, but — as requested — I am not using that inference as a substitute for an explicit definition. \[1]

#### Is connectedness part of Definition 2.1?

**Not as a separately listed condition.** Definition 2.1 begins with "a plane graph" and lists the two alternation conditions plus minimum vertex degree and minimum face size; connectedness is not one of those bullets.

Immediately afterward, however, the paper states that every APG is at least 2-edge-connected, explaining that edge-connectivity one would produce a face adjacent to itself. Thus connectedness is treated as a consequence of the APG conditions and surrounding plane-graph conventions, rather than as an explicit bullet in Definition 2.1. \[1]

House of Graphs now makes the convention explicit by saying "simple, connected plane graph." That is a wording difference, not a contradictory mathematical status claim. \[5]

### Other prior-art searches

Exact and near-exact searches for the paper title, "Conjecture 10.2," the (3,4,5)-APG terminology, individual exceptional ranges, and combinations with thesis, preprint, talk, construction, graph, Zenodo and repository terms did not surface a post-2015 work claiming a settlement. The results repeatedly led back to the original paper, the authors' historical pages, House of Graphs, the old GitHub generator, and the two later survey/review citations above. This is negative search evidence, not proof that an unindexed announcement cannot exist. \[6]

I found no public author status page that says, in current dated language, either "Conjecture 10.2 remains open" or "order \(n\) has now been settled." The most current author page points only to the original software and House of Graphs collection. \[4]

### Contradictions and ambiguities

1. **Unrestricted versus restricted:** no contradiction. "All orders from 19 onward" concerns unrestricted APGs; the paper separately states the restricted conjecture and the 26 unknown orders. \[2]
2. **House of Graphs rows at 48, 50, 51 and 55:** not restricted solutions. Those rows belong to the weak degree-\(2\)-and-\(k\) table. \[5]
3. **Connectedness:** the paper omits it from the bullet definition but derives at least 2-edge-connectivity; House of Graphs states connectedness explicitly. This is a presentation difference, not a substantive conflict. \[1]
4. **Althöfer's Nimczick–Schreiber counts:** one page says 25 faces, another 26, while the caption says 25 inner faces. I did not resolve the discrepancy by assumption. \[2]
5. **ResearchGate citation count:** "3" records correspond to two distinct works because one article is represented in both journal and preprint form. \[6]

### What I could not verify

* I could not perform an exhaustive search of the **broader House of Graphs user-upload database**; I verified only the indexed meta-directory census.
* I could not access Althöfer's linked unrestricted APG construction table at `https://althofer.de/apg/table.html`.
* I could not retrieve complete live citing-paper lists from Google Scholar, Crossref, OpenAlex or Semantic Scholar.
* I found no explicit boundary-walk definition of face size in the paper; the standard convention cannot be promoted from inference to quotation.
* I found no dated, current author declaration explicitly reaffirming the 26 cases as open.
* The forward-citation list is therefore a verified minimum, not certified exhaustive.

### Final record-status conclusion

On the publicly accessible evidence retrieved on **August 31, 2026**, there is **no verified publication, author announcement, repository deposit, or accessible maintained-table entry settling any of the 26 exceptional orders**. Subject to the specifically documented House of Graphs and citation-index limitations, all 26 remain open in the public record.

### Sources as cited in the answer

1. `https://amc-journal.eu/index.php/amc/article/view/584/798`
2. `https://althofer.de/alternating-plane-graphs.html`
3. `https://althofer.de/alternating-planar-graphs.html`
4. `https://nvcleemp.be/academic/`
5. `https://houseofgraphs.org/meta-directory/alternating-plane-graphs`
6. `https://www.researchgate.net/publication/285493639_Alternating_plane_graphs`
7. `https://arxiv.org/abs/2305.03234`
8. `https://arxiv.org/abs/2508.20825`
9. `https://dblp.org/pid/93/6359.html`
