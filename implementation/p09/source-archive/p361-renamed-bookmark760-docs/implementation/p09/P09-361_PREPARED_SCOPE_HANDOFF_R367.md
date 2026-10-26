# P09 전체 입력 준비 결과와 실행 비용

2026-10-14 현재 공식 승인은 153/249, 잔여 96개, 다음 사례 160, generation 48이다. P09/A12/A13은 OPEN이고 P10 구현은 시작하지 않았다. 준비 결과 생성과 scope 재구성은 완료했지만, 새 runtime 연결과 제품 승인은 아직 성립하지 않는다.

## 전체 준비 결과

원 전체 선행 oracle과 최종 재읽기를 실행해 `p09-361-case160-prepared-input-checkpoint-r834.v1.json`을 생성했다. 원 controller DATA039·preflight039·authority153·성공159와 실제 29쌍 manifest를 유지했다. 제품·Native·GO는 실행하지 않았다.

| 항목 | 실제 기록 |
| --- | ---: |
| 준비 경과 시간 | 361.414573초 |
| reader 입력과 최종 재읽기 | 1,145 / 1,145 |
| 전체 선언 scope | 2,835개 |
| 이 단계에서 최종 재읽기한 scope | 1,145개 |
| 선언했지만 이 단계에서 최종 재읽기하지 않은 scope | 1,690개 |
| 선언된 현재 Rust 입력 | 787개 |
| Rust 파일 바이트의 이번 최종 재읽기 | 0개 |
| 읽기 횟수와 바이트 | 2,398회 / 528,138,313bytes |
| PC 전체 CPU 최대와 가용 RAM 최소 | 42.05% / 57.988290% |
| 검증 프로세스 CPU 최대 | 4.188859% |

Rust 입력을 포함한 전체 scope의 두 실제 Native 읽기는 후속 runtime 조건으로 남는다. 저장된 준비 결과는 2,693,611bytes이며 SHA-256은 `73f321efd4ffd05adebeff806c2d5f5c620c8307e73209a47583de35371b1233`이다. 이전 CPU 중단 r833과 이번 준비 결과는 모두 보존했다.

## Scope 재구성 검증

`prepared_scope_handoff_v1.py`는 저장된 checkpoint의 실제 바이트 pin과 현재 명시적 입력, 원 manifest 표현, 현재 Rust 입력 집합을 대조한다. 최종 재읽기와 선언만 된 입력의 분할을 검증하고, 전체 scope에 checkpoint 자체를 추가한다. scope를 줄이거나 새로운 실행 권한을 반환하지 않는다.

단위검사 20개에는 실패한 준비 결과, 권위·manifest 변경, 부분 최종 검사, 중복 pin, Rust 누락, bool/int 치환, projection의 scope 변경 및 원 자원 중단 전파를 포함했다. exporter 17개와 terminal progress 9개를 합친 46개 검사가 통과했다.

최초 독립 qualifier r836은 test loading 조건에서 실패한 상태로 보존했다. 저장소 root의 module 경로를 보강한 r837은 실제 checkpoint와 bounded graph 21개 입력을 사용해 재구성을 통과했다. 원 64 reads/262,144bytes bootstrap 한도는 유지했다.

| 재구성 검증 항목 | 실제 기록 |
| --- | ---: |
| 전체 선언 scope와 checkpoint | 2,836개 |
| qualifier 입력까지 포함한 scope | 2,839개 |
| 원 alias를 적용한 physical scope | 2,810개 |
| 현재 Rust 집합과 manifest | 787개 / 29쌍 |
| 실제 Rust inventory 요청 | 167회, 20/s pacing |
| qualifier 최종 재읽기 | 38 / 38 |
| qualifier 읽기 | 76회 / 7,888,384bytes |
| 경과 시간 | 18.070373초 |
| PC 전체 CPU 최대와 가용 RAM 최소 | 38.04% / 59.665367% |
| 검증 프로세스 CPU 최대와 private RAM 최대 | 4.177763% / 48.054688MiB |

이 검사는 원 전체 준비를 다시 수행하지 않았다. 위 두 단계는 검증 목적과 입력이 다르므로, 시간·바이트 차이를 실제 제품 실행의 성능 개선율로 해석하지 않는다. cleanup은 두 단계 모두 완료됐다.

## 실행 비용 거부와 다음 조건

checkpoint와 새 qualifier 입력을 포함한 원 Native 모델의 예상 비용은 decoder 5초를 포함해 **603.148728초**였다. 원 600초 제한과 60초 margin을 유지했으며 `ENVELOPE_SCOPE_BINDING_COMPLETE_COST_PLUS_SHARED_DECODER5`가 이를 거부했다. 재구성 CODE46의 PASS는 이 비용 거부나 실제 runtime을 PASS로 바꾸지 않는다.

다음은 checkpoint 등 입력의 무손실 표현을 검토해 실제 파일 읽기 비용을 줄이고, 새 실제 연결 scope로 비용을 다시 계산하는 작업이다. 이후에만 실패 run003 검토와 새 run004 identity, 전체 controller preflight, 실제 두 Native 바이트 경계 및 독립 case160 제품 oracle을 연결한다. 기존 run003은 재실행하지 않는다. Native600/shared720, 전체 의미 입력, 원 자원 보호와 독립 승인 조건은 그대로 유지한다.

새 worker·Native·제품 실행, 승인 증가, 접근 허용·UAC, OS 설정 변경, 외부 프로세스 종료, 삭제·이동 및 원격 push는 없었다. 목표는 ACTIVE이며 PC freeze 해결은 미증명이다. 실패 r836과 당시 코드·준비 결과는 `7146439`에 보존했다.
