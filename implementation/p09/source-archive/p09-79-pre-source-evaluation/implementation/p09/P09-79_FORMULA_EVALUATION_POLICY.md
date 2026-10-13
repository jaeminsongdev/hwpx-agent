# P09-79 표 계산식의 실제 값 평가 경로

## 현재 경계

P79는 **진행 중**이다. 기존 P73은 실제 수식 AST와 저장된 cache를 읽지만 값을 평가하지 않는다. 이번 단계는 그 다음 제품 경로에 필요한 bounded exact-decimal evaluator를 구현한다. explicit typed numeric grid/원래 AST에 대한 수학 검증이며 실제 HWPX numeric-cell source adapter와 authenticated service 연결은 아직 NOT_RUN이다. 새 결과를 native cache, 기존 문서 결과, 실행 승인·layout·product acceptance로 취급하지 않는다.

## 입력·계산 규칙

- 입력은 유한한 exact grid와 위치가 고정된 숫자/원래 검증된 AST/Unavailable이다. duplicate 또는 out-of-bounds cell, 잘못된 원래 AST/grid를 거부한다. 기존 `FormulaCell::from_draft`를 그대로 사용해 original parser/AST/coordinate/dimension 검사를 재사용한다.
- 전체 ordered input·grid·새 limits를 allocation-free bounded SHA serialization으로 묶는다. 전체 JSON을 먼저 메모리에 만들어 제한을 검사하지 않는다. AST는 immutable borrow, 숫자는 고정 snapshot이며 caller 변경은 새 context로 받아야 한다.
- 숫자는 원래 `FormulaDecimal`이다. f32/f64, locale coercion, 문자열·blank→0 또는 bool→number 변환을 사용하지 않는다. numeric 의미가 확인되지 않으면 Unavailable/missing value로 거부한다. 저장된 `FormulaCache`는 입력도 출력도 아니며 기존 cache를 바꾸지 않는다.
- original canonical grammar의 add/subtract/multiply/divide/unary와 bounded integer power, SUM/AVG/PRODUCT, 모든 직사각형 range cell을 처리한다. 상대·절대 reference는 이미 고정된 actual coordinates로 평가한다.
- scalar arithmetic의 각 결과는 i64 coefficient와 설정된 유한 decimal scale 안에 정확히 표현돼야 한다. overflow, 0 division, 비종결 중간 decimal, precision 초과, fractional/과대한 exponent, 0^0은 typed 오류다. 반올림·근사·native 강제 계산 fallback이 없다. 이 닫힌 경계는 모든 native numerical/coercion 의미 지원 주장이 아니다.
- aggregate 내부는 checked i128 rational과 GCD 약분을 사용해 i64를 넘는 내부 합·곱도 최종 값이 표현 가능하면 보존한다. 예: AVG(i64::MAX,i64::MAX), SUM(i64::MAX,1,-1), PRODUCT(i64::MAX,2,0.5). 외부 결과가 유한 범위를 벗어나면 거부한다.
- reference dependency는 한 evaluation 안에서 memoize하고 방문 중인 cell을 다시 만나면 cycle로 거부한다. requested formula targets의 caller order를 유지하고 duplicate/empty/non-formula target을 거부한다. range는 scalar로 첫 cell 선택하지 않으며 aggregate에서 streaming으로 소비한다.

## 유한 예산과 결과

cells≤65536, work≤8000000, depth≤128, exponent≤256, decimal places≤18, input/result bytes 각각≤16MiB의 hard ceilings가 있다. 기본값은 더 작다. 과대한 limits를 clamp하지 않고 거부한다. work와 depth는 expression과 dependency recursion을 모두 포함한다. range 확장·power iteration에도 예산이 적용된다.

모든 target 계산에 성공한 경우에만 values와 whole input/result SHA/count/work의 receipt를 반환한다. 실패 시 partial 결과가 없다. 새 context/values/debug는 redacted이며 receipt는 숫자·셀 내용·native source 값 대신 hashes/counts와 `explicit_numeric_grid_exact_math_not_native_cache_layout_authority_or_execution` scope를 사용한다. receipt·input·값은 임의 public 실행 action이나 제품 admission이 아니다.

## 원본 보호와 다음 필수 연결

old domain root에 새 module declaration 하나만 추가한다. 원래 formula parser/cache/model/reader/service/SQL/dependency/tests/locks를 변경하지 않는다. root와 PLANS 변경 전 whole files, 초기 strict lint source를 archive로 보존한다. 새 declaration을 제거하면 root 전체 bytes/SHA가 같아야 한다.

다음은 실제 HWPX의 원본 cell/field/AST/owner/grid/모든 의존성·숫자 출처를 묶는 source adapter다. string/blank/merged/ambiguous/opaque 셀 의미를 추정하지 않는다. 저장 service에서 원래 fresh source·ACL/AEAD/head/scope 검증을 유지하고, 실제 기존 corpus와 current independent consumers로 평가·보존·실패를 기록해야 한다. 기존 native saved caches는 별도 비교 대상으로만 사용하고 현재 native acceptance로 승격하지 않는다.

이 source/service 경로와 남은 필드·참조·댓글, 전체 importer/lineage/policy/issuer/manifest/publication/lifecycle/whole qualification/current admission을 마쳐야 한다. P26 non-green, P62 16fde8 UNRESOLVED, INPUT_CHANGED_RE_ADMISSION_REQUIRED, full34 NOT_RUN/0green, P09 Gate OPEN/Goal ACTIVE/no P10/접근허용 금지를 유지한다.
