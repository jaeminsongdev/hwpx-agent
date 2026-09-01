# P02 Official Catalog Importer·Capability Registry

P02는 immutable source lock을 format별 extractor로 읽어 `SourceRecordV1`을 만들고, candidate/review/binding/probe/signing 단계로 넘긴다. 원본 source를 수정하지 않으며 raw action은 metadata로만 보존하고 public/LLM 실행 surface로 노출하지 않는다.

## Task reports

- `P02-01_REPORT.md`: SourceRecord v1 schema, samples, negative cases and generated models.
- `P02-02_REPORT.md`: source-locked read-only Help extractor and private actual extraction.
- `P02-03_REPORT.md`: source-locked Automation PDF extractor, private actual extraction and independent verification.
- `P02-04_REPORT.md`: source-locked KS X 6101/OWPML schema and package-part extraction with independent coverage verification.

## 현재 task

`P02-05 정규화·중복 후보`를 현재 PC 로컬 범위에서 구현한다. P02-02~04의 provenance를 보존하고 후보를 자동 병합하지 않으며 restricted 입력의 파생 graph도 private evidence에만 발행한다. 사용자 문서나 한글 UI 조작은 필요하지 않다.
