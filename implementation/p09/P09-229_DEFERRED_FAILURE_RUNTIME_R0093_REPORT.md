# P09 r93: 종료 실패 capture 연결과 case060 새 실제 수용

2026-10-09. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용54/249 · 잔여195(일반189+corpus6) · 미closing후보0 · 다음index61.
whole재조정대기51. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.
현재 수는 고정 r07 개별 runtime 큐이며 P09 전체 완료율이 아니다.

## 전 상태와 새 연결

r92 P226 notice14737bytes/SHAdf2713cd6b0461108bfa486ca13d3196f990034702252d74004efebe133ce1a7의
53/next60/22bound=fresh/finished/cleanup/resume=false/parent connection=false를 현재 파일에서 대조했다.
원 P222 실패 root208007bytes/SHA78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0와
0byte body/SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855는 보존한다.
기존 실패를 PASS로 바꾸거나 그 빈 body에서 semantic/Job 결과를 추정하지 않았다.

deferred_parent_failure.Capture를 새 P228 caller의 원 P208 RAW_DUMP에 연결했다.
PASS는 원 P222 packed writer/frame.check를 그대로 사용한다.
CPU STOP일 때만 원 row 참조를 보관해 live STOP 동안 copy/gzip/Native·frame 재검사/
새 읽기·쓰기/새 sampler를 하지 않는다. 원 parent가 Job 정리 후 반환하면
caller가 source frame·outer owner를 정리하고 새 failure sidecar를 exclusive-create로 쓴다.
32KiB/16MiB/모든 원 JSON 값/상태 유지/no gzip/no write retry를 적용한다.
정리 실패/활성 Job·핸들/상태·identity 변경/두 번째 writer·sidecar 호출을 거부한다.
원 source frame/guard/고정 EXE/기존 수용 helper·실패 원장은 수정하지 않았다.

원 parent는 시작 전 중단을 DEFERRED_NOT_STARTED로 기록한다.
P226 지원 writer는 frozen 그대로 보존하고 r2를 새로 만들어 STOPPED_NOT_ACCEPTED와
DEFERRED_NOT_STARTED를 원문 그대로 구분했다. 시작 전 Job가 없으면 없음 그대로 보존하며
worker/Job가 이미 생성됐다면 실제 empty Job 확인이 필요하다. 누락 Job를0으로 만들지 않는다.
실행 전·후 상태와 실제 실행 flag가 모순되면 거부한다.

P227 연결 qualification6857bytes/SHA3e980627f22938f16a9fc46f14b1fa1cf3fe8b63fa7907e73333bc93e1f60c68:
44계약=원 writer16(r2 replay)+시작 전6+adapter22, 17bound=fresh/finished/cleanup/오류·stop=null.
원 P208 run_parent 호출 경로에서 ORIGINAL_RUN만 합성 STOP로 대체해
STOP 반환/0byte placeholder/종료 후 실제 새 sidecar 기록을 확인했다.
generated synthetic sidecar1823bytes/SHAcb93fd81ea4d58cbe990da4e1d94a9787982b7b9e54eff8f3118d71c231d2767.
합성 Frame/Job 값으로 caller 연결을 검사한 것이며 실제 EXE/Job/GO/source frame은 실행하지 않았다.
실제 CPU STOP 재현은 NOT_RUN. PC를 고부하로 밀어 STOP를 재현하지 않았다.

## 새 driver와 source scope

P228은 exact immutable P226 STOP review/원 실패 root/0byte body만 감사된 미수용 상태로 인식한다.
그 외 FAILED/STOP/partial/정리 실패는 여전히 재개를 막는다. 감사된 실패는 수용 수에 더하지 않는다.
원 P22034+P22235~59의 수용53개 본문을 재실행하지 않고 strict record로 다시 대조했다.
새 코드7개만1510 scope에 추가, extra controller43개. 원1503을 제외/변경하지 않았다.
자원 정책/32open/s/no burst/600초/1440표본/한 watcher/원두 실제 byte 읽기/identity/finalfresh/
affinity1/BelowNormal/Job·GO/CPU·RAM·commit 보호를 유지한다.
실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결을 유지했다.
driver144계약=원88+연결44+새경계12이며 서로 다른 runtime144개라는 뜻이 아니다.
LIGHT는155bound=fresh/finished/선택60/accepted product0/stop=null/cleanup으로 통과했다.

## 실제 새 case060/run001

P228 root572432bytes/SHAf864face44fdfaf2277c0c4bf958fffacf0f968955fd8cc7d169f369e7dac04f.
body167339bytes/SHA9bb595dc4cedf4a5aff617f78c6f34cd2a9da8bfd7a221d540e04bcdcd28b02a.
actual_import::formula_policy_issuer::provision::provision_approval_write_and_postcommit_failures_preserve_exact_outcome_without_retry.
합성 registry mode1~4의 Denied/CommitOutcomeUnknown/Acknowledged 결과를 정확히 구분하고
증거 artifact 보존/approval_writes==1/no_publication을 검사한다.
실제 SQL 운영 등록·issuer 설정·atomic/native/UI/Gate 인수가 아니다.

exact1PASS/248filtered/exit0/COMMITTED, 지원144계약 통과.
전후1510입력 각118894821bytes, 원 Rust785/고정EXE/두 전체 실제 byte 읽기 유지.
잠금1816/복제3020 모두close/잔여0/close 실패0, held identity 파일1510·directory306/
ancestor walk305/Job active0/tree empty를 확인했다.
원 CPU STOP은 보존하고 이 새 완료 원장만 별도로 수용54에 더한다.

system CPU max70.86%, controller CPU max2.462121%(machine), private42549248bytes,
RAM 여유 최저42.4268%, Job CPU 누적3.328초/peak private25.93MiB,
parent201.54초/root696표본, preparation156bound=fresh/finished/read193825841bytes.
STOP/Native warning/pause0, watcher cleanup=true/new sampler=false.
실제 입력1510/118894821은 지원 입력7개 때문에 이전1503/118841107과 구분한다.
LIGHT 이후 prep 증가76476bytes는 LIGHT 물리원장38238을2회 읽은 값과 일치한다.
저장/연결/실제 정상 PASS 증거이며 동일 조건 성능 비교·CPU 원인·PC 해결 증거는 아니다.
실제 이번 STOP branch는 미발생이다. 합성 STOP 기록과 정상 제품 경로 연결은 검증했지만
live CPU STOP에서의 새 sidecar 기록을 이번 PASS로 간주하지 않는다.
root 저장은 원 resource cleanup 뒤 terminal 검사이며 위 표본이 저장 전체를 감시한 것은 아니다.

## 후속 재사용에서 발견한 계약 scope 문제

P228 첫 재개 test fixture는 과거 STOP(next60/base53)과 현재 plan을 혼용한다.
현재60 수용 뒤 plan54/next61로 P228 계약을 재실행하면 next60 고정 assertion이 실패한다.
이 제약은 첫60의 실제 PASS를 소급해 무효화하지 않지만 미래61 재사용 수용을 증명하지도 않는다.
수용된 P228 source/test1510 pin을 수정하면 기존 증거가 깨지므로 보존한다.
다음에는 새 caller generation에서 과거 audited STOP fixture와 현재 next-case fixture를
분리하고 계약/선택/소스 scope를 검증해야 한다. 같은 P228로61을 실행하지 않는다.
문서 validator는 P228 고정 감사 base53으로144계약을 재검증하고
현재54는 별도 strict progress/record로 확인한다. 이를 generic 미래 인수로 승격하지 않는다.

## 문서와 다음 경계

r92 두 문서의 notice pin/길이/SHA를 대조해 evidence/runtime-progress-r92/에
overwrite 없이 복사하고 동일 r93 prefix+원 byte suffix를 보존한다.
P229는 이전 STOP notice와 원 실패 보존/새 P2281pair/current54/144+문서12계약/
최종fresh/cleanup/오류·stop=null을 terminal receipt로 검증해야 문서를 수용한다.
보고서 작성만으로 문서 PASS를 선언하지 않는다. 문서 validator는 제품/Frame을 새로 실행하지 않는다.
CPU 보호 중단 시 자동 재시도 금지. 새 중단 때 실패·정리·해당 경로 검토/안전한 최적화 검증 후 재개한다.
원 STOP/FAILED와 이전 날짜·전체 history byte를 보존한다.
다음index61 전 caller 계약 scope 일반화가 필요하다.
전체249/corpus6/signed16/whole 재조정·실제 SQL/운영 issuer/Native·P09 Gate는 계속 미수용이다.
Git/Cargo/build/SQL/Hangul/접근 허용/Defender·WSL·OS 설정/삭제·이동 없음.

