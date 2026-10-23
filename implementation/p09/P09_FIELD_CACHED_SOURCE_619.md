# P09 저장된 필드 캐시 관측과 Source API 연결

저장된 필드의 캐시를 의미 분석과 분리해 읽는 제품 코드를 구현하고, 주 Source/실제 CLI 출력 v15의 `field_cached_source`에 연결했다. 일반 텍스트·탭·줄바꿈은 디코딩된 데이터의 해시와 개수로 관측하며, 중첩 필드나 다른 제어는 StructuredUnqualified로 명시한다. **읽기 구현·Source 연결 검증은 완료됐지만 캐시 최신성·Native 표시/재평가와 P09 전체 Gate는 미완료다.** 목표는 ACTIVE이며 P10은 시작하지 않았다.

## 원본 구조를 보존하는 캐시 읽기

`SourceFieldCachedInlines::import`는 이미 검증한 `ImportedDocumentFields`를 빌려 원래 paragraph와 field range를 사용한다. fieldBegin/fieldEnd 바깥 텍스트는 제외하고, 공백·XML entity의 디코딩 값·한글·탭·줄바꿈을 정규화하거나 합성 기본값으로 바꾸지 않는다. 빈 캐시는 빈 데이터의 SHA를 가진 실제 관측으로 남기며 필드 부재와 구분한다. 값 원문·명령 원문을 결과나 Debug에 출력하지 않는다.

중첩 field marker, 책갈피 ControlRef/BookmarkAnchor, 다른 제어·수식·변경 span 등은 임의로 펼치지 않는다. 그 범위에는 텍스트 SHA를 부여하지 않고 미해석 구조와 inline 개수만 반환한다. 전체 원본과 범위는 field import receipt의 source/graph SHA에 결속된다. Native 평가와 currentness 및 complete-reference qualification은 항상 false다.

필드마다 문단을 다시 읽지 않도록 문단별 시작·끝 이벤트를 정렬하고 누적 개수를 한 번 계산한다. 구조가 없는 leaf cache의 데이터만 복사 없이 스트리밍 해시한다. 부모가 중첩 제어를 포함하면 재해시하지 않으므로 깊게 중첩한 캐시를 반복 스캔하지 않는다. 추가 DocumentGraph clone은0이며, node/inline 작업·필드 수·텍스트·전체 해시 데이터·출력 예산을 검사한다. 128개 field 시험에서 prefix event256·hashed text128B·inline scan384 이하를 확인했다.

기존 공개 field-meaning v2와 의미 graph partial-v3은 유지했다. Source v15는 `field_cached_source`를 별도로 제공하므로 캐시를 typed command 의미나 Native 계산 결과로 섞지 않는다. 주 Source의 미해결4개·Incomplete·validation_report null·CLI 종료3은 그대로다. 기존 Source 본문과 시험은 버전 문자열 및 새 cache 연결을 되돌리면 archive와 일치한다.

## 실제 저장본의 관측 결과

[최종 audit004](evidence/p09-361-field-cached-source619-audit004.v1.json)의 일반 실행 빌드로 고정010 산출물24개를 주 Source API에서 읽었다. opened8개에는 새 CROSSREF가 없고 saved/reopened16개에는 각각 디코딩된 텍스트 캐시가 있었다. 다른 원래 필드의 캐시도 누락하지 않았다.

- saved/reopened의 CROSSREF cache snapshot은8쌍 모두 일치했다.
- BookmarkName 표시의 saved/reopened4개 관측값은 같은 원본에서 해석한 명령 대상 이름의 SHA와 일치했다.
- 이 비교는 디코딩된 저장 데이터와 원래 명령 이름의 일치다. Native 이동 성공, 페이지/상대위치 계산, 캐시 최신성이나 실제 화면 표시 정답을 판정하지 않는다. 기존010의 effect_unknown·Native qualification 표시도 변경하지 않았다.

일반 관측 EXE는 `target/debug/examples/p09_field_cached_source619.exe`,7170048B/SHA0479b6998c01957341f20eb8cb84ef841eb6fb6faa32caea27eddb7815014397다. Source가 제공한 field range/meaning/cache reference를 같은 package 안에서 결속하고, package를 다시 읽어 같은 bytes/SHA임을 확인한다. 모든 결과는 원문 값 없이 해시·개수·비교 여부로 저장한다.

## 시험과 실패 기록

총104시험 조건은 새10·Source/실제 CLI79·기존 통합9·field-meaning6이다. 새 시험은 텍스트/탭/줄바꿈/공백, 빈 캐시, 중첩 부모와 자식, 책갈피 구조, cross-run·note/table 소유 관계, 명령과 cache 변경의 분리, 입력·텍스트·필드·출력 예산, 선형 작업량, Source v15 결속과 원문 비노출, 실제24개 산출물을 확인한다.

| 근거 | 결과와 수정 범위 |
| --- | --- |
| [audit001](evidence/p09-361-field-cached-source619-audit001.v1.json) | 새10개 중9통과·1실패. 책갈피가 원래 모델에서 ControlRef와 BookmarkAnchor 두 inline으로 표현되는데 시험이1개로 기대했다. 실제 구조2개와 전체inline4개를 요구하도록 수정했고 원래 실패는 보존했다 |
| [audit002](evidence/p09-361-field-cached-source619-audit002.v1.json) | 위9개는 동일 코드·입력으로 유지하고 수정1+영향94개를 실행해95개 통과. 일반 빌드도 exit0였지만 시험 전용 타입의 unused import 경고 때문에 전체 FAILED로 마감했다 |
| [audit003](evidence/p09-361-field-cached-source619-audit003.v1.json) | 시험 전용 타입을 cfg(test)로 한정한 뒤 rustfmt의 import 줄 배치를 원문 대조식이 예상하지 못해 사전검사 실패. Rust/Native 미실행이며 대조식만 수정했다 |
| [audit004](evidence/p09-361-field-cached-source619-audit004.v1.json) | 모든104개의 기존 통과 근거를 product source·시험/관측 본문·compiler input·시험 바이너리 동일성으로 유지하고 반복하지 않았다. 새 일반 빌드와 실제24개 관측을 실행해 경고0·exit0,934fresh/final934·artifact10개 전후 일치·cleanup true를 확인했다 |

import의 시험 전용 조건 외에는 시험/관측 함수 본문이 동일하다. 최종 일반 실행은 캐시 관측을 수행한 것이며104개 시험을 새로 재실행한 것으로 보고하지 않는다. 이전 FAILED 영수증과 코드는 `source-archive/p361-field-cache619/`에 그대로 보존한다.

검증기는 초기 입력 집합을 한 번 물리적으로 읽고 그 reader의 bound snapshot에서 이전 pin과 비교하도록 정리했다. 같은 사전검사에서 과거 입력 전체를 다시 물리적으로 읽는 중복을 피하고, 끝의 전체 실제 재해시는 유지한다. 기존 admission/CPU/RAM/Job/입력 보호나 실패 판정 조건은 낮추지 않았다.

## 자원 관측과 완료하지 않은 범위

최종251.031초, 시스템 CPU 관측최고65.53%, 가용RAM 최저42.200%였다. 앞선 시도를 포함하면 가용RAM 최저39.847%다. 모든 시도에 보호 중단은 없었으나 이 수치를 PC 프리즈 원인의 해결 근거로 삼지 않는다.

Job readback은1코어 affinity·머신CPU6.25% hard cap·낮은 우선순위·breakaway disabled를 확인했다. 최종 일반 빌드와 관측 Job CPU 시간은 각각1.734초/1.438초, peak private memory는753.77MiB/54.95MiB였다. 시스템 최고 CPU 표본에서 Python 부모 CPU는0%였고 commit 사용은50.974%였다. 따라서 직접 실행 tree 부하만으로 시스템65.53%를 설명할 수 없지만, 외부 프로세스나 검증이 유발한 간접 반응 중 어느 것인지 이 기록만으로 특정하지 않는다. Defender/다른 앱 설정 변경이나 외부 프로세스 종료는 하지 않았다.

원래 한글/COM/Native·공식249 전체·소비된010 probe는 실행하지 않았다. 최종 원문349446B/SHA5ecbf9ebcb533fc2a08e39f4ff1894094713e5b65bad67cff8a1ead8edc7e548는 immutable private spool에 먼저 보존했고,111591B/SHA6ff80f76a17e3e5fb320d60967d33f09860a7a9773488302a0e523ea3847849a packet은 원래256KiB publisher/4MiB 복원 한도를 유지한다.

Native 대상 해석·화면 표시·재평가·캐시 최신성, 다른 CROSSREF 대상 종류, 전체 reference edge/auxiliary state/flow와 P09 통합 Gate는 남는다. 다음에는 CPU 부하의 직접/간접 원인을 낮은 부하로 구분할 관측을 보강하고, 캐시 관측을 field-specific 진단에 연결한다. 공식249 큐158수용/잔여91/next165와 P09/A12/A13 OPEN은 유지한다.
