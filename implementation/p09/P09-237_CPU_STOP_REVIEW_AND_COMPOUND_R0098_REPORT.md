# P09 P234~P237 CPU STOP 검토·독립 source 마감·결합 수용

2026-10-09. 목표 active. P09·A12·A13 OPEN. 제품 완료 및 PC 프리즈 원인·해결 미확정.

## 현재 결과와 다음 경계

- runtime 수용 72/249, 잔여 177(일반171+corpus6), 미closing후보0, 다음index79, whole재조정대기69.
- r97 69개에서 case76·77 정상 원 경로 수용 및 case78 별도 compound 수용으로 3개 증가.
- 제품 본문 재실행 없음. case79 본문 NOT_RUN. 통과한 body 1~78 중 기존 수용 대상은 반복하지 않는다.
- 원 P230 caller 자체는 78 FAILED로 차단. 후속 실행 caller NOT_RUN: P236 proof를 소비하고 새 제어 코드까지 전체 source frame에 묶는 새 실행기 구현·검증이 다음 단계다. 원 P230 validator·수용 코드 수정 및 FAILED 무시 금지.
- 이 보고서와 P237은 새 문서 상태 snapshot이다. 전체 runtime/source/whole 재검증 또는 product/Gate 수용이 아니다.

## 중단과 관측

case78의 exact-one body는 exit0, terminal passed1/failed0/filtered248, bounded stdout256/stderr0로 완료됐다. CPU 보호는 이후 final_source_freeze의 원 1512입력 중 1362번째까지/110635044 bytes를 읽은 상태에서 EXE의 부분 읽기를 중단했다. tests_passed 필드는 원 STOP에 없으며 새로 채우지 않았다.

원 parent에서 시스템 CPU100%가 4개 연속 표본으로 관측됐다. 그 경고 구간 자체 parent 최대0.195312%, Job CPU0% 및 활성 프로세스0개였다. 외부 CPU 원인이나 간접 IO 영향은 이 자료로 특정하지 않는다. 전체 시스템 CPU 피크와 자체 CPU를 혼동하지 않는다. root의 resource_stop_reason=null은 원 parent의 STOP_SUSTAINED_SYSTEM_CPU가 없다는 뜻이 아니다.

원 읽기 backpressure는 ≥95% 경고1/3 pause windows/1.5초로 실제 연결돼 있었다. 보호 기준을 풀거나 소스 입력을 줄이지 않았다. 원 잠금1818개와 복제2874개가 모두 정리됐고 deferred terminal writer가 원 parent full sidecar를 보존했다. 실제 STOP 기록 보존은 이번 관측으로 확인됐으며 의도적인 CPU stress 재현은 하지 않았다.

## 코드 검토와 적용한 최적화

- 최종 읽기 경로: OwnedReader → 기존 PressureCheckpoint → 원 CPU/RAM/commit/IO/잠금 guard가 유지됨을 확인했다. 무제한 루프·병렬 실행·별도 표본 스레드를 추가하지 않았다.
- Native open/borrowed stream 경로: 기존32open/s·no-burst·한 직렬 stream·원 stream identity·중단 후 guard 없는 cleanup을 유지한다.
- 원 source/EXE/worker와 수용 helper는 고치지 않았다. new generation의 검토·마감·결합·문서 코드만 추가했다.
- metadata pin 선행 read와 JSON parse read를 같은 첫 실제 read의 SHA/length binding으로 결합했다. P236의 원 정상 body도 원 record validator를 그대로 호출하면서 첫 중복 read를 없앴다. 마지막 전체 fresh 재읽기는 유지하며 다른 run의 캐시로 대신하지 않는다.
- 정상 본문을 재실행하지 않고 P212의 기존 독립 증거 결합 방식을 현재 literal STOP에 적용했다. 원 STOP를 PASS로 보이게 복사하거나 partial after를 완성했다고 주장하지 않는다.
- 문서는 텍스트 확인용과 원bytes suffix 확인용으로 중복 읽지 않고 같은 bounded byte buffer에서 둘 다 검사한다. 최종 freshness는 별도 실제 읽기로 유지한다.
- CPU 보호 중단 시 자동 재시도 금지. 다음 중단도 phase·자체/Job CPU·전체 입력/정리 상태·관련 코드 검토 후 진행한다. 최적화 전부 완료나 PC 프리즈 해결을 주장하지 않는다.

## 검증 증거

| 증거 | 결과 | bytes / SHA256 |
|---|---|---|
| r97 문서 receipt `p232-current-doc-delta-r0097-run01.v1.json` | 이전 상태69 보존 | 349552 / `45c2c83a326b87dc603fadc89958c5849ff9b6da6629947177565c3a081f6cbe` |
| case76 원 `p230-case-076-run016.v1.json` | runtime70, 정상 exact1 | 578360 / `64d79b84c7f7e15e7830d80e44fffb5624696412b39ae97b7ab9f9b72323cb11` |
| case77 원 `p230-case-077-run017.v1.json` | runtime71, 정상 exact1 | 581136 / `1e3bb6ada09cf04ea3ab083da9f772f180c22f90668aa274255200086a0a56b2` |
| case78 원 root `p230-case-078-run018.v1.json` | FAILED_NOT_ACCEPTED 보존 | 885680 / `0f426067907084932489b7bb00425cca017851b726ca2f466dba4777d456ebf1` |
| case78 원 parent `cases/p230-failure-078-run018.json` | STOPPED_NOT_ACCEPTED 보존 | 600156 / `66127715459940855848724d8e918add4f3bad4fa3227a73e804cee5702904db` |
| case78 placeholder `cases/p230-case-078-run018.json` | 0-byte 원본 보존 | 0 / `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| P234 `p234-current-stop-review-run01.v1.json` | 후보 검토20+peak8, runtime 아님 | 15243 / `64bf2c461028d753d9f55e562f215f670c3237f5fbd042e78c7ec53313c9c30e` |
| P235 `p235-current-stop-source-frame-run01.v1.json` | 독립 전체 source 마감12, runtime 아님 | 1336314 / `cc7793e2ee7cc9facc9de8bcf72c64551ae629124d7c683fb95e367747582b62` |
| P236 `p236-case078-compound-run01.v1.json` | 새 compound20 수용72/다음79 | 355396 / `1761365334369863fd3aaf9afc5747456b6a4101dac37cdddbb9e69b3cfbf462` |

증거 상대경로의 기준은 `implementation/p09/evidence/locked-r07/`다. P237 receipt는 `p237-compound-status-doc-r0098-run01.v1.json`에 신규 작성하며, 이 보고서의 마지막 수정 전에 성공을 선기록하지 않는다.

P235는 원1512 + 새4 = 1516입력/118950560 bytes의 전후 실제 두 읽기, 잠금1822·복제3032의 모두close/잔여0, held identity 검사를 통과했다. 원1MiB/s EXE·2MiB/s 기타 읽기, 600초 IO/잠금, CPU/RAM/commit 보호를 유지했다. Native warning1·8 pause windows로 압력 대기가 작동했고 resource_stop_reason=null이었다. 전체CPUmax100%는 순간 관측이고 지속98x4 STOP는 없었다. 자체max1.151631%, private peak36110336 bytes(약34.44MiB), 가용RAM최소23.441324%였다.

P236 metadata는 206fresh=finished/cleanup, STOP없음, 계약20 통과였다. 본문과 전체 source frame 재실행 없이 원 기록들을 원 validator로 검증했다. 자체max4.519231%, private peak41676800 bytes(약39.75MiB)였으며 시스템max100%의 원인을 단정하지 않는다.

## 보존과 미수용 영역

r97 두 문서의 원bytes 사본을 `implementation/p09/evidence/runtime-progress-r97/`에 no-overwrite로 확인했으며 원文書의 suffix로 보존한다. 실패/0-byte/sidecar 증거 삭제·이동·재작성 없음. Git·Review·Cargo/build·접근허용·한글 GUI·SQL 실행·Defender/WSL/OS 설정 변경 없음.

249 전체 runtime, corpus6, signed16, whole 재조정69, 실제 SQL/생산 issuer/native UI 및 P09 Gate는 이 검사로 통과하지 않았다. runtime 목록의 잔여를 P09 전체 작업 완료율로 바꾸지 않는다.
