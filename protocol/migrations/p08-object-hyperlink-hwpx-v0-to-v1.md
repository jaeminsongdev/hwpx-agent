# P08 object hyperlink HWPX v0 to v1 migration

There is no accepted v0 representation. The v1 adapter is additive: it lowers the existing exact
`obj.object_hyperlink` property transition for the reviewed shape-component kinds to the common
HWPML 2011 root `href` attribute without reinterpreting geometry, appearance, object-specific
payload, resources, embedded content, or opaque properties.

V1 requires one exact direct run-level picture, basic shape, text box, drawing canvas, or embedded
object, its complete typed property state, exact before/after document-flow digests, and one
unqualified root `href` attribute. Empty, validated HTTPS, `mailto:` and `#bookmark` values are the
only admitted lexical forms. A real transition edits only that attribute value span. Chart is
outside the shape-component inheritance branch and is rejected rather than partially interpreted.

Any wrong identity, kind, ordinal, missing, duplicate, nested, qualified, ambiguous or unsupported
target, unsafe scheme, stale state/flow, section/object/href/plan mismatch, target readback failure,
preservation failure, or bounded-limit violation must fail closed. There is no legacy fallback, no
migration switch, and no partial output.
