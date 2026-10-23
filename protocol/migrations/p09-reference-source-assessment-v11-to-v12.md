# Reference source assessment v11 to v12 migration

`reference-source` emits `hwpx-agent.product.reference-source-assessment/v12` and adds
`note_style_selections` for typed replacement of actual body-spine section note styles.
The API reads the already imported XML token documents; it does not reconstruct
ZIP/XML/Form input again. Existing note and caption selectors retain their meaning.

## Selection fields and scope

Each array item has exactly three fields:

- `style_id`: source-generated identity bound to document, whole package, part and position.
- `source_style_sha256`: the actual style subtree SHA256 as a JSON array of 32 byte values.
- `kind`: `footnote` or `endnote`, from the actual section style tag.

The array follows body-spine XML order, including separate declarations in separate
sections even when their local data and subtree fingerprints match. It does not expose
raw XML, note/main text, native attributes, user/prefix/suffix characters or the current
style values. No style declaration yields an empty array, not inferred native defaults
or a successful zero-reference validation. Non-body effective styles and layout remain
unqualified.

## Stricter source rejection

The existing source-style reader requires unique main-body section properties and unique
family declarations with all five known child elements and 16 required attributes.
Missing required attributes, hidden/nested/duplicate declarations, unsupported spellings
and family-incompatible values fail with `REFERENCE_SOURCE_NOTE_STYLES_REJECTED`.
They never fall back to an empty selector array. An absent declaration stays absent.

Native `newNum` is an unsigned source value. A locked historical Hancom source has
`newNum="0"` for both note families, and the official
[numbering.h](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/numbering.h)
stores that attribute as `UINT`. The reader preserves an observed zero; it does not
infer its effective numbering meaning or replace it with one. A mutation may retain
zero only when it already exists and the numbering restart mode is unchanged. Creating
new zero or changing its restart mode is rejected. The complete domain NoteStyle's
positive-number validation and unresolved Native numbering status remain unchanged.

Source count/text limits combine the finite note-style reader profile with caller reference
limits; exhaustion remains `REFERENCE_SOURCE_INPUT_LIMIT`. Section and serialized output
limits remain enforced, and output is rejected rather than truncated.

## Client changes

Recognize v12 before using `note_style_selections`. Preserve historical v11 responses;
do not synthesize selectors when the field is missing. There is no stored-document or
database migration. Changing the document or any package content requires fresh selectors.

Construct `NoteStyleReplacement` from the API style ID and fingerprint plus a complete,
explicit caller-chosen `NoteStyleValues` replacement. `kind` selects the appropriate
numbering/placement family, not source defaults. No caller-side Form/Note/style import is
needed for selection. Requests cannot change note kind or manufacture a missing style.

The stored provider independently rechecks scope/head/ACL/quarantine/AEAD and whole source
before preparation and every byte exposure. The final head check precedes the consumer.
Selectors, digests, retained candidates and receipts are not authorization or atomic CAS.

## Preserved incomplete result

`status=incomplete`, four unresolved stages, `validation_report=null` and CLI exit code 3
remain. This API does not qualify complete auxiliary/protection state, Native numbering
or layout, save/reopen/reference update/render, DB/issuer/execution/publication or the
P09 Gate. Executable-route denial remains active.

## Verification

The first API run recorded 55 passes and two failures on native source zero. The original
failure is preserved in `implementation/p09/evidence/p09-361-source-note-style-api-components023.v1.json`.
The recovery retained 49 unaffected positive API passes, reran six style API tests and the
two historical failures, and passed all eight. API coverage is therefore 57 unique cases,
not 57 newly executed recovery cases. The same recovery passed 12 core tests and three
stored tests, including API JSON request construction and existing-zero preservation/new-zero
rejection. See `implementation/p09/evidence/p09-361-source-note-style-api-recovery024.v1.json`.
These results qualify the source API and component joins, not Native or the P09 Gate.
