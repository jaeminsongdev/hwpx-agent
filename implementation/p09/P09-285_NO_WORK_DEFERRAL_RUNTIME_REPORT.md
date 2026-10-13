# P284~P285: 실제97 준비 CPU STOP 검토·무작업 admission 보류 처리·97 수용

2026-10-09. 목표 ACTIVE. 실제 runtime 부분집합 수용91/249, 잔여158(일반152+corpus6), 다음index98, whole 재조정대기88, 독립source 마감대기0. P09·A12·A13 OPEN. 91/249는 P09 전체 완료율이 아니다. whole1470/historical67/full249/signed16/제품 완료/PC 프리즈 해결은 미확정이다. 접근허용·한글 UI·빌드·Git·설치·OS/Defender/WSL 설정 변경 없음.

## 최초97: 준비 최종fresh CPU STOP, 미수용

원 P282 actual run004는990 계약 후97을 선택했지만 final_fresh_preparation에서 STOP_SUSTAINED_SYSTEM_CPU로 끝났다. 준비435 reads/226 bound/fresh126/51,066,725bytes, finished false였다. 원 Native Frame·parent·Job·제품 본체는 호출 전이며 body/Frame/post-reader 필드는 없다. 수용0, watcher cleanup 확인. 부분fresh를 전체fresh로 승격하거나 실패를 재분류하지 않았다.

77 표본, 시스템CPUmax100%, 검증 CPUmax6.100818%, private58,638,336bytes, 가용RAMmin18.130902%. 마지막8 CPU는76.87/93.97/72.24/97.27/100/100/100/100%. 마지막6 표본은 검증 CPU0 및 logical read 증가0이었다. 기존 early90이1회/2 windows(1초), 원95가1회/4 windows(2초) 대기한 상태에서 원98%x4 보호가 중단했다. 공통 entry/byte90 callback과 원95 base·clock/rate32/reader/원 보호는 실제 실패에서도 연결돼 있었다.

관련 코드의 유한 pacer 재시도·sleep, 기존 sampler0.5초 debounce/재사용, 원CPU/RAM/600/720, parse16MiB, STOP 뒤 unguarded cleanup을 검토했다. 이번 경로에서 신규 무한루프·스레드/표본 증식 또는 추가 확인된 코드 결함은 발견하지 못했다. 검토 범위 밖 전체 저장소가 최적화 완료라는 의미는 아니다. 관측값만으로 Defender·WSL·Codex·Git·다른 프로세스를 단독 원인으로 단정하지 않는다.

## P284: 보호된 reader 생성 전 admission 보류

원95/96 수용과 최신97 실패를 검토하는 불변 P284 후보(1595 입력, 예정1114 계약)를 만들었다. 원95/96은 저장된 root/body·원 전체 pair/queue validator로만 검토하도록 했고 본체 재실행은 하지 않았다. 사전 자원 admission3 표본은14.52/7.48/10.07%였지만, 실제 P284 light run001의 admission 첫 표본은 시스템100%였다. 원 정책이 DEFERRED_ALREADY_SATURATED_SYSTEM으로 보류했고 resource_stop_reason은 null, cleanup 확인, 검증 CPU0%, private28,348,416bytes였다.

P284에서는 보호된 입력 reader·계약 검사·Native Frame·원parent/Job·제품 본체·사례 선택이 시작되지 않았다. metadata logical counters는 null로 남겼으며 0으로 발명하지 않았다. Python 실행/모듈 import 자체의 파일 접근까지 없었다는 뜻은 아니다. P2841114 계약과 전체1595 runtime은 당시 미실행이었다. 원 후보와 실패 receipt는 보존했다.

## 코드 개선: 무작업 보류에 새 실행기를 계속 만드는 흐름 제한

이전 progress는 모든 FAILED early row를 차단했다. 보호된 reader를 만들기 전의 단일 admission 보류도 같은 불변 실행기를 사용할 수 없어 새 source/test generation을 요구하는 구조였다. P285는 **무작업 admission 보류만** 엄격한 review로 소비한다. 원 실패 row의 state는 FAILED_NOT_ACCEPTED 그대로, 수용/큐 전진은0이며 PASS로 바꾸지 않는다.

허용 조건은 정확한 schema/error/phase/ValueError, 원 CPU emergency admission 표본, watcher cleanup, reader counters null·관측 false, 사례 선택·계약 실행·제품 실행 없음, 전체 Gate OPEN이다. preparation_IO/Frame/body/post-reader/queue 필드가 하나라도 있거나 실제 STOP·부분 읽기·제품 실패·정리 미확인·새 sampler가 있으면 거절한다. own case 실패는 원 closed_attempt validator를 그대로 적용한다. 부분읽기가 시작된 원 P28297 CPU STOP은 이 예외로 소비하지 않고 고정SHA/단계/관측/원 pair/queue 검토를 유지한다.

새 자동 재시도 loop/스레드/CPU query, CPU 시작35% 기준, guard 완화, clock/credit/counter 초기화, 원 읽기·identity 검사 삭제는 없다. 재개 전 원 admission이 다시 현재 상태를 확인한다. 이 개선은 무작업 보류 뒤 같은 불변 코드/테스트를 재사용할 수 있게 해 불필요한 코드 파일 증가를 줄이는 제어 흐름 개선이며, CPU 풀로드 원인 해결이나 부하 감소의 측정 증거는 아니다.

18개 무작업보류/거부조건 단위 검사와 원 P284 literal 보류 review를 통과했다. 종료 후 같은 schema의 canonical reader 경로·progress의 큐 불변·partial IO 거절을3개 synthetic workflow check로 확인했다. **실제 P285 own admission 보류 후 같은 namespace 재개는 아직 NOT_RUN**이다. 실제로 검토한 보류는 원 P284 기록이며, 이를 P285 전체 연결에 반영했다.

## P285 전체 연결 사전검증

원1563+34=1597 입력, extras130, ancestor308. 기존 단일 pacer 획득14/s·byte20/s·metadata32/s·byte binary1/other2MiB/s·원600/720/CPU/RAM/Job/두 실제 byte/identity/정리 조건을 유지했다. 새로운 경로는 원1114+현재82+다음82=1278 계약을 실제 실행했다. 원P284에서1114 계약을 실행했다고 소급 주장하지 않는다.

light run001은1278 계약 PASS, 준비608 reads/232 bound 및 최종fresh/69,897,291bytes·STOP null·cleanup 확인. 명목 예산578.7173924309867초 < 원600초이며 완료 보증이나 보호 연장은 아니다.94 표본의 시스템CPUmax27.91%, 검증 CPUmax6.036721%, private56,446,976bytes·가용RAMmin19.312478%. 이 단계는 실제 전체 Native byte/제품 수용을 대신하지 않는다.

## 실제97 새 경로: exact1 수용

P285 actual run002는 PASS_EXACT_R07_NO_WORK_DEFERRAL_RUNTIME_NOT_WHOLE_OR_GATE이며 원 제품 parent는 PASS_SCOPED_NOT_GATE·tests_passed1·원 작업 트리/Job 정리 확인으로 끝났다. 기존 수용95/96이나 최초97의 본체를 재실행한 것이 아니다. 최초97은 본체 미실행이었고 이번 새 경로가97의 첫 실제 본체 실행이다.

| 확인 항목 | 실제97 결과 |
| --- | ---: |
| 원 현재/다음 포함 계약 | 1278 |
| 전후 각 입력 수/bytes | 1597 / 119944363 |
| Frame/registry | COMMITTED / 해제 |
| held regular/directory identity | 1597 / 308 |
| 잠금 opened/closed/remaining | 1905/1905/0 |
| duplicate opened/closed/remaining | 3194/3194/0 |
| Native reservation / metadata checks | 5099 / 7004 |
| 준비 reads / bound=fresh / bytes | 610 / 233 / 69996311 |
| 후속 reads / bound=fresh / bytes | 2 / 1 / 380414 |
| 원 CPU 표본 수 | 892 |
| 시스템CPUmax / 검증 CPUmax | 67.43% / 6.023801% |
| 검증 private max | 57741312bytes |
| 가용RAMmin | 18.579434% |
| 원 Job active / CPU total / private peak | 0 / 8.281초 / 37.82MiB |
| Native 획득 완료 elapsed | 138.164604초 |
| Native parent 종료 / release 직전 elapsed | 406.814738 / 407.032876초 |
| 원parent elapsed | 268.61초 |
| STOP / cleanup | null / 확인 |

original_two_actual_byte_boundaries, shared offset reset3194, pathname reopen0, 잠금/duplicate/stream/binding 잔여0·원 Job active0를 원 validator로 확인했다. 준비+후속612 reads는 공유720 이내다. 원Native/IO600, CPU98%x4/기존90/95 대기, RAM hard8%/soft7% 및 가용RAM/commit, Job6.25%/affinity1/BelowNormal/최대16/kill-on-close/no-breakaway를 유지했다. 초기 실패와 달리 이번 실행은 과부하 STOP 없이 닫혔지만 원인 해결/인과적 성능 개선은 미확정이다.

종료 후 root/body SHA·길이, 고정 compiled inventory249/원P212 legacy plan, 원 전체 record/Native/Job/metadata/queue validators 및 현재34 추가 source/test/preimage pin/AST를 확인했다. 원 수용90 목록에 선택된97 이름 한 개만 추가해91/다음98/잔여158(152+6)/whole대기88을 재계산했다. 이 문서 검토에서 전체1597 소스/제품을 다시 실행한 것이 아니다.

## 불변 증거

repository root 기준 경로다.

| 경로 | bytes | SHA256 |
| --- | ---: | --- |
| implementation/p09/evidence/locked-r07/p282-case-097-run004.v1.json | 145146 | 934136216dedefeb8e6148665c72e16a7bb91013499c7be19a1ccb48346fe551 |
| implementation/p09/evidence/locked-r07/p284-light-run001.v1.json | 6526 | a7f54e2bb991b4b9f803ef25dc7723bed609d457986235bb6de5d1dee81c51ea |
| implementation/p09/evidence/locked-r07/p285-light-run001.v1.json | 49510 | bc9dfa8cca08e65be4210c4bb345a0cc96829d23bfabcb2962494461bf4b51eb |
| implementation/p09/evidence/locked-r07/p285-case-097-run002.v1.json | 651680 | c3a30dbab87698fd605a40a18c3926777b1382dc392bc2b8683ad238a11b90a6 |
| implementation/p09/evidence/locked-r07/cases/p285-case-097-run002.json | 190207 | 2550d3d6dbd93378054d3b1d2fac1364e5be6b69fdc5e7098574f69e29b1276a |
| tools/p09/resume_post97_stop_runtime.py | 37570 | 4cde33b63c7a72e3788a6a781bd4ec8c749d1f7d6c72cbffb3f8588659edbdfb |
| tools/p09/tests/test_post97_stop_runtime.py | 10595 | 2c30f776a3eac749331fabd45c60264d0300460490ffa05b3b50dbf6456a183d |
| tools/p09/resume_no_work_deferral_runtime.py | 38204 | e637d4af60423ddbfde7165a1b83caf778fb62b3bbdeb7fc695795cbb5464267 |
| tools/p09/tests/test_no_work_deferral_runtime.py | 14756 | 2084e58009f57dddbababf5dd62ad78f9c6c18c8855849c2e1684bf39d8816ed |

## 다음 경계

목표 ACTIVE. 다음은 같은 불변 P285 실행기의 actual run003에서 미실행98번 한 건이다. 원 수용 기록 검토·현재/다음1278 계약·전체1597/ancestor308·원600/720 및 모든 보호를 유지한다. 실제 CPU STOP/부분 IO/제품 실패 시 해당 단계·코드를 다시 검토하고 즉시 반복하지 않는다. 보호된 reader 생성 전 무작업 admission 보류만 원 실패를 보존한 엄격한 review 후 같은 코드의 새 run에서 다시 원 admission을 받을 수 있다. 통과 본체 재실행·접근허용 실행·P09 Gate 미완료 상태의 P10 진입은 하지 않는다. 문서 r114 원byte suffix/별도archive를 보존한 r115 갱신은 whole/Gate 수용이 아니다.
