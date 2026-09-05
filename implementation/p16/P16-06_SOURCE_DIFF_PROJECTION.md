# P16-06 source-bound semantic diff projection

- Scope: actual immutable domain graph/diff computation, not a completed renderer/server endpoint.
- Review: STRICT / HIGH; recommended reasoning `max`.
- No new dependency, public MCP tool, original rewrite or predecessor contract change.

`domain-ir::SemanticDiffSummary::from_diff` now supplies the plan-review `diff` shape directly from
`SemanticDiff` and its exact before/after `DocumentGraph` values. The only serialized fields are
added/modified/removed counts and closed kind/count category records. There is no raw text, path,
selector, content hash or identifier in this public summary. Internal digest getters bind the
summary to its source diff and both graphs for downstream storage/cache checks; these are skipped
by serialization and Debug. Deserialization is deliberately unavailable.

The server must still authenticate and authorize project/revision access, load the stored plan,
verify the plan's base revision/graph binding and combine current route/risk/signature/dry-run
evidence. The projection cannot set `execution_allowed` or prove that a candidate graph resulted
from executing a particular plan. No endpoint, persistent plan store or registered host is claimed
by this foundational change. The existing staging driver remains fixture-driven.

## Semantics and bounds

- One count per original semantic change record. A table may have distinct node/table/cell records;
  these must not be relabeled as unique edited objects. No record is dropped for presentation.
- Added and removed retain their direction. Moved and modified-and-moved count once as modified.
- Eight stable category names match the existing widget schema. Node subtypes are read from the
  exact graphs, not guessed from `EntityKind::Node`. Only image-kind resources/image-backed drawings
  map to image; filenames, fonts and vector-only drawings cannot manufacture an image classification.
- Classification changes across revisions map to other. Section breaks differ from page/column
  breaks. Table, drawing and note descendants are included; unknown categories remain other.
- Default/hard limits: 100,000 change records, 200,000 classification entries per graph, depth 128,
  and 64 MiB serialized bytes independently for each graph and the diff. Smaller positive limits
  are supported. Invalid bounds and exceeded limits fail; counts never saturate or truncate.
- Streaming serialization hashes the same canonical bytes as the source APIs without allocating
  an additional full graph/diff buffer. Sources are immutable, category order deterministic.

## Validation boundary

New API tests initially failed because projection exports did not exist (not a pre-existing
behavioral regression). A test fixture's incorrect Inline field was corrected before acceptance.
Nine focused tests and one comprehensive existing-graph integration test cover exact serialization,
eight-category coverage, totals, inverse/move handling, source mismatch, image-kind classification,
node kind transitions, nested notes/drawings, all finite limits, deterministic replay and redaction.
The complete domain package suite passes 65 tests; package all-target Clippy passes. Current-source
full CI, independent exact-checkout full CI and server/registered-host integration remain required.

The next implementation is authenticated stored-plan-to-renderer binding. Do not substitute this
pure projection or local screenshots for that missing product path or close P16-06 on this evidence.
