# P09-348 — source035 CPU STOP, 검증 코드 재점검, Defender 점유 확인

> 후속 P349: 사용자 동의 뒤 관리자 timed capture 실행을 요청했지만 사용자가 승인 버튼을 누를 수 없다고 알렸다. helper 미시작·ETL없음 확인 후 exact owned launcher만 취소했다. Defender 파일/프로세스별 성능 추적은 NOT_RUN이며, P348 관측을 추가 인과 증거로 승격하지 않는다. 세부 P09-349_DEFENDER_UAC_NOT_RUN.md.

날짜: 2026-10-10. 목표 ACTIVE. 검증 실패를 PASS 또는 제품/Gate 완료로 취급하지 않는다.

## 요청과 실제 수행 순서

1. 변경되지 않은 current v17 code2와 review031/730 계약 자격, source034 실패의 exact 해시를 확인했다.
2. 성공 계약을 다시 실행하지 않고 새 closing-source run035를 단 한 번 실행했다.
3. CPU STOP 후 해당 검증 코드와 원 실패 수치를 먼저 점검했다.
4. 그 다음 Defender 상태·검사/업데이트 이벤트·외부 CPU 점유를 읽기 전용으로 확인했다.
5. 관리자 권한이 필요한 검사 대상 추적은 실행하지 않았다. 동일 검증 재시도도 하지 않았다.

## 새 검증 결과

- 명령: python.exe -B tools/p09/resume_preserved106_queue_runtime.py --mode closing-source --run 35 --closing-review-pin '<review031 exact JSON pin>'.
- receipt: evidence/locked-r07/p340-closing-source-run035.v1.json
- bytes 482430, SHA256 0ad8be685abcd1ca91c6f8dfe999a260e8c009a0d2dc3131405b9e9e3aad201e.
- FAILED_NOT_ACCEPTED / STOP_SUSTAINED_SYSTEM_CPU / source_frame_acquire.
- preparation 209bound=209fresh, 418reads, 43,485,170bytes, finished TRUE.
- 계약 실제 재실행0, 기존 current730 자격 재사용. 새 제품 child0.
- 전체1658 입력 프레임에서 디렉터리93개 Native 획득 완료. 94번째 디렉터리 take는 Native open 진입 전에 보호 STOP.
- regular file Native 획득0, 실제 byte boundary0. 전체 source 수용 불가.
- 원93핸들 전부 close, 잔여handle/reader/stream/closefailure0, frame CLOSED, watcher cleanup TRUE.
- 표본78, 시스템 CPU 최대100%, 자체 CPU 최대1.771654%, 자체 private 최대83,484,672bytes, 가용RAM 최소21.255763%.
- 마지막4표본은 시스템100%, 자체0%, 감사 대상 논리읽기 증가0. 전체 물리 디스크 I/O가0이라는 뜻은 아니다.
- PTY29036 terminal exit1. 이후 큐 Python0 확인.

## 1. 검증 코드 재점검

점검 경로: resume_preserved106_queue_runtime.py의 closing_main, AcquisitionInputLocks, MetadataReader,
locked_runtime_inputs.py의 OpenPacer/Native/InputLocks, runtime_input_frame.py의 Frame,
qualify_acquisition_phase_pressure.py, lower_native_acquisition_pressure.py,
native_open_backpressure.py, sql_percentage_resources.py.

- 조상 디렉터리는 이미 방문한 조상 집합을 재사용한다. 같은 조상을 파일별로 끝까지 재순회하지 않는다.
- open pacer는 유한64회, 실제 sleep, no-burst 방식이며 획득 rate14/s·복구20/s를 유지한다.
- watcher는 Event.wait(0.5s), admission은 sleep(0.5s), sampler는 lock으로 직렬화된다.
- 원 CPU/RAM/deadline/identity/two-byte/cleanup 보호는 유지된다.
- 실패 Native inspect93개 합계0.003293초. open 합계7.051355초는 pacing/pressure 대기 포함이다.
- take94는 Native operation 이전에 중단됐다. handle93개 정리와 frame 해제까지 완료됐다.
- 이 검토에서는 새 busy-spin/무한 재시도/미정리 핸들 또는 제거할 수 있는 비싼 중복을 특정하지 못했다.
- 코드나 테스트를 변경하지 않았다. 자체 직접 CPU 풀로드를 입증하는 실패가 아니며, 간접 Defender 유발 가능성은 배제하지 않는다.

## 2. Defender 점검

- 검증 terminal 후 08:17:49 시스템 CPU100%, 해당 큐 Python0 관측.
- 코드 검토 뒤 08:19:55의 약2초 paired raw PerfProc 창: 전체100%, MsMpEng PID20952가85.2%, System4.51%, maple-re3.93%.
- 프로세스별 CPU는16논리CPU로 정규화했다. PID/이름/시작 카운터가 일치하는 endpoint만 비교한다.
- 이 후속 표본은 검증 중 순간100%와 동일한 측정 창이 아니다. 이번 전체 포화 상태에서 Defender가 주 점유자였음을 보여 주지만 검증 유발 인과는 입증하지 않는다.
- 최근25분 Defender Operational의1000/1001/1002/2000/2001/2002 이벤트는 조회 결과 없음.
- real-time protection은 켜져 있고 full scan 기록은 NULL, 서명 마지막 업데이트는00:11:21.
- 따라서 새 예약 검사/서명 업데이트보다는 실시간 또는 다른 엔진 작업을 우선 조사하는 가설이다. 이벤트 부재만으로 검사 종류를 확정하지 않는다.
- 별도 MapleRust python/maple-re 실행을 확인했다. 그 작업이 Defender 검사를 유발했다는 증거는 아직 없다.
- Defender 설정·제외 규칙·OS·WSL을 변경하지 않았고 다른 프로세스를 종료하지 않았다.

## 남은 권한/검증 경계

현재 shell은 관리자 권한이 아니다. New-MpPerformanceRecording과 Get-MpPerformanceReport는 설치되어 있고
이 환경에는 Seconds 매개변수가 있다. Microsoft 문서상 성능 기록에는 관리자 권한이 필요하다.

다음은 관리자 권한의 짧은 timed Defender 성능 기록으로 스캔을 유발한 프로세스·상위 파일 유형/대상을
분석하는 단계다. 기존 검증을 다시 실행하지 않고 현재 자연 발생 부하부터 기록하는 것이 다음 범위다.
원시 ETL/전체 파일 경로/명령줄은 공개 로그로 출력하지 않고, 요약만 보고해야 한다.
관리자 권한 부여 없이 기록하거나 권한을 우회하지 않았다.

참고: [Microsoft Defender Performance Analyzer reference](https://learn.microsoft.com/en-us/defender-endpoint/performance-analyzer-reference).

## 보존과 미완료

- 원 review031/source032/source034, 현재 runtime/test code2를 수정하지 않았다.
- source035 실패를 그대로 보존하고 별도 bounded 진단 JSON을 추가했다.
- 수용 증가0, P09/A12/A13 OPEN, 전체source/compound 수용 및 PC 프리즈 원인·해결 미확정.
- 목표 상태는 tool에서 ACTIVE 확인. 이 단일 재개 턴에서 임의 pause/blocked/complete 처리하지 않았다.

