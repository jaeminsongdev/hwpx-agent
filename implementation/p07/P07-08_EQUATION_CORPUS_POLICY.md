# P07-08 equation corpus policy

## Decision

P07-08 is `unit_passed / tier_b_target_not_run`. The hash-pinned A/B/C manifest, bounded multi-adapter
runner, exact negative checks and byte-preserving legacy boundary are implemented. Tier A is
component-complete. Tier B has semantic component coverage but is not target-qualified until the
exact current Hangul build executes and reopens every Tier B case.

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
  combinatorics, symbol mixtures and presentation MathML. The current 14/14 result is component
  evidence only; target insertion, visual inspection, edit and save/reopen remain `not_run`.
  It is component evidence only.
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

Actual Hangul Tier B execution, render quality, editor double-click flow, save/reopen, automation
parity, differential evidence, P07 completion, other Hangul versions, production and product
completion remain `false` / `not_run`.

The exact-target harness is implementation-ready. Its hash-pinned plan builder revalidates the full
64-case manifest and emits all 14 canonical Tier B scripts with semantic hashes. One bounded x86
STA session inserts, reads, saves, closes, reopens and reads every case; a separate strict native
HWPX oracle then checks each artifact and records layout extents. This tooling does not itself
promote the still-unrun target or visual fields.

Reasoning level: `max`. P07-09 remains `max` because editor mutation, native readback and
save/reopen evidence must be bound without confusing UI success with semantic success.
