# P07 equation automation v0 to v1

There is no stored v0 payload to migrate. Version 1 is a new fail-closed boundary.

A caller MUST rebuild a request from normalized `MathAst`, the complete current source state and
an independently qualified opaque binding-set digest. It MUST NOT import raw automation
identifiers, raw XML, arbitrary scripts, private paths or a legacy success flag into the public
request. Insert, edit and readback are distinct semantic operations. Edit/readback additionally
require the exact selected native object ID and its expected semantic digest.

The P07-06 exact-target probe reads raw identifiers only from the hash-pinned private P02 source and
writes the executable request only below ignored private evidence. Its redacted receipt and public
target evidence contain digests and counts, never those values. This probe does not rewrite or
promote the frozen P02 registry and is not a P10 production executor.

Effect-unknown and failed receipts cannot be retried or treated as success. P07-07 layout/render,
P07-09 editor double-click smoke, direct/automation differential, production security/execution and
other Hangul versions remain separate P07 and later Gates.
