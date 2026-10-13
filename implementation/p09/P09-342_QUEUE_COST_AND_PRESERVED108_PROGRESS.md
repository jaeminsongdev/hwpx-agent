# P09-342 — CPU 중단 코드 검토, 원본 범위 계산 및 계약 fixture 복사 최적화 (2026-10-10)

## 목표와 범위

목표 ACTIVE, P09/A12/A13 OPEN. P09 Gate를 닫기 전 P10으로 넘어가지 않는다. 249개 runtime 검증군의 수용101/잔여148(regular142+corpus6)/next108에서 이어서 진행했다. 이 숫자를 전체 P09 진행률이나 전체 잔여 항목 수로 해석하지 않는다. 원 사용자 소스/fixtures/실패·성공 기록과 frozen93 코드 bytes/hash를 보존한다.

## 직전 실패 검토

- 원 v7 actual108 run013은 source_frame_acquire에서 CPU STOP. metadata172fresh 완료 후 Native163/163 전부 close·byte boundary0·제품0·정리TRUE, last4 host100/ownCPU0/읽기증가0, private63287296bytes. 원 FAILED를 PASS로 바꾸지 않았다.
- 원 v7 stop-review014는 anchor CPU STOP. metadata116bound/0fresh·Native/제품0·정리TRUE, 마지막3 host100/ownCPU0/읽기증가0. 원 별도 검토가 완료되지 않았다는 기록을 유지한다.
- 새 v8에서는 원 v7 code2 archive 및 qualified LIGHT/FRESH11/12, CPU STOP13/14를 같은 Reader의 정확한 pin으로 독립 바인딩하고 원 stopped_before_product 검증기를 기대 scope/schema7로 호출했다. 원 실패의 cleanup·제품 미시작을 검토하되 current_GO와 재실행 허가는 FALSE다. 현재 큐 수용 증가0이며, 이 검토 자체는 Native/제품 자격이 아니다.
- v8 light015는 contract_tests CPU STOP. 부분12 started/12 stopped/12 before/11 after, runner1/returned0, metadata176bound/0fresh/176read/14332863bytes·Native/제품0·정리TRUE. 308 계약 PASS가 아니다. last4 host100/ownCPU5.448718,0,0,0/읽기증가0/private71380992bytes, freeRAMmin32.532755%. 원 partial308 코드2와 실패를 보존하고 v9에서 독립 검토한다.

## 적용한 최적화

1. 원본 범위 budget의 조상 경로 계산: 파일1658 각각의 부모는 확인하되 이미 등록된 부모에서 상위 순회를 종료한다. 전체308 디렉터리 집합은 기존 모든 parents 집합과 정확히 같다. 원 Native 잠금·identity·전체 byte 읽기를 제거하거나 변경하지 않으며, Native InputLocks의 기존 중복 조상 제거와 일관된다. CPU 프리즈 개선율을 측정했다는 주장이 아니다.
2. 같은 Reader의 qualification JSON 재사용: LIGHT/FRESH 각 마지막1개, 총2개만 유지한다. 파일크기128KiB 이하의 정확한 scoped filename·맞는 state·source_attempted=False·product=False·closing_component=None만 대상이다. 재사용 직전 원 checkpoint를 호출한다. oversized/제품/실패/Native 자료는 cache로 대체하지 않으며, 별도 명령 간 cache도 없다. 모든 원 bound-input 최종 fresh hash는 그대로 읽는다.
3. LIGHT 합성 fixture projection: 전체 Native frame/body를 매 LIGHT 테스트마다 deep-copy한 뒤 버리던 비용을 없앴다. runner별 full TEMPLATE에서 필요한 LIGHT projection을 한 번 생성하고 매 테스트 그 projection을 별도로 deep-copy한다. source requirement1658/current-next cursor 및 모든 원 거부 조건은 유지한다. full TEMPLATE 무변이, 중첩 테스트 자료 독립, unused Native frame 제거를 테스트한다. 실제 제품/Native receipt를 줄이거나 재작성한 것이 아니다.
4. 원CPU STOP들의 archive-bound 검토: v7 원code2/실패2·v8 원code2/부분12 실패를 보존한다. previous272 qualification과 current320 qualification, partial308 실패를 분리한다. noGO/acceptedDelta0/Native·제품 미시작/정리를 확인한 후 현재 코드 새 contract 및 독립fresh를 요구한다.

새 Runtime source helper를 추가하지 않고 기존 고정2경로만 수정한다. scope1658/code95/controller191/directory308 유지. 보호함수/원 resource owner/guard threshold/실행 oracle은 변경하지 않는다. own1LP/BelowNormal, CPU98x4(.5s), RAM 비율, JobCPU6.25%/active16/killclose/RAMcap8%·stop7%, acquisition14/native20/meta32 no-burst, binary1/other2MiB/s, Native600/metadata720/parent1200, 원 전후 전체byte/identity/정리 검사를 유지한다.

## 현재 코드 검증

- v9 AST syntax 및160 test method 확인.
- light016: 현재160+다음160=320 실제 계약 PASS, 모든 setUp전/tearDown후 및 runner2 전후 원 checkpoint. metadata179bound/179fresh/358reads/29143458bytes·정리TRUE·Native/제품0. ownCPUmax6.395349%machine/private76152832bytes/freeRAMmin32.434672%; hostmax100은 transient 관측값이며 sustained98x4 STOP은 없었다. CPU 개선 원인 또는 프리즈 해결을 주장하지 않는다.
- light-review017: 별도 최신성 검토 PASS, 새로운 계약 실행0/정확히320 재사용, Native/제품0·정리TRUE.
- code2는 evidence/p340-formal320-code/에 bytes/hash 일치로 보존했다. source63174bytes SHA df27dcd564610c1488afa63877e72280e5558e73b978449fecbba996f8f2af3d; test35821bytes SHA caa6165d523f9b3b465a7a6d7fa8cec1d9e235f6cea0baca8ec6ec78ff9cc34b.
- v8 partial code2는 evidence/p340-v8-partial308-code/에 보존했다. 원 v7 qualified272 code2, actual107 code2(v5), frozen93은 불변이다.


## 실제108 결과와 현재 확정 상태

actual108 run018에서 제품 자식은 실제 Job에서 정확히1회 실행되어 exit0·passed1/failed0/ignored0/filtered248, selected test `actual_import::no_form_stored_source_preserves_real_body_without_policy_attestation`를 통과했다. 실제 Job membership/limits 확인, capture complete_streams, owned_tree_empty/cleanupTRUE, Job final active_processes0/owned_processes[]다. 자식 JobCPU 총0.172초, peak private21.05MiB(전체RAM0.066071%). 직접 자식의 CPU·RAM 풀로드라는 증거는 없다. 간접 파일 접근/보안 검사 기여와 PC 프리즈 인과는 여전히 미확정이다.

이후 final_source_freeze에서 host CPU98x4로 중단됐다. caller root는 FAILED_NOT_ACCEPTED/owned_parent, sidecar는 STOPPED_NOT_ACCEPTED/final_source_freeze, 원 빈 body는0bytes다. root의 actual_product_child_executed=False를 제품 자식 미실행으로 해석하지 않는다. sidecar의 실제 자식 실행·passed_test_names·terminal_summary·Job 증거가 위 실행을 확인한다. 원 caller/sidecar를 PASS로 재작성하지 않는다.

원 전체before는1658/121039342bytes 완료했다. after는728/63288057bytes 부분이며 원 partial kind counters도 그대로 보존한다. Native lock1966/1966 close, duplicate2386/2386 close/resets, 남은 handle/reader/stream/close-failure0, FrameCLOSED/unregistered. source full Native 마감은 미완료다.

metadata181bound/181fresh/362read/29354226bytes는 완료했으나 이것을 Native after 완료로 바꾸지 않는다. 전체694표본 ownCPUmax1.862197%machine/private69611520bytes/freeRAMmin31.422142%. 마지막4 host100/ownCPU0, 읽기증가14503,0,0,0, commit39.825~39.964%, 자체 private는 동일하다. child Job IO 마지막 delta는 모두0이었다.

따라서 수용은 **101/249 그대로**, 잔여148(regular142+corpus6), next108이다. 성공 제품의 **source closing pending은0→1**, pending108, whole reconciliation pending98. 새v9 current95의 전체 Native/제품 수용 및 PC 프리즈 해결은 아직 주장하지 않는다. 이번 턴 실제 제품108을 다시 실행하지 않았고, 다음에도 성공 제품을 다시 실행할 권한/GO는 없다.

## 원본 마감 경로 검토와 다음 작업

원 complete_preserved106_source의 source-only 구현, runtime_input_frame.read_boundary/commit, owned_read_backpressure를 코드로 확인했다. 독립 Frame은 모든 입력을 새 before+after로 실제 읽고 original Job cleanup을 확인한 후 held identity를 검사·close한다. 원 partial-after나 cached pin을 실제 읽기로 대체하지 않는다. commit은 semantic product PASS를 만드는 함수가 아니므로, 제품 capture 검토와 독립 source-qualified/compound acceptance를 분리해야 한다.

다음 구현은 고정 runtime2경로 안에 원108 product-success/partial-after를 보존하는 source-only review/closing/accept를 연결하는 것이다. 현재 qualified v9 code2 archive/원 frozen93/원1658 before/sidecar/빈 body를 정확한 pin으로 묶고, 성공 제품의 재실행을 차단한다. 새 코드가 기존 두 controller 경로를 바꾸는 경우 원 executed code95(v9)와 현재 Native/source code95의 별도 epoch를 명시해 검증한다. 원 product Rust/fixture/source1656을 제외하거나 재작성하지 않는다. 이 경로의 구현·검증은 아직 NOT_RUN이다. 원 generic pre-product STOP review로 제품 이미 실행된108을 retry 후보로 분류하면 안 된다.

이번에 원 after reader의 보호·유한 전체입력 순회·두 byte·held identity/borrowed stream 경로를 재확인했다. 새 busy-loop나 sampler를 추가하지 않았고, 별도 경로 reopen은0이다. 이미 멈춘 읽기/자식 상태에서 host 포화가 계속된 것을 근거로 보호 기준을 낮추거나 강제 재시도하지 않는다. 실효성·검증 정합성을 근거로 적용 가능한 큐/자료 복사 최적화를 수행했으며, 전체 저장소 모든 성능 문제 해소를 주장하지 않는다.

## 증거와 문서

- light016: 53610bytes SHA405f431597d4137acb0a9e5f0cabce7b44fd760a709efce20155c0724353b0da.
- light-review017: 51774bytes SHAbe2680ef2bb5256ef671dc187386b2f6df377662388260fd2e07ddc32bb63c25,180fresh/360reads/29250678bytes, 새계약0/재사용320.
- actual108 root018: 988355bytes SHA1a9896bd97da63066101075aa65f2d0a0fdf42bdf5405755faaa2a57849f186d.
- 실패 sidecar108/018: 557079bytes SHAeaa7265c260f5e2ab39813016f317ab4a5d6507c94b2bba473e484a8cb4397f8.
- investigation summary: implementation/p09/evidence/p09-342-queue-cost-and-preserved108.v1.json.

r134 문서3개 전체 byte를 evidence/runtime-progress-r134/에 정확한 SHA로 보존하고 최신요약만 prepend했다. 문서 원 suffix/JSON 수량/AST/code archive 확인은 가벼운 구조 검증이지 제품/Native 또는 현재 문서 final-fresh qualification이 아니다. 문서 최종 fresh마감 NOT_RUN, 마지막 기존 문서 자격 r128/P325와 구분한다.

PTYS11264(v8 light)/27815(v9 light)/3526(fresh)/52973(actual108)는 모두 종료했다. 목표 ACTIVE, Gate OPEN. 한글/접근허용/Git/빌드/설치/push/삭제·이동/Defender·WSL·OS 설정 변경/외부 프로세스 종료는 하지 않았다.

