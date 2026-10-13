# P09 r97: 공개 요청 주입 차단과 registry7 전체 개별 수용

2026-10-09. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용69/249 · 잔여180(일반174+corpus6) · 미closing후보0 · 다음index76.
whole재조정대기66. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.
이 수는 고정 r07 개별 runtime 큐이며 P09 전체 잔여 작업 수·완료율이 아니다.

## 실제 확인 범위

원 P230 caller/source1512와 수용된 helper/test/EXE/Rust785는 수정하지 않았다.
기존 수용61개 본문은 재실행하지 않고 strict record/소스 동일성만 확인했다.
68/run008부터75/run015까지8개를 한 번씩, 이전 종료·읽기 전용 요약·CPU/RAM·
COMMITTED/Job active0/핸들 정리 확인 후 다음 한 개만 실행했다.
69~75 도구 순차 루프도 한 번에 실제 실행 하나만 유지하고,
실패/관측 오류/95이상 경고 기록이 있으면 다음 실행을 시작하지 않게 구성했다.
이는 원 자원 정책 변경이나 일반 부하 시작 임계값 추가가 아니다.
이번8개 모두 Native warning0/pause0/CPU STOP 없음이었다.

68: 요청6개 주입 필드(issuer/approval/public_key/signature_hex/trust_generation/now)를
서버 trust 읽기 전에 거부/trust_calls0/audit 수 불변/no_publication.
69: 승인 record의 policy·root 버전/generation/branch·document/artifact alias/
최대 generation9가지와 source-head generation 불일치 별도 거부/redacted Debug/no_publication.
70: prepare 후 registry denied를 설정하여 with_verified_bytes 거부/
consumer callback 미호출/no_publication.
71: 원본·현재 입력 각각에서 original Ed25519 제품 경로의 검증 bytes==current(original)/
Changed receipt 일치/역사적 미허용 current product route 거부/
명시적 읽기 ACL을 준 reader의 동일 검증 bytes/no_publication.
72: root artifact의 잘못된 kind/media/AEAD 변조/digest 불일치/
reader root ACL 부족/quarantine을 거부하고 valid root baseline을 확인/no_publication.
73: same-generation root 변경=Drift/모의 clock 역행=Clock/만료=Time/
provider·record redacted Debug/no_publication. Windows 시간 변경 없음.
74: root JSON unknown/duplicate/coercion/positional/trailing/빈·중복 key/
잘못된 scope·issuer·version/32769bytes oversized payload 등15가지 거부/no_publication.
75: 보호 조건과 위조 Ed25519 서명을 신뢰 메타데이터만으로 대신하지 못하게 거부/no_publication.

검증은 제품 코드의 합성 registry/artifact fixture 경로다.
실제 SQL 운영 연결·등록/생산 key custody·issuer 운영 인수/한글 UI acceptance가 아니다.
고정 inventory339893bytes/SHA7b06997d3b8090967597fad1d12b94446e20e3a17ba206233ae8711fdb1d455d와
case75 root를 원 Reader로 새로 읽어 registry required7/accepted7/missing[] 및68수용을 확인했다.
이 census는2bound=fresh/finished/cleanup/stop=null이며 새 EXE·제품 Gate 실행이 아니다.

## 자원 기록

원 watcher 표본 범위의 최대·최소값이며 원인 귀속이나 전 PC 무중단 보장이 아니다.
owner 종료 후 최종 root 쓰기는 이 CPU 표본 범위 밖이다.
자체CPU최대3.495146%/가용RAM최소41.059647062213145%/
Job peak최대35.12MiB. 전체CPU최대82.69%,95이상 경고 기록·새 지속 CPU 중단 없음.

| index | parent초 | 전체CPU최대% | 자체machineCPU최대% | 가용RAM최소% | Job CPU초 | Job peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 68 | 196.5 | 30.67 | 3.495146 | 41.49150451884687 | 0.938 | 24.16 |
| 69 | 198.31 | 35.48 | 2.923977 | 41.158354885951454 | 3.359 | 29.21 |
| 70 | 204.78 | 82.69 | 2.901354 | 41.059647062213145 | 3.406 | 29.27 |
| 71 | 236.8 | 45.18 | 3.468208 | 41.837478444827646 | 38.984 | 35.12 |
| 72 | 202.35 | 43.19 | 3.059273 | 41.39721040974597 | 5.688 | 29.31 |
| 73 | 199.25 | 38.4 | 2.819549 | 41.60841891546449 | 3.25 | 29.38 |
| 74 | 198.31 | 78.05 | 2.767528 | 41.636556346277985 | 3.328 | 29.09 |
| 75 | 197.62 | 37.27 | 2.862254 | 42.05082024595425 | 1.875 | 24.2 |

### 68/run008

actual_import::formula_policy_issuer::public_request_cannot_supply_issuer_approval_keys_clock_or_signature_before_server_reads.
root 575408bytes/SHAc4c367f9762aa01d1718acb4255906e3842a27f2e1e57722e1ca701b8315f995.
body 164583bytes/SHAbe9cb69c4f15de861ce75d7f35b9c87c10c35526e0ea3928b8f4d0bb92d0c365.
prep175bound=fresh/finished/read207743439bytes/
702표본/private최대42340352bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

### 69/run009

actual_import::formula_policy_issuer::registry::registry_approval_rejects_wrong_policy_root_scope_alias_and_generation.
root 575268bytes/SHAf5d3d7bd3127defed838c7739fcd963e7f38b81c8426ac18cfdff2154ee83ea6.
body 166699bytes/SHA8c8ee8520097e41703671651360aa06cbb5db6d736d4ec6578a9d804238da412.
prep177bound=fresh/finished/read209388004bytes/
707표본/private최대41836544bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

### 70/run010

actual_import::formula_policy_issuer::registry::registry_denial_after_prepare_never_calls_consumer_or_publishes.
root 578652bytes/SHAe75effa8f946315f27817924a680bf2696c5d58d17777689b349f9e8cf2068cd.
body 168615bytes/SHAb18eed34d6aa40bac2e97d687f6542af1decf14cea0e89813caa6ca7c37fbb92.
prep179bound=fresh/finished/read211038637bytes/
718표본/private최대42143744bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

### 71/run011

actual_import::formula_policy_issuer::registry::registry_genuine_changed_current_and_historical_owner_reader_use_original_ed25519_product.
root 582788bytes/SHA7524ac1f668d57a3ec4194eca018cbcdf215b2d8dd0ef3375592b17dac002dac.
body 178815bytes/SHA3a70729b42b18458d94cdaeb5073fa84d829164c25c8e6965cfc99f8195e3e26.
prep181bound=fresh/finished/read212701786bytes/
783표본/private최대42258432bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

### 72/run012

actual_import::formula_policy_issuer::registry::registry_root_artifact_media_kind_digest_acl_and_aead_fail_closed.
root 577732bytes/SHA33c088d1f85a90015ab3ac377c9c69e22c0c61243b650786debcd3549654e04b.
body 168723bytes/SHAdedaa37ab34b3c40947316ba3abc93523fe2718eb5cb1dd027e0e8f887d93768.
prep183bound=fresh/finished/read214403807bytes/
720표본/private최대42364928bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

### 73/run013

actual_import::formula_policy_issuer::registry::registry_root_same_generation_change_and_clock_backward_expiry_are_denied.
root 577696bytes/SHAf90083052991f661d221fe51c60fad0c1a7bf4e0a1896a854ac2546a77219923.
body 167867bytes/SHA56083be3e2ad892093737564a0212b84dc262dff51217de0dd010bc688eb607c.
prep185bound=fresh/finished/read216065440bytes/
715표본/private최대42741760bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

### 74/run014

actual_import::formula_policy_issuer::registry::registry_root_strict_payload_rejects_unknown_duplicate_coercion_positional_and_trailing.
root 578656bytes/SHA43b671f62791040ee5bf634f8817a32019bbb17daa6e05111bb21083a8276854.
body 166595bytes/SHA8a5b2134884510fcace0846e89d7f9c72067837d26aa0553bfa3f2794470db00.
prep187bound=fresh/finished/read217724433bytes/
719표본/private최대43122688bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

### 75/run015

actual_import::formula_policy_issuer::registry::registry_trusted_metadata_does_not_replace_ed25519_or_protection_checks.
root 577312bytes/SHA4aab8f03edf2f0bb9d5a295160de1f52d7894b8ed38e4a7550a659860012da96.
body 163823bytes/SHA54f89776c14111dd6566e55714978f8f865d9144729c644d45258788a49440ee.
prep189bound=fresh/finished/read219381530bytes/
715표본/private최대42442752bytes.
exact1PASS/248filtered/exit0/COMMITTED/156계약/Job active0/tree empty/cleanup/stop=null.

모두 전후1512입력 각118919360bytes/잠금1818·복제3024 모두close/잔여0/
close실패0/resets3024/directory306/ancestor305/별도 pathname reopen0/
원 cleanup 후 release/두 전체 실제 byte 읽기/held identity/finalfresh 유지.
실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결 유지.
원 Job CPU6.25%/affinity1/BelowNormal/RAM percent/GO 뒤 실행/한 watcher/
32Native open/s/no burst/600초/1440표본/98x4 hard STOP는 바꾸지 않았다.
JSON 필드 제거0/기존 원장 재작성false/new sampler false/CPU 성능 개선 주장false.
이번 회차는 수용된 실행 코드 변경 없이 기존 보호·검증 경로로 진행했다.
성능 향상이나 프리즈 해결을 새로 입증했다고 주장하지 않는다.

## 문서 동기화 및 남은 경계

r96 원장318318bytes/SHAe417cff2f2ca1569ae1a41824728b4f93ab3717794509c19344c3f4c6d52993a/
수용61/next68/187fresh/cleanup 상태와 실제 pin을 대조했다.
r96 rootdoc 전체 bytes는 runtime-progress-r96에 exact SHA/크기/덮어쓰기 없는 사본으로 보존한다.
CURRENT_STATE.md 438970bytes/SHA5c6eaacf98e89f78faf38046d3c183bb5057e0addf36717ead956261716f6a30.
P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md 532602bytes/SHA9f5994dc257bdd408e9c85ec7fa3cbdd840d4956d2f622a3affa97e92ee90e95.
새 동일 prefix만 추가하고 이전 bytes 전체를 suffix로 보존한다.
원 P232 verifier를 수정 없이 재사용해 현재156+문서24계약/새actual pair8개=
plan 증가량8/이전문서 suffix/각root SHA/모든 finalfresh·cleanup을 대조한다.
문서 검증 자체는 새 EXE·GO·full source frame을 실행하지 않는다.

CPU 보호 중단 시 자동 재시도 금지: 관련 경로의 CPU·RAM·Job·핸들·최종 쓰기/정리 증거를
먼저 검토하고 가능한 개선을 새 버전으로 검증한 후 재개한다.
실제 CPU STOP 재현은 NOT_RUN. 이번에 실제 STOP sidecar 기록을 주장하지 않는다.
원 P222 STOP root SHA78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0와
0byte body SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855 보존.
P227 합성 parent STOP 연결 지원 SHA3e980627f22938f16a9fc46f14b1fa1cf3fe8b63fa7907e73333bc93e1f60c68 보존.
지난 r96/P233의 순간100% 피크 검토·원인 미확정 상태도 보존한다.
full249/whole1470/historical67/signed16/실제 SQL/생산 issuer/한글 접근허용/
통합·제품 Gate는 별도 미완료다. P09·A12·A13 OPEN, 목표 active 유지.

다음index76:
actual_import::formula_policy_issuer::server_trust_requires_explicit_nonempty_unique_keys_exact_scope_generation_and_lifetime.
