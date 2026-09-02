# P02 Official Catalog Importer·Capability Registry

P02는 immutable source lock을 format별 extractor로 읽어 `SourceRecordV1`을 만들고, candidate/review/binding/probe/signing 단계로 넘긴다. 원본 source를 수정하지 않으며 raw action은 metadata로만 보존하고 public/LLM 실행 surface로 노출하지 않는다.

## Task reports

- `P02-01_REPORT.md`: SourceRecord v1 schema, samples, negative cases and generated models.
- `P02-02_REPORT.md`: source-locked read-only Help extractor and private actual extraction.
- `P02-03_REPORT.md`: source-locked Automation PDF extractor, private actual extraction and independent verification.
- `P02-04_REPORT.md`: source-locked KS X 6101/OWPML schema and package-part extraction with independent coverage verification.
- `P02-05_REPORT.md`: deterministic review-only candidate graph over all P02 source records.
- `P02-06_REPORT.md`: complete semantic disposition of every candidate node/edge against the canonical capability matrix.
- `P02-07_REPORT.md`: exact-target binding schema/codegen and complete current-2020 candidate/unavailable registry.
- `P02-08_REPORT.md`: exact current-PC 2020 x86/STA disposable runtime probe and independently verified trace.

## 현재 task

`P02-09 Registry signing·drift`를 exact current-PC 2020 범위에서 구현한다. private binding registry와 independently verified P02-08 trace를 입력으로 target-scoped signed manifest와 deterministic drift report를 만들되, runtime evidence가 없는 binding을 승격하거나 routing을 활성화하지 않는다.
