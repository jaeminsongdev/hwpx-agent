# P04-07 Semantic diff policy

## Boundary

`domain-ir::SemanticDiff` is a pure comparison boundary over two already validated immutable
DocumentGraph v2 values. It performs no filesystem, network, process, COM, HAction, backend or graph
mutation operation.

## Identity and trust

- Both snapshots must use one exact document identity.
- Each declared graph digest must match the graph's canonical bytes.
- One revision identity cannot name two different graph digests.
- Revision IDs and logical IDs are hashed with a type prefix before publication.

## Semantic subjects

- Document and section settings are separate from ordered flow nodes.
- Nodes use stable logical ID and a typed parent/ordinal path. Nested table-cell, drawing and note
  flows remain distinct.
- Table grid and cell span/property changes, equation source/display/property changes and object
  resource/geometry/property changes have dedicated categories.
- Styles, resources, references, notes, review entries and opaque preservation handles are indexed
  independently. Style/resource changes carry before/after reference-impact counts.
- Unrelated remove/add pairs are never guessed to be a rename or move.

## Privacy and determinism

The result contains no raw document values or identifiers. Subject, revision and value identities are
SHA-256 references; paths expose only typed scope, hashed parent, finite indices and depth. Changes
use a canonical enum/key order. All entity, change, depth and serialized-size limits are finite and
fail closed without a partial diff.

## Deferred boundaries

This task does not prove HWPX lifting/lowering, native formula equivalence, layout rendering or
Hancom visual fidelity. Those require later vertical/runtime Gates. P04-07 compares the semantics
represented by DocumentGraph v2 exactly and makes opaque changes visible rather than interpreting
them.
