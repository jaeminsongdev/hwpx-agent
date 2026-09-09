# P17 legacy mutable source qualifications to frozen v1

## Old behavior

Historical `verify` paths regenerated expected documents or compared successor hashes with today's
worktree. Normal product evolution therefore invalidated old tests even though the committed
qualification documents and their original evidence were unchanged.

## New behavior

- v20-v39 current-workspace source qualifications are verified through their exact predecessor and
  `base_commit` Git chain.
- Five local qualification families are verified from exact contract/current snapshots and all
  recorded runtime/guard blobs at a single pinned commit per family.
- v12 and P15 source-successor pairs are verified from fixed Git ancestry without requiring the
  successor to remain the current worktree version.
- The old generators and current-admission helpers are preserved. Historical tests call the frozen
  readers; generation or genuinely current admission may still use the old tools explicitly.

No test is skipped and no positive claim is broadened. Receipt blobs outside Git, actual Hangul,
registered-host behavior, production, pull/push, phase completion and product completion remain
outside this migration.
