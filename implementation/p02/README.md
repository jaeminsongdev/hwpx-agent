# P02 Official Catalog Importer·Capability Registry

P02는 immutable source lock을 format별 extractor로 읽어 `SourceRecordV1`을 만들고, candidate/review/binding/probe/signing 단계로 넘긴다. 원본 source를 수정하지 않으며 raw action은 metadata로만 보존하고 public/LLM 실행 surface로 노출하지 않는다.

## Task reports

- `P02-01_REPORT.md`: SourceRecord v1 schema, samples, negative cases and generated models.
- `P02-02_REPORT.md`: source-locked read-only Help extractor and private actual extraction.

## 현재 task

`P02-03 Automation extractor`를 현재 PC 로컬 범위에서 구현한다. 사용자 문서나 한글 UI 조작은 필요하지 않다.
