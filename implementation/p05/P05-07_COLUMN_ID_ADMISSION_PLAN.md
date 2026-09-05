# P05-07 column identity: evidence and bounded next implementation

- Date: 2026-09-05; inspected implementation checkpoint `9f493a5`.
- State: offline design/next-task boundary, not implementation or acceptance PASS.
- Scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86 only.
- No new actual run, fixture mutation, identity waiver or public revision publication occurred.

## Observed facts and existing contracts

Attempt21 saved the two synthetic nonempty `colPr/@id` values as empty strings. Its before/after
package identities and trace are fixed in `P05-07_ATTEMPT21_DIAGNOSTIC.md`; the original artifacts
remain unchanged. Other observed column type/layout/count/width/gap/separator values were retained.
This is a byte/typed-field observation, not proof of document-wide identity or layout equivalence.
The same output fails the requested landscape geometry, independently of the identity question.

The package `ColumnDefinition` includes `control_id` in full equality. Its ID index declares
nonempty `colPr/@id` as `ColumnProperties`; only an empty ID on the exact current-profile section
metadata is treated as an absent declaration. An absent identifier cannot stand in for two
distinct original identifiers. Changing equality globally or remapping both to the empty string
would silently erase information.

The existing product design already separates these cases:

| Contract | Relevant requirement |
|---|---|
| `docs/03_document_model/12_preservation_roundtrip.md` | Surgical editing preserves source bytes/relationships; a Hancom normalization is a separate revision with a preservation report and ID remap table. |
| `docs/03_document_model/01_document_graph_ir.md` | Logical IDs remain stable across backend ID reallocation, or an explicit remap receipt is generated. |
| `docs/12_implementation_guides/04_documentgraph_operation_engine.md` | Structural fallback requires an expected fingerprint; zero/multiple selector candidates must not be resolved by choosing the first. |
| `docs/02_architecture/03_backend_interfaces.md` | A backend receipt records input/output identities, semantic diff and normalization events; object identity remains a cross-backend requirement. |

Current `domain-ir` exposes backend-neutral logical IDs and `SourceAnchorHandle` with an opaque
handle and fingerprint. A text search and inspection found no implemented column-specific
source-to-saved identity rebinding receipt in these inspected modules. Existing type definitions
alone therefore do not qualify the actual saved document's identities.

## Decision: retain the failure; make its evidence independent

Keep the strict target inspector and all existing expected values. The next bounded implementation
should add source-bound diagnostic comparison, not an alternative accepting inspector:

1. Admit both complete packages with existing bounded graph/header/section readers. Bind the
   comparison to exact source/output SHA-256 and the actual build/trace, with no arbitrary path
   or raw XML in public output. Invalid structure rejects before comparison.
2. Compare all page/column semantics, text, section order and span counts without early loss of
   other diagnostics. Record page geometry and control-ID differences as separate results.
3. Classify a nonempty-to-empty column ID only as an **observed removed backend identifier**.
   Do not label it preserved, equivalent, an authorized degradation, or a successful remap.
4. Overall acceptance stays failed while either layout or identity requirements fail. Diagnostic
   field-level equality cannot publish a revision or qualify P05-07/P05/P12.
5. Preserve full equality for direct/surgical edits. Any future native-normalization admission
   needs an explicit mode/plan decision and a source/output-bound logical-identity receipt.
   It must preserve logical IDs and prove unique structural/context correspondence. Empty backend
   IDs are absence, not receipt keys. Ambiguous/duplicate/reordered/changed contexts fail closed.

The general cross-backend normalizer remains P12 work. This bounded P05 diagnostic must not claim
to implement it or introduce a permissive global route merely to remove the P05 hold.

## Required failing-before/passing-after coverage

- Two valid packages with identical definitions: all dimensions pass, zero normalization events.
- Nonempty-to-empty ID with otherwise equal fields: identity failure is retained and reported.
- Orientation mismatch and ID removal together: both are reported; overall failure cannot depend
  on which field was compared first.
- Changed width/gap/separator/type/layout, section count/order or text cannot be hidden as ID-only
  normalization. Invalid graph/header closure fails before any equivalence result.
- A stale source/output digest, missing actual build/trace, ambiguous correspondence or two removed
  IDs cannot produce a verified remap or preservation result.
- Existing direct lift/lower and surgical unselected-span equality regressions remain unchanged.

Only after offline diagnosis and a meaningful corrected fixture is ready should a fresh
user-present request trigger another bounded actual run. The prior request's attempt21 has ended;
there is no pending access click and no automatic relaunch. Recommended reasoning: `max`.
