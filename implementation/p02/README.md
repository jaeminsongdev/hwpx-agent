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

## 현재 task

`P02-08 Runtime probe tool`을 exact current-PC 2020 x86/STA 범위에서 구현한다. private binding registry를 입력으로 disposable fixture와 bounded trace를 만들되, 실제 한글 실행 전까지 모든 binding을 `unverified`로 유지한다. harness가 준비될 때까지 사용자 조작은 필요하지 않다.
