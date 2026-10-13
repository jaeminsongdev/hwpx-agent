# P09-97 기존 댓글·숨은 설명 본문 출력 정책

P09~P20 전체 제품 목표를 유지한다. P09 Gate 전에 P10 새 구현을 시작하지 않는다.
이번 단계는 실제 관측된 기존 MEMO/hiddenComment의 subList 안 문단 전체를 typed
paragraphs로 교체해 HWPX bytes를 생성하는 필수 출력 경로다. 새 댓글 삽입, 표시/해결/삭제,
작성자·시간·좌표 결속, 전체 rich Flow 출력 또는 full comment compiler 통합의 완료가 아니다.

## 원래 경로와 보존

- 원래 ImportedDocumentReviewBodies에서 얻은 실제 marker anchor와 fresh 원본만 받는다.
  LLM/public body API는 XML/action/byte offset/새 native metadata를 받지 않는다.
- 원래 TextFlowWriter로 모든 요청 문단을 생성·재검증한다. 각 문단의 자체 namespace가
  완전하므로 기존 wrapper에 namespace 선언을 덧붙일 필요가 없다. opaque/nested field,
  비정상 문자, dangling style, 문단 ID 충돌을 우회하거나 기본값으로 메우지 않는다.
- 원래 PreservingPatchEngine에 ReplaceElementContent를 추가한다. 기존 namespace-bound
  selector 검증을 사용하며 source start/end tag·unknown 속성·바깥 문맥을 바꾸지 않는다.
  자식 수와 전체 fragment byte 합을 확인한 뒤 allocation한다. 기존 overlap/ID/preservation
  검사는 그대로 적용한다. 범위 밖 엔진·기존 테스트/fixture를 재작성하지 않는다.
- 원래 FormulaV3 ID + Hangul2020PreviewTextV2 profile의 완전한 patch/writer 검사를 사용한다.
  원래 source/forms/paired fields/review importer로 전체 출력을 다시 읽고 요청 문단의 typed
  결과를 전부 비교한다. 선택된 내부 범위 앞뒤의 section bytes 및 다른 모든 expanded parts는
  exact다. field markers/parameters/metaTag/main body/다른 review를 보존한다.
- 기존 body가 없는 marker, 외부 source selector, 빈 문단 목록과 no-op은 거부한다.
  숨은 설명과 MEMO 모두 기존 body가 있을 때만 지원한다. caller가 지정한 교체 대상 내부의
  이전 문단·리소스 참조는 의도적으로 교체될 수 있으며 그 내부까지 byte 보존을 주장하지 않는다.
  원본 HWPX 자체는 그대로 두고 새 결과는 메모리에만 생성한다.

원래 TextFlowLimits(default: 문단 XML2 MiB/text1 MiB 등), PatchLimits와 source/graph/writer
제한을 그대로 적용한다. 문단 수는4096 이하, 생성 fragment 전체는8 MiB 이하이며 실제 출력
package와 원래 source mapper의 더 작은 제한이 있으면 원래 검사가 거부한다. target에는
typed 문단/run/text/tab/lineBreak를 받으며 새 table/drawing/opaque Flow 출력은 미지원이다.
문단 ID는 명시적으로 주고 기존 ID 검사로 충돌을 거부한다. allocator나 자동 ID default는 없다.

## 저장된 원본·권한

기존 StoredImportedReviewBodies에 prepare_body를 연결한다. 원래 scope/ACL/quarantine/
AEAD/head/whole-review 검증을 전후 적용한다. cached output callback은 fresh checks와
전체 lowering replay + artifact verify 뒤에만 실행된다. 반복 읽기는 atomic lease가 아니며
전체 보호 정책·신뢰된 issuer·revision commit·publication 권한으로 바꾸지 않는다.
require_current_product_route는 fresh 검증 후 항상 RouteUnqualified다.

## 검증과 원본 증거

신규 양성은 기존 원래 fixture/builder를 사용한 in-memory synthetic native-format package다.
실제 AES-GCM/ACL/head 코드와 in-memory repositories/actor/scanner/key를 구분한다.
기존 capture 및 historical actual36에 review body가 없다는 사실은 native 양성으로 승격하지 않는다.
원래 caller-owned full typed comment state/5 operations/partial/protection guard는 그대로다.

부모4개와 실패 당시 파일 전체를 별도 보관한다. patch.rs의4개 추가 블록과 나머지3개 module
declaration만 제거하면 원래 parent bytes 전체가 동일해야 한다. 이전 P96 whole checkpoint와
P95 raw records는 current bytes 또는 정확한 whole archives로 재검증한다. 과거 실행 파일은
새 target/p09-97-*에서 빌드해 보존한다. 기존 실패와 미검증/Gate 상태는 변경하지 않는다.

한글/COM/UI/접근허용, actual SQL, 운영·trust DB, 설치·설정, commit/push, 삭제·이동은 하지 않는다.
root PLANS.md는 삭제 상태를 유지한다. 전체 P09 검증과 native queue는 별도 남아 있다.
