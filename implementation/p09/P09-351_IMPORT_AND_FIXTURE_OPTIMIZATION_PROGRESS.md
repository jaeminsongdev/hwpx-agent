# P09-351 — fixture 투영·helper import 중복 제거, 정식790 자격과 source038 중단

날짜: 2026-10-10. 목표 ACTIVE. 상태: **PASS_CURRENT790_CONTRACTS_SOURCE038_FAILED_NOT_ACCEPTED**.

P350의 수정/미실행 상태에서 이어서 진행했다. 사용자 외출 중이라는 경계를 유지해
UAC/한글 접근 허용을 띄우지 않았고 Defender/OS/WSL/외부 프로세스 설정은 바꾸지 않았다.
P09 Gate OPEN이며 P10 새 구현으로 넘어가지 않았다.

## 실제 구현·검증 진행

- metadata oracle에서는 같은 schema/전체 `preparation_IO`만 독립 deep-copy한다.
  검사에 사용하지 않는 문서·1658 required pin 맵을 반복 복사하지 않는다. 해당 oracle의
  검사 함수/IO 수치/거부 조건은 그대로다.
- held-path source oracle은 원 review/source/scope/code를 모두 유지하되 사용하지 않는
  accepted 문서만 복사하지 않는다. 실제 source contract 검증은 그대로 수행한다.
- projection 독립성/원 IO 보존/불필요 복사 미발생6검사를 추가했다. V18 작은51검사 PASS.
  전체770 review036은 anchor에서 CPU STOP으로 실제 계약 실행0이었다.
- V19 `--mode closing-chain` 추가: 기존 review→source→accept `main`을 같은 Python
  프로세스에서 한 번씩만 호출한다. helper/test module import만 공유한다. 각 단계는 새
  resource owner/Reader/전체 preparation/final-fresh/원 Native·byte·receipt 경로를 사용한다.
  별도 원본 증거와 정확한 hash pin을 연결하며, 원 단계 실패 시 즉시 끝나고 재시도하지 않는다.
  세 출력 경로의 사전 존재 여부, 성공 상태/정리/계약 실행 수/정확한 run pin도 확인한다.
- 연결 제어10검사를 추가했다. 첫61검사에서 existing-output mock 설정1건이 실패했다.
  patcher가 아닌 실제 started mock에 side_effect를 설정하도록 고쳤다. 원 실패 code2를
  archive로 보존했고, 수정 후 작은61검사는 전부 PASS였다.
- 진단용 첫 wrapper의 `runtime.guarded` 속성 오류도 보존했다. 정확한 경로는
  `runtime.m.guarded`다. 그 오류 때 실제 검사0/소유자 finally 종료이며 runtime PASS가 아니다.
- 무거운 runtime/test import 전에는 기존 `PercentageResources` admission을 가볍게
  확인했다. 정책 변경/보호 우회가 아니다. 통과 후 작은61검사와 closing chain을 같은
  프로세스 PID371404에서 실행했다.

전체 COUNT395/current+following790이다. 고정 code2/full1658/code95/frozen93/ancestor308,
Native/Job/두 전체 byte/CPU98x4/RAM비율/600초/720읽기/기존 pacing/cleanup을 유지한다.
helper import 공유는 preparation 결과/바이트 해시/수용 증거를 재사용하는 cache가 아니다.

## review037 — 실제790 계약 PASS

원본: `evidence/locked-r07/p340-closing-review-run037.v1.json`.
190535바이트, SHA256:
add11f331e8fb653aeecdc3e6ccb5001b44d26196a47c32d0ae2a0189d6ffb5d

- `PASS_PRESERVED108_SOURCE_REVIEW_NOT_NATIVE_OR_PRODUCT`, V19.
- 실제395×2=790 계약/감시자 정리 TRUE/제품 child0.
- preparation208 입력,416 읽기,43,135,132바이트,208 final-fresh 완료.
- 요청별 fresh lstat416/중복 original is_file 호출0/원 predicate1248/요청 간 cache0/원 root 복구.
- host CPU 최고13.48%, own CPU 관측 최고6.534653%, private 최대95,154,176바이트,
  RAM 여유 최저25.333459%. 샘플 수77. 단일 논리 CPU/BelowNormal 상태도 별도 관측했다.
- current code2는 `evidence/p340-formal790-code/`에 exact 보존했다.

구조·계약 자격이다. Native 전체 source/제품/P09 Gate PASS가 아니다. 진단용 bounded
carrier 해제는 이 원본 내용을 확인한 것이지 별도 runtime 자격을 새로 만든 것이 아니다.

## source038 — 독립 source 미수용, 전부 정리

같은 프로세스의 다음 단계로 원 검토 자격790을 재사용했다. 이번 계약 재실행0/제품 child0.
원본: `evidence/locked-r07/p340-closing-source-run038.v1.json`.
677754바이트, SHA256:
dee271027870e666dde4431ed8e0d667ded9924eb0923ebbe4eeeaa2dbaa2862

- `FAILED_NOT_ACCEPTED / STOP_SUSTAINED_SYSTEM_CPU`, 단계 `source_frame_acquire`.
- preparation209 입력,418 읽기,43,516,202바이트,209 final-fresh 완료.
- 요청별 fresh lstat418/중복 original is_file 호출0/원 predicate1254/원 root 복구.
  P350의 예상 감소가 이 API 호출 계수에서 확인됐다. OS 내부 전체 syscall/Defender CPU
  개선율을 측정한 것은 아니다.
- ancestor308 + regular1393 = 원1701 handle 획득/1701 close. 1702번째 take의 open pacing
  guard에서 중단했다. 원 kernel CreateFileW 전의 reservation checkpoint 위치를 확인했다.
- 잔여 handle/reader/stream/close failure0, borrower 없음, frame CLOSED/unregistered,
  실제 byte 경계0, 감시자 정리 TRUE. 전체 source/Native 자격은 미완료다.
- Native inspect 총0.0476483초/최대0.0004057초. open-with-pacing 총125.288403초는 원
  속도 제한·CPU 완화 대기를 포함하므로 kernel open의 실제 CPU 시간으로 해석하지 않는다.
- host CPU 최고100%, own CPU 관측 최고1.635992%, private 최대92,962,816바이트,
  RAM 여유 최저22.958317%. 마지막4 표본은 host100/own0/논리 읽기 증가0.
- PTY39444 exit1 종료/owned chain worker0을 확인했다. accept039 파일은 없으며
  수용 단계는 실행하지 않았다. 이미 성공한 제품107/108 재실행0.

중단 뒤 reserve의 bounded64/sleep, 원 take/ancestry dedup/phase14 복원/close 및 current
Native 계측 경로를 다시 검토했다. 새 busy-spin·자동 retry·누수 결함은 특정하지 못했다.
그러나 파일 열기가 Defender/driver/다른 후속 부하를 유발하지 않았다는 증거는 아니므로
검증 코드 무결함·Defender 인과·프리즈 해소를 확정하지 않는다. 관리자 추적은 하지 않았다.

## 다음 실행과 현재 경계

current code2 SHA/바이트가 review037의 exact95와 같을 때만, 가벼운 preimport admission
후 `closing-source` 새 run으로 review037 pin을 재사용한다. 이미 통과한 작은61/정식790/
성공 제품107·108을 다시 실행할 필요는 없다. source가 PASS한 뒤만 독립 accept를 수행한다.
source038 실패를 수용하거나 partial 획득/byte0을 전체 증거로 승격하지 않는다.

수용101/249·잔여148·next108 source 마감 대기·whole 재조정98/P09·A12·A13 OPEN 유지.
문서 final-fresh 마감은 아직 NOT_RUN이며 최신 문서 추가 자체를 자격으로 주장하지 않는다.
현재 턴은 실제 코드 변경/61·790 실행/새 Native 실패·정리 증거를 얻은 진행이다.
목표를 임의 paused/blocked/complete로 바꾸지 않았고 전체 P09~P20 목표를 유지한다.

원 P350/V18/부분61/정식790 code2 archive와 모든 실패 원본을 보존했다.
bounded JSON 원장: `evidence/p09-351-import-and-fixture-optimization.v1.json`.
