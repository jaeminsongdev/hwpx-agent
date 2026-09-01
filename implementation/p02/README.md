# P02 Official Catalog Importer·Capability Registry

P02는 immutable source lock을 format별 extractor로 읽어 `SourceRecordV1`을 만들고, candidate/review/binding/probe/signing 단계로 넘긴다. 원본 source를 수정하지 않으며 raw action은 metadata로만 보존하고 public/LLM 실행 surface로 노출하지 않는다.

## Task reports

- `P02-01_REPORT.md`: SourceRecord v1 schema, samples, negative cases and generated models.
- `P02-02_REPORT.md`: source-locked read-only Help extractor and private actual extraction.
- `P02-03_REPORT.md`: source-locked Automation PDF extractor, private actual extraction and independent verification.
- `P02-04_REPORT.md`: source-locked KS X 6101/OWPML schema and package-part extraction with independent coverage verification.
- `P02-05_REPORT.md`: deterministic review-only candidate graph over all P02 source records.
- `P02-06_REPORT.md`: complete semantic disposition of every candidate node/edge against the canonical capability matrix.

## 현재 task

`P02-07 Binding model`을 현재 PC 로컬 범위에서 수행한다. reviewed catalog와 exact 2020 target profile을 고정하고 action/method/parameter binding schema와 codegen을 구현하되, P02-08 probe 전에는 실행 가능성을 `unverified`로 유지한다. 사용자 문서나 한글 UI 조작은 필요하지 않다.
