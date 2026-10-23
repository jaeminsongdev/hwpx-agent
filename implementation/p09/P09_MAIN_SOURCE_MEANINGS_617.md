# P09 Source assessment와 CLI 필드 의미 통합

주 `assess_package_source`와 실제 `reference-source` CLI가 책갈피 CROSSREF를 포함한 필드 의미 정보를 반환한다. Source 출력 스키마는 v14이고, 추가한 `field_meanings`는 기존 공개 field-meaning API v2와 같은 receipt와 selector를 제공한다. **이 연결의 구현과 검증은 완료됐으며 P09 Gate와 목표 전체는 미완료다.** 목표는 ACTIVE, P10은 미시작 상태다.

## 제품 동작과 대상 인덱스 재사용

`ReferenceSourceAssessment::field_meanings()`와 JSON의 `field_meanings`에서 의미 종류, source field hash, meaning hash, 의미 inventory receipt를 확인할 수 있다. 같은 원본의 별도 `assess_package_field_semantics` 결과와 동일하며, command·대상 이름·캐시 원문을 출력하지 않는다. status Incomplete, validation_report null, 기존 미해결4개, CLI 종료 코드3을 유지한다. 잘못된 keyed 책갈피 명령은 API 오류와 CLI 종료 코드2로 거부하고 부분 JSON을 반환하지 않는다. 다른 종류와 Command key가 없는 CROSSREF는 Unsupported로 명시한다.

주 Source 경로는 원래 만든 package/forms/fields/target inventory를 재사용한다. `ImportedReferenceTargets`가 원래 structure 객체와 admission limits를 보관하고, `SourceFieldMeaningIndex::import_using_targets`는 두 조건이 정확히 일치할 때만 재사용한다. 별도로 import한 동일 바이트 원본이나 다른 한도의 inventory는 CROSSREF가 없는 문서에서도 거부한다. 동일 source·limits에서는 기존 standalone index와 의미·receipt가 같고, 원래 fresh reconstruction 검증도 유지한다. 이 연결을 위해 추가 ZIP/form/field/target import나 DocumentGraph clone을 만들지 않는다.

출력 버전 변경으로 기존 v13의 정확한 스키마 기대값은 v14로 이관했다. 기존 Source 시험 본문 전체는 새 module 선언과 버전 문자열 변경을 되돌리면 archive와 일치한다. 기존 field-meaning 시험에는 주 Source와 동일 결과라는 assertion을 추가했다. 다른 assertion이나 오류 조건을 제거해 통과시키지 않았다.

## 검증 결과

최종 [audit004](evidence/p09-361-main-source-meaning617-audit004.v1.json)은 **111조건, 938fresh/final938, compiled artifact13개 전후 일치, cleanup true**다. 통과한 Source79조건은 원래 기록과 현재 코드·입력·시험 본문·바이너리 동일성으로 유지하고 반복 실행하지 않았다. 영향받는 기존 field-meaning6·616통합9·엄격한 책갈피 API10·의미 인덱스7, 합계32조건을 현재 실행했으며 모든4step의 exit0·diagnostic0·cleanup true를 확인했다.

새9조건은 8표시/hyperlink 조합, 원본·한도에 결속된 inventory 재사용과 foreign 재사용 거부, Missing/Ambiguous 상태, 잘못된 Command의 API/실제 CLI 거부, 혼합 Unsupported 보존, package/document/target 변경 결속, 출력·입력 한도, 실제010 산출물24개의 주 Source 연결, 실제 CLI의 opened/saved/reopened 출력 비교를 포함한다. 새 CLI 검증은 실제 자식 프로세스4개를 사용했다. 과거 Source70조건도 같은 제품 코드에서 실행돼 유지됐다. 실제 수식16개와 원래 HTTPS·필드/graph 회귀 검증도 범위에 포함된다.

정상 CLI `target/debug/hwpx-agent-cli.exe`는8676352B/SHA4c2f96abc3c62bd69c1ac5fb8f574e499729aa329d05ef940d8309c7f4357add다. Cargo test가 생성한 `target/debug/deps/hwpx_agent_cli.exe`와 동일한 bytes/SHA이며, 실제 dep-info의 main.rs 및 모든 선언 입력이 사전 pin에 포함돼 있다. 원래 소비된010 probe는 byte-exact 유지했다.

최종 검증은321.5초, 시스템 CPU 관측최고29.3%, 가용RAM 최저34.234%였다. CPU/RAM/commit/Job 보호·단일 작업·낮은 우선순위·debug assertions/overflow checks를 유지했고, 이전에 검증한 CLI package의 codegen-units2를 재사용했다. 보호 중단, 새 한글/COM/Native 실행, 공식249 전체 재검증, Windows/Defender 설정 변경은 없다.

## 실패 기록과 후속 수정

| 기록 | 실패 단계와 처리 |
| --- | --- |
| [audit001](evidence/p09-361-main-source-meaning617-audit001.v1.json) | Source79개 이름을 전부 전달해 원래64개 인자 제한에서 자식 생성 전 거부됐다. 원래 cleanup false 기록은 보존한다. 제한을 바꾸지 않고 전체 Source target 실행과 정확한79개 결과 대조로 수정했다 |
| [audit002](evidence/p09-361-main-source-meaning617-audit002.v1.json) | Source79개 중74개와 새9개는 통과했다. 기존 시험5곳에 남은 v13 기대값 때문에 전체 FAILED였다. 제품 코드를 바꾸지 않고 남은 스키마 기대값만 수정했다 |
| [audit003](evidence/p09-361-main-source-meaning617-audit003.v1.json) | 실패5개 재실행은 모두 통과했다. 그 뒤 검증기가 cargo build의 top-level dep-info를 가정해 FileNotFoundError로 마감됐다. Cargo test의 실제 deps 하위 dep-info/image 위치를 확인해 검증기를 고쳤다 |
| [audit004](evidence/p09-361-main-source-meaning617-audit004.v1.json) | 위79개는 각 원래 기록과 코드·입력 동일성으로 유지했다. 추가32조건과 전체 전후 입력·산출물 경계를 닫았다. 앞의 FAILED 영수증은 수정하거나 PASS로 바꾸지 않았다 |

코드 원본과 실패한 검증기·시험은 `source-archive/p361-source-meaning617/`에 보존했다. 최종 결과 원문381658B/SHAba92375ca064cecc85de9020435a77193b9356db398ae40754e80fbe06249232는 immutable private forensic spool에 먼저 저장했다. 무손실 파생 packet118727B/SHA26e0fd6e9dc98b7cb039830038b800c8396447337ea47323fe592bc70b7b73e3이며, 원래256KiB publisher와4MiB 복원 한도를 유지했다.

## 남은 P09 범위

Source 미해결4개는 OtherTargetFamilies, ReferenceEdgeSemantics, CompleteAuxiliaryState, DocumentFlow다. 이번 결과는 source-local 필드 의미와 주 Source/CLI 연결의 근거이지, 모든 reference edge나 Native 대상 해석·페이지/상대위치·캐시/표시·재평가·실행 승인 근거는 아니다. 객체·각주/미주 CROSSREF의 typed 의미와 나머지 경로도 남는다.

다음에는 보존한010 실물 증거에서 이미 확인 가능한 대상·표시 정보와 추가 실행이 필요한 의미 검증을 구분해 이어간다. 공식249 큐는158수용/잔여91/next165이고 이번 수용 증가0이다. P09/A12/A13 Gate가 닫히기 전 P10을 시작하지 않는다.
