# Published known-answer fixtures

> **The `.plc` bytes referred to below are not in this repository.** No licence
> statement was found at their source, so they are not redistributed; each graph
> is re-expressed in this repository's own `apg-plane-rotation-v1` format, and
> the digest of every original is kept in
> [`../UPSTREAM_PROVENANCE.json`](../UPSTREAM_PROVENANCE.json). Byte-level checks
> described here skip unless the corpus is restored alongside this tree. See
> [`../../NOTICE.md`](../../NOTICE.md).

These four controls were downloaded on 2026-08-29 from the machine-readable
corpus linked by Ingo Althofer's page for the 2015 paper *Alternating Plane
Graphs*. The corpus table describes each download as `planar_code`, whose
neighbor lists are clockwise rotations.

Source table: <https://www.althofer.de/apg/table.html>

| stored source | direct source URL | SHA-256 | normalized JSON |
| --- | --- | --- | --- |
| `upstream/01_17-17_schneider17.plc` | <https://www.althofer.de/apg/apgs/01_17-17_schneider17.plc> | `648a97ff8331890b61031ddb83f0713f04c19cc71721ff7cd99ce69ef88c9fe3` | `schneider17.json` |
| `upstream/02_17-17_ghent17.plc` | <https://www.althofer.de/apg/apgs/02_17-17_ghent17.plc> | `6f9d5ba66b7e5fb1b9ec0c7fce778cfe8286196f9224c649edbd331499dc53b5` | `ghent17.json` |
| `upstream/08_20-20.plc` | <https://www.althofer.de/apg/apgs/08_20-20.plc> | `cf66ec94e724f574f24539e2ae2fa034cd2c249c63bf55a28c6c729002f53f22` | `order20.json` |
| `upstream/86_42-42.plc` | <https://www.althofer.de/apg/apgs/86_42-42.plc> | `0de4200db2fb26bcd348eccc30c144e80919201fe84757079fe8426957a94c4a` | `order42.json` |

The two order-17 files are independently attributed in the source table to
Frank Schneider and to the Ghent group with Frank Schneider. Orders 20 and 42
exercise the same definition at two additional published orders, including the
largest order reported from the paper's heuristic search.

`import_planar_code.py` performs the one-way conversion. It rotates each
clockwise neighbor list so its smallest label appears first, then writes the
deterministic JSON schema consumed by `verify.py`. The production verifier does
not import or call the converter. The test suite re-runs each conversion and
requires byte-for-byte equality with the stored JSON fixture.
