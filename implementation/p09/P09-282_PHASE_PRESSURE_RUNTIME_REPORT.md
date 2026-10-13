# P282: 최신 CPU STOP 검토 후 전체1593 연결·실제95/96 수용

2026-10-09. 목표 ACTIVE. 실제 runtime 수용90/249, 잔여159(일반153+corpus6), 다음index97, whole 재조정대기87, 독립source 마감대기0. P09·A12·A13 OPEN. 90/249는 개별 runtime 부분집합이며 P09 전체 완료율이 아니다. 전체249/signed16/whole1470/historical67/제품 완료/PC 프리즈 해결은 미확정이다. 접근허용·한글 UI·빌드·Git·설치·Defender/WSL/OS 설정 변경 없음.

## 중단 검토와 재개 조건

직전 P280 light는 anchor에서 CPU STOP으로 끝났고 본체·Native Frame·원parent·Job 호출 전이었다. 같은 namespace를 즉시 반복하지 않았다. 관련 callback/pacer/parse 한도/기존 sampler의 debounce/정리 코드를 검토했다. 확인된 cached entry95 callback 보완은 P279에서 이미54 계약과 실제 reader29 fresh를 통과했으며, P280 실패에서도 entry/byte 공통90 선택은 확인됐다. 원95 base가 먼저 호출된 다음100% 표본에서 원guard가 중단한 것이다. 이번 재개는 추가 CPU 보호 완화나 근거 없는 성능 수정을 적용한 재시도가 아니다.

새 실행 전 기존 자원 observer의 admission만 확인했다. 별도 reader/Frame/Job/제품 본체/새 sampler thread 없이3 표본 CPU6.79/1.90/4.18%, STOP null, cleanup 확인, 가용RAMmin21.448875%였다. 이것은 당시 시스템 상태의 변화일 뿐 지속 안정성이나 원인 해결을 보증하지 않는다.

P282는 최신 원P280 STOP을 고정 길이/SHA와 단계·partial fresh·공통 callback·정리·원CPU 표본으로 검토한다. 원 실패는 미수용으로 유지하고 본체 미실행을 확인한다. 원P280 코드/테스트와 원28 추가입력을 보존하며 새 실행기/테스트2개만 추가한다. 원1563+30=1593, extras126, ancestor308. 원 보호/byte/identity/Job/clock/counter와 최신 STOP을 제거하지 않는다.

## 전체 연결 사전검증

P282 light run001은 원870 계약을 실제로 실행하고 현재60+다음60을 추가하여990을 통과했다. 원P280에서870을 실행했다고 소급 주장하지 않는다. IO524 reads/221 bound 및 최종fresh/65,092,872bytes, STOP null, watcher cleanup 확인. 전체1593의 원Native20/획득구간14/metadata32/byte binary1·other2MiB/s 선택과 추가파일 예산을 검증했다. 예측577.9352378300258초 < 원600초는 완료 보증이 아니며 보호 시간을 연장하지 않았다. 사전검증은 Native 전체 두 byte boundary 또는 제품 runtime 수용을 대신하지 않는다.

사전검증86 표본의 시스템CPUmax25.33%, 검증 CPUmax6.040128%, private56,373,248bytes, 가용RAMmin20.153328%. 이때 제품 본체는 미실행이었다.

## 실제95·96: 각각 한 건 수용

두 실제 실행은 같은 불변 P282 코드로 직렬 실행했다. 기존 통과92/93/94 본체와 새 통과95 본체를 다시 실행하지 않았다. 96 선택 시95는 저장된 root/body의 binding/전체 Native/Job/정리/큐 조건만 검토했다. 각 실제 실행에서 현재/다음990 계약을 유지했다.

| 항목 | 95 run002 | 96 run003 |
| --- | ---: | ---: |
| 제품 본체 | PASS_SCOPED_NOT_GATE, 1개 | PASS_SCOPED_NOT_GATE, 1개 |
| root | PASS_EXACT_R07_REVIEWED_SHARED_ENTRY_RUNTIME_NOT_WHOLE_OR_GATE | 같은 상태 |
| 수용 runtime 부분집합 | 89/249 | 90/249 |
| 다음index | 96 | 97 |
| 전후 각 입력 | 1593 / 119843238bytes | 1593 / 119843238bytes |
| Frame | COMMITTED / registry 해제 | COMMITTED / registry 해제 |
| 잠금 opened/closed/remaining | 1901/1901/0 | 1901/1901/0 |
| duplicate opened/closed/remaining | 3186/3186/0 | 3186/3186/0 |
| Native reservations / metadata checks | 5087 / 6988 | 5087 / 6988 |
| ancestor walk / held directory identity | 307 / 308 | 307 / 308 |
| 준비 reads / bound=fresh | 526 / 222 | 530 / 224 |
| 준비 bytes | 65186156 | 66838362 |
| 후속 reads / bound=fresh / bytes | 2 / 1 / 371630 | 2 / 1 / 372238 |
| 기존 CPU 표본 수 | 864 | 868 |
| 시스템CPUmax | 34.77% | 45.16% |
| 검증 프로세스CPUmax | 6.031064% | 5.979553% |
| 검증 private max | 55832576bytes | 57126912bytes |
| 가용RAMmin | 19.426511% | 18.911553% |
| 원 Job active / CPU total | 0 / 2.984초 | 0 / 3.078초 |
| 원 Job private peak | 24.88MiB | 28.87MiB |
| 원parent 실행 구간 elapsed | 258.77초 | 258.77초 |
| Native 획득 완료 elapsed | 136.236838초 | 136.401553초 |
| Native parent 종료 elapsed | 395.040092초 | 395.207754초 |
| STOP / watcher cleanup | null / 확인 | null / 확인 |

전후1593 byte 확인, 동일한 held regular1593/directory308 identity, share offset reset3186, 바이트 pathname 재open0, remaining lock/duplicate/stream/binding0, 원 Job active0와 소유 작업 트리 종료를 확인했다. 원 byte reads·hash·identity 범위를 줄이거나 첫 pin을 최종fresh로 대신하지 않았다. 준비+후속 metadata 각각528/532 reads로 공유720 한도 이내였다.

획득1901회는 기존 단일 pacer에서14/s로 완료하고 성공 후 원20/s로 복구했다. clock/previous/credit/reservation counter 초기화·추가 sampler·guard/cleanup 변경은 없었다. 원 잠금/IO600초, RAM hard8%/soft7%, 가용RAM/commit 기준, CPU98%x4 STOP 및 기존 조기90/95 보호, 원 Job6.25%/affinity1/BelowNormal/최대16/kill-on-close/no-breakaway를 유지했다. 모델상 획득 밀도30% 감소가 실제 전체 경로에 연결됐음을 두 실행에서 확인했지만 CPU 개선의 인과관계나 프리즈 해결을 입증하지는 않는다.

종료 후 root/body 길이와SHA, 원 Native pair·Job·early·metadata 연결 validators, 각30 추가 source/test/preimage pin 및 Python AST를 재확인했다. 고정 compiled inventory249와 원P212 legacy plan의 길이/SHA를 확인하고 원 전체 record/queue validator로95→89건/다음96, 96→90건/다음97을 재계산했다. 각 큐는 이전 accepted name 목록에 선택된 이름 한 개만 더했고96 prior plan이95 final plan과 같았다. 현재 전체1593 소스를 다시 읽는 새로운 runtime 검증을 수행한 것은 아니며, 종료된 실제 전후 byte 증거와 현재30 추가코드 pin의 일치 검토다.

## 불변 증거

모든 경로는 repository root 기준이다.

| 경로 | bytes | SHA256 |
| --- | ---: | --- |
| implementation/p09/evidence/locked-r07/p280-light-run001.v1.json | 16577 | 97ca3589b715c599861b707dd1d584377041f4fc69afbc5aacde9b57c4baf4c3 |
| implementation/p09/evidence/locked-r07/p282-light-run001.v1.json | 46642 | e8f6e7a4ea7b15a35a92dc484614bc0e339e33c240ee192181925f6c77556e4e |
| implementation/p09/evidence/locked-r07/p282-case-095-run002.v1.json | 640288 | a9b1661b2d81e12b123b20d0c269c79dc7c11019baa297fe46363b6aa046c587 |
| implementation/p09/evidence/locked-r07/cases/p282-case-095-run002.json | 185815 | 42d6dc174a334118c558b00336a86352fcef42cefda3d2f4db46f0ac2c764c43 |
| implementation/p09/evidence/locked-r07/p282-case-096-run003.v1.json | 641320 | 0c748d7f03e0e8c15f07267b26427ab48fead4401b7819b3febda6cafb489e97 |
| implementation/p09/evidence/locked-r07/cases/p282-case-096-run003.json | 186119 | 01183a3a0a82693775e3f2990618fcb3f09f51afe135620d8fb3965e071de253 |

실행기 `tools/p09/resume_reviewed_shared_entry_runtime.py`: 35239bytes, SHA ded2e00a4cf64564928e02a9ca34f63bf7431195495a9b7a57e39eba32a2a9a3. 테스트 `tools/p09/tests/test_reviewed_shared_entry_runtime.py`: 10311bytes, SHA 55535107ba5795161dfe03c0f9bd5bb53a68aba397d13ceaf7e8b7192638da24. 실행/수용 코드와 원 실패 receipt를 이후 수정하지 않는다.

## 다음 경계

목표 ACTIVE. 다음은 같은 불변 P282 실행기의 미실행97번 한 건이며, 기존 수용 root/body의 원 전체범위·큐 조건과 현재/다음990 계약을 검토한 후 동일한 원 보호로 직렬 실행한다. metadata720/원600/정확한 전체 입력·ancestor 예산을 벗어나면 수용하지 않고 해당 단계부터 검토한다. CPU STOP 시 즉시 반복하거나 guard를 완화하지 않는다. 통과 제품 본체 재실행, 접근허용 실행, P09 Gate 미완료 상태의 P10 진입은 하지 않는다. 문서 r113 원byte suffix/별도archive를 보존한 r114 갱신은 제품/whole/Gate 수용을 대신하지 않는다.
