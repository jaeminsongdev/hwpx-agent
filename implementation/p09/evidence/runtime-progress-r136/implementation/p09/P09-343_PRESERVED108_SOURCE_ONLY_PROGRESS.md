# P09-343 — 보존108 source-only 마감 경로와 현재95 고정 코드 검증 (2026-10-10)

## 범위와 원칙

목표 ACTIVE, P09/A12/A13 OPEN. 수용101/249, 잔여148(regular142+corpus6), next108, 성공제품의 source closing pending1에서 시작했다. 이249개 검증군은 전체P09 항목 수/진행률이 아니다. 원108 제품은 이미 정확히1 PASS/exit0·Job membership/cleanup이 확인됐지만 final_source_freeze CPU STOP이므로 원 FAILED/STOPPED/부분after728/빈body를 보존한다. 제품108을 재실행하지 않는다.

## 구현

변경은 기존 tools/p09/resume_preserved106_queue_runtime.py 및 tools/p09/tests/test_preserved106_queue_runtime.py 두 경로에 한정했다. 새 runtime/helper source 경로는 추가하지 않았다. full1658/code95/controller191/directory308을 유지한다. frozen93 및 실제108 실행 code95(v9) 원본은 바꾸지 않고 archive bytes/hash로 연결한다.

- pending108_review: 원 root018/sidecar/빈body, qualified320 light016/fresh017, v9 code2를 독립 바인딩한다. 실제 자식 실행/exit0/정확한 테스트/capture/Job, 원 전체before1658·partialafter728·1966잠금/2386duplicate 모두 close·원 metadata181fresh를 확인한다. 원 FAILED를 수용하거나 pre-product retry 후보로 바꾸지 않는다.
- actual108 재실행 차단을 별도 명시했다. 기존 빈body와 실패queue 차단에 추가하며, source-only 마감 뒤에는 다음109부터만 진행할 수 있다.
- closing-review/source/accept 세 모드와 정확한 literal pin chain을 구현했다. review는 current/following202x2=404 실제 계약, source/accept는 새계약0/정확히404 재사용 및 모든 입력의 별도 final-fresh를 요구한다.
- source는 원 resource owner/InputLocks/Frame/OwnedReader를 사용해 현재 full1658 전체byte를 새 before+after로 실제 읽는다. 옛 executed95의 two-controller(v9) pin과 현재 controller2 pin을 별도 epoch로 기록한다. 나머지 원1656 입력은 동일 pin이며 모두 읽는다. commit 시 원108 Job cleanup을 확인하고 held identity를 검사·release한다. 새 제품/부모/Job을 실행하지 않는다.
- Native source oracle은 기존 complete_preserved106_source.validate_source를 재사용한다. 106 전용 metadata header만 현재108의 명시적 header validator로 바인딩하고, 원 두byte/fullscope/borrowed handle/identity/CPU600/정리 oracle은 그대로 유지한다.
- accept는 정확한 review/source/current95를 같은 Reader로 검토하고 새 full metadata freshness 후 독립 compound102만 만든다. 원 root의 PASS 재분류나 부분after의 full 승격은 FALSE다. accept 이후 ordinary queue는 compound102를 먼저 검토한 뒤 다음 항목을 선택한다.
- 별도 bounded closing namespace와 current-code/cursor/state/원제품미재실행/원 실패보존/정리 거부 검사를 추가했다. 범위/검사를 줄여 수용하지 않는다.

own1LP/BelowNormal, CPU98x4(.5s), RAM 비율, JobCPU6.25%machine/active16/killclose/RAMcap8%·stop7%, acquisition14/native20/meta32 no-burst, binary1/other2MiB/s, Native600/metadata720/parent1200, 원 원본/metadata fullfresh/identity/정리 제한을 바꾸지 않았다.

## 구현 과정의 실패 보존

- v10 최초 실행 준비는 Python 정적 중첩 블록 제한 SyntaxError로 진입하지 못했다. AST parse만으로 실제 compile 성공을 주장하지 않는다. 원200+기존 fixture 패치들을 patch.multiple 한 바인딩으로 묶어 같은 자료/reset/restore를 유지했다. precompile code2는 evidence/p340-v10-precompile400-code/에 보존한다. 이 실패에서는 resource watcher/Native/제품이 시작되지 않았다.
- closing-review019는 실제 current200/runner1에서 합성 pin 변조 검사2가 실패했고, Native/제품0·정리TRUE·resource reasonNULL이었다. 비교용 기대 pin과 결과 안 pin이 같은 객체라 변조가 양쪽에 반영된 fixture alias였다. 기대 pin을 독립 deep-copy하고 두 객체 분리 검사를 추가했다. 원 실패를 PASS로 바꾸거나 검사 삭제하지 않았다. 원 code2는 evidence/p340-v10-partial400-code/에 보존한다.
- v11은 원 closing-review019 pin/code2·실패2 ID·200 전후/runner1·186bound/0fresh·Native/제품0/정리를 독립 확인한다. previous400 qualification은 NOT_PASSED로 유지한다.

## 현재 코드 qualification

closing-review020: current202+following202=404 실제 계약 PASS, 원 setUp전/tearDown후 및 runner2 전후 checkpoint, 기존 unittest 결과/guard/coverage 유지. Native/제품0·정리TRUE. CPU 프리즈 해결과 전체 제품 완료를 주장하지 않는다.

Qualified v11 source90666bytes SHA cbc7051ab7542ab71efe239758dcd9651954e20edfd739ce434dae1c193c3dc4, test44786bytes SHA fa3a811c945d3ca6b2087a99d4704f8784599d9142a148c8d62a9cb22b51ee1e. 같은95/full1658 코드2를 evidence/p340-formal404-code/에 해시 일치로 보존했다. 원 v9 qualified320 실행코드, 원108 sidecar 및 frozen93은 그대로다.


## Source-only 실제 시도와 확정 결과

closing-source021은 새 제품/부모/Job 없이 진행했다. metadata190bound/190fresh/380read/34211174bytes 완료 후 원 full1658 Native 잠금1966개를 획득했고, 첫 실제 byte 경계 metadata_hash에서 CPU STOP이었다. FrameCLOSED/unregistered,1966/1966 잠금 close·duplicate426/426 close/resets, 남은 handle/reader/stream/close-failure0, source_frame boundaries[]다. 426개의 읽기 진행을 전체before나 최신SourcePASS로 승격하지 않았다. SourceQualifiedFALSE·제품FALSE·정리TRUE로 원 FAILED를 보존한다.

원481표본 ownCPUmax1.252236%machine/private74620928bytes/freeRAMmin29.719257%. 마지막4 모두 hostCPU100/ownCPU0/읽기증가0·logicalreadpasses806(380metadata+426source)로 고정됐다. 원 early90 경고는3entries/12pause windows/6.0초였고, hard98x4·600·원IO를 유지했다. 자체 CPU·RAM 풀로드의 직접 증거는 아니며, 파일 접근의 간접 부하와 프리즈 원인은 미확정이다. 같은 Source 명령을 자동 재시도하지 않았다.

현재 **수용101/249 그대로**, 잔여148(142regular+6corpus), next108, 성공제품 source closing pending1, whole reconciliation pending98다. source-only 경로 구현과404 계약 검사는 완료했지만, current95(v11) fullNative/source 및 compound102 수용은 미완료다. closing-accept는 실행하지 않았다. 원 제품108 및107 재실행0, Gate OPEN.

## CPU STOP 후 추가 코드 검토와 다음 작업

runtime_input_frame의 Registry/check/ordered read_boundary/commit/close, Borrower.sources/open/release, audit_evidence_io._source/_read/fresh_pin 및 OwnedReader pressure를 확인했다. frame guard는 owner-reference와live-state/원deadline을 확인하고, 원 source byte loop는 bounded chunk/pacing 및 매 read checkpoint를 유지한다. duplicate borrow는 원 held stream identity 검사와 serial cleanup을 유지하며, pathname reopen은0이다. 새 sampler/spin/guard 완화가 없다.

이번 실패의 metadata_hash 경로에서는 borrowed source adapter가 원 audit reader의 is_file/is_symlink/is_junction 경로 검사를 각 파일에서 먼저 수행하는 것을 확인했다. 이 세 논리 검사를 실제 held handle의 신선한 metadata로 함께 판정하면 반복 pathname 조회를 줄일 수 있는 후보가 있다. 아직 구현·측정·Native 자격은 NOT_RUN이다. 적용하려면 모든 원 상대경로/link/type/identity/owner/guard 의미를 유지하고, 살아 있는 정확한 handle과 parent-directory 잠금 범위만 사용하며, serialized pin이나 과거 cached metadata로 대체하면 안 된다. 작은 Native 자격 확인은 full1658 source 마감을 대신할 수 없다.

다음 목표 작업은 이 Source 읽기 경로의 중복 pathname 조회 후보를 검토/정합성 구현·원조건 거부검사·Native 검증한 후, 정확한 source021 실패 검토와 새 독립fresh를 거쳐 source-only 마감을 완료하는 것이다. 원108 제품 재실행은 계속 금지한다. source 실패의 partial/정리 결과와 원 code95 epoch를 보존하며 검증 범위·CPU 임계치·deadline을 낮추거나 늘리지 않는다. 현재 단순 retry 또는 P10 진행은 없다. 아직 안전한 관련 코드 최적화 작업이 남아 있어 목표는 ACTIVE로 유지한다.

## 증거, 문서, 종료 상태

- closing-review020: 186067bytes SHA d6ad33748c2092ea1065938fa9d2834975b6380c12d77fce836d12d0eecb769a,404 계약/189fresh/378reads/33839040bytes/정리TRUE.
- closing-source021: 819478bytes SHA 8c94da41f340ef9d877a488b1a56ab23d10fa6f6dfda566777dc5d2530b30f95,원 FAILED/Native partial/제품0/정리TRUE.
- closing-review019 원 실패:429686bytes SHA d47ba93eb8c8d40be27658663574203929332932639dd2be20385900e86f39b2.
- 요약: implementation/p09/evidence/p09-343-preserved108-source-only-progress.v1.json.

r135 문서3개 전체 byte는 evidence/runtime-progress-r135/에 SHA 일치로 보존한 뒤 새요약만 prepend했다. 문서 suffix/AST와compile/진단JSON/code archive 확인은 가벼운 구조 검증이며 제품/Native/현재 문서 final-fresh 자격을 대신하지 않는다. 문서최종fresh 마감NOT_RUN, 마지막기존문서자격r128/P325와 구분한다.

이번 PTYS42071(review019)/61387(review020)/9955(source021)는 모두 종료했다. Native 잠금과 원 감시기의 종료를 원 기록으로 확인했다. 한글/접근허용/Git/빌드/설치/push/삭제·이동/Defender·WSL·OS 설정 변경/외부 프로세스 종료는 하지 않았다.

