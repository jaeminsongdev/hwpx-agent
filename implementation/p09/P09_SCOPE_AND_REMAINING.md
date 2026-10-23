# P09 경계와 잔여 작업 — 2026-10-23

> 현재 기준: [640~643 블록 책갈피 원본 준비](P09_BLOCK_BOOKMARK_SOURCE_PREPARATION_640_643.md). 기존 추적 후보142/메타데이터2752개에서 선택 범위의 블록 후보0개를 확인했고2610개는 미파싱이다. SDK 원문/설치 선언을 확인해1문서8범위·생성/재열기2세션 고정 계획을 검증했다. 계획 제어10개는 재실행 없이 보존하고 게시 round-trip16/16·cleanup=true다. 실제 제품 기준은639이며 Native entry/블록 HWPX/Content 양성은 아직 없다. 다음은 고정 P09 source worker/adapter의 구현·offline 실패 검증이다. P09/A12/A13 OPEN·31묶음/65기능·목표 ACTIVE·현재 사용자 명령 불필요·새 Native0·새 P10 미시작.

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
- [624 audit002](evidence/p09-361-bookmark-request624-audit002.v1.json)는 strict/owned/common 요청10+직접 영향20조건, 일반 실행 빌드의 실제 캡처 원본1개,926fresh/final926·artifact4final·cleanup true를 확인했다. 현재 원본·변경 후보를 소유해 공통 compiler/전달로 이어지지만 F11 새 삽입·등록된 실행 route·C05 전체 완료는 아니다. [원 audit001](evidence/p09-361-bookmark-request624-audit001.v1.json)의 기대 SHA 복사 오류/제품시험0/FAILED는 보존했다. 새 verifier는 고정623 영수증의 원본 pin을 그대로 비교하며 소비010을 변경/실행하지 않았다. [제품 범위 보고서](P09_BOOKMARK_OWNED_REQUEST_624.md)를 따른다.
- 과거 conformance v2는 당시 component/unit/integration inventory이며 최신 source/editor 전체를 자동 재판정한 현행65기능 PASS가 아니다. 621~623의 부분 수용도 해당 범위로만 사용한다.
- [626 새 필드 삽입](P09_SOURCE_BOOKMARK_INSERTION_626.md)은 같은 원본의 일치하는 Command 형식을 사용해 실제 새 CROSSREF 범위를 추가했다. 고유8조건(기존 통과6 보존+수정/신규2 실행), 실제 저장본8종·935fresh/final935·artifact2final·cleanup true다. 최초 생성/다른 대상·공통 제품 실행·Native 표시/재열기는 남고 F11 전체는 UNCLOSED다. 001 준비 CPU 중단/002 fixture 실패는 원본대로 보존했다.
- [627 최초 삽입·로컬 제품](P09_BOOKMARK_FIRST_INSERTION_627.md)은 기존 CROSSREF가0개인 실제 원본에 표시4종/hyperlink2종의 새8필드를 각 후보로 생성했다. 신규7+보존한 영향8의15조건, 일반 제품 빌드/원본8조합·실제 saved/reopened16과 전체 매개변수 일치·948fresh/final948·artifact6final·cleanup true다. 626의 기존 형식 재사용 API는 그대로이며 새 경로는 template을 요구하지 않는다. 실제 Native 효과·다른 대상·허용 실행/저장 경계는 남는다. 원 컴파일 실패2건을 보존했다.
- [628 저장 원본 결속](P09_STORED_BOOKMARK_INSERTION_628.md)은 현재 원본/ACL/head/AEAD를 최초 삽입 후보와 전달 callback에 연결했다. 고유8조건(보존7+강화한 양성1 실행)·실제 비공개8후보·930fresh/final930·artifact/출력12final·cleanup true다. 격리된 repository/scanner/키를 운영 route/CAS 자격으로 확대하지 않았다.
- [629 실물 준비 검사](P09_BOOKMARK_NATIVE_PREPARATION_629.md)는 읽기 전용18조건·실제 Codex 상위 Job 거부와8후보·210fresh/final210·cleanup true다. 외부 현재 관찰은 NOT_RUN이며 실제8종 실행기는 미완이다. 사용자의 명령 인계 후 정지 요청에 따라 목표를 PAUSED로 둔다. 원628 경고 실패/629 실행 전 allowlist 실패를 보존했다. 한글·접근 허용·소비된 실행을 시작하지 않았다.
- 이후 사용자가 실행한 외부629는 실제 파일8개·211fresh/final211·등록/현재 image/상위 Job 없는 조건/빈 제한 Job·cleanup true를 확인했다. 이것은 미래 Native 세션 자격이 아니다. [630 새 캡처 실행기](P09_PREPARED_BOOKMARK_NATIVE_CAPTURE_630.md)는 고유26코드/모델조건과 현재 worker 준비 거부를 결속했고 code006은267fresh/final267·cleanup true다. 고정8개 후보의 열기/새 저장·독립 재열기/PDF를 수집할 단발 명령을 인계한다. 실제 캡처·필드 의미·렌더는 아직 NOT_RUN이며 목표는 사용자 요청에 따라 외부 결과 대기 PAUSED다.

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
| P09-F11 | 상호참조 삽입·대상 결속 (REF-035) | 627/628 최초 삽입·저장 원본/후보에 이어 실제8종 캡처와632 게시 복구,635 책갈피4표시×hyperlink2종의 저장 후 필드 값/인수·독립 재열기 보존을 확인했다. 제품의 대상/Field/DocumentGraph 결속·렌더·대상 이동/이름 변경·다른 P09 대상과 계획/허용 backend/새 출력이 남는다. 제한된 field-readback을 전체 F11 PASS로 확대하지 않는다. |
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
| P09-C05 | 로컬 제품 요청·backend·출력 연결 | 624 strict/owned/common·627 최초 삽입 로컬 제품·628 현재 저장 원본/ACL/head/AEAD 재확인과8개 비공개 후보는 검증됐다. 격리된 repository/scanner/키를 운영 CAS/route로 승격하지 않는다. 새 삽입의 계획·허용 실행/지속 가능한 새 출력 및 다른 P09 필수 operation 연결이 남는다. SQL 서비스 전체·운영 key custody는 합치지 않는다. |
| P09-C06 | 필수 실물·직접 영향 회귀 | 65기능 계약상 필요한 현재 target의 효과/저장·독립 재열기/렌더·차분을 모아 실행한다. 공식249큐158수용/91대기/next165와 문자 스타일6종 등 현재 필수 사례를 대조하고 중복을 제거한다. 과거 통과분은 입력/변경 영향에 따라 재사용하며 기존 소비 Native를 재실행하지 않는다. 새 Native는 현재 자격·해당 실행 범위 허가가 필요하다. |
| P09-C07 | 최종 P09 증거·계약·Gate 마감 | 실제65기능의 required fixture/negative/readback 증거와 제한·지원 불가 근거를 대조한다. 436 등 P09 결과의 미마감 입력/자원/정리를 원본 보존 하에 마감하고 schema/migration/registry·ROADMAP_STATUS·CURRENT_STATE·handoff를 동기화한다. 전역/GA609감사는 P18이며 P09/A12/A13은 실제 근거 전까지 OPEN이다. |

## 접근 허용과 시험 대기열의 구분

F/S 및 C01~C05의 코드·원본 해석·단위/로컬 제품 검증, C07의 증거/문서 대조는 한글 접근 허용 없이 진행할 수 있다. 하지만 각 기능의 required Native 효과·저장/재열기·렌더 근거는 C06에서 실제로 확인해야 한다. 이 단계는 접근 허용이 필요할 수 있고 현재 자격과 실행 범위를 갖춰야 한다. 과거001~010·Native008~010 소비분을 다시 실행하거나 Native011을 임의 실행하지 않는다.

공식249큐의158수용/91대기/next165는 별도 사례 원장이다. **91을31에 더해122개라고 하지 않으며**,65기능 수나 전체 P09 남은 퍼센트로 환산하지 않는다. 사례와 F/S/C 요구사항을 대조해 중복/불필요 재실행을 줄이고 실제 필수 검증을 빠뜨리지 않는다.

## 실행 순서와 완료 판정

624의 preflight 수정/build/직접 영향 검증은 마감됐다. 다음 직접 구현은 **F11의 실제 상호참조 삽입**이다. 아래는 현재 코드·원본 재사용과 의존성을 기준으로 택한 실행 우선순위이며 소요 시간 보장이나 완료율이 아니다. 각 행의 공통 C 항목은 필요한 부분을 해당 기능과 함께 구현하고 마지막에 그 범위를 닫는다. C01~C05 전체 완성을 첫 기능의 선행 조건으로 두지 않는다.

| 순서 | 실제 처리 대상 | 이 순서의 이유와 종료 기준 |
| --- | --- | --- |
| 준비 | 실물 자료/자격 의존성 조기 확인 | 기존 corpus로 F11 다른 대상·F02 번호·F12 차례·F13 색인·F14 인용·F15 메일머지의 필수 원본이 있는지 먼저 대조한다. 부족한 근거/고정 기대 결과/필요 허가를 한 묶음으로 준비한다. 지금 Native를 자동 실행하거나 새 보조 서비스를 만들지는 않는다. 기다리는 동안 독립적인 로컬 구현을 계속한다. |
| 1 | F11 + 필요한 C01/C02/C05, 이어서 F09→F10 | 현재 실제 책갈피/CROSSREF corpus와 source/stored/공통 compiler를 즉시 재사용한다. 새 삽입→새 출력→필드/대상 readback부터 닫고 책갈피/링크를 연결한다. 기존 명령 편집을 삽입으로 세지 않고 F11 전체를 책갈피만으로 축소하지 않는다. |
| 2 | F02 + 필요한 C03/C04, 이어서 F03→F01 | 실제 번호/흐름/결과 상태의 불확실성을 먼저 줄인다. 기존 필드 core와 공유하는 source 추출·잠금·보존을 재사용한다. |
| 3 | F04→F05→F06→F07→F08 | 이미 있는 양식·각주/미주·숨은 설명·메모 adapter를 기능별로 닫는다. 범용 저장/운영 서비스를 다시 확장하지 않는다. |
| 4 | S01→S05→S06→S07→S03→S02→S08→S04 | 공통 검색/치환과 정규화·개인정보·정렬의 현재 경로부터 마감한 뒤 컨트롤/서식/폰트·스타일, 실제 흐름 이동을 연결한다. C04는 이동 작업 직전까지 미루지 않고 2단계의 실제 번호 근거와 함께 준비한다. |
| 5 | F16→F12→F13→F14→F15 | 앞서 준비한 보조 상태/다단계 원본을 사용한다. 차례·색인·인용·메일머지는 P09의 표시/초기 생성·삽입과 보존만 닫고 P11 관리/독립 refresh/생성 실행을 끌어오지 않는다. |
| 6 | C06 | 실행 가능한 준비분부터 필요한 실물 검증을 묶는다. 공식91사례·문자 스타일6종과 기능별 필수 근거를 매핑해 중복 실행을 줄인다. 모든 로컬 구현이 끝날 때까지 외부 자격 문제를 숨겨 두지 않는다. 현재 자격·해당 실행 범위 허가·CPU/RAM 보호를 유지한다. |
| 7 | C07 | 65기능별 required fixture/negative/readback·남은 실패·입력/정리 경계를 대조하고 계약/registry/상태를 동기화한다. 권위 있는 근거가 모두 닫힐 때만 P09/A12/A13을 판정한다. |

### 작업 속도를 위한 실행 규칙

- 매 기능에서 `현행 근거 대조 → 필요한 코드 변경 → 새 기능+직접 영향 시험 → 새 출력/의미 readback → 해당 원장 갱신`으로 끝낸다. 문서/압축/계측/요청 복구 모듈을 독립 제품 목표처럼 연쇄 확장하지 않는다.
- 과거 PASS는 입력 pin·코드 영향·필수 target 조건이 그대로일 때 재사용한다. 영향이 있거나 계약상 필수인 검증만 재실행한다. 검증 자체/보호 중단의 실패 원본은 남기며 미확인 단계를 PASS로 바꾸지 않는다.
- 한 작업 묶음 시작/종료의 전체 입력 감사와 각 실행의 현재 입력 확인을 구분한다. 매 작은 사례마다 과거 전체 이력을 누적 재검증하지 않는다. 신규 변경/직접 영향 시험은 한 번 빌드한 실행 파일과 직렬 실행을 재사용한다.
- 검증기의 입력 목록도 실제 build 대상을 따른다. 626은 전체165.219초/build-test2.562초였고 기존 CLI용935입력을 단독 package 시험에도 확인했다. 이후 단독 package에서는 manifest·전이 로컬 의존·build/include·runtime helper·실제 compiler dep-info를 대조해 자격을 얻은 범위만 검사한다. 단순히935를317로 바꾸거나 필수 입력을 빼지 않는다. CLI 변경에는 CLI 의존 범위를 유지한다.
- CPU/RAM 보호 중단이면 같은 명령을 즉시 반복하지 않는다. 해당 단계의 코드·파일 IO·프로세스 생성·잔류 실행을 확인하고 필요한 최적화/안전한 새 검증 세대를 준비한다. OS/다른 앱을 임의로 종료하거나 보호를 낮추지 않는다.
- 실물 접근 허용이 필요한 사례는 준비된 범위를 모아 실행한다. 과거001~010·Native008~010을 다시 사용하거나 Native011을 임의 실행하지 않는다. 외부 실행이 필요할 때만 정확한 명령과 기대 종료 상태를 안내한다.
- 후속 단계 소유 작업은 해당 phase의 미완료로 보존한다. P09가 실제로 쓰는 원본/권한/head/owner/허용 backend/보존/필수 readback 경계는 제외하지 않는다.

현재 진행은 **1단계 F11 새 삽입 경로**다. 627로 기존 CROSSREF가 없는 원본의 책갈피 최초 삽입과 일반 로컬 진입점을 검증했다. 다른 대상·현재 저장/허용 실행·실제 Native 근거는 남는다. 31묶음 중 하나를 닫으려면 그 행의 필수 조건과 현재 근거가 실제로 충족돼야 한다. 모든 P09 필수 조건이 닫히기 전 P10 새 구현은 하지 않는다. P14~P20의 별도 제품/운영 Gate는 해당 단계에서 검증한다.

## 근거

- [원 P09 phase 계약](../../docs/09_roadmap/P09_fields_forms_notes_references.md)
- [기능 소유권 목록](../../FEATURE_COVERAGE_MATRIX.csv), [검색 계약](../../docs/04_feature_catalog/contracts/03_search_contracts.md), [참조 계약](../../docs/04_feature_catalog/contracts/10_ref_contracts.md)
- [P09 검색 현황](P09_SEARCH_SOURCE_INDEX_PROGRESS.md), [책갈피621~623 범위](P09_BOOKMARK_COMMAND_COMPILER_623.md)
- [인용의 P11 경계](P09-08_CITATION_REPORT.md), [메일머지의 기존 경계 조정](P09-09_MAIL_MERGE_REPORT.md)
- [원 단계별 소유권](../../WORK_BREAKDOWN_STRUCTURE.csv), [마스터 roadmap](../../docs/09_roadmap/00_master_roadmap.md)

이 정리는 검증 기준을 낮추거나 완료를 선언한 것이 아니다. 전체 P09~P20 범위·기존 증거·보호를 보존하면서 phase별 책임과 지금 닫을 항목을 명시한 것이다.

