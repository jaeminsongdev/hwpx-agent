# P09 경계와 잔여 작업 — 2026-10-23

P09는 현재 선언된 개발 PC/한글 대상의 **검색·필드·양식·주석·참조 기능 구현과 필요한 실제 제품/한글 검증**을 닫는다. 전체 운영 서비스·GA까지 P09 하나의 선행 조건으로 묶지 않는다. 전체 목표 P09~P20은 유지하며 이 문서에서 후속 단계로 분류한 작업은 삭제하거나 완료 처리한 것이 아니다.

## 현재 적용 기준

이 문서와 [기계 판독 원장](P09_SCOPE_AND_REMAINING.v1.json)이 현재 P09 실행 범위를 정리한다. 이전 `P09_COMPLETION_EXECUTION.md` 등에 누적된 전역 SQL/worker/custody/운영 게시 작업은 아래 소유권 표에 따라 읽는다. 과거 완료/실패 원본과 당시의 실행 지시는 역사 기록으로 보존하며 새 실행 허가로 사용하지 않는다.

기능 소유권은 `FEATURE_COVERAGE_MATRIX.csv`와 개별 feature contract의 phase를 따른다. P09 WBS의9개 큰 제목만으로 범위를 축소하지 않는다. 기능 목록이 P09로 지정한 검색19+참조46=65개를 모두 유지한다. 기존 WBS의 인용/참고문헌·메일머지/labels 표현은 이미 P09-08/09 보고서에서 수행 범위를 구분한 방식대로 REF-044/046의 삽입을 P09에, REF-043/045/047의 관리/생성 실행을 P11에 결속한다.

P09 기능의 초기 결과 생성/보존·필수 평가를 확인하는 일은 P09에 남는다. 독립 기능 REF-036 상호참조 새로고침, REF-040 차례 새로고침은 P11이며 이를 혼동하지 않는다. 새 삽입 REF-035와 기존 명령 편집 API를 같다고 취급하지 않는다.

## 후속 단계 소유 — P09 전체 차단 조건으로 확대하지 않음

| 소유 단계 | 그 단계에 남기는 작업 | P09에서 여전히 필요한 경계 |
| --- | --- | --- |
| P10 | 범용 Windows Agent/STA/worker image·전체 supervisor·격리/재활용 제품 | P09 실물 검증에 사용하는 현재 세션·owner·CPU/RAM·승인 경계는 계속 필요하다. |
| P11 | REF-016/020/036/040/043/045/047 및 SEARCH-011/012/015/016/017/018 | P09 초기 생성/결과 보존/필수 평가 검증은 남긴다. 독립적인 상호참조·차례 refresh/참고문헌 관리·생성/메일머지 생성 기능은 이관한다. |
| P13 | 범용 oracle/render/evidence 서비스 전체 구축 | P09의 필수 한글 open/save/reopen·필요 render와 의미 검증은 기존 도구로라도 실제 수행해야 한다. |
| P14 | 일반 SQL/DB·artifact/revision/job/lease/fencing/idempotency/cleanup/retention 서비스 전체 구현·운영 승격 | P09가 실제 소비하는 현재 원본/권한/일관된 출력 경계는 검증한다. 격리 모델/SQL 기록은 그 범위를 넘어 운영 PASS로 승격하지 않는다. |
| P15 | OAuth/OIDC·공개 MCP transport/handlers·async UX·원격 artifact delivery·quota/telemetry/staging 전체 | P09 로컬 제품 요청/schema/오류 비노출·안전한 backend 연결은 남는다. 원격 서비스 전체 구현은 P09 선행 조건이 아니다. |
| P18 | 전609기능 RC/보안/fuzz/용량/SLO/전체 chaos·DR·backup restore·release supply-chain 감사 | P09 코드의 bounded 처리·CPU/RAM 보호·필수 부정/복구/보존 시험은 남긴다. |
| P19 | production infra/배포·운영 secrets/TLS/회전·정식 라이선스 범위·canary/rollback/submission/GA | 현재 개발 PC의 정품 seat·실물 실행 허가·외부 자료 권한은 계속 필요하다. 운영 배포 자격은 별도 단계에서 마감한다. |

후속 소유 모듈을 재사용하거나 실제 결함을 고칠 필요가 생길 수는 있다. 그렇다고 그 모듈의 범용/운영 완성 전체를 새 P09 선행 조건으로 추가하지 않는다. 반대로 현재 원본 보호·정확한 owner/권한/head·허용된 backend·자원 보호·필수 readback은 제거하지 않는다. 부분 source를 full-context로 승격시키거나 signed route 거부를 문서만으로 해제하지 않는다. 더 좁은 qualified profile이 필요하면 기존 schema/guard를 속이지 않고 별도 계약·negative·실제 근거를 설계한다.

## 최신 결과와 현재 변경

- [623 검증 결과](evidence/p09-361-compiled-bookmark623-audit004.v1.json)는 그 입력 세대에서 compiler8+저장12의 고유20조건, 일반 빌드/실물 원본1개,928fresh/final928·cleanup true를 뒷받침한다. 이것은 P09 전체 완료가 아니다.
- 624 owned/strict/common 요청 연결 코드는 추가됐지만 **현재 build/시험 본문은 NOT_RUN**이다. [624 audit001](evidence/p09-361-bookmark-request624-audit001.v1.json)은 새 verifier의 기대 SHA 한 자리 복사 오류로 preflight에서 멈췄다. 실제 소비010 EXE SHA는 원래 값이고 새 제품/Native/SQL 실행0·cleanup true다. 오류 수정과 현재 build/영향 시험은 C05/C07에 남긴다. 현재 tree의624를623의 PASS로 표현하지 않는다.
- 과거 conformance v2는 당시 component/unit/integration inventory이며 최신 source/editor 전체를 자동 재판정한 현행65기능 PASS가 아니다. 621~623의 부분 수용도 해당 범위로만 사용한다.

## 잔여 작업 목록

**31개는 완료 근거를 닫기 위한 작업 묶음 수다.** 새로 미구현인 기능31개, 원자적 세부작업 수, 검증 사례 수 또는 완료율이 아니다. F/S는65개 기능을 중복 없이 분류하고 C는 여러 기능에 필요한 공통 마감이다. 이미 통과한 core·source/stored adapter·시험을 전부 다시 만드는 목록이 아니다. 모든 묶음은 아직 UNCLOSED이며 기존 수용분을 보존한 채 아래 남은 경계를 마감한다.

### 참조·필드·양식16묶음

| ID | 기능 범위 | 남은 완료 조건 |
| --- | --- | --- |
| P09-F01 | 필드 입력·사용자 정의·누름틀·날짜/시간·파일 이름 (REF-001, REF-002, REF-003, REF-004, REF-005) | 기존 typed core를 재개발하지 않고 실제 source의 정의·값·인수 결속, 생성/변경의 제품 경로와 field readback을 마감한다. |
| P09-F02 | 쪽·구역·개체·캡션 번호 (REF-006, REF-007, REF-008, REF-048) | 실제 쪽/구역/개체·캡션과 번호를 결속한다. 과거 개체 번호가 저장 후0으로 된 실패를 보존하고 실제 개체가 있는 저장·재열기 결과로 마감한다. |
| P09-F03 | 필드 결과 갱신·잠금 (REF-009, REF-010) | P09 필드 결과의 계산/보존 정책과 잠금 효과를 실제 제품 경로에서 확인한다. P11 REF-036 전용 상호참조 새로고침 기능을 합치지 않는다. |
| P09-F04 | 양식 컨트롤6종 (REF-011, REF-012, REF-013, REF-014, REF-015, REF-017) | 텍스트/check/radio/combo/list/date의 실제 source 상태·값 변경·보호와 저장 후 readback을 기능별 required fixture에 대조한다. |
| P09-F05 | 양식 속성·탭 순서 (REF-018, REF-019) | 기존 static-section 모델/수입의 적용 범위를 확인하고 실제 속성·탭 순서 변경과 보호/보존·저장 결과를 마감한다. |
| P09-F06 | 각주·미주 입력/모양/변환/저장 (REF-021, REF-022, REF-023, REF-024, REF-025) | 기존 source/stored adapter를 재사용해 본문 연결·구역별 모양·변환/추출의 의미와 제품 결과를 required fixture로 마감한다. |
| P09-F07 | 숨은 설명 (REF-026) | 숨은 설명의 실제 내용·포함/제외·보존과 변경 결과를 계약/재열기에 대조한다. |
| P09-F08 | 메모 입력·모양·표시·해결 (REF-027, REF-028, REF-029, REF-030) | 기존 rich-comment/flow/stored 구현에 author/time·section/protection·해결/표시 상태의 실제 readback 증거를 결속한다. |
| P09-F09 | 책갈피 입력·삭제 (REF-031, REF-032) | 실제 원본의 책갈피 생성/삭제·이름 충돌/보호·참조 보존과 저장/재열기 경계를 마감한다. |
| P09-F10 | 하이퍼링크 입력·편집 (REF-033, REF-034) | 기존 HTTPS 정책·source/stored 변경을 P09 로컬 제품 실행/출력 의미에 결속한다. 대상/권한·외부 링크 안전 검사는 유지하되 운영 서비스 전체 구축은 별도로 둔다. |
| P09-F11 | 상호참조 삽입·대상 결속 (REF-035) | 책갈피 command 해석/변경/compiler는 부분 수용으로 유지하고 새 상호참조 삽입과 P09 대상 종류·표시/이동·이름 변경 시 결속 보존·저장/재열기를 마감한다. 명령 편집을 삽입 PASS로 쓰지 않는다. |
| P09-F12 | 차례 표시·숨김·생성 (REF-037, REF-038, REF-039) | mark/hide/create의 다단계 원본·번호 연결·생성 결과를 readback한다. 독립적인 차례 새로고침 REF-040은 P11 소유다. |
| P09-F13 | 색인 표시·생성 (REF-041, REF-042) | 표시와 생성 결과·항목/본문 위치 연결·다단계 corpus·저장 결과를 마감한다. |
| P09-F14 | 인용 삽입 (REF-044) | 기존 citation component를 실제 citation field 매개변수·자료/표시·저장/readback에 결속한다. 자료의 provider/format 근거는 필요하지만 참고문헌 관리/목록 생성은 P11이다. |
| P09-F15 | 메일머지 필드 삽입 (REF-046) | 실제 필드의 자료/열 선택·매개변수·placeholder/readback과 개인정보/권한 거부를 마감한다. preview/batch/label 생성 실행은 REF-047/P11이다. |
| P09-F16 | 보조 형식·문자열·교정·자료 연결·깨진 참조 (REF-049, REF-050, REF-051, REF-052, REF-053) | 날짜/시간 형식·파일 이름 문자열·교정부호·자료 연결의 실제 의미/변경을 마감하고 깨진 참조 검사는 source-derived 대상/edge/보조 상태/흐름을 사용해 불완전 상태를 정직하게 반환한다. |

### 검색·변환8묶음

| ID | 기능 범위 | 남은 완료 조건 |
| --- | --- | --- |
| P09-S01 | 문자열·정규식·다시 찾기·치환 (SEARCH-001, SEARCH-002, SEARCH-005, SEARCH-006, SEARCH-007) | 기존 matcher/cursor/strict 요청/치환을 재사용하고 전체 요구 범위·보호·match_set/semantic_diff/reopen의 현재 제품 근거를 마감한다. |
| P09-S02 | 서식 찾기·치환 (SEARCH-003, SEARCH-008) | 직접 서식/참조 정의 지원 위에 남은 유효 cascade·visibility·서식 축/보호 조합과 실제 일치·치환 결과를 마감한다. |
| P09-S03 | 컨트롤 찾기·치환 (SEARCH-004, SEARCH-009) | 탭/줄바꿈 등 수용된 종류는 유지하고 남은 계약상 개체/필드/조판 부호와 query/replacement·보존/실행 경계를 닫는다. |
| P09-S04 | 쪽·구역·문단·개체 찾아가기 (SEARCH-010) | 실제 document-flow/쪽·선택 위치에 결속한 이동과 범위/경계 결과를 마감한다. |
| P09-S05 | 대소문자·폭·Unicode·공백 정규화 (SEARCH-013, SEARCH-014, SEARCH-022, SEARCH-023) | 통과한 변환 core/strict 제품은 재개발하지 않고 실제 실행/출력·보존·target 계약과 필수 reopen 근거를 마감한다. |
| P09-S06 | 개인정보 바로 바꾸기·찾아서 바꾸기 (SEARCH-019, SEARCH-020) | 기존 탐지/마스킹 후보와 현 source·범위·정책을 결속하고 실제 바뀐/보존된 값·개인정보 비노출/거부 및 결과 검증을 마감한다. |
| P09-S07 | 텍스트·문단 정렬 (SEARCH-021) | 남은 중첩 구조·선택 범위·안정 정렬·보호/보존 조합과 실제 제품 출력의 순서를 검증한다. |
| P09-S08 | 폰트·스타일 일괄 대체 (SEARCH-024, SEARCH-025) | 전체 계약 옵션·설치/대체 글꼴·유효 서식·보호 조합과 실제 실행 결과를 마감한다. 문자 스타일6종의 필요한 실물 근거는 C06에 모은다. |

### 공통 제품·검증·최종 마감7묶음

| ID | 항목 | 남은 완료 조건 |
| --- | --- | --- |
| P09-C01 | P09 대상 해석 | OtherTargetFamilies 중 P09 기능에 필요한 대상 종류를 actual source에 결속한다. P11 전용 대상/작업의 전체 구현을 선행 조건으로 추가하지 않는다. |
| P09-C02 | P09 참조 edge | ReferenceEdgeSemantics 중 P09 기능의 실제 target/이름 변경/대상 없음·중복·깨짐 관계를 마감한다. 전체 제품의 모든 edge 완성을 요구하지 않는다. |
| P09-C03 | P09 보조 상태 | CompleteAuxiliaryState 중 P09 계약에 필요한 필드/서식/번호/참조 보조 상태를 실제 source에서 얻는다. 불완전 import를 full-context로 승격하거나 모르는 값을 기본값으로 채우지 않는다. |
| P09-C04 | P09 문서 흐름 | DocumentFlow 중 쪽 번호·위치 참조·찾아가기 등 P09 기능이 소비하는 흐름을 qualified evidence에 결속한다. 임의 문서/모든 후속 기능 호환성으로 확대하지 않는다. |
| P09-C05 | 로컬 제품 요청·backend·출력 연결 | P09 operation을 실제 로컬 제품 입력에서 검증된 backend와 새 출력/readback으로 연결한다. 기존 source/ACL/head/보호·허용된 실행·원본 보존 경계는 유지한다. 624 strict/owned/common 변경은 현재 미검증이며 고정 해시 오타 수정 후 실제 build/시험 확인이 필요하다. SQL 서비스 전체·운영 key custody는 여기에 합치지 않는다. |
| P09-C06 | 필수 실물·직접 영향 회귀 | 65기능 계약상 필요한 현재 target의 효과/저장·독립 재열기/렌더·차분을 모아 실행한다. 공식249큐158수용/91대기/next165와 문자 스타일6종 등 현재 필수 사례를 대조하고 중복을 제거한다. 과거 통과분은 입력/변경 영향에 따라 재사용하며 기존 소비 Native를 재실행하지 않는다. 새 Native는 현재 자격·해당 실행 범위 허가가 필요하다. |
| P09-C07 | 최종 P09 증거·계약·Gate 마감 | 실제65기능의 required fixture/negative/readback 증거와 제한·지원 불가 근거를 대조한다. 436 등 P09 결과의 미마감 입력/자원/정리를 원본 보존 하에 마감하고 schema/migration/registry·ROADMAP_STATUS·CURRENT_STATE·handoff를 동기화한다. 전역/GA609감사는 P18이며 P09/A12/A13은 실제 근거 전까지 OPEN이다. |

## 접근 허용과 시험 대기열의 구분

F/S 및 C01~C05의 코드·원본 해석·단위/로컬 제품 검증, C07의 증거/문서 대조는 한글 접근 허용 없이 진행할 수 있다. 하지만 각 기능의 required Native 효과·저장/재열기·렌더 근거는 C06에서 실제로 확인해야 한다. 이 단계는 접근 허용이 필요할 수 있고 현재 자격과 실행 범위를 갖춰야 한다. 과거001~010·Native008~010 소비분을 다시 실행하거나 Native011을 임의 실행하지 않는다.

공식249큐의158수용/91대기/next165는 별도 사례 원장이다. **91을31에 더해122개라고 하지 않으며**,65기능 수나 전체 P09 남은 퍼센트로 환산하지 않는다. 사례와 F/S/C 요구사항을 대조해 중복/불필요 재실행을 줄이고 실제 필수 검증을 빠뜨리지 않는다.

## 실행 순서와 완료 판정

1. 현재624의 preflight 오류/미검증 tree를 먼저 정리해 build/직접 영향 검증을 닫되, 보조 API를 새 P09 필수 기능으로 추가하지 않는다.
2. C01~C05와 필요한 F/S 기능을 실제 입력→변경→새 출력→의미 readback의 수직 경로로 마감한다. 부수 계측/압축/문서 전용 검증 주기를 계속 늘리지 않는다.
3. 실제 target 근거가 필요한 고정 사례는 묶음으로 준비하고 현재 자격/허가에 따라 C06을 수행한다. 이미 통과한 본문은 입력·영향이 동일하면 재사용한다.
4. C07에서65기능별 계약·required fixture/negative·현재 target 제한과 실제 증거를 대조한다. 근거 없는 것은 NOT_RUN/unverified/unavailable로 유지하며 지원 불가도 실제 근거 없이 선언하지 않는다.
5. 모든 P09 필수 조건이 권위 있는 결과로 닫힐 때만 P09/A12/A13을 닫는다. 그 전까지 P10 새 구현은 하지 않는다. P14~P20의 별도 제품/운영 Gate는 그 단계에서 남은 요건을 그대로 검증한다.

## 근거

- [원 P09 phase 계약](../../docs/09_roadmap/P09_fields_forms_notes_references.md)
- [기능 소유권 목록](../../FEATURE_COVERAGE_MATRIX.csv), [검색 계약](../../docs/04_feature_catalog/contracts/03_search_contracts.md), [참조 계약](../../docs/04_feature_catalog/contracts/10_ref_contracts.md)
- [P09 검색 현황](P09_SEARCH_SOURCE_INDEX_PROGRESS.md), [책갈피621~623 범위](P09_BOOKMARK_COMMAND_COMPILER_623.md)
- [인용의 P11 경계](P09-08_CITATION_REPORT.md), [메일머지의 기존 경계 조정](P09-09_MAIL_MERGE_REPORT.md)
- [원 단계별 소유권](../../WORK_BREAKDOWN_STRUCTURE.csv), [마스터 roadmap](../../docs/09_roadmap/00_master_roadmap.md)

이 정리는 검증 기준을 낮추거나 완료를 선언한 것이 아니다. 전체 P09~P20 범위·기존 증거·보호를 보존하면서 phase별 책임과 지금 닫을 항목을 명시한 것이다.

