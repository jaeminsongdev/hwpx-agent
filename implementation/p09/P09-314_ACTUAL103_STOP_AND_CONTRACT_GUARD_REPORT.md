# P314~P315: actual103 CPU STOP 검토와 계약검사 보호 연결

날짜: 2026-10-09. 목표 ACTIVE. 제품 수용이나 P09 Gate 완료 보고가 아니다.

## 현재 수용과 실행 경계

- 수용 96/249, 미수용 153(일반147 + corpus6), 다음103.
- whole 재조정93, source 마감 미완료 후보0. P09/A12/A13 OPEN.
- 수용102의 기존 본문·Native 경로는 재실행하지 않았다. metadata typed classifier로만 96 상태를 재계산했다.
- 원 P312 r3 소스·테스트·light·102 PASS·103 실패는 수정하지 않았다. 실패를 PASS로 재분류하지 않는다.

## actual103 정확한 중단

원 실행: `python -B tools/p09/resume_completed101_compound_runtime_r3.py --mode actual --run 3`.

- `final_fresh_preparation`에서 `STOP_SUSTAINED_SYSTEM_CPU`. 실제 실행 exit2; 외부 PowerShell의 exit0은 제품 성공이 아니다.
- 기존 계약230 완료. metadata109읽기/10,717,316bytes/98bound/최종fresh11, 미완료.
- Native Frame 생성 전이다. Native handles=0이라는 측정값을 만들지 않고 NULL/미시작으로 보존했다.
- Job/제품/body/실패 sidecar 미시작·없음. 수용 증가0. watcher 정리 TRUE.
- 기존 표본22; 전체 CPU 최대100%, 자체 최대5.303584%, private50,900,992bytes, 가용 RAM 최소21.641644%.
- 마지막4표본은 전체100%, 자체CPU0%, 감사 대상 논리읽기 증가0이다. 물리 디스크 I/O 전체가0이라는 뜻은 아니다.
- inner90 보호는 1회 진입, 4개 대기창/2초 대기. 기존 hard guard가 지속 포화에서 STOP했다. 기존 callback 복원 확인.
- 이 실패는 대기 콜백의 busy-spin 또는 own CPU100%를 입증하지 않는다. 98x4/RAM/600/720 기준을 완화할 근거가 아니다.

원 root: `evidence/locked-r07/p312-case-103-run003.v1.json`
88,058bytes, SHA256 `aa0abde2db6cca5f36cd20c6e87be162ade9bf1a1f96841cd5eba54a5fc451cc`.

## 별도 process CPU 창

원 실행 전후 PerfProc snapshot2개, 23.419691초 창. 원 sampler/guard에 이 값을 공급하지 않았다.

- Idle-derived host busy40.033601%; MsMpEng 평균21.132724%; System3.894626%.
- Git2개 관측 구간 평균0%. 검증 Python은 구간 내 생성·종료해 두 endpoint 비교에서 빠지므로 자체CPU0으로 꾸미지 않는다. 자체 peak는 위 원 sampler 표본을 사용한다.
- before365/after372행, 비교360, identity drift1 제외, 종료2/새9.
- Defender의 유의미한 CPU 기여가 관측됐다. 이는 순간100% 단독 원인, 검증이 Defender를 유발했다는 인과, PC 프리즈 원인·해결의 증거가 아니다.
- Defender/WSL/OS 설정, 제외 규칙, 프로세스 종료는 하지 않았다.

원 packet: `evidence/locked-r07/p314-actual103-perfproc-before-after-raw-run01.v1.json`
254,917bytes, SHA256 `f74ded0bdc96804b740358d028d62ad7cbaaeba41ce6bd14972b925a280466fe`.
비밀값·명령줄·전체 로그를 보고에 포함하지 않는다.

## 검토 결과와 구현한 개선

P312 `contracts()`는 기존 원30 + leading18 + inner30 + current76 + following76을 동기 묶음 실행한다. 각 unittest의 setUp/tearDown 경계에서 원 checkpoint를 직접 호출하는 연결이 없어 보호 신호가 발생한 묶음의 중단 응답성이 제한될 수 있다. 이번 실패 지점은 계약검사 이후 fresh 단계이므로 이 누락을 이번 포화의 원인으로 단정하지 않는다.

새 `tools/p09/resource_guarded_contract_suite.py`:

- 각 검사 setUp 전, tearDown 후 원 callback 확인.
- 각 runner 진입·정상 반환 시 원 callback 확인. STOP은 다음 테스트로 넘기지 않고 호출자에게 전파.
- 기존 unittest 결과, failures/skips/failfast/custom result 유지.
- 성공/오류/CPU STOP/KeyboardInterrupt 모두 원 TextTestRunner 복원. 중첩·다른 runner 교체는 거부.
- 새 thread/sampler/프로세스/무조건 sleep, 새 자원 기준, 검사 제외, source 읽기 생략 없음.
- callback은 기존 Reader의 보호·bounded90 냉각 경로를 그대로 사용한다. 실제 guard가 대기할 수는 있으나 새 실행기가 별도 sleep을 추가하지 않는다.

새 테스트21개 PASS. 실제 원230개 모두 원 Reader checkpoint 연결로 1회 수행: 시작/종료230, 전후 보호확인 각각230, runner5개 전후확인5. 총 실제251계약검사 PASS. 원1486/PerfProc24를 이번 실행횟수로 합산하지 않았다.

Qualification의 metadata100bound=최종fresh100/200읽기/13,408,678bytes/정리TRUE/STOP없음. 기존 Native/제품 workload는 실행하지 않았다.

Qualification: `evidence/locked-r07/p315-guarded-contract21-and-existing230-qualification-run01.v1.json`
48,227bytes, SHA256 `c85cfc594f6401adbea4e11be5e40d5d12a0a6c023bb7f8995d9bdc036d537b3`.

## 미완료와 다음 단계

- 새 helper는 위 계약검사 qualification에만 연결했다. 제품 runtime 연결, full-source Native 포함, actual103 성공은 NOT_RUN이다.
- 기존 code77은 수용102 Native 범위로 닫혔다. 새 helper/test2는 metadata qualification일 뿐 기존77의 Native PASS를 확장하지 않는다.
- 다음 새 runtime은 103 실패 root, 수용102, P315 qualification, current77 + 새 실행기 코드를 정확히 바인딩해야 한다. 기존 실패 P312 namespace에 직접 재시도하지 않는다.
- 연결 시 전체 source 두 읽기/identity, 원 Job/CPU/RAM/600/720, original cleanup을 유지하고 실제 읽기·실행한 계약 수와 재사용 qualification 수를 분리한다.
- CPU 보호가 다시 발생하면 해당 단계/코드/표본/정리를 검토하고 정당한 개선 뒤 진행한다. 통과 본문 재실행과 맹목 재시도 금지.

r124 두 문서 원본은 `evidence/runtime-progress-r124/`에 byte-exact 복사했다. 현재 문서는 r125 prefix 외 이전 suffix를 보존한다. 원본 이동·삭제 없음.

## 추가 마감 확인 실패와 재검토

- P316 run01은 `DEFERRED_ALREADY_SATURATED_SYSTEM`으로 Reader 생성 전 유예됐다. 기존 watcher 정리 TRUE, resource STOP reason은 NULL이다. CPU98x4 STOP과 혼동하지 않는다.
- 부하를 기다린 뒤 한 번 수행한 run02는 typed96/103실패/251qualification/code77+새2/문서 suffix를 읽고 최종 fresh 중 `STOP_SUSTAINED_SYSTEM_CPU`로 중단됐다. 총117읽기/108bound/fresh8, `finished=false`, 정리 TRUE. 따라서 문서 최종 검증 PASS를 주장하지 않는다.
- inner90은 1진입/5대기창/2.5초 대기했고 원hard guard가 STOP했다. 원callback 복원 확인. 현재 마감 script는 별도 원 sampler 관측 summary를 저장하지 않았으므로 이번 마감 중 자체CPU peak를 만들어내지 않는다.
- 관련 traceback의 hard → inner90 → 원95 → outer90 → Reader 경로와 대기·복원을 재검토했다. 추가 busy-spin 또는 정당한 검사삭제 근거를 특정하지 못했다. 보호 완화나 동일 마감 검증의 반복을 하지 않는다.
- `p316-r125-status-final-fresh-stop-run02.v1.json`: 77,763bytes, SHA256 `743106b144a8c2f44c73c5491a15728cbb16847f8252b569f7a2f090e3268de8`. 불변 FAILED 원본이다. 이 실패 이후 보고서·현재문서에 미완료 주의를 추가했으므로 실패 receipt의 당시 문서 pin을 현재 PASS로 사용하지 않는다.
- 새 실행기251 qualification의 독립 PASS는 유지한다. 제품 runtime 연결 및 actual103 수용은 여전히 NOT_RUN. 현재 수용96/249, 목표 ACTIVE. 살아 있는 검증 child/Job/감시 session 없음.

