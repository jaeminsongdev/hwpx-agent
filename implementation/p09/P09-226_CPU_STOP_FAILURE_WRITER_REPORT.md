# P09 P226: case060 CPU STOP 검토와 종료 실패 writer 지원 수정

2026-10-09. 목표 active. P09·A12·A13 OPEN. P10 새 구현 없음.
runtime 수용53/249 · 잔여196(일반190+corpus6) · 미closing후보0 · 다음index60.
whole재조정대기50. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.
이는 고정 개별 runtime 큐의 수이며 P09 전체 완료율이 아니다.

## 실제 완료와 중단

같은 P222 case058/run018·case059/run019는 각 exact1PASS/248filtered/exit0/COMMITTED/
88지원계약/전후1503입력 각118841107bytes/잠금1809·복제3006 전부close/Job active0/
tree empty로 수용됐다. 이전 수용51개 본문 재실행 없음.
58은 한 비트 서명 변조·다른 도메인·외부 키·최신 승인 누락 거부이다.
59는 fresh callback 안에서 trust denial 및 Clock의300 점프로 만료를 유도해
소비자 callback을 호출하지 않는다. Clock unavailable 검사가 아니라 시각 점프 조건이다.
58 root SHA72145bf8602f96fd42a3f6023abd6fa4b9ed55c46de924cd919b66fcab0847df, body SHA9765f12a5389e3a26025b482e3894f98e83940f9f40ecc37c01e657a495a63be.
59 root SHAc7cf3da34fff99b65716bda258bf73d797b1537a7f63f36391743a2c8ed6cea6, body SHA7839ce1dd88561496c52531a5afc7fe53723926efe93e2d0a0fa9b34baebdee4.
CPU peak83.71/55.24%, RAM 여유 최저42.0049/41.3328%, STOP/Native warning0.
실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결 유지.
실제 SQL/운영 issuer/Hangul/native/UI/Gate 인수로 승격하지 않는다.

case060/run020는 FAILED_NOT_ACCEPTED/STOP_SUSTAINED_SYSTEM_CPU.
error=P206_LOCK_P208_FRAME_LIVE_STATE. root208007bytes/
SHA78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0.
body는 존재하지만0bytes/SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.
둘 다 보존하며 삭제·덮어쓰기·복원·PASS 재분류하지 않았다.
semantic test 완료/실행 여부/원 Job 최종 결과는 이 빈 body로 확정하지 않는다.
root actual_product_child_executed=false는 callback 완료 전 default일 수 있어 미실행 증거로 쓰지 않는다.
60은 미수용 그대로며 자동 재시도 없음. 기존 P222의 failed-attempt resume 차단을 유지한다.

## 중단 시점과 정리

원 root669표본 중 >=95/98가 각각4회, >=98 최대4회 연속으로 hard STOP에 도달했다.
phase tag는 final_fresh_hash이다. caller phase는 외부 PID나 OS 원인을 뜻하지 않는다.
전체 own CPU peak1.223776%(machine), 고부하4표본 own최대0.378788%이며
Job CPU 필드는 원 root에 없어 null/관측 수0이다. Job 값 없음은 0이 아님.
RAM 여유 최저29.5223%, own private 최고41062400bytes.
CPU100%4연속은 사실이며 직접·간접 원인 미확정. PC 프리즈 해결 미확정.
잠금1809/복제2210 모두close/잔여0/close 실패0/active binding·stream0/
frame CLOSED·registered=false, resource watcher cleanup=true.
전후 byte read 두 번째가 완결되지 않아 COMMITTED/current full source closing을 주장하지 않는다.
preparation136bound=fresh/finished/read191664856bytes는 완료됐으나 runtime PASS가 아니다.
현재 남은 Python1개는 CIM 명령 정보상 p09/hwpx-agent가 아닌 다른 관찰 작업이었다.
그 프로세스나 다른 시스템/앱 설정은 변경·종료하지 않았고 CPU 원인으로 단정하지 않는다.

## 관련 코드 검토와 안전한 수정

runtime_input_frame.Frame.read_boundary는 CPU STOP 등 예외에서 state=BROKEN으로 전환한다.
P208 run_parent의 최종 write는 STOP row도 RAW_DUMP로 전달한다.
P222 parent_writer는 STOP row에서도 packed.dump(checkpoint=frame.check)를 호출한다.
Frame.check는 BROKEN을 거부하므로 STOP body를 기록하기 전에0byte 파일만 남긴다.
이 연결상의 실패 증거 유실을 재현 가능한 계약 대상으로 분리했다.
원 P208/P222/frame/guard/고정 EXE/수용된 소스와 원 실패 receipt는 수정하지 않았다.

새 terminal_failure_receipt.py는 정리 완료 후 실패 sidecar를 쓰는 지원 코드이다.
정확한 STOP/OPEN/미완료 flags/부모 Job cleanup·empty/
outer owner 종료·정리/frame CLOSED/잠금·stream 잔여0 확인 뒤에만
전체 JSON 값을 공백 없는 ASCII로 보존한다. 32KiB batch/16MiB cap/short-write 즉시 실패/
no retry를 적용한다. gzip·Native/live frame 재검사·새 sampler·원본 읽기 없음.
PASS를 이 경로로 보존/수용하는 것은 금지한다. 실패 상태와 원 full values를 바꾸지 않는다.
종료 경로의 불필요한 gzip·실패할 live check 제거는 구현했으나 CPU 개선 측정 증거는 아니다.
실제 parent에 아직 연결되지 않은 SUPPORT_ONLY/actual_connection=false이며,
이번 빈 body를 복구하거나 이미 잃은 test 결과를 추정하지 않는다.

CPU 보호 중단 시 자동 재시도 금지. 보호 기준·전체 입력·전후 read/fresh/Job·GO를 약화하지 않는다.
입력 잠금/원장 기록/issuer·provision의 bounded 입력·전후 live 재검사와 no-retry를 검토했다.
검토한 구간에서 원래 검사를 제거해 CPU를 줄이는 변경은 적용하지 않았다.
프로젝트 전체 최적화 완료/제품 CPU 원인 해결을 주장하지 않는다.

## 지원 검증과 다음 단계

P226 review receipt14694bytes/SHAf1ee9b8c0250cecd2ec51852f5a8dcfc8c9ff5ca9499f39ddc57a75d4a3eb530.
state=PASS_BOUNDED_STOP_REVIEW_AND_FAILURE_WRITER_SUPPORT_NOT_RUNTIME_OR_GATE.
지원 writer16계약+기존 peak8계약/12bound=fresh/finished/cleanup/오류·stop=null.
16계약은 PASS·오류 reason·미정리 Job/frame·bool zero·Gate 승격 거부,
전 값 보존·입력불변·32KiB bounded token·16MiB cap·short write no retry·도중 상태 변경 거부를 확인한다.
제품 재실행 없음/실제 writer 연결 없음/resume_authorized=false/원인·PC 해결=false.
정식 다음 단계는 새 caller의 stop capture→정리 후 writer 연결·계약/실제 연결 검증과
STOP를 보존하는 resume/document 경계 설계이다. 그 전까지60을 재시도하거나 다음61을 건너뛰지 않는다.
새 notice는 기존 r91 문서 길이/SHA를 대조한 archive byte suffix를 보존하고
53/196/next60과 STOP·지원 한계를 반영한다. 원 P225 progress가 실패를 거부하므로
P225 성공을 조작하지 않고 별도 STOP notice validator로 문서를 대조한다.

