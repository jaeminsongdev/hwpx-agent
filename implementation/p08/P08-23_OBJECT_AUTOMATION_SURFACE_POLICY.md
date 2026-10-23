# P08-23 object automation surface policy

## Scope

P08-23 may verify only that an exact official P08 automation candidate is exposed by licensed
Hancom Hangul 2020 `11.0.0.9136` x86 on the current PC. It does not execute a candidate, observe an
effect, enable routing, or satisfy a direct-vs-automation differential.

The fixed input is the P08-22 40-candidate binding overlay. `OBJ-003` drawing-gallery load and
`OBJ-043` point editing are known-modal and are excluded from the unattended batch. The remaining
38 candidates run in one x86 STA COM session and one shared, unsaved blank document.

## Allowed calls

- `IsActionEnable`, `CreateAction`, `CreateSet`, and `GetDefault` may be used for an ActionTable
  candidate.
- The `InsertPicture` automation method may be checked for presence but must not be invoked.
- `XHwpDocuments.Add(false)` and discard-close are allowed only to provide an empty disposable
  context.
- The runner must refuse a pre-existing `Hwp.exe`, verify the exact 32-bit COM server and launched
  process SHA-256, bound inactivity, and clean only the exact process it owns.

## Forbidden calls and claims

- No fixture or user document may be opened by Hangul.
- No candidate Action or automation method may be executed.
- No document may be saved and no registry or system setting may be changed.
- A disabled Action or `GetDefault=false` in the blank context remains a present surface, not a
  runtime effect failure.
- Surface presence is not automation runtime support, routing, Undo/rollback, differential,
  release-green, P08 completion, production readiness, or product completion.

## Evidence and privacy

The private trace may retain exact Action or method identifiers. The public qualification exposes
only feature/capability identity, source kind, SHA-256 of the source identifier, context result and
bounded counts. Absolute private paths, raw identifiers, probe values and document content are
forbidden in public evidence.

Failed and superseded attempts remain immutable. Only
`p08-23-object-surface-20260915-06` is the promoted surface attempt.

