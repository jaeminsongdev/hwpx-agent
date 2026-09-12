# P09-10 reference auxiliary policy

## Decision

`REF-048` through `REF-053` receive one closed typed component contract. This is unit evidence only.
No HWPX lowerer, Hancom execution, field refresh, external-source access, repair, render or
automation support is implied.

## Exact semantics

- `ref.caption_sequence` replaces the complete caption-sequence and caption-binding state. Sequence
  identity, object kind, label/separator, number format, start value, continuous/per-section restart,
  document order, resolved number, cache projection, object binding and the official caption
  side/full-size/width/gap/last-width/sub-list envelope are bound. Existing sequence, caption,
  object, section and document locks fail closed.
- `ref.date_time_format` changes only an existing typed `DATE` or `DOC_DATE` field format. Locale,
  time-zone offset, calendar, generic field pair and opaque native parameters remain bound. Because
  no clock/evaluator is qualified, the preserved display cache becomes `stale`; the operation does
  not claim `ref.field_update`.
- `ref.file_name_literal` inserts a frozen leaf-name string whose UTF-8 digest equals the bound
  source leaf-name digest. Directory separators and drive syntax are rejected. It is not a dynamic
  `PATH` field and does not disclose a filesystem path through Debug output.
- `ref.correction_mark` inserts one of all 19 official proofreading field types with exact anchor,
  logical/native pair, author/time/content metadata, opaque parameters and collision checks.
- `ref.data_link` replaces or removes the document-level link using an encrypted artifact identity,
  encryption envelope, allowlisted-location digest, source revision, relationship state and all four
  page/footnote inheritance combinations. Raw paths and source access are outside the model.
- `ref.reference_validate` is a read-only deterministic graph inspection. It reports missing,
  inactive, kind-mismatched, cyclic, stale-cache and unavailable external-data references. The
  expected report digest is request/plan/build bound; no repair or reference refresh occurs.

## State and failure boundary

The state binds complete sections, caption targets/sequences/bindings, date fields, filename
literals, correction marks, data link, validation targets/edges, occupied native IDs and all
unrelated P09/object/numbering/style/relationship/resource/protection/opaque inventories. Every
operation rechecks canonical source state and document flow at request, plan and build and uses a
sealed deterministic plan. JSON is bounded, duplicate/unknown keys are rejected, and Debug/errors
redact identities, content, filenames, locations and digests.

The pinned official model proves caption envelope attributes, the generic field pair, `DATE`,
`DOC_DATE`, `PATH`, all 19 `PROOFREADING_MARKS_*` values, and document `linkInfo` path/inheritance
attributes. It does not prove caption numbering inside the sub-list, date/PATH/proofreading parameter
keys, filename freeze behavior, data-link access/update semantics or a broken-reference validator.
Those native semantics remain unverified.

## Gate

Component promotion requires happy, boundary, negative, preservation, drift, strict-JSON, privacy
and tamper tests plus locked source qualification. Release-green still requires direct HWPX,
semantic reopen, field readback, reference update, licensed Hancom open/save, render and differential
evidence on the exact target.
