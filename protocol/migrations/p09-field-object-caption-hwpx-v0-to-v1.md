# P09 object-caption composition v0 to v1

There is no accepted v0 object-bound caption adapter. P09-16's existing numeric
section adapter remains unchanged and separately qualified; this v1 composes it
inside one verified existing native object's caption. No cached-result or plan
migration is implicit.

Callers must provide the unique native object ID/kind, logical object ID, complete
caption field state and paragraph map, styles, document-flow identity and finite
limits. Old standalone section plans cannot be used as caption composition plans.
Build a fresh sealed composition plan from exact source bytes. Missing or changed
selector/source/context, unsupported namespace scope and tampered plans fail closed;
there is no normalization, native-ID invention or fallback output.

No P09 row becomes green through this migration. Complete-object package and
exact-target semantic/render qualification require independent successor evidence.
Retain P09-17's failed fixtures/receipts and P08/P17 historical authorities.
