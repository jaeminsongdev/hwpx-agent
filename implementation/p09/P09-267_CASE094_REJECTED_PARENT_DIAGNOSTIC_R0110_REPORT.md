# P267 case094 실패 진단 보존 / runtime-r110

2026-10-09. 이 보고서는 기존 성공/실패 증거의 byte binding 및 새 진단 Capture 합성 검증용이다.
P267 qualification의 완료 여부는 `evidence/locked-r07/p267-case094-failure-review-run01.v1.json`의 실제 state로 판단한다. 파일이 없거나 FAILED면 qualification 완료가 아니다. 실제 runtime 연결 NOT_RUN; 94번 수용·재실행·Gate 종료 권한을 부여하지 않는다.

## 현재 범위

runtime 수용87/249; 잔여162(일반156+corpus6); 다음index94; whole재조정대기84; 독립source 마감대기0.
P09·A12·A13 OPEN. 원 STOP/FAILED 보존. 본문 재실행 없음. 원600초·CPU/RAM 기준은 변경하지 않음. PC 프리즈 원인·해결 미확정.

92/93은 기존 strict validator로 재계산한 실제 root/body pair만 수용한다. 합성 계약 횟수는 본체 PASS 개수가 아니다. 이전 r109 문서 byte 전체는 `evidence/runtime-progress-r109/`에 SHA/길이 검증 후 별도 복사하고, 현재 문서에는 같은 prefix만 붙인다. 원 receipt/helper/test는 변경하지 않는다.

## 실제93

- exact1PASS/exit0/elapsed253.43; 두 source boundary 각각1563입력/119418092bytes, COMMITTED/held identity 확인 및 등록 해제.
- 잠금1869, duplicate3126 모두 close/잔여0, 원 Job active0 확인. prep346reads/167bound=fresh, post2reads/1bound=fresh. 원498+current30+following30=558 계약 유지.
- 전체 CPU max100%, 자체 max5.958927%, private55586816bytes, 가용 RAM 최소36.797347%. 단발 ≥98 표본1, 연속98 최댓값1; 95% warning 당시 자체 CPU0.195312%. 기존 metadata softyield1초, 조기90% yield0. 부하 상승 원인이나 PC 프리즈 해결을 입증하지 않는다.

## 실제94: 수용 금지

94번 FAILED 수용 불가. 본체 PASS·원 parent 중단 사유·원 Job 정리 확인 불가. 94번 자동 재시도 금지.

- 원 root `TERMINAL_FAILURE_EXACT_STOP_NOT_PASS`, 외부 watcher STOP reason null/cleanup true. 원 parent placeholder0bytes, sidecar 없음. exact한 원 parent 중단 사유를 추정·복원하지 않는다.
- 앞 boundary1563입력/119418092bytes 완료, 뒤 boundary 없음, held identity commit 없음. duplicate3106 open/identity/offset reset/close는 뒤1543파일의 **해시 완료 증거가 아니다**. 잠금1869/duplicate3106 잔여0은 outer Native 정리 증거이지 원 Job 정리 증거가 아니다.
- prep350reads/169bound=fresh 완료; 이후 metadata 검증 없음. 원Native20/600초, CPU≥98 4회 연속/RAM·commit 보호 유지.
- 전체 CPU max100%, 자체 max6.054149%, private55791616bytes, 가용 RAM 최소37.038201%. ≥95 표본2/≥98 표본1/연속98 최댓값1. warning 당시 자체 CPU0%, 조기90% softyield1.5초. 외부 PID/원 Job CPU 원인 미측정. elapsed 관측만으로 원 Native deadline을 원인으로 확정하지 않는다.

## 확인한 코드 결함과 변경

`deferred_parent_failure.Capture.writer`는 CPU 전용 `_parent_closed` 성공 뒤에만 `_document`를 저장한다. CPU 이외 중단으로 validator가 거절하면 pending false 상태에서 parent row가 사라지고 exclusive-create 본체 파일만0bytes로 남는다. 이때 원 결과 요약 출력 전 예외가 발생한다.

새 `review_rejected_parent_diagnostic.Capture`는 원 writer/오류를 그대로 유지한다. exact identity가 맞는 실패 row가 거절되었을 때 **원 참조와 닫힌 오류 코드만** 보관하고 같은 오류를 다시 발생시킨다. live 경로의 copy/JSON/gzip/IO/Native query/새 sampler는 없다.

종료된 owner와 CLOSED/unregistered frame 이후 별도 diagnostic-only envelope를 최대16MiB/32768ASCII block으로 한 번만 기록한다. 미측정 값은 null, partial 정리는 partial 그대로 보존한다. 원 PASS/CPU STOP 수용 규칙은 변하지 않고, unknown cleanup은 qualified cleanup이 아니다. 짧은 쓰기/NaN/값 변경은 실패하고 재시도하지 않는다.

CPU 이외 실패 진단 보존은 합성 검증만 완료; 실제 runtime 연결 NOT_RUN.
예비 synthetic40개(기존22+새Capture18)는 통과했다. 최종 P267은 실제 실패 fixture 거부12까지 총52개, 기존 수용 pair 재계산, 문서 원 byte suffix, 모든 bound input의 final fresh를 원 watcher/720읽기/600초 보호로 확인한다. 제품 EXE/Job/전체source 재실행·Thread 추가는 없다.

다음 경계는 이 qualification 후 94번 실패의 실제 caller 연결과 source 경로/600초 시간 측정 코드 검토다. 새로운 측정이나 독립 source 검증 없이 94를 통과 처리하지 않는다. 완료되지 않은 실제 실행을 자동 재시도하지 않는다.

## 불변 증거 SHA-256

- 원 실패94 1345290bytes: `c347fd3df25cd2b4d52db6f8c27e6325c039f803ab0987f8e0902ac9005f31f9`
- 원0byte94: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- accepted92 root613296bytes: `e5c477adf0ea021a15f80febcd70aef552b0135543bda273366db159095155ab`
- accepted93 root599016bytes: `633db64d0d75fc206731b45b28c4581fc91161335cb145ef2e56dedb62b36c3a`
- P266 r10963618bytes: `d8dc2c028d57993631b360a3638cbe0bd7b8cad215209c84d031ec6b1d7f8e80`
- 原r109 CURRENT_STATE463649bytes: `ab7dc02bd8beb68fe192ea943dc38073e159cf379a9ba1617fa238ee84e8c741`
- 原r109 progress557281bytes: `92c2de97d9a800a77c48fb3df2d490d9f9be879073864e51ec619509acc7d2e2`
