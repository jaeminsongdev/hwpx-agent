# 보존된 P02 registry의 실제 서명 검증

`hwpx-agent.p09-pinned-p02-registry-evidence/v1`은 P02-09가 보존한 역사적 서명 자료를 실제 공개키로
검증하고 P09 검색 준비의 정책 거부에 연결한다. 서명된 과거 claim을 현재 PC의 동작 검증이나
새 실행 권한으로 승격하지 않는다. P02의 routing_allowed=false와 기존 RouteUnqualified는 유지한다.

## 고정된 원본과 공개 trust

소비 범위는 implementation/p02/P02-09_REPORT.md에 기록된 원본 snapshot 하나다. 새 일반 registry,
trust root 갱신, 최신 sequence 조회, key rotation 또는 실행 승격 API가 아니다.

| 입력 | 고정 identity |
|---|---|
| signed-registry.json | 963624bytes·SHA97c86645a4bf0696474cb6815699a2e4b012f650ae09ef81c582b672580b85e4 |
| P02 공개 trust policy | SHAc96c6f4d4eddecd62dfb4c95badc8f1693a3e4d05c3b3dbc96bf26850212054c |
| P02 공개 Ed25519 key PEM | SHA838f7ce354cb2e284ca8b1e108c4234481b66fdfc0c9d415de43dc7cd3da57f5 |
| 원 canonical payload | SHA3958ccc564be09d0f40889287fa4f2db36584596001a7a2b9e8df0ca57a9450f |
| 내장 source registry | SHA986953421c74d033bcb17dbd763eb6daa0b06c1a5a8b9e3720951fc674d6fd48 |

PinnedP02RegistryBytes는 envelope/policy/public_key의 빌린 바이트만 받는다. trust boolean·개인키·
caller executable 허가는 받지 않는다. 모든 원본 pin을 확인한 뒤 중복/escaped/nested key와 비객체
root를 거부하고 canonical payload를 원 해시와 대조한다. PEM의 Ed25519 SPKI DER prefix/크기와
DER 기반 key ID·공개키 identity를 확인한 뒤 ring의 실제 Ed25519 verifier를 호출한다.

서명 검증 후 내장 registry의 Base64/원 SHA·target·전체 capability 집합과 binding_key/feature_id
projection 및 coverage를 대조한다. payload·공개 policy의 target/sequence와 금지된 release 범위도
확인한다. 이 검사는 고정 bytes에 한정되며 임의의 새 registry에 대한 전체 P02 schema/probe 검증기가 아니다.
개인 서명키나 원 과거 probe 실행은 읽기/재실행하지 않는다. P00~P08 파일을 변경하지 않았다.

## 역사적 claim과 실행 권한

PinnedP02RegistryEvidence는 외부 생성자와 역직렬화가 없는 불변 객체다. 같은 검증 호출에서536개의
SignedSupportClaim을 한 번 색인하고 이후 capability 조회는 보관한 index를 사용한다. 원문/base64/
raw binding을 보관 객체·Debug·공개 receipt에 노출하지 않는다.

원 snapshot의 source candidate32/unavailable504와 서명된 verified2/failed1/blocked17/not_run12를
보존한다. SignedSupportClaim의 VerifiedCurrentTarget은 원 서명에 담긴 과거 주장일 뿐 새 현재 검증이 아니다.
signature_verified는 true지만 routing_enabled/execution_authority와 runtime_probe_reexecuted/
current_installed_target_observed는 false다. signed_target도 원 서명 대상이며 현재 설치 관측이 아니다.
require_routing은 이 고정 policy에 따라 항상 RoutingDisabled를 반환한다.

prepare_compiled_search_json_with_pinned_registry는 기존 닫힌 schema 분류 뒤 원본 읽기/후보 준비 전에
그 정책을 확인한다. Form/Formula·미지원 schema는 원 분류에서 거부하며, 알려진 검색 schema라도
금지된 registry의 요청은 원본에 접근하지 않는다. 현재 금지된 상태에서는 기능별 내부 요청 검증/후보
생성까지 진행하지 않는다. approved/support/target/registry_trust/routing_enabled나 복제 receipt의
true를 실행 허가로 사용하지 않으며, 원 strict 준비·compiler·보호·기존 route 본문은 그대로다.

## 자원 한도와 검증

기존 P02 한도인 envelope64MiB·내장 registry32MiB·공개 trust/key64KiB를 적용한다. Base64는
canonical padding bit·마지막 padding·alphabet/출력 상한을 할당 전에 검사한다. canonical payload는
원 bounded writer를 사용한다. 실제 허용 자료는 위 고정 pin뿐이며 다른 크기/내용으로 범위를 넓히지 않는다.

components225는 실제 고정 서명 자료를 사용한 crypto12+제품6=18pass·780fresh/final780·
진단/경고없음·cleanupTrue다. 실제 서명과 payload/signature/public-key 변조 거부·trust pin·empty 입력·
Base64 vector/padding/상한·중복/escaped/nested JSON/객체 shape·전체 claim 조회/비노출을 확인했다.
제품은 모든16개 schema의 원본 접근 전 정책 거부·legacy/미지/잘못된 외부 요청·caller 권한 flags·
복제 receipt·held snapshot의 현재성 미주장·원 candidate/manifest 실행 차단을 확인했다.
개인 서명키를 읽지 않았고 원본/보호44·compiler36·공식249는 반복하지 않았다.

225 전체125.281초·두 명령6.641/18.468초·시험0.36/1.29초·Job CPU합23.000초·
private최고996.93MiB/3.1290%·시스템CPU최고52.34%·가용RAM최저28.0415%다. 두 Job active0/empty/
handle closed와 한 코어 affinity4·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·
명령300초·guard600초를 유지했다. OS/Defender/다른 앱 변경이나 PC 프리즈 해결을 주장하지 않는다.
근거는 implementation/p09/evidence/p09-361-pinned-p02-registry-components225.v1.json이다.

## 남은 현재 P09 실행 경계

실제 자격을 갖춘 P09 target/registry와 Native 보호, 실행 dispatcher·ingest/commit/CAS·영속 멱등 실행·
transport/게시·전체 검색/참조·target match_set/semantic_diff/reopen·Native/Gate는 미완료다. 고정 P02를
그 자격의 대용품으로 쓰지 않는다. source API v12 incomplete/미해결4/report없음/exit3·공식158/249·
잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.
