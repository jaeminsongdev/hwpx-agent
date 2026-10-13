# P09-87 원본 숨은 설명·MEMO 본문 읽기 정책

## 범위와 원래 목표

P09~P20 전체 제품 구현 목표를 유지한다. 이번 변경은 P09-04의 실제 원본 읽기 누락을 줄이는 작업이며, 댓글 전체 구현·author/time/readback·native Gate를 대체하지 않는다. P09 Gate가 닫히기 전 P10 새 구현을 시작하지 않는다. root PLANS.md는 사용자 지시대로 삭제 상태를 유지한다.

기존 comment-model/v1, REF-026~REF-030 계약과 P11 review.comment_delete 소유권, 실패·private/frozen 증거를 유지한다. 작성자/생성·변경 시각/표시/해결/해결자 필드의 native 연결을 추정하거나 component fixture 값으로 대체하지 않는다.

## 실제 구현 경로

- 원래 ImportedSourcePackage → ImportedDocumentStructure/Forms → ImportedDocumentFields의 불변 원본·리소스·위치·필드 스택을 재사용한다.
- source-preserving paragraph reader에 MEMO의 subList 또는 parameters + subList envelope를 추가한다. 기존 parameters의 namespace/속성/cnt/공백/item/text 검사 본문은 그대로 재사용한다. 비-MEMO payload와 공개 typed paragraph writer/reader의 경계는 유지한다.
- ImportedDocumentReviewBodies는 hiddenComment/subList, 원래 paired MEMO 범위와 본문을 실제 anchor에 연결한다. 원래 Mapper가 문단·run·table/cell·opaque 구조를 읽고, 원래 DocumentGraph validator가 main + 관측 본문 전체의 IDs/resources/control references/aggregate limits를 검사한다. 검사용 임시 그래프는 반환·게시하지 않으며 관측 본문이 main text가 되지 않는다.
- 실제 marker/subList 속성과 전체 Flow 및 전체 source/graph/observation/receipt 결합을 유지한다. 없는 본문은 None이며 cached main text를 댓글로 만들지 않는다. metadata는 UnverifiedNativeMapping이다.
- 같은 XML 전체를 본문마다 다시 순회하지 않고, preserving parser의 start-token 순서에 따른 연속 subtree만 검사한다. item/text/source/graph 및 8MiB 관측 직렬화 한도를 유지하고, aggregate 관측 한도는 다음 본문을 만들기 전에 검사한다. performance acceptance를 주장하지 않는다.
- StoredImportedDocumentForms::import_review_bodies는 원래 provider의 ACL/quarantine/AEAD/digest/head/document/project/branch/tenant/subject 검사와 whole-source 재구성을 derivation/verify 전후에 실행한다. getter는 memory이며 현 시점 권한이나 execution lease가 아니다.
- 새 profile/scope 각각만 남겨도 full-document preparation은 거부한다. 기존 section-settings 거부 함수를 그대로 호출하며 기존 조건을 약화하지 않는다. 새로운 Artifact ingest/revision head commit/publication 경로는 없다.

## 명시적 미지원과 호환성

MEMO metaTag, 본문 안의 fieldBegin/fieldEnd·hiddenComment·footNote/endNote·bookmark 및 잘못된 body/control envelope는 이 읽기 경로에서 거부한다. 해당 의미가 완성됐다는 주장을 하지 않는다. parameters-only/empty MEMO는 관측되지만 본문 없는 것으로 기록한다. 기존 field semantics에서 MEMO는 Unsupported를 유지한다.

새 API는 readonly 내부 projection과 receipt이며 caller XML/map/graph/author/time 입력이나 Deserialize admission을 추가하지 않는다. 기존 comment-state/SQL migrations/capability routing/외부 wire schema와 dependencies/settings는 변경하지 않는다. 기존 36 actual inputs·원래 typed component·source/field/form/note/bookmark/product regression으로 호환성을 검증한다.

## 검증 및 증거 기준

신규 source-reader15 + stored-reader5 검사는 synthetic positive/negative envelope와 고정된 과거 원본을 사용한다. 실제 서비스 구현과 암호화는 실행하지만 actor/scanner/revision metadata는 fixture다. 실제 issuer/authentication, 새 native capture, PostgreSQL 재검증, atomic lease, full comment insertion/style/show/resolve/delete, native 저장·재열기/render/differential acceptance가 아니다.

5 crate lib/tests/examples strict lint, 신규 Rust5개 개별 format과 diff check를 실행한다. root PLANS 재생성, 한글/COM/UI/접근 허용, 운영·trust DB, stage/commit/push는 하지 않는다. 오류나 과거 qualification drift는 별도 기록하고 기존 증거를 덮어쓰지 않는다.

## 남은 원래 요구사항

원본 기반 author/time 및 native 표시/해결/스타일 연결, 나머지 미지원 필드·Date/외부 validation 등 전체 문서 의미와 source-bound policy authority/atomic execution/publication, source re-admission, 정확한 한글 native 의미·저장·재열기·렌더·differential 및 P09 phase Gate가 남아 있다. 지원 증거 없는 항목은 NOT_RUN/unverified/unavailable을 유지한다.
