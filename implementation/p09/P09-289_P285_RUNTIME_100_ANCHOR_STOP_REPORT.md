# P289: 실제100 수용과 후속 부분 anchor CPU STOP 검토

2026-10-09. 목표 ACTIVE. runtime 부분집합 수용94/249, 잔여155(일반149+corpus6), 다음index101, whole 재조정대기91, 독립source 마감대기0. P09·A12·A13 OPEN. 이 수치는 P09 전체 완료율이 아니다. whole1470/historical67/full249/signed16/제품 완료/PC 프리즈 해결은 미확정이다.

## 실행 범위와 원 조건

현재 P285 코드·test와 현재34 추가 source/test/preimage pin을 변경하지 않고 actual run005의100번을 직렬 실행했다. 이전99와 새100의 root/body SHA·길이 및 원 full record/Native/Job/metadata/queue 조건을 검토했다. 통과한 제품 본체를 재실행하지 않았다. 후속 actual run006은 reader anchor에서 중단되어101 선택·계약·Frame·Job·제품 본체에 도달하지 않았다. 두 시도 모두 CPU/RAM 보호를 유지했고 즉시 재시도·자동 재시도 loop는 없다.

원 Native20/획득14/metadata32/byte binary1·other2MiB/s, 원 CPU98%x4·기존90/95 완화, RAM hard8%/soft7%/가용RAM·commit, Native/IO600·공유metadata720, Job6.25%/affinity1/BelowNormal/최대16/kill-on-close/no-breakaway·원 전후byte/identity/정리 조건은 유지됐다. 접근허용·한글 UI·빌드·Git·설치·OS/Defender/WSL 설정 변경은 하지 않았다.

## 실제100: exact1 수용

| 항목 | 원 관측 |
| --- | ---: |
| root | PASS_EXACT_R07_NO_WORK_DEFERRAL_RUNTIME_NOT_WHOLE_OR_GATE |
| 제품 본체 | PASS_SCOPED_NOT_GATE, tests1 |
| 현재/다음 포함 계약 | 1278 |
| 수용 / 다음 | 94 / 101 |
| 전후 각 입력 수 / bytes | 1597 / 119944363 |
| Frame / held regular / directory | COMMITTED / 1597 / 308 |
| 잠금 opened / closed / remaining | 1905 / 1905 / 0 |
| duplicate opened / closed / remaining | 3194 / 3194 / 0 |
| shared offset reset / pathname reopen | 3194 / 0 |
| Native reservations / metadata checks | 5099 / 7004 |
| 준비 reads / bound=fresh / bytes | 622 / 239 / 75033049 |
| 후속 reads / bound=fresh / bytes | 2 / 1 / 377022 |
| 원 CPU 표본 | 897 |
| 시스템 CPU max / 검증 own CPU max | 90.43% / 6.110422% |
| 검증 private max / 가용RAM min | 57016320bytes / 16.703642% |
| 원 Job active / CPU total / private peak | 0 / 9.047초 / 31.43MiB |
| 제품 parent elapsed | 267.29초 |
| Native 획득 / parent 종료 elapsed | 138.048486 / 405.370333초 |
| 원 Guard 첫 오류 / STOP / watcher cleanup | null / null / 확인 |

원 두 byte 검증·held identity·닫힌 모든 lock/duplicate·원 Job active0을 원 record validator가 검증했다. 준비+후속624 reads는 공유720 이내다. 고정 compiled inventory249·P212 legacy plan pin으로 runtime plan을 재계산했고100 prior plan은99 final plan과 일치했다. 수용 이름은 이전 목록에 선택한 이름 한 개만 추가됐다. 현재34 추가코드/원보존 preimage는 SHA·길이/AST로 재확인했다. 이는 저장된 결과 검토이며 전체1597 source나 이전 제품 본체를 다시 실행한 것은 아니다.

## 후속 run006: 부분 anchor CPU STOP, 미수용

root는 FAILED_NOT_ACCEPTED이며 error/resource_stop_reason은 STOP_SUSTAINED_SYSTEM_CPU이다. failure_diagnostic.stage=anchor, exception_class=ValueError. 원 실행은 선택 전 anchor에서 중단됐다. selected test/index·prior/runtime plan·실행 계약 수·Frame·parent·Job·본체 pin/path 필드가 없고 actual_product_child_executed=false, accepted_exact_product_body_count=0이다.101번 본체 파일도 없다. Job/Native 측정이 없는 이 시도에0 값을 만들어 넣지 않았다.

| 항목 | 중단 관측 |
| --- | ---: |
| 준비 reads / bound / fresh / bytes | 164 / 151 / 0 / 26618671 |
| 준비 finished | false |
| entry 호출 / 완료 / 실패 / binding active | 164 / 163 / 1 / false |
| 원 CPU 표본 | 43 |
| 시스템 CPU max / own CPU max | 100% / 1.757812% |
| own private max / 가용RAM min | 55926784bytes / 22.691630% |
| 원95 pause entries / windows / requested | 1 / 6 / 3초 |
| early90 통계 | entry0 / window0 |
| watcher cleanup | 확인 |

마지막6 표본의 own CPU와 읽기 bytes 증가량은 모두0이다. 시스템 CPU는97.85,91.99,100,100,100,100%였다. 원 decision을43 표본 전부에 다시 적용해 마지막4 연속100%에서 같은 STOP이 발생하는 것을 확인했다. 시스템포화·검증 자체 CPU·읽기량을 구별한다. 외부 PID/물리IO/검증이 다른 프로세스를 유발했는지까지의 인과성은 미확정이다.

early90 통계0을 미연결로 해석하지 않는다. byte와 entry가 같은 기존 early 객체에 연결된 pin/summary를 확인했다. EarlySourceCheckpoint는 원95 base를 먼저 호출하며, 원95 대기 중 hard STOP이 예외로 올라왔으므로 outer90 통계 증가 전에 종료됐다. base 우선순위를 바꾸거나 원 hard STOP을 억제하지 않았다.

엄격한 admission-only no-work validator에 이 root를 넣으면 원 예외로 거부되는 것을 확인했다. 부분164 reads를 무작업으로 재분류하지 않는다. 실패는 FAILED 상태·원 byte를 보존하며 누적 수용/큐를 바꾸지 않았다. 따라서 같은 P285를 바로 다시 호출하지 않는다.

## 중단에 연결된 코드 검토와 최적화 판정

원 실제100 source_freeze pin과 다음10 파일의 길이/SHA/AST를 맞추고 관련 경로를 직접 읽었다.

- audit_evidence_io.py / weighted_audit_io.py:64KiB chunk·bounded64 pacer 시도·sleep·no-idle-burst. 현재 byte율은 원 live1/2MiB/s이다.
- near_saturation_read_backpressure.py / review_checkpoint_queue_stop.py:원95·early90 모두0.5초 sleep, 최대8 window, 원 guard 먼저 호출. 무한 busy loop가 아니다.
- qualify_early_metadata_pressure.py / qualify_metadata_entry_early_pressure.py / metadata_read_entry_pacing.py:원 reader·entry32/s·같은 byte/entry early객체·clock/counter 유지. STOP 후 binding 복원에는 checkpoint/sleep을 붙이지 않는다.
- live_sql_evidence_reader.py / sql_percentage_resources.py:600초 IO/기존 sampler 공유·0.5초 debounce·최대1440 표본. hot counter를 여러 sampler로 증폭시키는 새 경로는 없다.
- resume_no_work_deferral_runtime.py:부분IO STOP 거부·FAIL 보존·선택/제품 이전 단계·finally 정리·terminal-only 기록 조건을 확인했다.

이번 실패에서 검증 자체의 무한 루프·중복 sampler·무제한 allocation·재시도 폭주를 확인하지 못했다. 마지막6 자체CPU0/읽기0라는 관측은 검증 hot loop에 대한 직접 근거가 아니며, 외부 원인 또는 PC 해결을 증명하지도 않는다. 따라서 원 수용된 source를 임의로 재작성하거나 속도/보호/검사를 근거 없이 바꾸지 않았다. **이번 STOP에 근거한 새로운 실행 코드 최적화는 없다.** 이는 전 저장소의 모든 최적화가 끝났다는 뜻이 아니다. 이전 획득14/s·작은metadata entry32/s·byte1/2MiB/s·중복 callback 연결수정·무작업 보류의 제한적 불변 재사용은 유지했다.

누적 증거 reads가 사례당4씩 증가하는 경향(98:614,99:618,100:622)은 다음 재개 설계에서 검토할 실제 비용이다. 현재624/720은 통과했으며, 향후 cap에 맞추려고 검사/원 fresh·과거 실패 evidence를 삭제하거나720을 올리지 않는다. 재개 후보는 이번 부분 STOP을 명시 검토하고 원 큐·실패 미수용·모든 입력/원 fresh/동일 guard를 보존하는 qualification을 먼저 거쳐야 한다.

별도 inline 읽기검토 초기에 packed body를 plain으로 다룬 KeyError가 있었다. 검토 스크립트만 원 packed codec으로 바로잡아 검토를 완료했고 root/body/source·실행 결과는 변경하지 않았다.

## 불변 증거

| repository-relative 경로 | bytes | SHA256 |
| --- | ---: | --- |
| implementation/p09/evidence/locked-r07/p285-case-100-run005.v1.json | 653224 | 076ced0a53fe6924dd9616a4d03668e734dd7fbc200e0ba4d0cb743502508eb0 |
| implementation/p09/evidence/locked-r07/cases/p285-case-100-run005.json | 188511 | 25917131612934b478d4fa1718d2d3a81ab0387d6ac60261c02a7adeed6fff4a |
| implementation/p09/evidence/locked-r07/p285-admission-run006.v1.json | 72149 | b842f81632e76d748314aec90ef5dad2b69208240b783a15f66b9b79c1f0ecb7 |
| tools/p09/resume_no_work_deferral_runtime.py | 38204 | e637d4af60423ddbfde7165a1b83caf778fb62b3bbdeb7fc695795cbb5464267 |
| tools/p09/tests/test_no_work_deferral_runtime.py | 14756 | 2084e58009f57dddbababf5dd62ad78f9c6c18c8855849c2e1684bf39d8816ed |

## 다음 경계

목표 ACTIVE. 미실행 다음101은 그대로 유지한다. 다음 단계는 새 부분 anchor STOP의 명시적 재개검토/qualification이며 같은 P285 즉시 재시도나 passed body 재실행은 하지 않는다. source/test/새 generation 변경은 이번 턴에 없다. 전체 범위 및 원600/720·CPU/RAM·Job/전후byte/identity/정리를 유지하고, CPU 보호가 다시 작동하면 그 단계의 원 관측과 코드를 먼저 검토한다. 접근허용은 제외하며 P09 Gate가 닫히기 전 P10에 진입하지 않는다.

상태 문서 두 개는r116 원 byte와 별도archive를 보존해r117로 갱신한다. 문서·저장된 pair·지원 코드 검토는 whole/Gate 수용을 대신하지 않는다.
