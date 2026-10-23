# P09 627 — 기존 CROSSREF 없는 문서의 최초 삽입과 로컬 제품 경로

## 결과

[audit003](evidence/p09-361-bookmark-creation627-audit003.v1.json)은 다음을 확인했다.

- 실제 원본의 기존 필드는 HYPERLINK1개이며 CROSSREF는0개다. 같은 원본의 실제 책갈피와 원본 run을 선택해 **새 CROSSREF1개를 최초 생성**했다. 기존 CROSSREF template은 필요하지 않다.
- 표시4종 × hyperlink2종의 새8출력을 로컬 제품 진입점과 일반 실행 빌드에서 생성했다. 새 매개변수8개 전부를 기존 실제 saved8/reopened8의16개 표본과 독립 reader로 대조해 일치를 확인했다.
- Rust 고유15조건은 현재 실행한 최초 삽입7개와, 동일한 제품 코드·시험 본문·artifact로 보존한 공통 삽입 영향8개다. 이미 통과한 영향8/624의30조건을 재실행하지 않았다.
- 입력948개 시작/종료 hash 일치, compiled artifact6개 최종 확인, 전체 cleanup true다.

**이는 최초 삽입의 패키지 생성·보존·매개변수 호환성과 로컬 진입점 검증이다.** 실제 한글을 새로 실행하지 않았으므로 Native 계산/표시·이동·독립 재열기·렌더, 등록된 실행 route/저장 CAS, 책갈피 외 대상과 F11/P09 전체 완료는 아니다.

## 무엇이 바뀌었는가

626의 기존 `insert_bookmark_reference_from_source_envelope`는 원래 계약을 유지한다. 일치하는 원본 형식이 없으면 계속 거부하며, 새 생성으로 조용히 fallback하지 않는다.

새 `ImportedDocumentFields::create_bookmark_reference`는 실제 source의 책갈피와 typed 표시/hyperlink 값으로 SDK 후보를 만든 뒤, 관찰된 captured010 매개변수 profile을 생성한다. 외부 raw XML/Command/대상 이름/Native 매개변수 map은 받지 않는다.

| 표시 | 실제 표본과 대조한 `RefContentType` |
| --- | --- |
| Page | `OBJECT_TYPE_PAGE` |
| BookmarkName | `OBJECT_TYPE_NUMBER` |
| Content | `OBJECT_TYPE_CONTENTS` |
| RelativePosition | `OBJECT_TYPE_UPDOWNPOS` |

`RefPath`는 source-bound Command의 첫 payload와 세미콜론으로 생성한다. `RefType`은 `TARGET_BOOKMARK`, `RefOpenType`은 `HWPHYPERLINK_JUMP_CURRENTTAB`이며 `RefHyperLink`는 typed bool과 일치한다. `Fiexde`의 철자는 실제 표본 그대로 보존했다. 이 매핑은 선언된2020 대상의 캡처 표본 관계이지 모든 한글/대상 종류의 보편적 Native 자격이 아니다.

공통 core는 기존 whole-source/form proof, 문서 보호·변경 추적, 기존 필드 겹침, 전체 ID 충돌/소진, 한도, preserving patch/writer, 새 field/meaning 결속과 삽입 지점 밖/선택 run의 정확한 바이트 보존을 재사용한다. 기존 guard prefix와 envelope helper 본문은 원626과 동일함을 검증했다. 생성 모드는 Command뿐 아니라 매개변수8개 전체를 output에서 다시 확인한다. 새 삽입의 기존 표시 텍스트는 계산/갱신된 결과라고 주장하지 않으며 dirty를 설정한다.

## 로컬 제품 연결

`ReferenceValidationProductOperation::prepare_source_bookmark_reference_insertion`은 새로 import한 정확한 source, 전체 field coverage, fresh reconstruction을 통과한 후에만 후보를 만든다. 일반 실행 파일 `p09_bookmark_creation627`의 고정 관찰로 실제 원본8조합을 통과했다.

서비스 ACL/head/owner·승인·저장/CAS·실행 권한은 이 API가 대신하지 않는다. 후보는 inert이며 기존 full-context/signed-route 거부를 해제하지 않았다. 주 Source/field-meaning/의미 graph의 PARTIAL 및 미해결4조건도 그대로다. 일반 SQL/job/worker/운영 서비스 확장은 추가하지 않았다.

## 실패와 재사용

- [audit001](evidence/p09-361-bookmark-creation627-audit001.v1.json): 영향8조건은 PASS. 새7조건은 비교 reader가 crate-private 메서드에 접근한 E0624로 컴파일 단계에서 중단했고 본문은0개 실행했다. 원 reader를 공개된 원본 XML span 기반으로 수정했다.
- [audit002](evidence/p09-361-bookmark-creation627-audit002.v1.json): 새 시험의 Cow/String 소유 타입 E0308로 본문0개 실행. 값을 owned String으로 옮기도록 수정했다.
- audit003: 새7조건 실행·일반 빌드·로컬 제품8조합 통과. 원 영향8의 실제 PASS·시험/제품 소스 동일성·이전 executable/dep-info hash를 확인하고 최종 감사에 함께 결속했다. 실패 원본을 PASS로 바꾸지 않았다.
- normal example의 독립 reader에 필요한 `quick-xml`을 CLI **dev-dependency**로 명시했다. workspace/lock에 이미 있는 버전만 사용했고, 기존 lock 전체에서 해당 CLI dependency 선언 한 줄 외에는 변경이 없음을 검증했다. 새 다운로드/버전 변경/외부 설정 변경은 없었다.

## 자원과 근거

| 구간 | 시간 | job CPU | job private 최고 |
| --- | --- | --- | --- |
| 신규 Rust7조건 | 3.562초 | 3.469초 | 612.32MiB |
| 일반 제품 빌드 | 38.297초 | 37.234초 | 2046.61MiB |
| 일반 제품의 실제 원본8조합 | 1.968초 | 1.953초 | 54.93MiB |

전체224.797초, 시스템 CPU 최고15.43%, 가용 RAM 최저39.7693%, 해당 실행 보호 중단0회다. 모든 job은 종료 owned process0·cleanup true였다. 1코어·낮은 우선순위·machine CPU hard cap6.25%·RAM/commit95%·breakaway 금지 등 기존 보호를 유지했다. 관측 추가 비용은 합계 약0.095초였으며 WMI/새 sampler/thread를 만들지 않았다. PC 프리즈 원인 규명/해결은 여전히 미확정이다.

최종 영수증129097bytes / SHA256 `0b61edcc5b7ef4975b72ea20013863d1111d1da022ef263e893e5abd287e7a6f`.

일반 실행 파일6918144bytes / SHA256 `a9a63b847c088438281901dcc8c917ddfd51fc6cb7b4bc2f67b8590a016a443e`.

원 Command/이름/표시 원문·전체 로그는 출력하지 않았다. 원본 파일 덮어쓰기, 기존 소비010/Native/공식249큐 재실행, OS/Defender/다른 앱 변경은 없다.

## 다음 경계

F11의 ‘동일 원본에 기존 CROSSREF가 있어야만 새 삽입 가능’ 제한은 새 생성 경로에서 해소됐다. 남은 것은 책갈피 외 P09 대상의 실제 ID/순서/매개변수 결속, 현재 저장 원본·공통 계획·허용 backend/새 출력의 실행 경계, 실제 한글 효과/저장·독립 재열기/렌더와 이름 변경 보존이다. 준비된 실물 사례는 현재 자격·실행 범위 허가를 갖춘 묶음으로만 수행한다. 기다리는 동안 독립적인 로컬 구현은 계속한다.

목표 ACTIVE·31미마감묶음·P09/A12/A13 OPEN·공식158/249/91대기/next165·P10 새 구현 보류 유지. 이번 부분 수용을 F11/전체 P09 PASS 또는 작업 묶음 하나의 완료로 세지 않는다.
