# 설계 유지 도구

- `design-generation/generate_capability_contracts.py`: 기능 CSV에서 609개 계약·영역 문서를 재생성한다.
- `design-generation/generate_wbs.py`: P00~P20 phase 문서와 190개 WBS를 재생성한다.
- `design-validation/validate_design.py`: JSON/YAML, 기능/계약/WBS 일관성, JSON Schema 예제, skill frontmatter, Markdown fence를 검사한다.

저장소 루트에서 `python tools/design-validation/validate_design.py`로 실행한다. 생성기를 실행하기 전에 변경 파일을 커밋하고 생성 결과 diff를 검토한다.
