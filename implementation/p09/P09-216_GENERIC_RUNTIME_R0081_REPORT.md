# P09 r81: runtime19~21 및 Native open 부하 완화 지원 구현

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용21/249 · 잔여228(일반222+corpus6) · 미closing후보0 · 다음index22.
whole 수용3 / 통합 성공본문whole재조정대기18. 원 legacy pending1은 별도다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 위 수치는 P09 전체 완료율이 아니다.

## 실제 검증

원 P215 실행/잠금/strict validator source를 변경하지 않고 다음만 단독 실행했다.
기존1~18 본문 재실행 없음. 각 actual에서 원18개 큐 지원 계약도 통과했다.

1. case019/run006: 여러 section의 원래 필드를 대상으로 컴파일하고 후보 바이트가
   직접 계산한 결과와 일치한다. publication/제품 route/native 재계산 승격은 없다.
2. case020/run007: ACL/AEAD/head/quarantine 변경 이후 새 컴파일 및 캐시 소비가
   거부되고 소비자 closure가 호출되지 않는다. 현재 상태의 새 인증 읽기를 유지한다.
3. case021/run008: 기존 결과와 빈 결과가 섞인 문서에서 변경된 실제 필드만 컴파일,
   변경하지 않은 section의 원 바이트를 보존한다.

각 exact1 PASS/248 filtered/exit0, 전후1488입력 각118737453bytes 일치,
frame COMMITTED/READ잠금1794/복제stream2976 전부close/잔여0.
원 Job cleanup/tree empty=true, CPU·RAM 보호 중단null. 두 전체 byte 읽기와
identity/seek/원600초 deadline·32open/s·바이트 pacing을 줄이거나 생략하지 않았다.

| 관측 | case019 | case020 | case021 |
|---|---:|---:|---:|
| 시스템 CPU 최고 |78.60%|84.14%|100.00%|
| 제어 프로세스 CPU 최고(머신 분모) |0.728597%|0.756144%|1.296296%|
| 제어 private 메모리 최고 bytes |39317504|38301696|38215680|
| RAM 여유 최저 |44.8773%|40.2389%|44.1213%|
| 제품 Job CPU 누적 초 |3.938|4.594|2.906|
| 제품 Job peak private MiB |32.47|29.23|31.78|
| 준비 metadata bound/fresh/finished |38/38/true|40/40/true|42/42/true|
| 보호 중단 / 정리 |null/true|null/true|null/true|

## CPU 100% 표본 조사와 코드 보완점

case021의 원 560개 제어 표본에서 >=95%는1개, >=98% 최장 연속은1개였다.
100% 표본 시각 `2026-10-08T09:54:26.854594+00:00`, 구간 metadata_hash.
원 제품 부모의 첫 표본 `2026-10-08T09:54:52.845312+00:00`보다25.990718초 앞이다.
논리 읽기60225160bytes/121passes는 완료 준비 reader 값과 같고 해당 표본의
읽기 증가량0, 제어 프로세스 CPU0%, private37634048bytes, RAM 여유45.1576%였다.
이는 입력 READ 잠금 취득 구간이며 아직 원 제품 부모 실행을 시작하기 전이다.
제품 부모 표본의 시스템 CPU 최고86.93%, >=98% 표본0이다.

원 98%×4 hard stop은 충족되지 않아 원 STOP이 없는 사실을 그대로 유지한다.
제어 프로세스의 직접 CPU 사용과 제품 Job 실행을 분리했지만, Native open에 따른
간접 영향·Defender·다른 PID·실제 프리즈 원인을 증명하거나 배제하지 않았다.
입력 Native open은 원32/s pacing과 hard guard가 있으나 P185의95% soft yielding은
바이트 reader에만 연결돼 있었다. 따라서 이 구간의 부하 완화 공백을 보완했다.

새 `native_open_backpressure.py`는 원 P209 borrowed 잠금을 상속한다.
기존 P185 PressureCheckpoint를 Native pacer에 연결하며 원 owner 표본만 사용한다.
95% 이상이면 원0.5초 표본의 서로 다른 두 cool window(<95)를 기다린다.
95% 미만의 정상 부하에서는 추가 CPU 시작 문턱이나 대기가 없다.
원 CPU98%×4/RAM/commit/IO guard와 잠금600초 deadline을 대기 중에도 검사한다.
최대8 pause window, 원32open/s/no burst credit 유지, cleanup에는 pressure guard를
적용하지 않아 원 중단 후에도 소유 handle 정리를 계속 시도한다.
파일/byte/identity 검사·입력 범위를 제외하거나 증거를 PASS로 바꾸지 않는다.

지원10계약은 normal CPU 무대기, 두 새 cool window, 원98%×4 중단, 최대 대기,
stale 표본 거부, RAM/commit/IO 중단 전파, 잠금 deadline, idle/cooling burst 금지,
중단 후 무조건 cleanup, 실제 CPU/프리즈 개선 미주장을 검사했다.
light run01 PASS, metadata bound9=fresh9/finished=true, stop=null/cleanup=true.
**지원 계약만 검증했다. 실제 Native pressure frame/제품 bridge 연결은 NOT_RUN이다.**
원 P206/P208/P209/P215 수용 source 및 실제 증거는 수정하지 않았다.
다음 제품 실행 전에 새 helper·controller를 원 전체 입력 frame에 포함하고,
기존 runtime21 원장을 다시 실행 없이 소비하는 bridge를 검증해야 한다.
기존 `resume_generic_locked_runtime.py` 자체에는 새 helper가 아직 연결되지 않았다.

CPU 보호 중단 시 자동 재시도 금지. 높은 단일 표본도 보존·조사했으며,
원 검사·guard를 약화하거나 다른 앱/OS/보안 설정을 변경하지 않았다.
Git/Cargo/build/SQL/Hangul/접근허용 실행 없음.

## 추가 원장 표현 조사

case021의 JSON을 파일에 다시 쓰지 않고 메모리에서 공백만 제거한 표현으로
왕복 파싱했다. 원 dict와 모두 같고 root2103393→1469638bytes,
body810271→615526bytes였다. 표현상의 모델이며 기존 파일/bytes/SHA는 유지한다.
이는 실제 compact 제품 실행이나 측정된 CPU/시간 개선 증거가 아니다.
이런 증거 표현 최적화도 원 검증·모든 필드/실패 표본을 보존하는 별도 연결 검증이
필요하다. 현재 실행 경로의 JSON 형식은 변경하지 않았다.

## 증거 pin

경로 기준 `implementation/p09/evidence/locked-r07/`.

| 파일 | bytes | SHA256 |
|---|---:|---|
|`p215-case-019-run006.v1.json`|2083844|`4cae4ab3eb0e54cdc1a226b1afbc9999293ace5ff0243bbc769e1da21849a00e`|
|`cases/p215-case-019-run006.json`|810353|`4852058263767819facdd0b27fee1485b783cdd7d14af20508b658d63aebaf00`|
|`p215-case-020-run007.v1.json`|2143480|`5feb2874a71443cabe82cd003dbfd3a3496bef6a430cb1a8cacab849a5561da6`|
|`cases/p215-case-020-run007.json`|882400|`4338267dc01b31c4231a9d9298140256d184acb7e630598b3d06eba2b809ff86`|
|`p215-case-021-run008.v1.json`|2103393|`bbba659a0cf07291e5d283acfd63f3f00c2300899f8219605c445efe4070f80c`|
|`cases/p215-case-021-run008.json`|810271|`2d0b55af6bb4f8910a806af70b6dd33b058ac8b82a32810c766fe97ef893ece6`|
|`p217-native-open-light-run01.v1.json`|7106|`118263568c50a5b36fff75571191592a1917cd601b5a73499e2a366637d37c77`|

r80 문서 원bytes/SHA를 확인하고 `evidence/runtime-progress-r80/`에 복사한 뒤
같은 r81 prefix만 두 현행 문서 앞에 추가했다. 기존 고정 P216 delta 검증기는
원 runtime 큐/strict validator/지원18+8계약/최종 bound input fresh hash/old byte suffix를
재검증하며 제품/전체 source frame은 다시 실행하지 않는다. P217 light는 독립 지원
증거이고 문서 delta를 제품 Native pressure 실행 증거로 사용하지 않는다.

다음은 Native pressure helper의 전체 source frame 연결·검증 후 case022 단독 실행이다.
P09 Gate/whole1470·historical67 최신성/전체249/signed16 및 corpus6는 미수용이다.
