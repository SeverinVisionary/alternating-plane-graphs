# Cap-facial Boolean exact-map cloud run report

- UTC run window: 2026-08-31T05:37:45Z through 2026-08-31T06:12:36Z.
- Authoritative source commit: `5048157a686fe2422582b5f041f0f1c1ed1ccab5`.
- Authoritative source tree: `7159563eddfe7036bb3aacb0600076bbc19fd825`.
- Environment: isolated Linux x86_64 Cloud checkout; Python 3.14.4; Z3 5.1.0; one solver thread.
- Both mandatory controls passed. Order 20 was SAT/CANDIDATE and passed both independent verifiers. Dynamically capped A21 was SAT/CANDIDATE; its postprocessor was CERTIFIED with cap opening, all nine closures, t=0, and r gates passing.

## Target dispositions

| profile | raw disposition | Z3 | raw SHA-256 | block certificate exists | target certificate exists | nonexistence claimed |
|---|---|---|---|---|---|---|
| (28,12) | INCOMPLETE | unknown | `ee1b13c304a17a730adf225d7c6ce1f2c0992fb35aa8a51d93fa0c964790705e` | false | false | false |
| (29,12) | INCOMPLETE | unknown | `63784baad9a1726c92f2f6af0e922539a093d5ffc02b60de601b914ca4f8ddcb` | false | false | false |
| (31,12) | INCOMPLETE | unknown | `4b19ee07d6be3a4ff90755274fe559f96c9dc7b79e01eb0f032d61a9a96c8ae9` | false | false | false |

No target candidate qualified for postprocessing. The positive-triple gate was not met, so no promotion handoff was assembled and `CLOUD_TARGET_PROMOTION_JOB.md` was not run. These timeout/unknown outcomes make the target search INCOMPLETE/BLOCKED only; they do not establish nonexistence.
