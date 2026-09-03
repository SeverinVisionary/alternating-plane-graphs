# Third-party material

[`LICENSE`](LICENSE) covers everything in this repository. No third-party bytes
are redistributed here.

## Source of the problem

Ingo Althofer, Jan Kristian Haugland, Karl Scherer, Frank Schneider and Nico
Van Cleemput, *Alternating plane graphs*, Ars Mathematica Contemporanea **8**
(2015) 337-363, DOI [`10.26493/1855-3974.584.09a`](https://doi.org/10.26493/1855-3974.584.09a).
All four open problems settled or discussed here are theirs. The definitions,
Theorem 3.2, Theorem 8.1 and Lemma 9.2 are cited and restated in this
repository's own words; a few conjecture statements are quoted verbatim, in
quotation marks and attributed, as is normal in citing a source. Attribution in full:
[`ATTRIBUTION.md`](ATTRIBUTION.md).

## The published corpus, and why it is not here

This work was built partly against 33 `planar_code` files of published
alternating plane graphs, hosted at `althofer.de/apg/apgs/`. **No licence or
terms-of-use statement was found at that source, and absence of a licence is not
permission**, so those bytes are not redistributed.

Each graph they carried is instead re-expressed in this repository's own
`apg-plane-rotation-v1` format, described in [`FORMATS.md`](FORMATS.md). A
rotation system is a mathematical object, and the JSON here is an encoding of it
defined in this repository, not a copy of anyone's file.

[`certificates/UPSTREAM_PROVENANCE.json`](certificates/UPSTREAM_PROVENANCE.json)
records, for each of the 33, the SHA-256 of the original bytes and of the
re-expression. Anyone holding the originals can confirm the correspondence by
decoding them with [`import_planar_code.py`](import_planar_code.py) and
comparing digests.

**Nothing that is settled depends on the bytes.** Conjectures 10.1, 10.2 and
10.3 all verify without them and `witness_coverage.residue()` is empty. Eleven
tests whose subject *is* the byte format -- the planar_code decoder, the
byte-level census, and search-lane seed replays -- skip in their absence and
pass for anyone who restores the corpus alongside this tree. See
[`conftest.py`](conftest.py).

## Census counts

Exhaustive counts attributed to House of Graphs (`houseofgraphs.org`) are used
as context only and are explicitly not load-bearing: see the "taken on trust"
section of [`CONJECTURE_10_3.md`](CONJECTURE_10_3.md). A single verified witness
settles each order, and every witness is verified here.
