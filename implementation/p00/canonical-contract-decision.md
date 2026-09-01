# P00-08 Canonical Contract Decision

- Decision state: `accepted_for_implementation`
- Baseline reviewer approval: `pending`
- Canonical feature source: `FEATURE_COVERAGE_MATRIX.csv`
- Migration registry: `specs/capability-id-migrations.v1.json`

## Capability identity

`FEATURE_COVERAGE_MATRIX.csv`의 609개 `capability_id`를 유일한 canonical namespace로 사용한다. legacy ID는 runtime alias로 허용하지 않는다. planner/importer는 migration registry의 규칙에 따라 canonical operation으로 명시적으로 변환하고, 변환할 수 없는 모호성은 실패시킨다.

one-to-many legacy operation은 한 operation으로 숨기지 않는다. 예를 들어 `table.cell_border_background`는 전달된 인자에 따라 `table.cell_border`, `table.cell_fill`, `table.cell_padding`의 독립 operation으로 분해하며 DAG와 receipt에도 각각 남긴다.

## Enum identity

- Capability risk: `low | medium | high | critical`.
- Validation check state: `pass | fail | unverified | skipped_by_policy`.
- Validation overall state: `verified | partial | failed | unverified`.

check 상태와 overall 상태는 의미가 다른 별도 enum이다. 수행하지 못한 check는 `unverified`이며, 정책에 따라 의도적으로 금지한 check만 `skipped_by_policy`다. 둘 다 `pass`로 집계하지 않는다.

## WBS dependency model

각 phase는 다음 DAG를 사용한다.

1. 첫 task가 phase 선행 조건을 상속하고 계약·실패 조건을 고정한다.
2. 중간 task는 첫 task만 의존하며 `parallelizable=yes`다.
3. 마지막 task는 같은 phase의 앞선 모든 task를 의존하고 `parallelizable=no`다.

따라서 병렬 표시와 실제 dependency가 일치하며, 마지막 Gate task는 누락된 중간 결과가 있으면 시작할 수 없다.

## Fail-closed validation

`tools/design-validation/validate_design.py`는 `PyYAML` 또는 `jsonschema`가 없으면 오류로 종료한다. OperationPlan 예제의 capability reference, migration target, enum vocabulary, CSV/JSON WBS 동등성, dependency/parallelizable 규칙을 함께 검사한다.

## 승격 조건

이 결정은 구현 기준으로 적용됐지만 P00-08 `PASS`는 아니다. 생성 결과의 결정성, validator green, baseline reviewer의 명시적 승인까지 확보한 뒤에만 `PASS` 후보로 승격한다.
