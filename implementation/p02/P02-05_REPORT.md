# P02-05 Normalization and Duplicate Candidates Report

- Completed: 2026-09-02
- Audited source commit: `3df40e33b0564aea17af3b1835c8c46a8647cd55`
- Task state: `pass_current_pc_local`
- Review: `STRICT / xhigh`, blocker/major/minor `0/0/0`

## Delivered

- Internal Draft 2020-12 `CandidateGraphV1` schema with exactly three input roles, provenance-complete nodes, review-only pair edges and `auto_merge=false` invariants.
- Source-lock/source ID/source SHA, input-output SHA, SourceRecord schema/semantic validity, role/source-kind compatibility, global record-ID uniqueness and contiguous extraction ordinals are revalidated before graph generation.
- Deterministic label normalization: Unicode NFC, explicit accelerator/shortcut removal, camel-case boundary preservation, case folding and Unicode letter/mark/number tokenization. Original SourceRecords are never rewritten.
- Deceptive control, format and bidi characters fail closed. ActionTable's source-authored `+`/`-` ParameterSet indicators are preserved only inside I/O signatures as reversible `symbol-u002b`/`symbol-u002d` tokens.
- Every SourceRecord becomes exactly one node. Every exact-normalized-label pair becomes exactly one edge classified by independently checkable input, output and target/availability scope signals.
- Compatible edges remain `review_candidate`; conflicts remain `collision_review`. Neither state performs or implies a merge.
- Any restricted source makes the complete derivative restricted. Publication is atomic no-overwrite and confined to Git-ignored `implementation/p02/evidence`.
- Independent verifier reconstructs source-lock/license state, every node's normalized label/I/O/scope/availability digest, all exact-label pairs, edge states/reasons/IDs and coverage counts.

## Actual locked graph

| Metric | Count |
|---|---:|
| input SourceRecords | 3,680 |
| graph nodes | 3,680 |
| normalized labels | 2,736 |
| singleton nodes | 2,296 |
| review edges | 3,811 |
| compatible review candidates | 746 |
| collision reviews | 3,065 |
| automatic merges | 0 |

- Inputs: Help 4 records, Automation 2,532 records and OWPML 1,144 records; all three input file SHA-256 values are required by the command line and repeated in the private graph.
- Deterministic output: two emissions with different CLI input order were byte-identical at 5,486,451 bytes, SHA-256 `65f470fee6b4e79e94f71bc55b068ed7a686f12eb52cedfffe238cdcf71cb29a`.
- Independent verifier: node coverage 3,680/3,680, pair-edge coverage 3,811/3,811, errors 0 and automatic merge count 0.
- The graph is a restricted derivative because at least one locked input source is restricted. It is not committed or reproduced.

The authoritative graph remains local at [private candidate graph](evidence/candidates/candidate-graph.v1.json).

## Validation

- Windows P02 suite: 29/29 passed; compileall, schema validation, Prettier JSON check and independent actual-output verification passed.
- Official Python 3.13.13 Linux image `sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286`, read-only repository mount: 29/29 passed.
- Current repository FULL bootstrap: 5/5 lanes passed; secret findings, vulnerabilities and forbidden licenses 0; CycloneDX components 147.
- Clean clone at `3df40e3`: FULL bootstrap passed and post-run Git status changes 0.
- Negative coverage: input tamper, source identity mismatch, duplicate ID, ordinal/role mismatch, bidi/control label, empty normalized label, restricted-output escape, traversal, overwrite and automatic/missing pair edge.

## Preserved boundaries

- Candidate edges are review work items, not semantic mappings, bindings or runtime support claims.
- Original SourceRecords, source archives, installed Hancom files and user documents were not modified or committed.
- 한글/COM/UI was not opened or automated for this task.
- 2022/2024, other PCs, production/provider use and redistribution remain outside this current-PC local task.

## Failed checks retained

- The first actual run stopped because hundreds of ActionTable parameter signals contain the source-authored `+`/`-` indicator. Main record labels still reject empty normalization; only parameter signals now use reversible Unicode codepoint tokens. The full graph and all validation were rerun after this correction.
- The new internal JSON Schema initially had a Prettier style warning. Mechanical formatting was applied and the schema/tests were rerun.

## Next exact task

Perform `P02-06 Semantic capability review`: bind each of 3,680 nodes to a canonical capability or an explicit ignored-with-reason disposition, resolve all 3,811 review/collision edges, preserve provenance and do not promote documentation evidence to runtime support. Recommended reasoning effort: `max`; P02-07 binding model: `xhigh`. No user local operation is required at task start.
