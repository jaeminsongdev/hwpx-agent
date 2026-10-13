# P09-79 실제 값 평가 경로 — 진행 중

## 현재 결과

**새 explicit numeric math engine component PASS. 실제 HWPX source 연결·authenticated service 연결은 NOT_RUN이며 P79/P09 전체 완료가 아니다.** 원래 수식 AST/정확한 grid를 입력으로 계산하는 경로를 구현했다. native cache/실행 승인/제품 acceptance를 추가하지 않았고 한글·COM·UI·접근허용을 실행하지 않았다.

domain root에 `pub mod formula_evaluation;` 하나를 추가했다. 새 evaluator와 exact helper, 새 tests만 작성했고 기존 parser/FormulaDecimal/cache/reader/예상값·assertions·dependencies·source locks는 변경하지 않았다. root의 declaration을 제거한 whole inverse는 원본26177 bytes/SHA `6f44e4baca13f0665abc6c2599bc4ab0ff559af11b02f37d7747a9334c5ccb85`와 같다(83c6ef). 원본 root/PLANS 2개와 초기 실패 source 2개를 보존했다.

## 확인된 자동검증

- 새14 tests: 모든 산술·세 aggregate·직사각형 range·dependency diamond와 memoization·deterministic receipt·missing/Unavailable·self/indirect/range cycle·original AST/grid/중복·target order·typed overflow/0 division/precision·input/result/work/depth bounds·input snapshot drift·기존999999 cache 무시/byte-exact 보존·10240000-cell range의 streaming 예산 중단.
- 모든 부호의 integer add/multiply 3362개 property cases는 위14 tests 중 하나에 포함한다. 별도의 3362 test targets나 제품 기능 수로 세지 않는다.
- current domain 전체 lib/tests **53 targets/593 PASS, failed0/ignored0/filtered0**(f51379/c4e143). 새14개를 포함하며 이전 P78의 선택 domain42와 검증 범위가 달라 총합을 단순 비교하지 않는다. 초기12 tests42eb45, lint 수정 후12a9ffac도 실제 통과 기록이다.
- domain/package/CLI/artifact/revision 전체 lib/tests strict lint `-D warnings` PASS(c1245f); format/diff check0c4a5d PASS. 검사 allow/skip이나 기존 테스트 변경 없음.
- current CLI/package 전체 회귀는 시작했으며 완료 증거를 회수하기 전 PASS로 기록하지 않는다. 해당 live run은 다음 evidence로 이어진다.

## 산술·보존 경계

float/rounding/blank coercion 없이 checked exact rational arithmetic을 사용한다. scalar의 각 결과는 finite i64 coefficient/scale 안에 들어야 한다. aggregate 내부 wide intermediate는 약분 후 마지막에 bound한다. 지원하지 않는 분수 exponent와 비종결 중간 decimal은 명시적으로 거부한다. 이 수학 component를 한글의 모든 계산·형식·문자 coercion 의미와 같다고 주장하지 않는다.

새 result는 source package mutation·기존 cache overwrite·새 native cache 검증이 아니다. source authority 없는 caller graph/hash를 전체 importer로 승격하지 않는다. 입력과 숫자는 redacted debug이며 receipt에는 scope/hashes/counts만 넣는다.

초기 strict lint의 `many_single_char_names` 및 `derivable_impls` 오류(5e89be/eaed94)를 whole archives와 initial-failures receipt에 남겼다. 새 지역 변수명과 Default derive만 수정했다. 기존 P26/P62 실패나 native 원본·source locks를 바꾸지 않았다.

## 다음 정확한 작업

원래 actual table/field source에서 숫자·AST·owner·grid·dependency를 출처와 함께 읽어 evaluator에 연결한다. 모든 숫자 입력이 출처에 묶인 경우에만 계산하고, ambiguous/merged/blank/text/opaque/native coercion은 추정하지 않는다. 실제 corpus에서 independent consumer 및 fresh authenticated service 검증을 추가한 뒤 평가 결과와 원본 cache/문서 전체 보존을 분리해 기록한다. P79는 이 source/service 연결까지 미완료로 유지한다.

P78 source progress116142 bytes/SHA `bd39e62ae91eabe5f822b676e6bdc2b6ef18f8714580acc049f08d1e5b3dbf87`, final audit3906 bytes/SHA `cd68fa72a1b6598ee902499555dfd39d296fd09b95faf57c12da2db6294dbc33`는 그대로 보존한다. 현재 source epoch 변경을 이전 admission에 합격한 것으로 간주하지 않는다.

P26 failed_semantic_non_green/P62 16fde8 UNRESOLVED/current admission INPUT_CHANGED/full34 NOT_RUN·0green/P09 Gate OPEN/Goal ACTIVE/no P10를 유지한다. 한글·COM·UI·native dispatcher·접근허용·trust/config·stage/commit/push·원본 삭제/이동·dependency 설치는 하지 않았다.

- [정책](P09-79_FORMULA_EVALUATION_POLICY.md)
- [수학 경로 회귀](evidence/p09-79-formula-evaluation.math-regression.v1.json)
- [초기 실패](evidence/p09-79-formula-evaluation.initial-failures.v1.json)
