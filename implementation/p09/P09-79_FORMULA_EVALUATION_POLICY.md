# P09-79 표 계산식의 실제 값 평가 경로

## 현재 경계

P79는 **canonical numeric source/math/service COMPONENT PASS**다. 기존 P73은 실제 수식 AST와 저장된 cache를 읽지만 값을 평가하지 않는다. 이번 단계는 그 다음 제품 경로에 필요한 bounded exact-decimal evaluator와 실제 HWPX 숫자 출처 연결, fresh authenticated service를 구현한다. 보존된 실제36개 중 수식16개/숫자112개/전체 cell128개를 검증했다. 새 source10/service6 및 현재 domain593/CLI142/package921=1656 named tests가 통과했다. raw source qualification과 원래 whole qualification CLI/native/product acceptance는 구분하며 새 결과를 native cache, 실행 승인·layout·persisted product acceptance로 취급하지 않는다.

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

원래 code5곳의 변경은 domain module1/core meanings module1/stored meanings module1/test module pair1/원래 decimal helper의 crate-only visibility1이다. 원래 parser/cache/model/reader/service/SQL/dependency/test bodies/locks는 바꾸지 않는다. 이 다섯 선언 변경을 제거하면 각 원본 whole bytes/SHA가 같아야 한다. math 전 원본2/source 연결 전 원본7 및 초기 실패 whole sources를 보존한다.

실제 source adapter는 같은 원본 part/tree의 table/cell/begin/paragraph anchors 및 원래 owner/grid/AST를 묶는다. numeric cell은 병합되지 않은 하나의 실제 문단이어야 한다. 원래 `TextFlowReader::read_preserving_source`로 읽고 NFC/trim 없이 plain text atom을 이어 원래 canonical decimal parser를 호출한다. 원래 non-visible 분류와 정확한 HP `linesegarray`/leaf `lineseg` 구조가 모두 확인된 layout만 숫자 계산에서 제외한다. 그 표식/opaque nodes는 원본 전체 graph에서 제거하지 않는다. 숨은 text/control/foreign child, field cache, tab/break, 여러 문단, blank/text/locale/Unicode coercion, 병합 alias 의미는 추정하지 않는다. 사용하지 않은 비숫자 cell은 Unavailable로 보존하고 의존하면 typed MissingValue다. 모든 source FORMULA targets를 atomic 평가하고 일부 성공만 반환하지 않는다.

저장 service는 새 결과 생성·재사용 모두 원래 fresh source/meaning·scope5·read scope·ACL/AEAD/quarantine/head 검증을 먼저 수행한다. 계산 후 원래 authenticated whole source checkpoint를 다시 수행한다. immutable source/value/binding/receipt 전체가 같아야 한다. 읽기 권한이 없으면 원래 provider bind가 먼저 거부한다. 두 번의 head read는 atomic lock/CAS가 아니며 새 source/result/IR ingest, commit, publication 또는 issuer가 아니다. 현재 service 검사는 실제 bytes를 읽는 기존 in-memory metadata/scanner fixtures이며 새로운 PostgreSQL/durable/native acceptance 주장이 아니다.

기존 저장된 unverified caches는 계산 후 비교 대상으로만 사용한다. 실제16개가 같더라도 cache input/overwrite/native qualification으로 승격하지 않는다. 전체 원본 graph·resources·보호 상태와 partial markers는 유지하고 full document context는 여전히 거부한다. 전체 formatter가 만든 범위 밖 서식 변경6개는 whole archived 후 원래5 frozen hashes와 test-root 원래 순서로 복구했다. formatter check는 새11개 파일에만 수행하고 원래 formatting/guards를 바꿔 전체 PASS를 제조하지 않는다.

이 source/service 경로와 남은 필드·참조·댓글, 전체 importer/lineage/policy/issuer/manifest/publication/lifecycle/whole qualification/current admission을 마쳐야 한다. P26 non-green, P62 16fde8 UNRESOLVED, INPUT_CHANGED_RE_ADMISSION_REQUIRED, full34 NOT_RUN/0green, P09 Gate OPEN/Goal ACTIVE/no P10/접근허용 금지를 유지한다.
