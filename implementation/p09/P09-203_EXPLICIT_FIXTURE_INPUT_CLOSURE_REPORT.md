# P09-203: r07의 명시적 fixture 입력 목록과 실제 byte 확인

## 구현·실제 검증

2026-10-08. `tools/p09/runtime_fixture_inputs.py`는 compiled test module59개를 원785 Rust manifest의 pin과 대조하고, 파일 기반 fixture I/O 모듈6개를 확인한다. P77/form/note manifest 및 native note 증거의 고정 hash, 문서 경로·길이·digest, 중복 일치, ancestor link/reparse 조건을 검사하고 모든 고유 입력 byte를 처음과 종료 시 실제 읽는다. 변경/누락/범위 이탈이면 실패하며 접근 허용·native 실행은 없다.

`python -B tools/p09/runtime_fixture_inputs.py --run 1`은 terminal exit0으로 완료했다. 신규16계약 PASS, actual fixture 입력38개567619bytes, stop=null/cleanup=true/IO finished=true/bound118=fresh118다. 실제 logical read304회16122603bytes에는 sealed baseline metadata와 source/module 확인도 포함된다. 현재/과거 EXE hash, SQL/Hangul 또는 제품 테스트 실행은 없다.

입력 qualification은 `KNOWN_PREEXISTING_TEST_MODULE_FIXTURES_NOT_ALL_PRODUCT_IO` 범위다. 제품 라이브러리의 모든 파일 I/O, 실행 중 생성되는 산출물, Python worker/import 의존성 또는 full249 제품 수용을 증명하지 않는다.

## 명시된 입력 가족과 중복 처리

| 가족 | 참조 수 | 참조 bytes 합계 |
| --- | ---: | ---: |
| P77 actual source corpus | 36 | 510909 |
| form matrix source/output | 10 | 159833 |
| note generated/saved/reopened | 9 | 116099 |
| field 고정 캡처 | 1 | 15097 |
| object 고정 캡처 | 1 | 14556 |
| compiled header XML | 1 | 42154 |

참조58개는 동일 경로·길이·SHA의 중복만 합치면 고유38개다. 한 경로에 서로 다른 pin이 선언되면 거부한다. form10개·note9개·field 캡처는 P77 corpus 안에서도 참조되므로 같은 byte를 중복 로드하지 않는다. 기존 원1470 manifest에는 이 고유 입력 중2개가 있고, 나머지36개를 이번 목록에서 새로 명시했다. 원1470 manifest를 덮어쓰거나 변경하지 않았다.

문서 원본과 내용은 출력·수정하지 않았다. 증거 파일에는 검토 가능한 pin만 기록하고 stdout에는 합계와 폐쇄된 판정 코드만 출력한다. 실제 문서 byte의 첫 hash와 종료 fresh hash가 모두 일치해야 이 fixture 범위만 PASS다.

## 실패 증거·보호 조건

note manifest의 세 case와 native 증거의 saved/reopened 문서는 고정 case/slot/lane으로 제한한다. 기존 native note는 `failed_semantic_non_green`, green_rows=0 및 각 case 실패 상태를 반드시 유지한다. 이를 PASS로 재표기하거나 일부 snapshot을 생략하면 거부한다. 이번 Rust fixture 입력 확인으로 그 native 의미 검증이 통과한 것은 아니다.

새16계약은 동일 중복/충돌 digest, 경로 이탈·ADS·backslash, 파일명 범위, 길이 타입·0·상한, P77/form 수, note 중복/알 수 없는 case/실패 재분류/green count/누락 snapshot, 실제 hash 불일치, 고유 byte 읽기, 원본 객체 보존, 종료 fresh 단계 유지 등을 확인한다. 실제 run은 입력38개의 직접 파일·ancestor reparse 확인과 전체 hash 재확인까지 수행했다.

새 실행기의 제품 body 검증은 NOT_RUN이며 실제 runner source scope는 그대로다. safe_runtime_exclusions=[], exclusions_authorized=false이다. 프리즈 원인·해결은 미확정이다. 이 경량 run의 hostCPUmax21.55%·ownCPUmax0.970874%·ownprivate31604736bytes·availableRAMmin37.25297757158647%는 해당 표본이며 다른 run 대비 인과적 최적화 효과나 PC 안전성 증명이 아니다.

## 현재 큐 및 다음 단계

기존 제품 큐224계약과 runtime 수용10/249·잔여239(일반233+corpus6)·미closing후보0·다음index11은 변경하지 않았다. 원 whole 수용3/whole미확인성공7, compiled249=true/full249=false/signed16=false, whole/Gate 미수용, product=false, P09·A12·A13 OPEN이다. 16개는 새 fixture 입력 계약이지 새 제품 테스트16건이 아니다. 목표active/P10 새 구현 없음. 249는 이 r07 큐의 분모이지 P09 전체 분모가 아니다.

다음은 Python worker의 실제 import/직접 입력 의존성을 대조하고, 이 명시 fixture 목록을 포함하는 live 입력과 최종 원본 보존 확인을 분리하는 실행 경로를 구현하는 것이다. 과거 증거272개81.1MB를 파일명만으로 제외하지 않는다. 최종 원1470 whole reconciliation 및 signed16/P09 Gate 의무는 유지한다.

## 정확한 증거와 문서 동기화

새 fixture proof: `implementation/p09/evidence/runtime-r07/p09-203-fixture-input-closure-run01.v1.json`, 58730bytes, SHA-256 `14253bda2bf0f8e4d1200818482f9d6e75583160cacd90bc28360c1a881a4f16`.
재사용 제품 큐 계약: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-light-run07.v1.json`, 224계약, 88896bytes, SHA-256 `3146b518664ef4d02608b53771a0b43924fec2f8812c713f41fa39619934db4f`.

현재 수용에 사용하는 runtime closing 원본은 `implementation/p09/evidence/runtime-r07/` 아래다.

| closing | SHA-256 |
| --- | --- |
| p196-case-004-attempt-001-close-01.v1.json | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| p198-case-005-attempt-001-close-01.v1.json | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-case-006-attempt-001-close-02.v1.json | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| p198-case-007-attempt-001-close-03.v1.json | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-case-008-attempt-001-close-04.v1.json | e04e457e974217bb9bec4b50b286aa20ea1edca6f5cb2b8bbafdf6f47c621a54 |
| p198-case-009-attempt-001-close-05.v1.json | 08dd6dbf07f2de549d2bb1f57a6260f86ce5c619e9273bb56564252824119d29 |
| p198-case-010-attempt-001-close-06.v1.json | cfa19969a89e822e38b9b8e9094b3cfdcc6f9cde0dbf3cf0ef5fc4d300e24218 |

CPU 원 관측은 `implementation/p09/evidence/runtime-r07/p09-200-case010-cpu-spike-inspection.v1.json`을 유지한다. 동일 r72 prefix를 두 상태 문서에 추가하고 r71 이하의 모든 byte는 `source-archive/runtime-progress-r71/`와 대조해 보존한다. 별도 doc-sync는 현재224계약 controller pin 및 원 runtime validator를 재사용하고, 새16계약 helper pin·4manifest·38입력 목록을 다시 대조하며 실제 byte와 종료 fresh hash도 확인한다. doc-sync의 실제 terminal PASS가 있어야 문서 동기화 검증 완료로 판단하며 제품/whole/Gate PASS로 승격하지 않는다.
