# P09 review paragraph output v0 → v1

Additive typed source/component API, not a DB-schema migration or new advertised capability. Original whole-body and whole-cell API signatures and content replacement semantics stay unchanged.

| Existing | Added |
| --- | --- |
| Complete review body/cell paragraph-list replacement | Complete replacement of one source-anchored paragraph |
| Original content-only replacement and readback | Private paragraph outer-span replacement and one-paragraph readback |
| Fresh original source/service verification | Same verification and deterministic replay around the new stored route |
| Product route unqualified | Still unqualified; no issuer/publication authority |

ReviewParagraphReplacement contains marker and paragraph SourceAnchorHandle plus typed TextFlow. It is not deserializable as caller XML or an authority-bearing native CommentState. ReviewParagraphOutputReceipt wraps the original qualified output receipt and adds source paragraph identity, outside_selected_paragraph_exact/rich_siblings_preserved_exact=true and full_comment_product_acceptance=false.

Complete replacement is intentional inside the selected paragraph. Consumers must not read the outside guarantee as a text-only mutation or preservation of old paragraph internals. Unknown/opaque target output remains rejected, original package/ID/style checks remain enabled, and original nested-review shapes remain unsupported.

Source/document/version/marker ownership and all fresh stored checks are required even for cached bytes. Repeated reads are not an atomic lease. No component receipt upgrades native metadata/protection, actual SQL, save/reopen/render, full product execution or P09 Gate status.
