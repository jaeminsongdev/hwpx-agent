# P09 review observation: optional native string-value element identity

Status: internal partial readonly projection; NOT complete native comment metadata or execution admission.

## Additive representation

ImportedReviewBodyObservation gains optional meta_tag with source_anchor, element_sha256 ([u8;32])
and raw_bytes. None is omitted from serialization; old observations without native metaTag retain their
previous serialized field set. This changes Rust struct construction and adds data to existing partial
observations when metadata is actually present; it is not a new external command or Deserialize API.

The original observation digest and source-bound graph review property include the optional identity.
Lexical entity spelling changes and string-value changes invalidate the full source binding; decoding,
normalizing or parsing JSON cannot replace whole source bytes. Debug is redacted. Stored cached
observations require the original fresh source ACL/AEAD/head/scope checks.

## Unchanged admission

Profile hwpx-agent.document-import-review-bodies/partial-v1 and its qualification remain partial.
Metadata remains UnverifiedNativeMapping. Native author/time and visibility/resolution receipt flags
remain false. Complete comment-state wire contracts, REF ownership, original full-document rejection,
SQL schemas and product execution/publication authority are not modified. Existing unsupported
parameters/nested review/CDATA boundaries are not silently promoted.

## Evidence

P09-95_REVIEW_METADATA_POLICY.md and P09-95_REVIEW_METADATA_REPORT.md specify the supported envelope
and synthetic-versus-native limits. evidence/p09-95-review-metadata.*.v1.json records failures,
regression, raw preservation and the current source checkpoint. Actual native semantic validation is
NOT_RUN; P09 Gate stays OPEN and P10 new implementation is false.
