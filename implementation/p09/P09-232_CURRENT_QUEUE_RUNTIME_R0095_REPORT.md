# P09 r95: case063 실제 수용과 재사용 문서 전이 검증

2026-10-09. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용57/249 · 잔여192(일반186+corpus6) · 미closing후보0 · 다음index64.
whole재조정대기54. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.
위 수는 고정 r07 개별 runtime 큐이며 P09 전체 잔여 작업 수·완료율이 아니다.

## 이번 실제 사례

actual_import::formula_policy_issuer::provision::provision_root_failure_keeps_artifact_and_distinguishes_commit_outcome.
새 root 573668bytes/SHA1bad273f10d520ceead33c4d633cd2fef2ea9aa88e4ffd51fc14b53f1cc2e2dc.
body 164887bytes/SHA00863f44f6fdf5a76f90f5bbcd662563f55ca96da039711c913e7d2046d43e93.
exact1PASS/248filtered/exit0/COMMITTED/지원156계약/Job active0/tree empty.
신뢰 루트 등록 fixture mode1~4에서 Denied/CommitOutcomeUnknown/Acknowledged를
정확히 구분하고 실패 artifact를 읽을 수 있게 보존/root_writes==1/
redacted failure Debug/no_publication을 검사했다.
합성 registry fixture이며 실제 운영 SQL/생산 키 설치/issuer 운영 등록 인수가 아니다.

prep165bound=fresh/finished/read199495002bytes.
parent196.15초. 693표본,
전체CPU최대41.25%/자체machineCPU최대3.137255%/
자체private최대41959424bytes/가용RAM최소41.64849789643586%.
Job CPU0.172초/peak17.86MiB/active0.
STOP/Native warning·pause는 없었다. 원 watcher 표본 범위의 수치이며 전체 PC 과정의 무중단 보장은 아니다.
owner 종료 후 최종 root 쓰기의 CPU는 이 표본 범위 밖이다.

전후1512입력 각118919360bytes, 잠금1818/복제3024 모두close/잔여0/close실패0/
resets3024/directory306/ancestor305/별도pathname reopen0.
Rust785/고정EXE/held identity/두 전체 실제 byte 읽기/finalfresh/cleanup 유지.
실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결 유지.
원 P228/P230 source·tests·수용된 원장은 수정하지 않았다.
CPU6.25%/affinity1/BelowNormal/RAM percent/GO 뒤 실행/한 watcher/
Native32open/s/no burst/600초/1440표본/원 hard STOP는 바꾸지 않았다.
기존 통과 본문 재실행 없이 원장·source 동일성만 확인했다.

## 재사용 문서 verifier

새 sync_current_queue_document_delta.py와 test_current_queue_document_delta.py를 추가했다.
이전 P231 코드·test는 보존한다. revision/이전 원장의 정확한 경로·크기·SHA/
같은 세대 report 경로를 CLI로 받아 실제 Reader pin과 비교한다.
첫 r95는 P231 r94만, 이후는 바로 전 P232 revision/run01만 허용한다.
이전 schema/PASS/156 runtime 계약/16 또는24 문서 계약/모든 fresh/cleanup/
STOP·이전 문서 bytes 보존/OPEN Gate/제품 완료false를 검사한다.
현재 runtime plan은 원 P230 anchor/progress/record로 다시 확인한다.
현재156계약은 과거 STOP.prior plan과 현재 fixture를 분리하여 검사한다.
새 actual pair1~8개와 plan 증가량을 일치시키고 보고서에 해당 SHA가 있어야 수용한다.
새 문서24계약=원P23116+새전이8. 하위 child/thread 실행은 금지한다.
이 verifier 자체는 새 EXE/GO/full source frame을 실행하지 않는다.
이는 중복 verifier 생성을 줄이는 유지보수 개선이며 CPU 성능 향상 측정 결과는 아니다.

r94 원장297412bytes/SHAf2d3f531900dc2b09c14ec794d7122628aff8f3fe924166433b4b5980e7d4d63 확인.
rootdoc 두 개는 runtime-progress-r94에 정확한 사본을 덮어쓰기 없이 만들었다.
CURRENT_STATE.md 436040bytes/SHA2b22e7b61a9a2f619348833497fd14d4950f32fff654aceca4fdf9d69d1a4bb8.
P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md 529672bytes/SHA08d51ab04e34ca420c5a46087651cb39a5ed9b159d93fb2413f02e672f820420.
두 현재 문서에는 동일 새 prefix만 붙이고 이전 bytes 전체를 suffix로 보존한다.
최종 문서 수용은 fresh/정리/156+24계약/실제 새 pair 대조 뒤에만 허용한다.

## CPU 중단과 Gate 경계

CPU 보호 중단 시 자동 재시도 금지. 해당 경로의 CPU·RAM·Job·핸들·최종 쓰기/정리
증거를 먼저 읽고 실제 개선 가능한 부분을 새 버전으로 검증한 뒤 재개한다.
이번 actual에는 STOP가 없어 새 STOP sidecar의 실제 기록을 주장하지 않는다.
실제 CPU STOP 재현은 NOT_RUN. 강제 고부하·보호 완화·외부 PID 종료·OS 설정 변경 없음.
원 P222 실패 root SHA78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0와
0byte body SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855는 보존한다.
P227 연결 지원 SHA3e980627f22938f16a9fc46f14b1fa1cf3fe8b63fa7907e73333bc93e1f60c68는
원 parent 호출/합성 Frame·Job·STOP/종료 후 sidecar를 검사한 지원 증거일 뿐이다.
PC 프리즈 원인·해결 미확정. runtime queue 전체/whole1470/historical67/signed16/
실제 SQL/생산 issuer/한글 접근허용 UI/통합·제품 Gate는 별도 미완료다.
목표 active 유지. 다음index64.
