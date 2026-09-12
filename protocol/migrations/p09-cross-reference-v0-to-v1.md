# P09 cross-reference v0 to v1

- There is no accepted v0 wire representation.
- Producers must emit `hwpx-agent.cross-reference/v1` with complete ordered section, target,
  cross-reference and occupied non-crossref native-ID/name inventories.
- Raw XML, HAction names, filesystem paths, display strings, inferred anchors and implicit native
  parameters are not migratable inputs.
- Targets migrate only with a stable logical ID, exact kind and anchor, required semantic projection
  digests, complete sorted dependency IDs, opaque state/properties and protection.
- Cross-references migrate only with fresh logical/begin-control/field identities, a live compatible
  target, exact display kind, current target-projection and cached-display digests, complete native
  pair, opaque state/properties and protection.
- Generic HWPX CROSSREF parameters remain opaque under `unverified_field_parameters`; v1 does not
  imply direct HWPX lowering, REF-036 update automation or installed-Hangul support.
- Missing, duplicate, dangling, self-referential or cyclic targets, stale insertion cache, occupied
  native IDs, malformed topology/preservation digests, locks or opaque state fail closed. No defaults
  are synthesized.
