# P07-08 equation corpus policy

## Decision

P07-08 is `target_passed / tier_b_target_pass`. The hash-pinned A/B/C manifest, bounded multi-adapter
runner, exact negative checks and byte-preserving legacy boundary are implemented. Tier A and Tier C
are component-complete. All 14 Tier B cases are additionally qualified on the exact current Hangul
build through native insertion, save, close, reopen and native readback.

## Immutable corpus

The current manifest is `hwpx-agent.equation-corpus/v1` for Hangul 2020 11.0.0.9136 x86 ko-KR.
Its exact raw bytes are pinned by SHA-256. Strict JSON rejects duplicate and unknown fields,
unsupported profiles, duplicate or malformed case IDs, empty or oversized sources, incomplete
tiers and untrusted bytes. The minimum admission set is 40 Tier A semantic cases, 10 Tier B
semantic cases, 2 Tier C exact-preserve cases and 2 Tier C exact-reject cases.

The committed current manifest contains 64 cases: 44 Tier A, 14 Tier B, 2 Tier C preserve and 4
Tier C reject. All positive cases parse through their declared LaTeX, MathML or EqEdit adapter,
compile through the current EqEdit compiler, reparse and require normalized `MathAst` semantic
equality. Ambiguity, unsupported positive input and any round-trip drift fail closed.

## Tier boundary

- Tier A proves the finite common-source profile with no ambiguity or approximation.
- Tier B covers matrices, cases, aligned piles, delimiters, double/triple integrals, annotations,
  combinatorics, symbol mixtures and presentation MathML. Component semantic checks pass 14/14.
  The exact Hangul 2020 11.0.0.9136 x86 ko-KR target run also passes 14/14 native insert and
  save/reopen readback checks with zero silent approximation. Render and visual inspection remain
  outside this card and therefore remain `not_run`.
- Tier C has two disjoint outcomes. `preserve_exact` admits only opaque `legacy_eqedit` bytes and
  returns those same bytes. `reject` requires the exact stable adapter error. A rejected case that
  succeeds is `equation_corpus_silent_approximation`.

## Preservation and privacy

`LegacyEquationScript` binds non-empty finite UTF-8 bytes to an exact SHA-256, rejects NUL and never
parses or rewrites them. The HWPX integration fixture changes adjacent text in the same XML part and
proves the complete expected part digest, including the unchanged unsupported legacy script.
This is synthetic package evidence, not a real-document or Hangul PASS.

Receipts contain only counts, pass ratios, state and a manifest digest. Debug output redacts corpus
content and digests. No private source, path, automation identifier or document text is emitted.

## Non-claims

Render quality, editor double-click flow and automation parity remain outside this task. P07 phase
completion is claimed only by the separate aggregate Gate; other Hangul versions, production and
product completion remain `false` / `not_run`. Actual Hangul Tier B execution and save/reopen are
qualified only for the exact pinned target and 14-case corpus.

The exact-target harness has passed. Its hash-pinned plan builder revalidates the full
64-case manifest and emits all 14 canonical Tier B scripts with semantic hashes. One bounded x86
STA create session inserts, reads and saves every case; a second bounded session reopens and reads
every case. A separate strict native HWPX oracle checks each artifact and records layout extents.
The private evidence is promoted through a redacted hash-bound target qualification; visual fields
remain unpromoted.

Reasoning level: `max`. P07-09 and the aggregate differential are now separately closed; neither
changes this task's render non-claim.
