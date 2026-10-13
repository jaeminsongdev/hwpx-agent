# P09 P241~P247 CPU STOP 검토와 두 파일 접근 밀도 제어

2026-10-09. 목표 active. P09·A12·A13 OPEN. 프리즈 원인·해결 미확정.

## 현재 결과와 다음 경계

- runtime 수용 73/249, 잔여176(일반170+corpus6), 다음index80, 미closing후보0, whole재조정대기70.
- 이 runtime 목록은 P09의 일부 검증 목록이며 P09 전체 완료율이 아니다.
- 통과 본문 재실행 없음. case80 본문 NOT_RUN. 두 CPU 보호 중단은 FAILED_NOT_ACCEPTED로 보존한다.
- 새 소규모 지원 검증은 전체 source/runtime/Gate PASS가 아니다. Native20 전체 실제 검증 NOT_RUN, metadata32 전체 실행기 연결 NOT_RUN, P239 실제 pre-GO CPU STOP 경계 NOT_RUN.
- 다음은 새 실행기에서 완료된 STOP 검토와 metadata 지원을 명시적으로 소비하고 추가 소스까지 전체 입력에 묶는 것이다. P241/P244 실패 caller를 다시 실행하거나 index80을 건너뛰지 않는다.

## 첫 STOP: P241 Native 잠금 획득

P241은 P239 Capture 지원을 기존 전체 범위에 추가한 1525입력/119022055 bytes 실행기다. 사전156+18+8=182계약과217fresh는 PASS다. 실제80/run002는 Native 획득 중 지속 시스템CPU98% 이상4연속 기준으로 STOP했다.

- 본문·원 parent 호출·Job·Borrower·실제 byte boundary 모두 시작 전. 획득 요청 true, 완료 false.
- 잠금854 opened=closed, 잔여·활성reader·stream·정리 실패0, frame CLOSED/등록해제.
- preparation218fresh=finished,230665600 논리bytes. Native32의 reservations854, 자체 접근을1.5초 양보한 뒤 원 보호 STOP.
- metadata286표본, 전체CPUmax100%, 자체max5.847953%, 자체 private44576768 bytes, 가용RAM최소31.478625%. 경고4개 표본 자체CPU0%, Job CPU는 미관측(null).
- P242 검토20+peak8/9fresh 통과. 원 실패를 PASS로 바꾸지 않고 미실행·정리만 검증했다.

## P243/P244: Native 밀도 제어와 두 번째 STOP

원 OpenPacer의 instance만32→20회/s로 낮추며 idle 후 burst 금지·원 PressureCheckpoint·잠금600초·CPU/RAM/IO·identity·한 직렬 Borrower·원 두 읽기를 유지했다. 전역 상수/수용 코드는 수정하지 않았다. 명목 Native reservation 밀도37.5% 감소일 뿐, 측정된 CPU 개선률이 아니다.

P243 원10+새6=16계약과 실제 파일3개의 두 읽기에서 잠금7/복제6/정리·identity 검사를 통과했다. P244 새 실행기 전체 범위는1532입력이며 사전190계약/228fresh/231793602 논리bytes에서 STOP 없이 통과했다. 사전 표본230개 전체CPUmax93.94%, 자체max5.093633%, 자체 private44032000 bytes, 가용RAM최소31.014793%였다.

P244 actual run002는 준비 metadata 읽기 단계에서 STOP했다. 아직 test 선택·Native20 instance·frame 획득·본문·Job·Capture가 없다. 따라서 Native20 실제 전체 성공이나 해결로 해석하지 않는다.

- metadata_read_parse 경고4개 표본 시스템98.86~100%, 지속98 이상4개, 자체 warning최대0.378788%, Job 미관측(null).
- metadata71표본 자체max1.308411%, 자체 private39489536 bytes, 가용RAM최소31.591322%. 원 pressure3windows/1.5초 후 STOP.
- metadata125읽기/69547076 논리bytes/72bound, finalfresh0/finishedfalse. 부분 준비 결과는 수용하지 않는다.
- 제품/Native/sidecar/placeholder는 생성하지 않았다. 원 자원 watcher 정리는 확인됐다.
- P245 STOP 검토12+peak8/8fresh는 run02에서 통과했다. run01 검토 실패는 음성 검사 fixture가 실제 peak 필드 대신 다른 키를 주입한 오류였다. 정확한 owned_job_cpu_machine_percent 키로 수정하고 음성 검사를 그대로 유지했으며 원 run01 실패 증거도 보존했다. 제품 검증 재시도가 아니다.

두 STOP의 자체 CPU 표본은 검증 프로세스가 직접 전체 CPU를 쓰는 루프임을 입증하지 않는다. 파일 접근이 보안 검사 등의 간접 부하를 유발했을 가능성 역시 배제하지 않는다. 외부 원인/PC 프리즈 해결은 미확정이다. Defender·WSL·OS 설정이나 다른 프로세스는 변경하지 않았다.

## P246: 작은 증거 파일의 연속 시작 밀도

원 AuditReadPacer는64KiB byte credit을 short read/EOF 뒤 환급한다. byte 속도 제한은 있어도 작은 파일 수백 개의 _read 시작 자체는 짧은 시간에 몰릴 수 있었다. 새 instance binding은 각 원 _read 진입에 원 no-burst OpenPacer32회/s를 추가한다.

- 원 _read는 같은 name/parse 인자와 원 결과로 정확히 한 번 호출한다. 원 byte 속도1MiB/s EXE·2MiB/s 기타, hash,16MiB parse budget, 모든 반복 fresh 읽기, 원 STOP/600초 checkpoint를 그대로 유지한다.
- cached pin/parsed JSON으로 읽기를 대체하지 않는다. 작은 파일 refund 정책과 byte pacer는 그대로이며 파일 시작 밀도만 따로 제한한다.
- owner의 기존 pressure checkpoint를 재사용한다. 새 샘플러/스레드/외부PID 조회는 없다. STOP 후 binding 복원은 checkpoint/sleep/read 없이 수행한다.
- 원 Native 계약10+새 metadata 계약15=25통과. 실제 소규모11입력/22원 읽기와 finalfresh11, 예약22, failed0, binding해제, STOP없음/cleanup확인. 이 결과는 metadata32 전체 실행기 연결 NOT_RUN이다.
- 지원 단계 combined budget은 미래 입력상한1540·추가controller1MiB·metadata 원 읽기660회·Native20/metadata32 조건에서589.491초를 예상한다.600초 기준을 늘리지 않았다. 예측은 완료 보증이 아니며 새 runtime 연결 시 모든 상한을 실제 검사해야 한다.

## Exact receipts

기준: implementation/p09/evidence/locked-r07/. SHA256/length는 수용된 파일 그대로다.

| 증거 | 상태 | bytes / SHA256 |
|---|---|---|
| p240-post-stop-status-doc-r0099-run01.v1.json | r99 수용73 snapshot | 22730 / 77bbab276c830a841c13f4e1dc57920b32b2e4f022fdd4ff990f87527179bfe1 |
| p241-light-run001.v1.json | 사전182/제품 아님 | 48474 / 85096d817bcf17d10da8281aacd0fa9d63628e3bebac6647e823d4ec06f0e68d |
| p241-case-080-run002.v1.json | 원 Native STOP/FAILED 보존 | 277167 / 08745fbcf7738da69dbc4bbc9418ceddf811ea0f1a4a1999869ca6711aec6891 |
| p242-native-acquisition-stop-review-run01.v1.json | Native STOP 검토20+8 | 6512 / e936567327e23f8d36d084967f8dc4a8d9ed30f9816cf83d3ef35a9d313c1454 |
| p243-lower-native20-support-run01.v1.json | 지원16+실제소규모 | 15250 / b468a36fb3586ecd83758fa220ab5a57bc9092850b3fcbdcbf04a1360abf9dca |
| p244-light-run001.v1.json | 사전190/제품 아님 | 47554 / 7799f70bbd6641f187ead3c5901ee3173ee0d46ea498fb78aabc3940d4876233 |
| p244-admission-run002.v1.json | 원 metadata STOP/FAILED 보존 | 68645 / b0b1d3714afa9b47dff09361e51c7fbfdede7aeb9b4160a619bd11efb0b86319 |
| p245-metadata-read-stop-review-run02.v1.json | metadata STOP 검토12+8 | 6138 / 93cc3f95e2dfaae7407b7495f46de37e3d56103d96a34e797ec97818bbe687dd |
| p245-metadata-read-stop-review-run01.v1.json | 음성 fixture 키 오류/검토 실패 보존 | 4069 / 5b5b57c6a4a14b4cd2bfbf80612f853788c1c4957fe6c139c9b2b54214a6f226 |
| p246-metadata-entry32-support-run01.v1.json | 지원25/실제11입력22읽기 | 10741 / f44f9c27d569213536cfadc14969f6ef5195f4b883cecc451609b87e859bc261 |

## 문서·원본 보존

새 문서 상태 snapshot은 runtime 재검증이 아니다. r99 문서 exact SHA/length를 먼저 확인하고 runtime-progress-r99/에 no-overwrite 복사했다. CURRENT_STATE.md 및 P09-149 진행 문서는 기존 바이트 suffix를 유지한 동일한 r100 prefix를 추가했다. P247 검증은 literal 실패·지원·미실행 경계, 문서 suffix·계약·최종 fresh를 검사한다.

원본/기존 수용/모든 실패 증거를 삭제·변경하지 않았다. CPU 보호 중단 시 자동 재시도 금지. Git/Review/Cargo/build·원격push·SQL·한글 GUI·접근허용·Defender/WSL/OS 설정 변경 없음.
