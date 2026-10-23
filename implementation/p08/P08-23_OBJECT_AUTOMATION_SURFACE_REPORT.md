# P08-23 object automation surface report

## Result

Result: `exact_target_surface_inventory_pass / runtime_not_run / differential_not_run`.

Promoted attempt `p08-23-object-surface-20260915-06` completed the 38 non-known-modal P08 source
candidates in one licensed Hangul 2020 `11.0.0.9136` x86 session and one unsaved blank document.
It finished without timeout or inactivity recovery and left zero owned `Hwp.exe` processes.

## Observed surface inventory

- Source candidates: 40.
- Unattended probes: 38; known-modal exclusions: `OBJ-003`, `OBJ-043`.
- ActionTable surfaces created: 37/37.
- Automation-object methods present without invocation: 1/1.
- Enabled in the blank context: 10; present but disabled in that context: 27.
- Parameter sets created: 21; `GetDefault` passed: 10, returned false: 11, and was not applicable:
  17.
- Candidate executions, Hangul file opens, document saves and residual owned Hangul processes:
  0 each.

`GetDefault=false` and disabled state are expected contextual observations for object-property
Actions with no selected object. They do not remove the exact surface, and they do not prove the
effect that a selected-object canary must later verify.

## Preserved predecessors

Attempts 01 through 03 remain failed evidence: attempt 01 used the wrong COM collection call,
attempt 02 reproduced the target's first-file-open stall, and attempt 03 exposed instability from
repeated blank-document creation. Attempts 04 and 05 passed the surface read but were superseded by
the final exact COM-server/process identity and cleanup checks in attempt 06. None is relabeled.

## Boundary and next evidence

The public qualification contains no raw Action or method names; it binds the private trace,
wrapper receipt, progress stream, P08-22 overlay, target fixture manifest and both runner sources by
SHA-256. The source fixture manifest is an identity input only; Hangul did not open any fixture in
this run.

This result advances inventory knowledge only. Automation runtime support remains unverified,
routing remains disabled, all direct-vs-automation differentials remain `not_run`, the required
58-row matrix remains 0/58 green, and P08 remains in progress. The next evidence is a bounded
selected-object execution/Undo canary, split by modal risk and effect type.

