# P08-24 object selected-shape canary policy

## Scope

P08-24 may qualify only five nonmodal, selected-shape ActionTable candidates on licensed Hancom
Hangul 2020 `11.0.0.9136` x86 on the current PC. The fixed cases are `OBJ-026`, `OBJ-033`,
`OBJ-038`, `OBJ-045`, and `OBJ-013`. They run in one COM session and one unsaved disposable blank
document containing two runner-created rectangles.

This is a bounded runtime canary. It does not enable routing, prove the other P08 candidates, run a
direct-vs-automation differential, make a matrix row green, or complete P08.

## Effect and rollback rule

- The runner selects the first created shape through its control anchor before each candidate.
- Each candidate must be enabled, execute without an exception, change the in-memory `HWPML2X`
  semantic snapshot, and return to the pre-action semantic snapshot after one candidate Undo.
- The Action return value is advisory because the exact caption Action returns false while producing
  an observable, exactly undoable document change on this target.
- `OBJ-038` first establishes a reversed z-order context. Both the candidate Undo and the additional
  setup Undo must restore their respective pre-action snapshots.
- No fixture or user document may be opened by Hangul, no document may be saved, and the wrapper may
  clean only the exact Hangul process it owns.

## HWPML serializer normalization

The semantic hash removes only an empty `Name=""` attribute from a `DRAWTEXT` start tag. Hangul 2020
materializes this omitted optional default during the `OBJ-026` action and retains the empty form
after Undo even though the shadow value is restored. Non-empty names and every geometry, style,
text, and other attribute remain hash-significant.

The raw hashes and normalization counts remain in private evidence. Public evidence must state that
four cases are raw-byte exact and one is semantic-exact under this narrow rule; it may not relabel
the normalized case as raw exact.

## Evidence and privacy

The private trace may retain Action names and disposable HWPML snapshots. The public qualification
contains feature/capability IDs, hashes of Action identifiers, bounded outcomes, normalization
counts, and source/evidence identities only. It must contain no raw Action or parameter identifier,
document content, private absolute path, or user-document data.

Failed attempts 01 and 02, diagnostic attempt 03, and superseded single-case pass 04 remain
immutable. Only `p08-24-object-shape-canary-20260915-05` is promoted.

