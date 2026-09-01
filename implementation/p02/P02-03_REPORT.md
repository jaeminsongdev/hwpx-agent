# P02-03 Automation PDF Extractor Report

- Completed: 2026-09-02
- Audited source commit: `aed6308d4713c41600426b94e95802b00b9a24bd`
- Task state: `pass_current_pc_local`
- Review: `STRICT / xhigh`, blocker/major/minor `0/0/0`

## Delivered

- Read-only PDF layout extractor bound to the exact source-lock IDs and SHA-256 values for ActionTable, ParameterSetTable, HwpAutomation and EventHandler.
- Pinned `pdfminer.six==20251230`; no OCR and no inferred correction of source text.
- Separate document parsers for ruled Action rows, Parameter rows and page continuations, Automation object tables, the HwpAutomation event summary and explicit EventHandler `STDMETHOD` declarations.
- Original name, description, declared Type/SubType representation, method parameters, source page range, section and source identity in deterministic `SourceRecordV1[]`.
- Input/source-lock identity revalidation, bounded in-memory parsing, symlink/junction denial, Unicode replacement-character rejection and atomic no-overwrite publication.
- Restricted records may publish only below Git-ignored `implementation/p02/evidence`; raw action/parameter names remain internal metadata and are not connected to an execution surface.
- Independent verifier for all four input identities, schema/semantic validity, record/source kind compatibility, page range, section/anchor, extractor identity and ordinal continuity.

## Actual locked extraction

| Source ID | SHA-256 | Pages | Records | Record kinds |
|---|---|---:|---:|---|
| `hancom-action-table-2504` | `bb876a95ea4e0f4b052c94188a1390b5f981161223759f59f52fc324c8130a87` | 52 | 937 | `action_table` |
| `hancom-parameter-set-table-2504` | `6fa10e0ae69711af99a03e54c321c6c922796bd943badf8c21b2c7dfb780ad6e` | 179 | 1,205 | `parameter_table` |
| `hancom-automation-manual-2504` | `917142de2704ae037b0132f5a344ce5331b1fd96cc19dd574666aaacfbf0268c` | 69 | 379 | `automation_object`, `automation_event` |
| `hancom-event-handler-2504` | `ed58788419119d2c73e2abdc8195edeb2439c5bd1a14a2c91ec034c5d25b3afe` | 6 | 11 | `automation_event` |

- Total: 2,532 records: Action 937, Parameter 1,205, Object 363 and Event 27.
- Coverage: Action data pages 2-49; Parameter 121 sections and their data/continuation pages; Automation data pages 12-69 across 25 object sections; EventHandler declaration pages 3-4.
- Object declarations: 147 items with 267 parsed parameters. HwpAutomation event summary 16 records and EventHandler declarations 11 records remain separate source-bound evidence.
- Deterministic output: two final emissions were byte-identical, SHA-256 `03db035d408d03ce3f78d4eca8ca76d7f9e8076ef8fadd49d8f3ed4b885317b5`.
- Independent verifier: 2,532 records, every source has records, errors 0. Unicode replacement characters and NUL bytes 0.

The authoritative record text remains local at [private Automation PDF records](evidence/automation/automation-pdf.records.v1.json). It is not reproduced or committed.

## Source discrepancies preserved

- ParameterSet page 165 has 11 rows whose `Type` column is blank while `SubType` contains an explicit `PIT_*` token. They are preserved as `[Type missing] [SubType=...]`; no Type is invented.
- Ten Automation rows have a table item name that differs from the attached declaration function name. Both original strings remain in the same source-bound record; the extractor does not rename either side.
- The legacy private-use Hangul glyph present in the PDFs remains byte-faithful Unicode metadata. It is not replaced from memory.
- These records remain `documentation_only`; no discrepancy is promoted to a current-2020 executable binding before P02-06/P02-08 review and probe evidence.

## Validation

- Visual inspection after Poppler rendering: representative ruled table, continuation, object, event summary, event declaration and blank-Type pages. The document-specific layout boundaries match the parser rules.
- Synthetic suite: 8/8 Automation tests passed; combined P02 suite 16/16 passed on Windows and official Python 3.13.13 Linux image `sha256:355bfa66770995d7e9a0da4b3473b44d0cb451f6b56f5615ad9c39e3c4eca03f` with a read-only repository mount.
- Negative coverage: continuation without owner, duplicate declared types, unmarked object row, malformed event declaration and restricted-output escape; deterministic identity and four-source verifier binding are positive invariants.
- Current repository FULL bootstrap: 5/5 lanes passed; secret findings, vulnerabilities and forbidden licenses 0; CycloneDX components 147.
- Clean clone at `aed6308`: FULL bootstrap 5/5 passed, private evidence absent by design, post-run Git status changes 0.
- `pip check`, compileall, JSON format, schema/semantic validation and independent actual-output verification all passed.

## Preserved boundaries

- The four source PDFs, source archive, user documents and installed Hancom files were not modified or committed.
- 한글/COM/UI was not opened or automated for this task.
- The PDF metadata does not qualify a method/action on installed 2020; runtime support remains unverified until the binding/review/probe tasks.
- Other Hancom versions, production/provider use and redistribution remain outside the current-PC local scope.

## Failed checks retained

- Initial fixed-column parsing exposed real `PMT_*` array types and shifted columns; parser rules were narrowed to explicit header/type tokens and rerun.
- Automation declarations can span pages, contain overloads or differ from table names; parsing was deferred until row continuations were complete and source mismatches are preserved.
- HwpAutomation page 46 contains an event summary before object tables, and several pages omit a final horizontal border. Both structures now have explicit tests and deterministic boundaries.

## Next exact task

Implement `P02-04 OWPML extractor`: audit the locked KS X 6101/OWPML machine-readable source set, fail closed if authoritative XSD/package bytes are absent, then index namespace/version/package part/element/attribute records without executing raw XML. Recommended reasoning effort: `xhigh`; P02 final Gate: `max`. No user local operation is required at task start.
