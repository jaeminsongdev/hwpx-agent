# Capability Registry 생성과 유지

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 입력 source

- 공식 한/글 도움말 메뉴/기능 페이지.
- 공식 HWPX/OWPML schema와 변경 이력.
- 공식 HWP Automation ActionTable/ParameterSetTable/HwpAutomation/Event 자료.
- 공식 WebHWP 개발 가이드.
- target build runtime probe와 macro discovery 결과.

## generated artifacts

- `capabilities.generated.json`
- `action-bindings.<build>.json`
- `parameter-schemas.<build>.json`
- `feature-doc-index.json`
- Rust enums/validators.
- conformance test skeletons.
- coverage report.

## source record

각 source 항목에는 origin URL/file, version, fetched_at, checksum, parser version, license note, raw label, normalized capability candidates가 들어간다.

## human review

자동 importer 결과는 `candidate`다. semantic capability 이름, 위험, 권한, operation schema, expected effect, rollback, test fixture를 사람이 검토한 뒤 `verified_binding`으로 승격한다.

## build drift

새 한/글 build에서 action/parameter 목록, default values, output structure, render가 바뀌면 drift report를 만든다. 영향 capability는 자동으로 `unverified_for_build`가 되어 production route에서 제외된다.
