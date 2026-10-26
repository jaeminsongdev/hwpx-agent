> 현재 기준(2026-10-26): [768 본문읽기 실패 수정773~775](P09_CURSOR_TEXT_FIX_773.md) 완료. 768은 첫사례의 이동전 본문읽기에서실패했고 완료사례0·cleanup=true·자원보호중단0이다. 실패/코드원본을보존하고 전체문서옵션빈값/선택블록saveblock으로분리했다. 반환형식·길이·SHA 진단과잘못된반환시이동전거부를추가했다. 코드774의구문5＋Python8＋PS13 및실제READY차단/entry읽기통과·source1424/1424·cleanup=true·Native0. 새773은실물NOT_RUN이며외부1회실행대기. 사용자최신요청에따라이번오류정리만마무리하고목표일시정지하며별도속도개선작업은시작하지않는다. 최신제품766·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10미시작. 아래는이전이력이다.

> 현재 기준(2026-10-26): [761 실물8종 및 후속 제품 검증763~767](P09_RENAMED_NATIVE_READBACK_763_767.md) 완료. 이름변경 초기/저장/재열기24파일＋후보8의 제품판정과24쪽 픽셀 일치 확인. 기존 통과 실물 시험 재실행0. 다음은 [768 실제 책갈피 커서16건](P09_BOOKMARK_CURSOR_768_RUNBOOK.md)이며 코드772 준비 검증 완료·실물 NOT_RUN. 새 외부 명령1회 안내 후 사용자 요청대로 목표 일시정지. 링크 활성화/일반flow/local host·지속출력·현재head는 미수용. P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10 미시작. 아래는 이전 이력이다.

> 현재 기준(2026-10-26): [755 증거 읽기 오류 수정761~762](P09_RENAMED_ENTRY_CODEC_761.md) 완료. 755는 XZ 코드를 legacy DEFLATE reader로 읽어 첫파일에서 실패했으며 claim/한글/사례0·cleanup=true였다. 실패와 기존 실행기 보존. 새761은 코드XZ/제품754 legacy decoder를 명시적으로 분리한다. 신규12검사＋실제 entry.load_code 경로 통과·기존27/READY 재실행0·source1319/1319·shell1·cleanup=true·guard449·시스템CPU최고75%·가용RAM최저27.8780%·보호중단0. 새8종은 아직 미실행이며 별도 외부 PowerShell의761명령1회를 기다린다. 사용자 요청대로 안내 후 목표 일시정지. 최신 제품754·실물의미/링크/cursor/host/출력/head 미수용·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10 미시작. 아래는 이전 이력이다.

> 현재 기준(2026-10-26): [이름변경 새8종 Native755 준비](P09_RENAMED_NATIVE_BATCH_755.md) 완료·외부1회 실행 대기(NOT_RUN). 신규27검사와 실제 READY 거부(사례0·한글0) 통과. source1314/1314·shell1·cleanup=true·CPU최고15.83%·가용RAM최저38.7891%·보호중단0. 새파일의 initial/saved/reopened HWPX·전체쪽 BMP 수집이며 의미·링크/cursor·Gate 수용은 포함하지 않는다. 759 실패 보존·현재 제품754/공유 Native692 입력 각각 결속. 기존684/690 및 제품검증 재실행0. 최신 제품754·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10 미시작. 사용자 요청에 따라 명령 안내 후 목표 일시정지. 아래는 이전 이력이다.

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
