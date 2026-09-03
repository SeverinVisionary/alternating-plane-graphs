# Boolean socket-normal-form Cloud run

- Source commit: `1c406a43e8e201d2f000b0210ecf70e8e7be9455`
- Source tree: `4ff0fb7c7775bf3647a7c4ec08364c5f053737f0`
- Environment: isolated Linux x86_64 Cloud checkout; Python 3.14.4; Z3 5.1.0; one solver thread; seed zero.
- Source gate: clean initial checkout, exact commit/tree, `git fsck --full` passed; configured repository source binding used as directed.
- Controls: order-20 closed-map control `CANDIDATE/sat`, with both independent verifiers passing; canonicalized A21 control `CANDIDATE/sat/canonical=true`, postprocessed `CERTIFIED` with all nine closures and both gates passing.
- Target execution: strictly serial in the mandated order. No target emitted a candidate, so conditional target postprocessing did not run and no target certificate exists.
- `nonexistence_claimed=false` unconditionally. No promotion was launched.

| profile `(b,r)` | process exit | raw disposition | Z3 result | solver wall seconds | postprocessed | target_certificate_exists | final disposition |
|---|---:|---|---|---:|---|---|---|
| `(28,12)` | 0 | `INCOMPLETE` | `unknown` | 642.177 | no | `false` | `INCOMPLETE` |
| `(29,12)` | 0 | `INCOMPLETE` | `unknown` | 642.706 | no | `false` | `INCOMPLETE` |
| `(31,12)` | 0 | `INCOMPLETE` | `unknown` | 648.506 | no | `false` | `INCOMPLETE` |

## Candidate and certificate paths

- Targets `(28,12)`, `(29,12)`, `(31,12)`: none.
- Mandatory A21 control candidate and its nine closure certificates are retained under `bool_known_A21_socket_normal_form_postprocess_certificates/`; these are control evidence only, not target certificates.
