# P09-112 — 계산된 수식 결과의 실제 문서 출력 연결

## 이번 구현

기존 실제 문서 수식 계산 결과를 원래 preserving HWPX output 및 fresh authenticated stored provider에 연결했다.
새 caller 값/AST/XML/원본 선택자를 받지 않는다. 명령·저장 결과·visible result 세 leaf를 함께 변경하고
수식/format/원본 숫자 입력 및 나머지 package 전체 bytes를 보존한다. 원본 파일과 이전 in-memory 모델을 덮어쓰지 않는다.
빈 닫힌/self-closing cache도 원래 decoder가 수용하는 경우에만 갱신한다.

원래 P111 보호 helper body는 동일하며 내부 visibility만 crate 범위로 넓혀 재사용했다.
부분/native 의미를 full 승격하거나 issuer/atomic publication을 만들지 않았다. 현재 제품 route는 계속 거부한다.
주석 전체 실행은 실제 author/time/state/정책 근거가 부족하므로 열지 않았고 P09 field result 경로를 진척했다.

## 현재 소스 검증

| 검사 | 결과 및 범위 |
| --- | --- |
| package library + 관련 10 integration suites | 126 통과 |
| 기존 form_stored_provider 전체 | 170 통과, 295.28초 |
| 최종 합계 | 296 실행/296 서로 다른 전체 테스트명, 실패·ignored·filtered0 |
| 신규 Rust | source5 + generic leaf2 + stored3 = 10, 위 총합에 포함 |
| 현재 executable 목록 | final test12, unexecuted CLI copies2, pre-lint diagnostics13, failed2 = 29 |
| 원래 current-source component validators | 15 검증, green0, P09 OPEN |
| 원래 default conformance | matrix_drift/exit1 그대로 |

최종 package batch는 b25d1d/session96271 → f24379/exit0이며 final CLI는
1ea521/session87423 → eaafde/exit0이다. 마지막 test-only lint 정리 이후 package126을 다시 실행했다.
기존 P111의405 결과를 현재 core 변경의 결과로 가져오지 않았다. 반복/초기/진단 실행도 합산하지 않았다.
실제 current12 binary --list inventory b6889b와 byte/SHA는 regression/source-progress에 고정한다.
strict lint와 신규 Rust9 단독 fmt, diff/source ancestry 및 새 Python 결과는 최종 receipt에 기록한다.

## 원본 사례와 새 derivative

원래 locked actual36은16 formula/no-op +20 no-formula다. source bytes/SHA admission과 기존 evaluator가 같다.
formula를 포함한16개 모두 first-cell numeric derivative를 검사했으며 6개는 계산값이 달라 갱신,
10개는 계산값이 현재 cache와 수학적으로 같아서 NoChange였다. 이10개를 갱신 성공으로 세지 않는다.
별도 canonical 상대/absolute/negative/fraction 및 빈 닫힌/self-closing cache derivative, protected target,
stale source/tiny writer, 원래 AST/input/part preservation·output re-import를 검사했다.
새 native capture/한글 실행 증거는 없다. multiple formulas/sections 전체 동시 갱신의 추가 corpus는 아직 필요하다.

Stored3은 actual-source derivative를 실제 artifact/revision service API에 넣은 in-memory storage/fixture scanner/
synthetic actor/key 기반 검사다. 실제 SQL/durable issuer가 아니다. 새 prepare/output와 cached 재사용에서 ACL 회수,
AEAD 변조, quarantine, head 변경, actor/tenant/project/branch/document5 변경은 거부하며 callback은 실행되지 않는다.
새 ingest/commit/head/publication 없이 전후 원래 authorized source/math/output 검증을 한다.

## 실패와 보존

첫 source test는2 PASS/2 FAIL이었다: 첫16 input이 모두 formula이며 모든 first-cell 변화가 그 수식에 영향을 준다는
잘못된 fixture 가정, 실제 A1 입력을 확인하지 않은 예상값이 원인이었다. original native/math guard는 바꾸지 않았다.
36개 모두에서 실제 formula inventory를 고르고 NoChange를 실제 computed-vs-cache equality로 독립 확인했으며
absolute case는 입력에 무관한 typed 식으로 검증한다. 실패 source2와 failed executable을 보존했다.

새 derivative helper는 temporary borrow compile error(E0716)를 고쳤으며 그 source를 보존했다.
빈 self-closing result의 core mutation은 맞았지만 독립 보존 readback이 '/>' 확장을 expected edit에 반영하지 않아
4 PASS/1 FAIL(Preservation)이 났다. 원래 source-derived name으로 expected declared tail edit를 보완했고
실패 production/source test3·failed executable을 보존한 뒤 실제 source5/leaf2를 재실행했다.

초기 strict lint의 큰 readback helper/4bool struct/wildcard import는 helper 분리, unqualified authority enum,
정확한 imports로 고쳤다. warning 억제나 limit 완화는 없다. 그 source4와 pre-lint executable13을 보존했다.
새 test lint의 similar names/unnecessary wraps source1도 보존하고 수정했다. 중복 --lib 옵션의 command 실패는
검증 미실행으로 기록한다. 모든 실패는 초기 실패 receipt에 분리한다.

원래 source980 중974 unchanged + 부모6 whole preimages/정확한 선언 역변환을 검증했다(0b9d73).
이전 unmodified audit를 그 exact preimage view에서 실제 실행하여 inherited raw1881과 old executable349를 확인했다.
역사적 모든 qualification/실행 파일을 재실행했다는 뜻은 아니다. source 새17 포함 current997/delta23,
archive17/predecessor2/current executable29를 current manifest에 고정한다. 초기 실패/원본/private/user dirty를 보존했다.

## 잔여와 다음 실제 단계

field-result 후보 출력 연결은 진척했지만 full field/compiler/product envelope/durable policy/issuer/atomic publication은
미완료다. 다음 안전한 검증은 multiple-formula/multi-section batch에서 보호·stale·부분 출력 방지와
원래 source-policy/full compiler/ExecutionManifest 요구를 연결하는 것이다. native author/time/state나 정책을 추정하지 않는다.

metadata/coordinates, full comment/rich compiler/source mapping, durable integration, fields/date/external/document 의미,
trusted protection/atomic publication, actual P84 SQL 원인·회귀의 최소6 큰 묶음은 유지하며 이번에 닫힌 묶음은0이다.
P09/A12/A13 OPEN/green0, native34 NOT_RUN/INPUT_CHANGED_RE_ADMISSION_REQUIRED,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED/product false/no P10/전체 목표active를 유지한다.
한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설정·설치/stage·commit·push/삭제·이동을 실행하지 않았다.
HEAD/사용자 dirty/private/원본·실패 증거 및 루트 PLANS 삭제 상태를 유지했다.

