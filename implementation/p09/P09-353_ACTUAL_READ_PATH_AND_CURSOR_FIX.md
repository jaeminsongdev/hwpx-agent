# P09-353 — 새 cursor 오류 수정·828 자격·실제 바이트 경로 최적화 연결

날짜: 2026-10-10. 목표 ACTIVE. 상태: V20_828_PASS_V21_ACTUAL_PATH_IMPLEMENTED_NOT_QUALIFIED.

## 이번 진행

P352의 독립 source040/accept041은 수용102이다. 새 cursor102/next109에서는 원 별도
LIGHT/FRESH가 필요하므로 이전 cursor의 자격을 현재 GO로 승격하지 않았다. 사용자 외출
경계를 유지했으며 UAC/한글 접근 허용/Defender 추적·설정 변경은 수행하지 않았다.

### 재현한 검증 코드 오류 두 건과 V20 자격

1. light042: current395만 실행 후 Source021StopReviewTests의 긍정 검사1개 실패.
   SOURCE021은 역사적 cursor101 기록인데 current102 FIXTURES를 썼다. current/following
   모두 당시 PENDING108_BASE를 사용하도록 수정했다. 원 기록/원 guard는 그대로다.
2. 기존790/code V19의 accept041을 새로운 코드에서 검증할 때 nested metadata oracle이
   V20 SCHEMA를 참조했다. light045 selection에서 ORIGINAL_HISTORICAL_METADATA_COUNTS로
   실패했다. 아직 실제 계약/Native/제품0이었다. metadata/common/header/재귀 closing을
   모두 literal V19/395x2=790으로 분리했다. 원 code2 archive도 매번 exact 확인한다.

13개, 추가 보강 후19개 작은 합성 검사 PASS. V20 light048은 실제414x2=828 PASS,
217 fresh/434 reads/46548014바이트 완료·정리 TRUE. 별도 fresh049도 PASS, 계약재실행0.
light048 host 최고100% 표본은 있으나 sustained STOP은 없었고 own 최고6.525912%,
private 최대95977472바이트/RAM여유 최저23.426943%였다. 일부 짧은 표본 CPU가 한 논리
CPU의 명목 machine 비율을 조금 넘는 관측을 hard-cap 해제 증거로 해석하지 않는다.
qualified V20 code2는 evidence/p340-formal828-code/에 exact 보존했다.

### actual109/run050 — 제품 body 미시작, 원본 실패 유지

828과 fresh049를 재사용해 단일109만 선택했다. whole input lock1966(dir308+regular1658)
획득 완료, 이후 원 parent before-byte 읽기805번째 부근에서 STOP_SUSTAINED_SYSTEM_CPU.
원 parent 표본은 DEFERRED_NOT_STARTED, owned_tree_empty/cleanup TRUE, 실제 제품 child0.
사례109 PASS가 아니며 body placeholder0과 별도 실패 sidecar를 보존했다.

- 원 frame 입력1658/121199645바이트. 완성된 before/after byte 경계0.
- 원1966/복제805 handle 전부close; 잔여handle/reader/stream/close failure0;
  frame CLOSED/unregistered, resource watcher 정리 TRUE, PTY50833 exit1/관측 PID106756 종료.
- preparation219 fresh/438 reads/46805742바이트 완료.
- 원 Native inspect 전체0.0587404초, open140.636816초에는 pacing 대기가 포함된다.
- host 최고100%, own 최고1.584158%, private 최대140472320바이트(약133.96MiB),
  RAM 여유 최저21.621770%. 마지막4는 host98.17/100/100/100, own0.182815/0/0/0,
  logical-read 증가239730/0/0/0. 직접 CPU 폭주·RAM 누수 또는 간접 부하 인과를 확정하지 않는다.
- 별도 stop-review051도 final_fresh_preparation에서 CPU STOP, 정리 TRUE/제품0.
  독립 STOP 검토 PASS가 아니며 다음 GO로 사용할 수 없다. PTY47934 exit1.

### CPU STOP 후 실제 부모 경로의 누락을 수정 — V21 아직 미자격

코드 검토에서 read_with_held_path_guards가 독립 closing-source에만 연결돼 있었음을 확인했다.
실제 ParentConnection은 원 Frame.read_boundary를 직접 호출하므로, pathname 메타데이터
최적화가 실제 제품 준비 경로에 적용되지 않았다.

V21 ActualHeldPathGuards를 같은 Frame instance에 연결했다. 원 bound method를 정확히
한 번 호출하며, helper에는 original boundary를 명시해 재귀를 피한다. 매 Reader/request의
fresh held Native metadata/token, 원 boolean predicates, 원 stream identity/두 전체 byte/
Job/CPU·RAM/deadline/pacing을 유지한다. 성공/STOP/alias drift 뒤 instance method와 Reader
root를 복구한다. 새 sampler/thread/handle cache는 만들지 않는다. PASS oracle에는 실제
연결·복구·두 경계 전체 query 수를 추가로 요구한다.

새 adapter6/수용거부3 검사를 추가했다. 정의423/요구846 및 source2 AST compile PASS.
작은 fake-held 동작검사는 admission의 CPU100/100으로 실제0회였다. 따라서 현재 V21의
fake 동작/846/Native/제품/부하 감소는 NOT_RUN 또는 NOT_QUALIFIED다. 원828은 역사적
V20 자격이지 새 V21 자격이 아니다. V21 candidate code2도 별도 exact archive에 보존했다.

다음에는 literal V20 LIGHT048/FRESH049/STOP050을 원 epoch로 엄격히 검증하고, 원 독립
STOP-review 요구를 유지한 채 새 코드에 연결해야 한다. 그 뒤 adapter 동작 및 current/
following846·별도 fresh를 통과해야109를 시작할 수 있다. 기존107/108 재실행은 금지한다.
미검토 STOP를 무시하거나 archive classification만으로 current GO를 만들지 않는다.

## CPU 관측 검토와 남은 경계

CPU 계산은 idle/(kernel+user) 차분으로 원 구현과 Microsoft GetSystemTimes 정의를
대조했다. 정상 구간의 원 counter15.05/14.23%와 별도 Windows formatted counter12/14%를
확인했다. 포화 구간 동시 교차 검증은 아니므로 관측 오류 완전 배제 또는 Defender 원인
확정은 아니다. 관리자 추적/보호 완화는 하지 않았다.

근거: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes

수용102/249·잔여147(regular141+corpus6)·next109·성공 body 마감 대기0·whole 재조정99.
P09/A12/A13 OPEN, full249/signed16/whole1470 미완료, 문서 final-fresh NOT_RUN. P10 시작0.
모든 failed/partial receipt 및790/828/candidate archive 보존. 목표 ACTIVE이며 이번 단계는
실제 코드 변경·정식828·새 중단/정리 증거를 얻은 진행이다. 완료·pause·blocked 처리0.
Git/빌드/OS·Defender·WSL 변경/외부 종료/삭제·이동0.

bounded 수치·원본 hash 원장: evidence/p09-353-actual-read-path-and-cursor-fix.v1.json.

