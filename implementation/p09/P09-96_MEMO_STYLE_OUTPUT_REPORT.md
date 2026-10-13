# P09-96 실제 memoPr 스타일 출력 결과

기존 원본 catalog에서 선택한 memoPr의 스타일7개 속성을 실제 HWPX 패키지 bytes로 출력하고
원래 source/fields/catalog/ID/patch/writer 경로로 다시 검증한다. 저장된 원본 경로에도 연결했다.
전체 댓글 입력/metadata/보호 정책/컴파일러/native 실행 통합을 대체하지 않는 필수 출력 분기다.

## 구현과 검증

- 원래 ID index에 공식 hh:memoPr/id 선언을 추가했다. legacy memoShape는 유지하며 중복,
  foreign namespace, dangling 및 wrong-type 거부를 그대로 적용한다.
- 원래 ImportedDocumentCatalog에서 실제 memo definition anchor만 선택하고 원래 patch/writer를
  호출한다. ID/unknown 속성/namespace/다른 스타일/본문/리소스 등 나머지 expanded bytes는 보존한다.
  별도 importer, ZIP writer, raw XML/offset admission 또는 source overwrite를 만들지 않았다.
- PackageArtifact의 새 callback은 원래 verify 후에만 bytes를 제공한다. 저장소 callback은 원래
  scope/ACL/quarantine/AEAD/head/whole catalog 검증과 전체 lowering replay 후에만 실행된다.
  제품 execution/publication route는 계속 거부한다. ingest/revision commit/publication은 없다.
- Rust228 PASS, failed/ignored0: package lib42 + original ID8 + patch6 + memo catalog6 +
  P95 metadata8 + 신규 style output4 + stored provider130 + original stored comment16 + comment8.
- 새 기능 검사는 public package4 + original stored provider2다. width16/line18/type4를 각각
  원래 catalog로 재열어 검사했으며 Cartesian product 전체나 installed native acceptance가 아니다.
- Python 보존 verifier8 PASS: 기존 raw/preimage3 + inherited/delta manifest 범위·누락·변조·
  미검증 acceptance 승격 거부5. 모의 manifest 검사는 실제 byte 감사로 재집계하지 않는다.
  package/new test 및 product/lib/stored provider strict clippy PASS.
  신규 Rust4개 format 및 git diff --check PASS. 원래 current-source component15 PASS,
  green0/P09 OPEN; 기본 conformance FAIL:matrix_drift는 다시 확인해 유지했다.

신규 검사는 기존 원래 builder/memo fixture의 in-memory synthetic native-format package다.
선택된 스타일7개 값의 정확한 header byte 변환과 나머지 part bytes 전체를 비교했다. 의미가 같은
numeric/color casing은 바꾸지 않는다. 잘못된 selector/fresh source/values, no-op 및 작은 출력
한도는 거부한다. 저장소 결과는 실제 AES-GCM/ACL/head 코드를 실행하지만 repositories/actor/
scanner/keys는 fixture다. 권한 철회·재부여/AEAD 변조/head 변경 후 cached callback은 거부된다.
현재 actual capture36의 memo definition 부재는 계속 유지하며 새 positive native 증거로 세지 않는다.

## 실패·원본 보존

첫 출력은 CoreV1 profile에서 실제 preview/paired-field 문단의 ID-like attributes를 거부했다.
새 package test는 1 PASS/3 FAIL, 새 stored test는 0 PASS/2 FAIL이었다. 첫 새 source/test4개 전체를
보관했다. 원래 CoreV1을 약화하거나 unknown ID 오류를 무시하지 않았다. 원래 table/field 및
preview text를 지원하는 FormulaV3 profile을 명시적으로 사용해 같은 원래 trust chain을 통과했다.
Strict lint의 긴 함수, 읽기 어려운 숫자 literal, 불필요 import/name/update, 중복 fixture module
선언을 수정했고 allow를 추가하지 않았다. fixture는 기존 module을 parent-only visibility로 재사용했다.

이전 P95 checkpoint253,422 bytes/9f21a4848e38c89b6ef5858cb0fe668d7a67ca6bb0abdd765cb9fd46d2d65f99와
raw pin1,183개를 현재 bytes 또는 정확한 수정 전 전체 preimage에서 확인했다. 기존 source803개 중
797개가 같고 변경 부모6개는 보관됐다. 원래 ID/writer/catalog/test body는 허용된 추가만 역변환하면
전체 bytes가 일치한다. 과거 실행 파일62개는 덮어쓰지 않았다. 모든 과거 qualification/최초 baseline
전체를 재실행했다고 주장하지 않는다. P96 snapshot은 이전 whole checkpoint + 변경 delta의 결속이다.

## 남은 원래 제품 경계

기존 스타일 header 출력은 구현됐지만 전체 댓글 header/body/MEMO 출력은 아직 미완료다.
native author/time/visibility/resolution/좌표 및 full typed state/compiler 연결, 원본 보호 정책,
trusted issuer/atomic execution/publication/durable SQL 제품 통합, P84 SQL 원인, 나머지 P09
의미와 actual 한글 저장·재열기/render/differential 및 P09 Gate가 남는다. 최소6 큰 작업 묶음 중
하나 전체가 완료됐다고 차감하지 않는다. 기존 5개 typed comment 준비와 이 native style 출력이
완전한 하나의 제품 실행 경로가 됐다는 주장도 하지 않는다.

P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; full native34 NOT_RUN; green0.
full_comment_product_acceptance=false, product_complete=false, P10_new_implementation=false,
goal_status=active. 한글/COM/UI/접근허용/실제 SQL/운영·trust DB/설치·설정/commit/push 없음.
root PLANS.md는 삭제 상태를 유지했다.

정책: P09-96_MEMO_STYLE_OUTPUT_POLICY.md. 증거: evidence/p09-96-memo-style-output.*.v1.json.
읽기 전용 감사: tools/p09/verify_memo_style_output_progress.py 및 --current 모드.
