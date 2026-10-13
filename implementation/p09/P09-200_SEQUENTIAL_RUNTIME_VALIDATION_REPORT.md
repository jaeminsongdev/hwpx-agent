# P09-200: 단일 runtime 검증 008~010 및 CPU 경고 관측

## 판정 범위

2026-10-08. P199 streaming dispatcher로 case008·009·010을 각각 한 번 실행했고 각 성공 body의 독립 runtime source closing을 완료했다. 성공한 001~007은 재실행하지 않았다. 세 run은 exit0, exact1PASS/248filtered, stop=null, watcher cleanup 및 owned tree empty로 종료했다.

현재 runtime 수용10/249·잔여239(일반233+corpus6)·미closing후보0·다음index11이다. 원 whole 수용3과 whole미확인성공7은 별도다. 249개는 이 r07 regression 큐의 분모이며 P09 전체 작업 수나 전체 완료율이 아니다. compiled249=true/full249=false/signed16=false, whole/Gate 미수용, product=false, P09·A12·A13 OPEN. P10 새 구현은 없다.

검증된 212 mock 계약의 controller 10개가 변경되지 않은 경우에만 계약 증거를 재사용한다. fixture 기반 Rust 경로의 성공은 실제 SQL/Hangul/native/signed16 제품 수용으로 승격하지 않는다.

## 실제 실행 결과

| case | 확인한 제품 경로 | body 시간(입력 확인 포함) | Job CPU | peak private | host CPU 최대 | 독립 closing |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| 008 | 저장된 field range가 whole direct graph와 일치하며 ingest/head 변경 없음 | 138.41초 | 0.312초 | 32.17MiB | 83.33% | PASS, 65.2082초 |
| 009 | 각 신규 partial marker가 기존 marker 없이도 full product 판정을 거부 | 133.06초 | 0.250초 | 28.26MiB | 36.11% | PASS, 65.1849초 |
| 010 | source ACL 철회 후 신규 range import와 cached range verification 거부 | 135.81초 | 0.188초 | 28.84MiB | 100.00% | PASS, 66.9506초 |

각 body의 원 runtime 입력 1415개를 실제 전후 117921706bytes씩 읽었다. 각 closing은 bound1416=fresh1416으로 종료했다. closing 읽기량은 각각 237857506/237799328/237830804bytes다. 속도·deadline·소유 Job·CPU/RAM 보호 및 실패 판정은 완화하지 않았다.

## case010의 CPU 100% 관측: 원인·해결 미확정

프리즈 원인·해결은 미확정이다. case010 body의 저장된 표본 154에서 host CPU 100%가 실제 기록됐다. 해당 표본의 부모 CPU와 owned Job CPU는 각각 0%, active Job process는 0이었다. 이는 테스트 자식이 종료된 뒤 입력 후확인 구간의 관측이다. available RAM 36.937838346475374%, commit 사용률 42.37425796742776%였다.

경고 표본(95% 이상)은 한 개다. 두 번째 source reader는 경고 진입 한 번, 0.5초 대기 두 번으로 총 1초간 읽기를 대기했다. 98% 이상 네 표본 연속 중단 조건은 충족하지 않았다. 이 조건 미충족은 프리즈 안전성이나 CPU 문제 해결을 증명하지 않는다.

주변 비동일 시간창의 프로세스 귀속 관측은 159개 조회 불가 프로세스를 포함했다. 직접 점유 주체를 특정할 수 없고, 검증 읽기가 유발한 간접 시스템 작업도 배제하지 않는다. Git/Defender/WSL/드라이버 또는 특정 제품 코드가 원인이라고 확정하지 않는다. 이 관측이 과거 사용자가 경험한 재부팅 필요 프리즈 자체를 포착했다고도 주장하지 않는다.

선별 관측 파일: `implementation/p09/evidence/runtime-r07/p09-200-case010-cpu-spike-inspection.v1.json`. 이 파일은 원 receipt의 선택된 숫자를 기록한 관측이며 새 runtime PASS나 원인 분석 PASS가 아니다. 새 부하 재현·외부 프로세스 재조회·원 receipt 수정은 없다.

100% 관측 확인 이후 새 제품 테스트를 시작하지 않았다. 다음 큐 index는 11이지만 우선 저장 증거와 reader/planner 코드에서 반복 읽기와 중복 검증을 조사한다. CPU 보호로 중단하거나 검사 강도를 낮추는 것을 최적화 완료로 간주하지 않는다.

## 정확한 증거 핀

새 body 경로는 모두 `implementation/p09/evidence/runtime-r07/cases/` 아래다.

| body | bytes | SHA-256 |
| --- | ---: | --- |
| p190-case-008-attempt-001.json | 965079 | f66e33f8ce31aad033f4c8bebcabfefb941099f59b261460dd5f07e83471c478 |
| p190-case-009-attempt-001.json | 935990 | 1228a87407f59655560b258160a22a5d114684e77609a0fe8a30ed0ca603e36d |
| p190-case-010-attempt-001.json | 951728 | b93d6ea8e8f790f1de3088c2ccb97bf9fc5f3340a38d9ed524ff5e9fe0ea5958 |

runtime closing 경로는 모두 `implementation/p09/evidence/runtime-r07/` 아래다. 기존 004~007의 원본도 현재 판정에 사용한다.

| closing | bytes | SHA-256 |
| --- | ---: | --- |
| p196-case-004-attempt-001-close-01.v1.json | 1160181 | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| p198-case-005-attempt-001-close-01.v1.json | 1135501 | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-case-006-attempt-001-close-02.v1.json | 1132322 | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| p198-case-007-attempt-001-close-03.v1.json | 1137890 | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-case-008-attempt-001-close-04.v1.json | 1137858 | e04e457e974217bb9bec4b50b286aa20ea1edca6f5cb2b8bbafdf6f47c621a54 |
| p198-case-009-attempt-001-close-05.v1.json | 1137513 | 08dd6dbf07f2de549d2bb1f57a6260f86ce5c619e9273bb56564252824119d29 |
| p198-case-010-attempt-001-close-06.v1.json | 1146621 | cfa19969a89e822e38b9b8e9094b3cfdcc6f9cde0dbf3cf0ef5fc4d300e24218 |

최신 queue receipt: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-plan-run03.v1.json`, 121399bytes, SHA-256 `78c85de30cb1b3fc2de6ad9d8d44a8aad1b25146e72775fcb5a9bb879043887e`.
재사용 계약 proof: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-light-run03.v1.json`, 61712bytes, SHA-256 `cb91f9ddf68299e67cece4f40a40711c1d73a645489e86a23988ac123faaeb4d`.

## 동기화·보존·남은 경계

`CURRENT_STATE.md`와 `P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md`에 동일 r69 요약을 추가하고 r68 이하의 원 byte를 `source-archive/runtime-progress-r68/` 사본과 대조한다. 원 runtime validator로 저장 body/closing을 다시 확인하며 CPU 관측값도 원 receipt와 대조한다. doc-sync 자체는 새 제품 실행·추가 heavy closing·EXE 재해시를 수행하지 않는다. 별도 doc-sync receipt가 PASS인 경우에만 동기화 검증 성공으로 판단한다.

과거 실패·whole 판정·원본/private 자료는 보존한다. 과거 EXE67개 반복 읽기, Git/Cargo/build/SQL/Hangul/접근허용, OS·Defender·WSL 설정 변경, 삭제·이동은 하지 않았다. 최종 whole reconciliation, signed16 및 P09 제품 Gate는 여전히 미완료다. 목표는 active이며 이 보고서는 P09~P20 완료 보고가 아니다.
