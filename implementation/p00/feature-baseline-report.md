# P00-08 Feature Baseline Review

- Review state: `passed`
- Approval state: `explicit_user_blanket_approval`
- Baseline: 2026-08-31 design package

## Structural inventory

- Domains: 16
- Feature rows: 609
- Generated capability contracts: 609
- Duplicate `feature_id`: 0
- Duplicate `capability_id`: 0
- Contract required-field gaps: 0
- WBS tasks: 190 across P00~P20

## Support disposition

| Disposition | Count |
|---|---:|
| `HYBRID` | 345 |
| `AUTOMATION_FULL` | 191 |
| `OPTIONAL_EXTERNAL` | 37 |
| `DIRECT_FULL` | 28 |
| `READ_ONLY` | 3 |
| `PRESERVE_ONLY` | 2 |
| `DISABLED_BY_POLICY` | 2 |
| `UNSUPPORTED` | 1 |

## Required fail-closed policies confirmed

- `sec.password_bypass`: `UNSUPPORTED`.
- Macro define/run: `DISABLED_BY_POLICY`.
- OLE insert/properties: `PRESERVE_ONLY`.
- Signature inspection/security audit: `READ_ONLY`.

## Resolved implementation drift

### Capability namespace

`FEATURE_COVERAGE_MATRIX.csv`의 609개 ID를 canonical source로 고정했다. JSON OperationPlan과 공개 문서의 legacy ID를 canonical ID로 교정했고, `specs/capability-id-migrations.v1.json`에 rename/args split/operation split 규칙을 기록했다.

runtime은 legacy alias를 직접 받지 않는다. planner/importer만 migration 규칙에 따라 typed canonical operation으로 변환하며, 모호한 변환은 실패한다.

### Enum vocabulary

- Capability risk는 `low|medium|high|critical`로 통일했다.
- Validation check state는 `pass|fail|unverified|skipped_by_policy`로 통일했다.
- Overall validation state는 의미가 다른 별도 타입 `verified|partial|failed|unverified`로 유지했다.

### WBS scheduling

중간 task는 phase의 첫 task만 의존하고, 마지막 task는 앞선 모든 task를 join하도록 생성기를 교정했다. 23개 생성 파일을 연속 두 번 생성한 SHA-256 비교에서 비결정 파일은 0개였다.

### Validator behavior

Python validator는 `PyYAML` 또는 `jsonschema`가 없으면 오류로 종료한다. OperationPlan capability reference, migration target, risk/check-state enum, WBS CSV/JSON 동등성, dependency/parallelizable 규칙을 추가로 검사한다.

## Validation closure

- `tools/design-validation/requirements.txt`의 pinned direct dependency를 설치했다.
- full validator는 16개 schema, 609 feature, 609 contract, 190 WBS를 오류 0으로 검증했다.
- `python -S` negative run은 필수 dependency 누락을 exit 1로 검출했다.
- 사용자의 전체 승인으로 baseline reviewer approval을 확보했다.

## P00-08 exit requirements

1. [x] Choose one canonical capability namespace and migration mapping.
2. [x] Choose one risk vocabulary and one validation-state model.
3. [x] Correct WBS generator dependency/parallelizable semantics.
4. [x] Make validator dependency checks fail closed.
5. [x] Add registry-reference validation for examples and generated plans.
6. [x] Re-run generation and prove deterministic output.
7. [x] Install the required validator dependency and obtain a green full run.
8. [x] Obtain explicit baseline reviewer approval.

P00-08 is `PASS`. 이 판정은 canonical design baseline에 한정되며 P00 전체 Gate나 Hancom runtime 증거를 승격하지 않는다.
