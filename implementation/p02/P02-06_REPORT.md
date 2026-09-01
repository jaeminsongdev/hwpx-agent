# P02-06 Semantic Capability Review Report

- Completed: 2026-09-02
- Audited source commit: `d29a4bac634ba8a662b06662b54655496f8296ad`
- Task state: `pass_current_pc_local`
- Review: `STRICT / max`, blocker/major/minor `0/0/0`

## Delivered

- Internal Draft 2020-12 contracts for manual review decisions and the reviewed capability catalog.
- A fail-closed generator that locks the source-lock identity, three SourceRecord SHA-256 values, candidate graph SHA-256, canonical matrix SHA-256 and review-decision SHA-256 before publication.
- Strict multi-signal proposals use the Action identifier, Korean description and desktop-automation backend eligibility. A proposal also needs a unique runner-up margin and an explicit human disposition; a label alone can never create a mapping.
- Every graph node is emitted exactly once as `mapped` or `ignored_with_reason`. Every candidate edge is emitted exactly once with collision/difference state preserved and `auto_merge=false`.
- Mapped entries carry the canonical feature/capability, scope class, support level, preferred/fallback backend, phase, source record reference, candidate references and review evidence.
- Documentation evidence remains `runtime_support_state=unverified`; the generator cannot emit a runtime-qualified claim.
- Restricted input propagation, canonical output containment, atomic no-overwrite publication and input-change detection include the source lock, all SourceRecords, graph, matrix and decisions.
- The independent verifier reconstructs the strict proposals, manual-decision coverage, all 3,680 node dispositions, all 3,811 edge dispositions, canonical projections and aggregate counts.

## Actual locked review

| Metric | Count |
|---|---:|
| candidate graph nodes | 3,680 |
| strict proposals reviewed | 35 |
| canonical mappings approved | 34 |
| explicit ambiguous rejection | 1 |
| ignored with reason | 3,646 |
| unresolved nodes | 0 |
| candidate edges disposed | 3,811 |
| collision edges preserved | 3,065 |
| compatible but unmapped edges | 746 |
| automatic merges | 0 |
| runtime-qualified entries | 0 |

Node disposition details:

- `strict_multi_signal_semantic_match`: 34
- `ambiguous_canonical_semantics`: 1
- `no_strict_canonical_semantic_match`: 902
- `binding_parameter_metadata_not_standalone_operation`: 1,205
- `automation_object_metadata_not_standalone_operation`: 363
- `automation_event_signal_not_standalone_operation`: 27
- `structural_schema_component_not_standalone_operation`: 1,144
- `documentation_navigation_not_executable_item`: 4

The one strict proposal rejected by manual review combined border/fill semantics and could resolve to several canonical table capabilities. It was not downgraded to a label-only mapping.

## Locked artifacts

- Candidate graph: SHA-256 `65f470fee6b4e79e94f71bc55b068ed7a686f12eb52cedfffe238cdcf71cb29a`.
- Canonical 609-row matrix: SHA-256 `695122da1bc8769f1f72ba23842036c94a152063fcd8c579f692dff8967d050d`.
- Private review decisions: 7,086 bytes, SHA-256 `f9403897a2682a1cc2283715d1dc96000beacc4aff762a89be1c7917df63d8d0`.
- Private reviewed catalog: 4,626,024 bytes, SHA-256 `88b4c5238c1911ae4cd3f40874a0328401a12dda9b57f51d2e1c5663834d5609`.
- Three no-overwrite emissions, including one from the committed source, were byte-identical despite different SourceRecord CLI ordering.
- Independent actual-output verification: errors 0; node 3,680/3,680; edge 3,811/3,811; runtime-qualified 0; auto-merge 0.

The authoritative local artifacts are [private review decisions](evidence/capability-review/review-decisions.v1.json) and [private reviewed catalog](evidence/capability-review/reviewed-catalog.v1.final.json). They are restricted derivatives and remain Git-ignored.

## Validation

- Windows combined P02 suite: 36/36 passed; Python compileall, Draft 2020-12 schema checks, Prettier JSON checks and `git diff --check` passed.
- Official Python 3.13.13 Linux image `sha256:aa938a849bcb82dce8f49480f056ab82bf5c1c3ebc294f0430f37b6820e7f286`, read-only repository mount: 36/36 passed.
- Current repository FULL bootstrap: 5/5 lanes passed; secret findings, vulnerabilities and forbidden licenses 0; CycloneDX components 147.
- Clean clone `D:\개발데이터\Temp\hwpx-agent-p02-06-clean-d29a4ba` at the audited source commit: FULL bootstrap passed and post-run Git status changes 0.
- Negative coverage includes locked-artifact tamper, missing/duplicate decisions, wrong canonical capability, ambiguity rejection, label-only under-threshold proposals, missing node/edge dispositions, automatic merge, runtime promotion, restricted-output escape, traversal and overwrite.

## Preserved boundaries

- The 34 mappings are documentation-derived semantic candidates, not executable bindings and not proof that the installed 한글 2020 performs the operation.
- `ignored_with_reason` is a review disposition, not a claim that the underlying Hancom item is permanently unsupported. P02-07/P02-08 must represent unavailable bindings and probe executable candidates without inventing action IDs.
- Raw restricted Action/Parameter/Object/Event names are not copied into public reports, schemas or Git history.
- Original official sources, extracted SourceRecords, installed Hancom files and user documents were not modified or committed.
- 한글/COM/UI was not opened or automated. Other PCs, 2022/2024, production/provider use and redistribution remain outside this task.

## Failed checks retained

- The first actual proposal pass rejected the canonical matrix's intentional `UNSUPPORTED` row because it has blank backends and phase `N/A`. Matrix validation was corrected to allow that combination only for `UNSUPPORTED`; all tests and actual review were rerun.
- The first two Linux attempts mounted the ephemeral dependency directory without an effective executable permission, so the native `rpds` module could not load. The repository remained read-only; the tmpfs mount was corrected with explicit `exec`, after which all 36 tests passed.

## Next exact task

Implement `P02-07 Binding model`: define schema/codegen for target-build invocation bindings, represent every `AUTOMATION_FULL`/`HYBRID` capability as a locked candidate or explicit unavailable state, keep raw action/method/parameter identifiers restricted, and keep all current-2020 execution claims unverified until P02-08 probes them. Recommended reasoning effort: `xhigh`; P02-08 runtime probe: `max`. No user local operation is required at task start.
