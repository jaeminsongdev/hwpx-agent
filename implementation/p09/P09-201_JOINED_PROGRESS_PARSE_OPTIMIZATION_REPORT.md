# P09-201: 큐 계산의 중복 JSON 해석 제거

## 구현 및 실제 확인

2026-10-08. `tools/p09/joined_runtime_resume_progress.py`와 신규 12개 계약을 추가했다. 기존 P198/P199 실행기와 통과 receipt가 pin으로 참조하는 controller 파일은 수정하지 않았다. 현재 입력이 동일한 기존 성공 body는 재실행하지 않는다.

이전 큐 계산은 신규 디렉터리의 성공 case를 먼저 JSON 해석하고 해제한 뒤 closing 확인 때 같은 case를 다시 읽고 JSON 해석했다. 새 경로는 case 하나와 해당 closing들을 묶어 처리한다. 두 번째 전체 byte 읽기와 SHA-256 동일성 검사는 fresh pin으로 유지하고, 그 byte가 같을 때에만 이미 해석한 동일 case에 원 case/closing validator를 적용한다. 각 case 처리가 끝나면 payload를 해제하며 cross-run raw/parsed cache는 사용하지 않는다.

`python -B tools/p09/joined_runtime_resume_progress.py --mode light --run 7`이 실제 terminal exit0으로 완료했다. 기존212+신규12=224계약 PASS, stop=null, watcher cleanup=true, IO finished=true, bound47=fresh47이다. 실제 저장된 신규 case 005~010 여섯 개의 JSON 해석은 12회에서 6회로 줄었고 기존 전체 byte 재확인 6회는 유지됐다. closing JSON 해석은 6회, 보유 신규 case payload 상한은 하나다. 기존 큐의 runtime_plan과 필드·이름·판정이 정확히 같았다.

기존 plan-run03은 read106/bound45/fresh45, 새 경로는 read110/bound47/fresh47이다. 추가4회 읽기는 새 controller 두 파일의 첫 읽기와 최종 fresh 확인이다. 기존 case 재읽기를 삭제하거나 과거 receipt의 byte/hash/pin을 바꾸지 않았다. JSON 해석을 생략한 원문 분량은 5714767bytes이나 논리 파일 읽기량 절감은 주장하지 않는다. 이 최적화는 중복 JSON 해석·할당 제거이며 PC 프리즈 원인 수정 완료가 아니다.

## 자원 관측과 판정 경계

이번 경량 확인에서 host CPU 최대23.53%, parent CPU 최대4.5773%, parent private 최대55877632bytes, available RAM 최소47.648195066570466%였다. 다른 run의 부하 조건과 같지 않으므로 이 수치로 인과적 개선율이나 프리즈 해결을 증명하지 않는다. 프리즈 원인·해결은 미확정이다.

새 제품 테스트·과거 성공 body 재실행·heavy closing·EXE 재해시·Git/Cargo/SQL/Hangul/접근허용·OS 설정 변경은 없다. 새 dispatcher 자체의 제품 실행(body/독립 closing)은 이번에 NOT_RUN이다. 기존 8/10-controller 증거와 향후 12-controller 증거를 구분하며, 새 controller를 선언한 미래 body는 두 입력을 전후 fresh scope에 실제 포함해야 한다. 기존 증거를 새 실행기 증거로 재작성하지 않는다.

현재 runtime 수용10/249·잔여239(일반233+corpus6)·미closing후보0·다음index11이다. 원 whole 수용3/whole미확인성공7, compiled249=true/full249=false/signed16=false, whole/Gate 미수용, product=false, P09·A12·A13 OPEN은 변하지 않았다. 249는 이 r07 regression 큐의 분모이며 P09 전체 분모가 아니다. 목표active/P10 새 구현 없음.

## 저장된 입력 분량 조사: 다음 최적화 대상

case010의 source_freeze 목록에 저장된 path·bytes를 분류했다. 실제 파일 추가 읽기·EXE hash·foreign PID 재조회는 하지 않았다. 아래는 경로 기반 비용 분류이며 제품의 의미상 의존성 판정은 아니다.

| 입력 분류 | 파일 수 | 한 번 읽는 bytes |
| --- | ---: | ---: |
| 현재 실행 EXE | 1 | 14216704 |
| 과거 evidence 경로 | 187 | 73619097 |
| source-archive 경로 | 88 | 7902972 |
| fixtures 경로 | 1 | 14384 |
| 나머지 .rs/Cargo.toml 경로 | 787 | 16360925 |
| 기타 frozen 입력 | 351 | 5807624 |
| 합계 | 1415 | 117921706 |

body 검증은 이 입력을 전후 두 번 읽고 closing도 독립 fresh 확인한다. 테스트 연산 자체의 Job CPU가 짧더라도 반복 증거 읽기 비용은 별개다. 읽기가 다른 시스템 작업을 유발해 CPU 포화에 기여했는지는 아직 미확정이다.

다음 작업은 기존 whole manifest와 실제 worker 의존성을 대조해, 실행 직전·직후에 필요한 live 입력과 원본 보존용 historical reference를 명시적으로 구분하는 것이다. 현재1415 입력 scope는 그대로이며 분류표만으로 제외·삭제·새 PASS 승격하지 않았다. 검증 계약을 보존하는 분리 설계 및 경량 부정 사례 확인 전 추가 제품 부하 재현을 시작하지 않는다.

## 정확한 증거

새 경량 확인: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-light-run07.v1.json`, 88896bytes, SHA-256 `3146b518664ef4d02608b53771a0b43924fec2f8812c713f41fa39619934db4f`.
비교 queue: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-plan-run03.v1.json`, 121399bytes, SHA-256 `78c85de30cb1b3fc2de6ad9d8d44a8aad1b25146e72775fcb5a9bb879043887e`.

현재 수용에 사용한 runtime closing은 모두 `implementation/p09/evidence/runtime-r07/` 아래 원본이다.

| closing | SHA-256 |
| --- | --- |
| p196-case-004-attempt-001-close-01.v1.json | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| p198-case-005-attempt-001-close-01.v1.json | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-case-006-attempt-001-close-02.v1.json | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| p198-case-007-attempt-001-close-03.v1.json | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-case-008-attempt-001-close-04.v1.json | e04e457e974217bb9bec4b50b286aa20ea1edca6f5cb2b8bbafdf6f47c621a54 |
| p198-case-009-attempt-001-close-05.v1.json | 08dd6dbf07f2de549d2bb1f57a6260f86ce5c619e9273bb56564252824119d29 |
| p198-case-010-attempt-001-close-06.v1.json | cfa19969a89e822e38b9b8e9094b3cfdcc6f9cde0dbf3cf0ef5fc4d300e24218 |

CPU 선별 관측: `implementation/p09/evidence/runtime-r07/p09-200-case010-cpu-spike-inspection.v1.json`. 원본 UTC는 `2026-10-08T04:13:45.303681+00:00`이다. P200 doc-sync-run002에서 추출 파일의 한국 시각 표기가 원문과 달라 `P199_DOC_WARNING_VALUES`로 실패했으며 실패 원본과 수정 전 관측 사본을 보존했다. UTC 원문을 복원한 뒤 doc-sync-run003이 원 receipt 값·전체 경고 목록·r68 문서 byte 보존을 검증해 PASS했다. 원 case010 receipt는 수정하지 않았다.

## 문서 동기화 확인

현재 원장에는 동일 r70 prefix를 추가하고 `source-archive/runtime-progress-r69/`의 두 문서 사본을 기준으로 이전 모든 byte를 보존한다. doc checker는 212 또는224의 명시적 proof 세대만 허용하고 현재 controller pin과 실제 closing-controller 선언도 대조한다. 224 경로에서는 새 joined planner로 기존 runtime 증거를 원 validator에 다시 확인한다. 별도 doc-sync의 terminal PASS가 있어야 동기화 성공으로 판정하며 이 보고서만으로 그 실행 결과를 선포하지 않는다.
