# P09-83 저장 정책 파일의 실제 읽기·해석·원본 연결 정책

## 완료 조건과 제품 경계

P09-82의 schema20 정책 metadata와 실제 암호화 artifact의 정책 값을 연결하려면, repository가 선택한 최신 유효 version만 읽고 원본 source/revision/head/provenance/graph와 정확히 일치하는 typed payload를 검증해야 한다. 이번 구현은 그 실제 ArtifactService 소비자와 엄격한 decoder다. SQL20 repository adapter, 기존 schema19 revision adapter의 새 exact profile, 등록 서비스/정책 issuer/전체 importer/실행·native Gate는 계속 후속 요구다. trait나 synthetic repository/scanner fixture를 실제 PostgreSQL 제품 연결 또는 외부 issuer로 세지 않는다.

## 동일성과 접근

- policy artifact 선택은 authenticated server repository에만 맡긴다. 요청자가 artifact ID, raw 정책 값, scanner verdict, authorization flag를 이 경로에 전달하지 않는다.
- read scope는 기존 provider와 실제 imported source에서만 구성한다. tenant/subject/project/branch/document/head를 전달하며 repository는 매 호출마다 최신 version/철회/프로젝트 membership/양쪽 artifact ACL/source head를 확인해야 한다. 과거 version fallback은 금지한다.
- SQL20 row의 source revision/head/Result artifact/package SHA/provenance SHA/observed graph SHA, policy version/generation/creator를 payload에 함께 고정한다. payload가 자기 digest를 포함하지는 않는다. 외부 row의 policy artifact/raw digest가 독립적으로 전체 payload를 고정한다.
- 기존 ArtifactService의 실제 descriptor/ACL/tenant/state/quarantine/AES-GCM/raw digest 검증을 재사용한다. Evidence 역할만으로 정책을 인정하지 않고 전용 media type과 최대1MiB를 검사한다. 검증 metadata는 decoder/domain validation을 대신하지 않는다.
- 원본 source는 기존 32MiB/실제 source reader와 whole importer 검증을 그대로 사용한다. row와 payload를 원래 source/observed graph에 비교한 뒤 원래 PolicyBoundDocumentForms로 전체 form state/graph를 재구성한다. 원래 names/items/current values/native IDs/styles/opaque state는 payload로 덮어쓸 수 없다.

## payload 계약

`hwpx-agent.source-form-policy/v1`: schema_version, binding, policies가 필수다. 각 policy는 node_id/source_anchor/values만 받는다. Text/Checkbox/Radio/Combo/List의 명시적 defaults/validation만 지원한다. 모든 unknown/duplicate/missing 필드는 거부한다. nullable selection/default/validation 필드는 null도 명시해야 하며 생략으로 기본값을 만들지 않는다. source anchor/order/kind/complete policy set/domain validation은 기존 source-bound component의 검사를 그대로 따른다. 정책을 실행하거나 external validator를 호출하지 않는다.

## 재검증과 한계

생성 시 repository read → 실제 policy download/typed decode/domain bind → repository re-read → fresh whole source authorization를 수행한다. cached verify는 이 전체 경로를 다시 실행하고 version/raw bytes/policies/whole graph/state/receipt를 모두 비교한다. 일반 access audit 이외 ingest/commit/head/manifest/publication은 없다. 이것은 반복된 fresh read로 관측 구간을 묶는 것이며 atomic SQL lease/CAS나 동시 revoke 방지의 증거는 아니다. 이미 읽은 메모리 component의 getter는 실행·접근 capability가 아니다.

## 보존과 검증

원래 구현/guard/정책 API/schema1~20를 변경하지 않는다. 두 parent에 module 선언만 추가하고 변경 전 전체 원문과 선언 제거 역비교를 보존한다. 새로운 세 Rust 파일만 개별 포맷한다. 실패한 fixture/lint/build 기록은 성공 결과와 별도로 기록한다. 실제 암호화 서비스에 synthetic repository/scanner와 test key를 연결한 검사임을 표시한다. 실제 한글/COM/UI/접근허용/운영 DB/grant/배포는 실행하지 않는다. root PLANS.md 부재를 유지한다.

P09 Gate OPEN, P10 새 구현 없음, 목표 active. P26 semantic failure/P62 UNRESOLVED/current native re-admission required/full native34 NOT_RUN을 그대로 유지한다.
