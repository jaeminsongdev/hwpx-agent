# P09 624 — 기존 책갈피 상호참조 명령의 owned/strict 공통 요청

## 결과와 범위

2026-10-23의 [audit002](evidence/p09-361-bookmark-request624-audit002.v1.json)는 요청10조건과 직접 영향20조건(저장12/공통 compiler8), 일반 실행 빌드 및 실제 캡처 원본1개 경로를 통과했다. 현재 원본을 소유하는 후보가 공통 요청 분기에서 기존 compiler/검증된 바이트 전달로 연결된다. **새 상호참조 삽입 REF-035, 등록된 실행 route, SQL/CAS, 실제 한글 효과, C05 전체 또는 P09 Gate의 완료가 아니다.**

## 구현

- `form_stored_provider/actual_import/bookmark_command_output/owned.rs`: 검증된 원본·후보·앵커와 sticky 거부 상태를 함께 이동한다. 전체 graph/output 재복사, 추가 의미 import/lowering, 거부 상태 초기화는 하지 않는다.
- `form_product_request/stored_operations/bookmark_commands.rs`: 엄격한 schema와 typed 표시/이동 값을 사용한다. 알 수 없는/중복 필드, null, 중복 선택, 잘못된 SHA/상한을 원본 접근 전에 거부한다. 호출자가 raw Command·이름·graph·출력 경로·실행 승인을 주입하지 못한다.
- 공통 dispatch가 이미 파싱한 요청을 전달하며 source를 한 번 import한다. 기존 권한/head/source/field/meaning/target 결속과 compiler 전후 검사·전달 시 최종 head 검사를 유지한다.
- scoped lookup의 기존/오류 결과는 준비 경로로 떨어지지 않는다. `NotObserved`만 준비할 수 있으며 claim/실행 권한이 생기지 않는다. 이번 lookup 증거는 격리된 repository 관찰 모델이며 운영 SQL 수용 결과가 아니다.

## 검증과 자원

요청10+직접 영향20=30조건을 한 번씩 실행했다. 실제 캡처 원본을 공통 owned 요청으로 전달하는 일반 빌드 경로도 확인했다. 926개 입력의 시작/종료 hash와 최종 artifact4개를 확인했고 cleanup은 true다.

총 292.328초, 관측된 시스템 CPU 최고62.5%, 가용 RAM 최저38.4021%, 보호 중단0회였다. 1코어·낮은 우선순위·machine CPU hard cap6.25%·RAM/commit95%·breakaway 금지를 유지했다. test job private 최고1342.34MiB, 일반 빌드767.86MiB, 실제 원본 경로55.38MiB였으며 종료 후 active process0을 확인했다. 이 관측은 PC 프리즈의 원인 규명이나 해결 보장이 아니다.

최종 영수증145512bytes / SHA256 `369bfe6beaa25fff01bc0826796717c7ed8d08432a81a1922cdf4aa6679a6705`. private 원문은 별도 보존했고 Command/이름/캐시·전체 로그는 이 보고서에 싣지 않는다.

## 최초 실패 보존

[audit001](evidence/p09-361-bookmark-request624-audit001.v1.json)은 기대 SHA 복사 오류로 preflight에서 FAILED했고 Cargo/제품 시험은 실행하지 않았다. 소비된010 실행 파일의 실제 hash가 변한 사건이 아니다. 원 실패와 원 verifier는 보존했으며 audit002는 기존623 원본 pin을 그대로 사용했다. 기존 실패를 PASS로 바꾸거나 소비010을 재빌드/실행하지 않았다.

## 다음 작업

기존 명령 편집의 보조 API를 계속 늘리지 않고 [P09 실행 원장](P09_SCOPE_AND_REMAINING.md#실행-순서와-완료-판정)에 따라 F11의 **실제 새 삽입**으로 진행한다. 31마감묶음과 P09/A12/A13은 여전히 미마감이다. Native/공식249 큐를 실행하거나 후속 P10 구현을 시작하지 않았다.
