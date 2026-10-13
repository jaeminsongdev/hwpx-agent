# P09-295~297 독립 source 마감과 STOP 검토

작성일: 2026-10-09. 목표 ACTIVE. P09/A12/A13 OPEN.

## 현재 판정

- 실제 runtime 수용은 94/249, 잔여155(일반149+corpus6), 다음 미수용 index101, whole 재조정91 그대로다.
- 101 제품 본체는 원 P291에서 terminal1 PASS/exit0 후 최종 source 단계가 중단됐다. 원 root FAILED/body STOPPED/zero placeholder와 부분474 읽기는 보존한다.
- 이번 독립 source 검사도 source_acquire에서 STOP. 새 runtime 수용은 0, 독립 source 마감 후보101 하나가 미완료다.
- synthetic27/22/14 PASS는 준비·판정 지원 증거다. 전체 source/Native/runtime/Gate PASS가 아니다.

## 적용한 작업

원 본체를 재실행하지 않는 별도 마감 경로와 정확한 결합 판정을 새 파일로 구현했다. 원1599 입력 및 검토/보존 prototype/새 마감·결합 코드18개를 합친1617개(120176339 bytes), ancestor308 전체를 대상으로 두 실제 byte 읽기·Native identity·정리를 요구한다. 마감이 실제 통과해야 별도 compound로 단 한 사례를 수용할 수 있다. 현재 실패 receipt에는 compound를 실행하지 않았다.

획득14회/초, global/byte Native20회/초, metadata32회/초, binary1/other2 MiB/초, original600초·720read·CPU98x4·RAM비율·Job 제한을 유지했다. 재사용한 sampler는 하나이며 별도 sampler/빌드/Git/한글/접근허용/OS 보안 설정 변경이 없다. 원 완료 본체와 기존 PASS 사례를 다시 실행하지 않았다.

새 STOP 검토는 원 실패 receipt의 전체 표본을 보존하고 제한된 수치만 별도 요약한다. 큰 원 로그를 새 review마다 복제하지 않는다. 이 요약 최적화가 PC 프리즈를 해결했다고 주장하지 않는다.

## 실제 source STOP

receipt: `implementation/p09/evidence/locked-r07/p295-r4-case101-source-actual-run02.v1.json`
300662 bytes / SHA256 `e19a2c8cbef7a83953fc68b83952700e204235e11a7fe571c5d6ef51bea9fd04`.

- 준비26개 입력의52read/3535114 bytes/fresh26은 완료; source_acquire 10.482585999998264초에서 STOP.
- guard2063회는 원 ancestor 입력1617개와111 Native 획득·pacer/checkpoint 경로에 대응한다. 검사를 제거하지 않았다.
- 잠금111 opened/111 closed/remaining0; Frame CLOSED/등록해제, reader/stream0, 실제 byte boundary0, product 실행0.
- 표본29: 시스템 CPU최대100%, 검증 own CPU최대2.111324%, private최대33923072 bytes(약32.35 MiB), working set최대44093440 bytes(약42.05 MiB), 가용 RAM최소23.494607605443335%.
- 마지막4개 시스템 CPU100%, own CPU0%, 논리 read 증가0; early90 대기5window/2.5초. 보호 정상 STOP과 cleanup 확인.
- 따라서 검증의 직접 연산이 시스템 포화를 일으켰다는 증거는 없다. Native open의 간접 영향/다른 프로세스 등은 배제하지 않았다. 원인 확정 및 프리즈 해결은 FALSE다.

## 관련 코드 재검토

`locked_runtime_inputs.py`: ancestor set 재사용으로 반복 상위 순회 방지; bounded acquire·no burst OpenPacer의 양수 sleep; cleanup은 guard/pressure와 분리.
`near_saturation_read_backpressure.py`와 `review_checkpoint_queue_stop.py`: 기존 마지막 표본만 참조; 0.5초 대기·최대8window; 원 hard guard 먼저 실행; 무제한 busy loop 없음.
`sql_percentage_resources.py`: sampler 하나, 표본 예산1440, watcher 없는 수동 sampling은0.5초 간격; checkpoint 호출마다 Native CPU query를 새로 수행하지 않음.
`build_current_issuer_probe.py`: 원 표본 freshness 확인 유지, 별도 sampler 없음.
`qualify_rejected_parent_connection_r2.py`: 추가 시계 읽기는 phase 경계/첫 예외만; 원 lock guard 매번 유지.

현재 자료에서 추가 hot-loop·무제한 할당·중복 sampler 결함은 확인되지 않았다. 실제 own CPU0인 STOP 직전에 불필요하게 rate/guard를 완화하거나 근거 없는 최적화를 하지 않았다. 전 코드 최적화 완료나 외부 원인 확정은 주장하지 않는다.

## 검증 및 보존한 실패

- R4 preparation27 PASS, receipt `p295-r4-case101-source-light-run01.v1.json`.
- compound22 synthetic PASS, `p295-r4-compound-synthetic22-run01.v1.json`. 별도 원 pin 배열 deep-copy로 인위적인 fixture alias를 제거해 controller drift 거부조건까지 검증했다. 실제 코드/증거에는 이 합성 자료를 수용하지 않는다.
- 실제 R4 source STOP의 정확한 검토14 PASS, `p297-r2-case101-source-stop-review-run01.v1.json`. 새 product/Native 실행 없음.
- 첫 preparation 실패: sampler flag 이름의 테스트 오타; R2는 byte 상수의 잘못된 기계적 치환; R3는 역사적 error literal까지 치환된 비교 오류. 모두 Native 시작 전/CPU STOP 아님. 각 실패 및 원 prototype12 파일을 보존하고 새 R4 경로로 수정.
- 첫 P297 review는 STOP 자료에 준비 PASS validator를 적용해 올바르게 거부됐다. `p297-case101-source-stop-review-run01.v1.json`와 원 reviewer 파일 보존; R2는 실제 STOP 상태 그대로 exact 범위/정리/수치만 검사한다. 실패를 PASS로 바꾸지 않았다.
- terminal지원 결과들은 합성/검토 전용이며 actual source 마감이나 새 runtime 수용으로 승격하지 않는다.

## 다음 경계

현재 actual source receipt는 실패로 고정되어 있다. P296 R4는 그 경로의 실제 PASS를 요구하므로 실행하면 수용될 수 없다. 같은 receipt 재시도/덮어쓰기나 원101 제품 재실행을 하지 않는다. 안전한 다음 단계는 검토·관측을 반영한 새 세대의 source-only 경로 qualification 및 실제 두 full-byte/identity 마감이다. 실제 마감 성공 뒤 새 exact compound를 검증하고95/next102로 한 번만 전진할 수 있다. 목표는 ACTIVE지만 이 조건은 아직 미달이다.
