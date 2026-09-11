# P07 MathML adapter v0 to v1 migration

There is no stored v0 adapter result to reinterpret or upgrade in place.

Version 1 introduces `hwpx-agent.mathml-adapter/v1` and
`hwpx-agent.mathml-profile/finite-v1`. Callers must submit one exact UTF-8 MathML source document
under the v1 request schema. The adapter classifies it as presentation or content, requires the
exact MathML namespace URI, rejects profile mixing and returns only a fully admitted P07-01
`MathAst` result.

Legacy XML accepted by another parser is not grandfathered. DTD, custom entity, PI, CDATA,
comment, foreign namespace/attribute, semantic adjacency, unknown operators and unsupported
structures MUST fail closed. A caller MUST NOT insert invisible multiplication or function
application on the adapter's behalf.

The v1 cross-profile corpus proves semantic equality only for the finite documented profile. It
MUST NOT be migrated into a full-MathML, EqEdit, HWPX, Hangul, render, production or P07 PASS;
those are separate P07 Gates.
