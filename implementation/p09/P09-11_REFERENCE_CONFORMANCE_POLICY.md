# P09-11 reference conformance policy

Decision: `MACHINE INVENTORY PASS / 40 P09 UNIT ROWS / 6 STATIC-SECTION INTEGRATION ROWS /
7 P11-DEFERRED ROWS / 0 TARGET / 0 GREEN / P09 INCOMPLETE`.

## Scope

P09-11 reconciles all 53 `REF-*` catalog rows against the generated capability contracts and the
ten P09 typed component profiles. It does not implement a new document mutation and does not change
the phase ownership recorded in the catalog.

- P09 owns 46 rows. All have typed component coverage; REF-018/019 additionally have the exact
  P09-12 static-section form-control adapter, REF-031/032 have the exact P09-13 point-bookmark
  adapter, and REF-021/022 have the exact P09-15 inline-note-payload adapter. Those six are
  `integration_passed`, while 40 remain `unit_passed`.
- P11 owns REF-016/020/036/040/043/045/047. They remain `cataloged` and are never counted as P09
  implementation gaps.
- The roadmap's broad wording for delete/update/generate actions does not override the generated
  catalog's exact P11 phase assignments.

## Row and evidence rules

Every row is present once in numeric order and retains its exact capability, phase, support,
preferred/fallback backend, validations, permission and fixture classes from the generated sources.
Each P09 component binding is collision-free and carries normalized SHA-256 locks for its Rust source
and public tests. Absolute/private paths are rejected.

`unit_passed` proves only the bounded typed component. P09-12/P09-13/P09-15
`integration_passed` proves only preserving generated section XML and typed target projection
readback for existing native form properties/tab order, point-bookmark insert/delete, or closed
plain-text footnote/endnote insertion. Neither stage proves a complete package, licensed Hangul
execution, field/reference update, rendering, automation, differential behavior, production
readiness or phase completion.

## Green rule

A row remains non-green until its support-specific backend reaches oracle verification, every
required validation and fixture class passes, negative and rollback/retry behavior passes, the
current licensed target executes and reads back when required, render thresholds pass, and the
direct/automation differential passes. Missing evidence is a blocker, never an implicit pass.

## Privacy and preservation

The matrix contains no document content, private path, raw action/parameter identifier or probe
value. It reads catalogs and evidence only. It never opens or modifies user documents, original
archives, private evidence or failed attempts.

Reasoning level: `max` for lowering, target qualification and phase gates.
