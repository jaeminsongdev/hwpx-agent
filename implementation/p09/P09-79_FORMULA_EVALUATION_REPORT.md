# P09-79 실제 문서 수식 값 평가 — source/math/service COMPONENT PASS

## 현재 결과

계산 엔진에 실제 HWPX 숫자 출처와 fresh authenticated service를 연결했다. source10/service6의 새 검사 및 현재 domain 전체53 targets/593 검사가 통과했다. **현재 named 전체 회귀는1656 PASS이며, P79는 이 canonical numeric source/math/service component 범위의 PASS다. P09 전체 importer·제품·native Gate 완료가 아니다.** 한글·COM·UI·접근허용은 실행하지 않았다.

## 실제 문서 연결

보존된 actual36개를 모두 읽었다. 수식이 있는 문서16개/table16/formula targets16, 원본 cell bindings128/숫자112/anchors144, whole meaning graph unchanged36이다. 다른20개는 수식이 없는 실제 source 검사이며 수식 성공16개에 더해 세지 않는다. 원본 unverified decimal caches16개와 계산 후 비교했으며 모두 같았다. cache는 계산 입력이 아니고 덮어쓰거나 native-verified로 바꾸지 않았다. independent fresh process2의 전체 payload equality는 `actual-consumer.v1.json`에 보존했다. 서식 복구 후 현재 source로 재빌드한 consumer의 두 fresh process도 전체 payload가 같았다(47c0da/2e0b53,0c8072/407d38). `actual-consumer.current-source.v1.json`에 current executable/build와 원본 SHA 복구 후 실행 범위를 별도로 기록했다.

원래 numeric paragraph/owner/grid/AST/cell/begin anchors를 그대로 쓴다. 기존 flattened graph가 layout opaque/control refs를 보존하는 것이 initial MissingValue 원인이었다. 새 adapter만 원래 source-preserving TextFlowReader를 사용하도록 수정했다. 원래 non-visible 판정과 exact HP lineseg 구조를 확인한 경우에만 계산에서 제외하고, 실제 원본 graph에서는 어떤 표식도 제거하지 않는다. 숨은 text/control/foreign metadata·field cache·blank/noncanonical/locale/Unicode 숫자·tab/break·여러 문단은 추정하지 않는다. 순환 참조와 0 division도 실제 in-memory source derivative에서 거부했다.

## 서비스 검증과 한계

기존 StoredFixture에 실제36개 bytes를 넣어 direct import와 values/bindings/receipts 전체를 비교했다. 생성과 재사용 모두 AEAD 변조·ACL 회수·head advance·quarantine 및 tenant/subject/project/branch/document scope5 치환을 거부한다. read scope가 없으면 원래 bind가 먼저 Scope로 거부한다. 계산 전 original whole source/meaning verify와 후 original authenticated exact-source checkpoint를 유지했다. 새로운 ingest/commit/head write가 없고 원래 whole graph/partial context denial이 같다.

이는 기존 in-memory repository/scanner/keys/sealed revision fixture 기반 service component 검사다. 새 PostgreSQL/durable source lineage/issuer/atomic CAS/publication/실행 경로를 증명하지 않는다. 수식 값 자료를 임의 public action 또는 전체 importer 승인으로 사용하지 않는다.

## 자동검증

- source 새10 PASS(a47da9), service 새6 PASS(146b1f). source actual36/targets16/cells128와 service actual36/targets16/cells128를 각각 검사했다. 별도 제품 기능 수로 합산하지 않는다.
- 원래 math14 tests(그중 한 test 안 integer property3362 cases 포함)/현재 전체 domain53 targets593 PASS(cd6593/23ec93).
- 원래 core epoch 전체 CLI136/package911=1047 PASS는 `core-product-regression.v1.json`에 유지한다. 새 source/service 전 결과이므로 현재 연결 경로 전체 PASS로 재사용하지 않는다.
- 새 연결을 포함한 첫 전체 회귀는 통과했으나 실행 중 formatter 복구가 있어 mixed-format epoch로 구분하며 현재 PASS에 재사용하지 않는다. 복구 후 최종 전체 회귀96f425…279146 exit0:105 targets/CLI142+package921=1063 PASS, failed/ignored/filtered0. 현재 domain593과 합계 named158 targets/1656 PASS다. source10/service6/math14는 이 총합에 포함하며 중복 합산하지 않는다.
- 현재 explicit5 crates의 lib/tests/examples strict lint PASS(5a9d48; earlier f3c12f/45b50a). 새11 files-only rustfmt check 및 git diff --check PASS(611789; earlier76edf2). 원래 frozen files를 다시 formatting하지 않는다.

## 원본과 실패 보존

원래 code5곳은 module declarations4(그중 test module pair1)와 decimal helper crate-only visibility1만 바뀌었다. 전체 역변환6928f6은 각각 원래 whole bytes/SHA와 같다. 원래 parser/helper bodies/AST/cache/readers/서비스 권한검사/dependencies/SQL/tests/assertions/locks는 바꾸지 않았다.

전체 formatter가 기존 frozen files5개와 기존 test module order에 서식 변화를 만든 것을 실제 보존 검사에서 발견했다. formatted whole6개를 보존하고 기존5개 math-checkpoint hashes와 test root 전체 body/order로 복구했다. 618625/6928f6/58af03으로 raw recovery와 source 전 whole originals7개를 확인했다. 신규 작업 archives26개를 보존했다. 초기 compile/no notes getter, actual MissingValue, lint, missing-read-scope fixture, noncanonical derivative와 두 audit failures는 `source-initial-failures.v1.json`에 남겼다. 기존 실패와 old expectations를 지워 통과시키지 않았다.

P59–P78 predecessor pins4540/원래1551 files·51047460 bytes/native originals75/P78 unchanged483 및 현재 math-checkpoint unchanged489 원본 해시를 확인했다(8e2714/4ffd52). raw preservation이며 원래 whole qualification scripts를 전부 재실행했다는 주장은 아니다. frozen P78 source116142/bd39e62a… 및 audit3906/cd68fa72…, P79 math checkpoint112796/7f757f6f…는 그대로 보존한다.

## 남은 작업과 Gate

현재 whole original code inverses/source/raw pins/actual inputs/named tests는 source-progress/final-audit에 묶는다. 이는 원래 전체 qualification CLI의 재실행이나 whole product acceptance가 아니다. 다음은 다른 field/reference/comment meanings, full importer/settings/catalog, 실제 committed source-result-IR lineage/policy/scanner/issuer/ExecutionManifest/publication/idempotency/lifecycle/recovery/load/whole qualification/current admission이 필요하다. 수식 계산의 finite decimal/precision/fractional exponent 경계는 전체 한글 수치·coercion 의미 지원이 아니다.

P26 failed_semantic_non_green/P62 16fde8 UNRESOLVED/current admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN·0green/P09 Gate OPEN/Goal ACTIVE/no P10를 유지한다. 원본 삭제/이동·trust/config·native dispatcher·stage/commit/push·dependency 설치 없음.
