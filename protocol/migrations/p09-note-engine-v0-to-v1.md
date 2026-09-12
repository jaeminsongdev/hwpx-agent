# P09 note-engine v0 to v1 migration

There is no accepted v0 note-engine schema and no migration switch.

`hwpx-agent.note-engine/v1` must be created from a freshly inspected complete ordered section and
note inventory. Legacy maps, raw XML fragments, untyped note bodies, guessed cross-family styles,
incomplete section styles, missing opaque state and external-export claims fail closed. Existing
logical/native identity, exact anchors, marker/native properties, body and plain-text digests,
styles, protection, resources, references, opaque payload and document-flow bindings must be
supplied explicitly.

Only `footNote` and `endNote` are qualified native note tags. `ref.note_export` v1 is a bounded
digest-manifest projection; migration must not interpret it as a file writer, content extractor,
HWPX lowerer or installed-Hangul result.
