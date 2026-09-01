# 기능별 구현 계약 사용법

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 산출물

- `specs/capability-contract-v1.schema.json`: 계약 한 건의 상위 스키마.
- `specs/capability-contracts.generated.json`: **609개 전 기능**의 기계 판독 계약.
- `docs/04_feature_catalog/contracts/`: 영역별 사람이 읽는 구현 계약.
- `FEATURE_COVERAGE_MATRIX.csv`: 지원 상태와 phase의 canonical 표.

## 구현자가 기능 하나를 시작하는 순서

1. `feature_id` 또는 `capability_id`로 matrix와 generated contract를 찾는다.
2. selector와 `args_schema`를 Rust type 및 JSON Schema로 승격한다.
3. target profile의 capability binding이 없으면 P02/P10 binding 작업을 먼저 수행한다.
4. `support_level`에 맞는 direct/automation 경로만 구현한다.
5. happy, boundary, negative, preservation, target-build fixture를 만든다.
6. semantic readback과 required oracle evidence가 성공한 뒤 registry 상태를 `implemented_unverified → verified`로 바꾼다.
7. MCP에 새 공개 도구를 만들지 말고 기존 `OperationPlan` operation으로 노출한다.

## 중요한 제한

이 계약의 `automation_binding.binding_key`는 안정된 lookup key다. 실제 HAction·ParameterSet 명칭과 필드 타입은 한컴 공식 ActionTable/ParameterSetTable 및 설치된 대상 build runtime probe에서 생성해야 한다. 문서에 문자열을 추정해 박는 것은 금지한다.
