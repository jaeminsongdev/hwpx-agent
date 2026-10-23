# Source note export XML context preservation

Moving a note body's child paragraphs out of subList must retain inherited XML context, not only
namespace bindings. The source note-file profile v1 now materializes xml:lang and xml:space on
detached roots and the section-properties-only run while keeping every original local attribute.
This is a source preservation correction, not Native layout qualification or a new execution route.

## Context rules

The [W3C XML language rule](https://www.w3.org/TR/xml/#sec-lang-tag) makes the nearest xml:lang
apply until a local override; an empty value explicitly resets language information. The
[XML space rule](https://www.w3.org/TR/xml/#sec-white-space) similarly inherits default/preserve.
The implementation uses those observed values without inventing a language or whitespace mode.
Materialized space values must be valid; no BCP47 language conformance or interpretation of
space attributes inside opaque descendants is claimed.

The root's absent language/space attributes are filled from its nearest ancestors. Original local
values and descendant overrides remain unchanged, including empty language resets. The original
expanded names and attributes are compared after closing; only the declared inherited additions
may differ. Context extraction walks ancestors under the existing finite depth limit and charges
new bytes to payload/section/output limits. It does not copy the whole unselected parent run.

Source paragraph mapping uses a private SourceXmlContext reader profile for p/run xml:lang and
valid xml:space, recording their original native attributes and source anchors. It does not broaden
standalone typed TextFlow admission/lowering or the existing SourcePreserving reader used by
other evaluators. Unknown namespaced p/run attributes and invalid space still reject. The new
source mapping profile retains the original field-parameter validation and field-stack checks.

## URI and native container limits

[XML Base](https://www.w3.org/TR/xmlbase/#granularity) gives ancestor bases URI meaning. Copying
the nearest lexical base after removing intermediate ancestors is not sufficient URI resolution.
Removed intermediate xml:base therefore rejects with NOTE_FILE_INHERITED_XML_CONTEXT_UNQUALIFIED.
The original section and part path remain in place; its existing context is not moved. This is an
explicit unsupported case pending URI binding, not implemented general XML Base support.

The official pinned Hancom ParaListType source declares direction, wrapping, vertical alignment,
dimensions, linked-list references and text/number-reference flags as container properties. They
are not blindly attached to ordinary paragraphs. Original source anchors and selected-body hashes
still bind those container bytes. Effective Native geometry/numbering and container-to-body layout
translation remain unqualified, and the receipt's existing Native qualification flags stay false.

The two local official files match the earlier immutable source qualification:
`ParaListType.h` SHA256 e25e4eb302e770fa913355aa04e30355d6523313a945f1033e6e092c7a937c91 and
`ParaListType.cpp` SHA256 64dc1b0276f857d25fe3db1d89786020aeb426a7cb920696becad26e8a88c6f0,
from commit 1453388472c703a4b299a0834f425cdac16644b9 in the Hancom hwpx-owpml-model repository.

## Verification

components035/036 are preserved compile failures from new tests attempting private value/source
access. Test-owned input bytes and public spans replace those attempts without exposing a private
production API. components037 then passes 52 core/reader/mapper cases (6 new and 46 affected)
but cannot compile the two new product cases because of an assertion delimiter error.

`implementation/p09/evidence/p09-361-note-export-context-product-recovery038.v1.json` proves the
assertion-only full-file inverse and unchanged production, core tests and other input pins from
components037. It runs only the two previously unexecuted product cases, passes both and excludes
284 others, with 459 fresh/final459 and confirmed cleanup. It does not rerun the 52 passing cases.
The preserved components037 plus recovery038 cover 54 unique tests, not 54 fresh product or Native
tests. All original failed receipts remain failed and no official queue acceptance is added.

Coverage includes effective text/secPr contexts, local overrides and empty language resets,
fifty separately scoped notes, inherited-attribute byte limits, strict typed reader boundaries,
intermediate base rejection, actual guarded product output and post-preparation ACL revocation.
Every owned job closed with active0/empty/handle closed. The 52-pass run's system CPU peak was
71.13%, minimum available RAM 12.8784% and Job peak 1562.72 MiB/4.9048%; recovery's values were
78.91%, 14.6709% and 902.80 MiB/2.8336%. Original resource safeguards and source validation remain.

Native layout/numbering/save/reopen/reference update/render, full protection, issuer/durable DB/
atomic CAS/exactly-once execution/publication and the P09 Gate remain open. Output metadata may
retain original source information, so this remains a non-redacting artifact candidate.
