# Published search seeds

> **The `.plc` bytes referred to below are not in this repository.** No licence
> statement was found at their source, so they are not redistributed; each graph
> is re-expressed in this repository's own `apg-plane-rotation-v1` format, and
> the digest of every original is kept in
> [`../UPSTREAM_PROVENANCE.json`](../UPSTREAM_PROVENANCE.json). Byte-level checks
> described here skip unless the corpus is restored alongside this tree. See
> [`../../NOTICE.md`](../../NOTICE.md).

These deterministic JSON rotations were imported on 2026-08-29 from the
machine-readable corpus accompanying the 2015 paper. They are positive
`(3,4,5)`-APG controls and starting points for bounded block-opening/local-move
searches. They are not new constructions.

Source table: <https://www.althofer.de/apg/table.html>

| JSON | upstream `planar_code` | SHA-256 of upstream bytes |
| --- | --- | --- |
| `order21.json` | [`09_21-21.plc`](https://www.althofer.de/apg/apgs/09_21-21.plc) | `88edfd11d4e4a90678253f5d198fac43ae257f57a985b5064dcbd2c4b4df997a` |
| `order22.json` | [`10_22-22.plc`](https://www.althofer.de/apg/apgs/10_22-22.plc) | `d5f4d817bfb361adfdc20500fd7e125a8ed2c680237f7711be45e2b261856bf1` |
| `order23.json` | [`14_23-23.plc`](https://www.althofer.de/apg/apgs/14_23-23.plc) | `010887bde4d3d7bc47d20ffa9c2f16963d9e926e1e58241db46e5fe12cc024b2` |
| `order25.json` | [`24_25-25.plc`](https://www.althofer.de/apg/apgs/24_25-25.plc) | `9836752f4b3c3d9a69bbca7a46b115dead54e344ea9ad890dd399dd84abddce6` |
| `order29a.json` | [`31_29-29.plc`](https://www.althofer.de/apg/apgs/31_29-29.plc) | `35267740b45725b97fb886c6df73322a2c24e9315e46b98878d6d5800b6eaaf2` |
| `order29b.json` | [`32_29-29.plc`](https://www.althofer.de/apg/apgs/32_29-29.plc) | `71ed9d08270a9176483d41d6010fac640a17cb077e7b95f68e901b4ac60db2c1` |
| `order34a.json` | [`51_34-34.plc`](https://www.althofer.de/apg/apgs/51_34-34.plc) | `1f2670651eb62019115375bacd8335aaedf3e711ec6e9f4173ca1fce5e605f76` |
| `order34b.json` | [`52_34-34.plc`](https://www.althofer.de/apg/apgs/52_34-34.plc) | `db3d63e7859df75034f0c1314e7cb164ce086783ca761c1c2e7772ab20be8c15` |

The deterministic near-opening gate also preserves the exact upstream bytes
for `27_26-26.plc` (SHA-256
`d78efd8db7aa415f36a15a9225cbf0b7c1bacfe096051514a7614edd683c4902`),
`28_26-26.plc` (SHA-256
`adf39c3bb116a259efedaa6f9bb5c42734f262652dbe3fafd8fe5aafec17799c`),
`34_30-30.plc` (SHA-256
`30780d7a870fd5736afa6c9cb3b223b4e70012d4c01f8ed7080c2dd8adf8080a`),
`51_34-34.plc` (SHA-256
`1f2670651eb62019115375bacd8335aaedf3e711ec6e9f4173ca1fce5e605f76`),
and `44_33-33.plc` (SHA-256
`b779feb98cac0025bf165abd3b3d8e7968bff96bac5e428d17c7e1d07017a414`)
under `upstream/`. Their named-fan openings are diagnostic search seeds, not
new APG or strict-block witnesses.

The first three contain the paper's recoverable A-C two-hexagon blocks after
two closure fans are opened. The order-25, order-29, and order-34 files are the
published APGs at the three priority block orders. A direct opening scan is a
restricted test of these particular seeds only; failure to expose a compatible
block says nothing about existence at that block order.
