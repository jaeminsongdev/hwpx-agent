# P09 case158 실행기 통합 및 실패 기록 보호 — r329

공식151/249·잔여98·next158, P09/A12/A13 OPEN, 목표ACTIVE.
P00-P08/user 원본/기존 승인 및 실패 자료 보존. 이번 신규 공식승인0.

## 구현과 사전검증

V19는 원래 engine/worker/whole preflight 본문을 유지하고 parent physical Frame,
full original oracle, fixed worker capsule transport를 통합한다. 모든 새 CODE 단계는
namespace/합성 연결 검사이며 실제제품 PASS로 승격하지 않았다.

- preflight020 FAILED: 이전157 검토의 nested pressure/window AST undo marker 충돌.
  이미 실제151 승인에 사용한 격리marker CODE5/r612를 재사용. 과거157제품 재실행0.
- preflight021~023 FAILED: original helper64 상한. startup75→60으로 최적화했지만
  imported modules 외 declared nonimported inputs까지 센다. 그 계산과 상한을 유지했다.
- exact raw namespace는 모든 nonimport AST 정의/상수/초기화 및 import alias를 보존한다.
  실제sys.modules 엔트리 삭제/숨김0. 14개 envelope와 원lean/V18/loader를 별도 namespaces로 연결.
  원래 파일들은 여전히 전체source scope에서 exact pin/fresh 확인 대상이다.
- r658 actual binding 진단: before62/after62/새import0, declared4, union66.
  여기에는 diagnostic-only module2가 포함되어 있어 product/current ceiling PASS로 주장하지 않는다.
- preflight024 실제 PASS: 원metadata10 검사/Rust787/import63/fresh913/final913/cleanupTrue.
  raw input representations2604/283401911bytes; projected actual physical2593/258900671bytes.
  model595.7088456562586초 < 원600, shared decode5 포함. 입력제외/guard/rate 변경0.
  CPUmax42.86%, 가용RAMmin56.5260%.

## 실제158 시도와 증거 한계

--run1을 한 번 호출했다. Native acquisition2933 및 metadata_hash2593 완료 진행을 관찰했다.
그 뒤 exit1/NATIVE_PRESSURE_FAILFAST_STOP_LATCHED_NATIVE_PRESSURE로 종료됐다.
원runtime root는 부재이고 당시 complete product capture/제품본문 여부/COMMITTED/explicit
handle close counters는 증명할 수 없다. 프로세스 종료와 관련Python잔여0만 별도로 관찰했다.
실제 제품 PASS·독립승인·Native cleanup receipt를 만들거나 소급 주장하지 않는다.
terminal 요약 및이증거한계는 r660 FAILED로 보존했다. 같은실행blind재시도0.

## 코드 재검토 및 수정

V1 정책은 원본경로뿐 아니라 모든Python open 전에 live Native checkpoint를 호출했다.
따라서 terminal latch 후 원래 실패 receipt.open(x)도 막힐 수 있다.
이를 회귀로 재현한 뒤, V2는 선언된원본경로에서만 guard-before-deny를 수행한다.
다른경로는 기존reader/resource/Frame/decoder guards를 그대로 사용하며추가Native guard를걸지않는다.
원래cleanup/receipt write가새policy때문에차단되는상황을제거한다. 보안sandbox/allOSguard 주장은없다.

r661 CODE4 4/4 PASS: V1 실패재현, V2 output delegation, 원본resource stop identity 유지,
원본deny/API restoration 확인. 이는 최초pressure warning의 실제CPU원인증명이 아니다.
전체V1 parent connector 코드 유지+명시V2 policy dependency로 연결했고 r662 CODE7 7/7 PASS.
현재새DATA024/새preflight025는아직실행하지않았다. 이전PASS024는V1만증명한다.

## 보존/다음

failed controller preimages와 oldCODE/DATA/failed020~023/pass024/r660을 모두보존.
최신code8개는p361-r329-qualified에exact archive. 기존문서 전체bytes 뒤에새현황만추가.
한글/접근허용/UAC/OS·Defender·WSL변경/다른앱종료/Git/삭제이동0.
PCfreeze 해결/CPU원인 미확정. source/code verification과제품/Gate를구분한다.

다음은 receipt-safe V2 fullpreflight025, failed attempt와분리된실행/diagnostic persistence 경로
qualification, current158제품1회와독립승인이다. 기존성공본문은재실행하지않는다.
원전체scope/600·720·1200/15초실제capture/공유decode5 및원CPU/RAM/Job한도유지.
