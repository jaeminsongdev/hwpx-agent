# P09-95 원본 MEMO 문자열 메타데이터 보존 결과

원래 MEMO 원본 읽기 경로에 metaTag 문자열 요소의 위치·전체 지문·byte 수 보존을 구현했다.
본문 및 기존 parameters를 같은 원래 reader/mapper/field stack으로 읽으며, 관측 전체는 기존
assembly와 인증된 stored-source reader에 전달된다. 별도 importer/provider를 만들지 않았다.
문자열이 JSON처럼 보여도 작성자·시간·해결·표시 상태로 해석하거나 값을 기본 생성하지 않는다.

## 검증 결과

- Rust 257 PASS, failed/ignored 0: package lib42, text_flow12, review15, assembly_review3,
  memo_catalog6, fields12, catalog7, 신규 review_metadata8, stored provider128,
  stored_comment_provider16, comment_operation8.
- 신규 원본 기능 검사는 13개다: public package8 + 기존 reader 내부 budget2 + 기존 stored provider3.
  원래 125개 stored provider 테스트 본문은 그대로이고 module 선언 2줄만 추가했다.
- 읽기 전용 보존 verifier의 Python 검사3 PASS. raw bytes/길이/누락, 이전 checkpoint 지문 변경,
  과거 실행 파일 지문 변경을 검사해 허위 성공을 거부한다.
- package lib/new public test, package 전체 tests, product lib/stored provider strict clippy PASS.
  신규·수정 Rust 개별 format 및 git diff --check PASS. 검사 완화나 warning allow는 없다.
- 원래 current-source 구성요소 검증15 PASS, green0/P09 OPEN.
  기본 conformance는 FAIL:matrix_drift를 다시 확인했고 실패를 유지했다.
  이 구성요소 결과는 신규 native metadata 의미 또는 전체 댓글 제품 acceptance가 아니다.

신규 positive는 기존 fixtures로 만든 synthetic native-format MEMO 문자열이다. 문자열/entity의
lexical-only 변화도 원본 전체/관측 지문을 무효화한다. assembly의 실제 스타일/본문과 원래 직접
import 결과를 전체 비교했다. 실제 captured fixture의 관측0 및 raw identity도 유지된다.
positive native author/time/state/style/좌표 캡처가 새로 생긴 것은 아니다.
실제 서비스의 AES-GCM/ACL/head 검사는 실행했지만 repository/scanner/actor/key는 in-memory/fixture다.
캐시 이후 AEAD 변조, 권한 철회·재부여, head 변경, malformed 메타데이터 및 full-document
projection 거부를 확인했고 새 artifact ingest/head commit/publication은 없다.

## 실패와 보존

첫 public 테스트는 없는 API 호출 때문에 compile 실패했다. 두 번째 실행은 CDATA를 positive로
기대한 새 테스트 1개가 원래 SafeXml 정책에 의해 거부됐다(6 PASS/1 FAIL). SafeXml을 약화하지
않고 CDATA를 명시적 negative로 고쳤다. 신규 private 테스트도 없는 TextFlowLowerer 이름으로
compile 실패했으며 원래 TextFlowWriter를 사용하도록 새 테스트만 수정했다. 세 실패 당시 전체
테스트 source를 보관했다. 중복 --lib lint 호출 실패는 실행 방식 오류로 기록했고 실제 strict
검사는 분리해 통과했다. 전체 원본 로그나 비밀정보를 보고서에 복사하지 않았다.

P94 checkpoint 252,320 bytes/417a464075f3206f65e39742e3bc0b3503a7a5f53544bac0229178230ddebb24
및 raw pin1,149개를 다시 확인했다. 기존 소스792개 중788개는 그대로이며 수정 부모4개의 전체
preimage는 source-archive/p09-95-pre-review-metatag에 보관돼 있다. 원래 MEMO body guard 전체와
기존 제품 테스트 module 선언 역변환이 byte 단위로 일치한다. P94까지의 과거 실행 파일51개를
덮어쓰지 않았다. 이번 P95 감사는 이전 raw pins 범위이며, 최초 baseline1,551개를 별도로 다시
전수 감사하거나 모든 과거 qualification을 재실행했다고 주장하지 않는다.

## 남은 실제 제품 경계

metaTag를 잃지 않고 읽는 지원 분기는 완료했지만 native author/time/state/style/좌표 결속,
HWPX header/body/MEMO 출력, durable SQL 제품 통합, 신뢰된 issuer/atomic execution/publication,
미지원 field/Date/external validation과 전체 문서 의미, P84 SQL 원인 및 실제 한글 검증은 남는다.
최소6 큰 잔여 묶음에서 하나가 통째로 완료됐다고 차감하지 않는다.

P09/A12/A13 OPEN; P26 failed_semantic_non_green; P62/P84_SQL UNRESOLVED;
native INPUT_CHANGED_RE_ADMISSION_REQUIRED; full native34 NOT_RUN; green0.
full_comment_product_acceptance=false, p09_complete=false, product_complete=false,
P10_new_implementation=false, goal_status=active. 한글/COM/UI/접근허용/실제 SQL/운영·trust DB/
설치·설정/commit/push 없음. root PLANS.md는 삭제 상태를 유지했다.

정책: P09-95_REVIEW_METADATA_POLICY.md. 증거: evidence/p09-95-review-metadata.*.v1.json.
읽기 전용 감사: tools/p09/verify_review_metadata_progress.py 및 --current 모드.
