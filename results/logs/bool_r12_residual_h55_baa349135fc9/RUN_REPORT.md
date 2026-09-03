# `r=12` residual-`H55` Boolean run report

- Run UTC: 2026-08-31.
- Source binding: commit `baa349135fc965f150460994bbb48ab8bec4707c`; tree `57858f688bd168e0cb0476ff12fee7a6ec0bc85b`.
- Source gate: clean initial checkout on Linux; `git fsck --full` passed.
- Runtime: Python 3.14.4; Z3 5.1.0; target solver settings were threads 1, random seed 0, timeout 600 seconds, strictly serial.
- Order-20 control: PASS — raw disposition `CANDIDATE`, Z3 `sat`, residual-H55 propagation false; both independent verifiers passed.
- Canonical A21 control: PASS — raw disposition `CANDIDATE`, Z3 `sat`, canonical and `t=0`, residual-H55 propagation false; postprocessor `CERTIFIED` all 9 closures.
- Profile 28: `INCOMPLETE` — Z3 `unknown` after the configured timeout; raw record confirms `require_residual_h55_c4=true`; no postprocessor run.
- Profile 29: `INCOMPLETE` — Z3 `unknown` after the configured timeout; raw record confirms `require_residual_h55_c4=true`; no postprocessor run.
- Profile 31: `INCOMPLETE` — Z3 `unknown` after the configured timeout; raw record confirms `require_residual_h55_c4=true`; no postprocessor run.
- `target_certificate_exists=false` for every target profile.
- `nonexistence_claimed=false` unconditionally.
- Promotion was not launched because none of the three target postprocessors emitted `CERTIFIED`.
