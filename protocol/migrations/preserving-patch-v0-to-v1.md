# Preserving patch v0 to v1

- Capability: `hwpx-agent.preserving-patch`
- From: absent
- To: `v1`
- Compatibility: additive internal core capability; no existing serialized schema is changed

## Added contract

`v1` adds a pure in-memory preserving patch transaction over P03-04 checked token/tree selectors, P03-05 preservation evidence and P03-06 typed IDs. The only intent variants are `ReplaceAttribute`, `ReplaceText`, `InsertSibling`, `DeleteSubtree`, `ReplaceSubtree`, `AllocateId`, `AddRelationship` and `AddPart`.

Selectors carry immutable source identity and structural indexes instead of caller-provided byte ranges. Values, fragments, relationship IDs, new-part content and output bytes remain private and non-disclosing. Patch result metadata is deterministic and the private artifact can be checked by path/size/hash without byte access.

## Fail-closed changes from no capability

- unsafe/non-token-stable XML, stale selector and source identity drift are rejected;
- overlap, nesting, same-anchor insertion and ambiguous dependency are conflicts, not reordered;
- semantic values are XML-escaped and fragments are single-root safe XML only;
- allocation is typed, deterministic, non-renumbering and transaction-local;
- added parts require exactly one matching internal relationship and rebuilt graph closure;
- all outputs are reparsed and reindexed through the full package trust chain;
- no ZIP or filesystem publication capability is introduced.

## Future migration triggers

A new contract version is required before adding an intent variant, exposing output bytes, accepting raw offsets/unvalidated XML, changing conflict boundary semantics, adding text-ID allocation, broadening opaque content policy, changing OPF relationship generation, or sharing this current-2020 profile with another Hancom build.
