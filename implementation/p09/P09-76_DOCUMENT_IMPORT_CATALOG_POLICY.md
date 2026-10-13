# P09-76 원본 typed header와 실제 스타일 참조 연결 정책

## 목적과 입력

P09 전체 문서 제품 경로에 필요한 스타일 카탈로그 누락을 닫는 source component다. 기존 Source→body/forms→field ranges→field meanings의 immutable 모델에서만 파생한다. caller graph, caller catalog, raw selector, 임의 artifact/path, 실행 승인 또는 기본값은 받지 않는다.

범위는 현재 지원 header `Contents/header.xml`의 Hancom 2011 `head/refList/styles`, `paraProperties`, `charProperties`와 실제로 typed body에 표현된 문단/run 참조다. 다른 header 위치나 전체 카탈로그/보안/설정/레이아웃의 완전한 의미를 주장하지 않는다. 각 원본 XML part와 subtree는 기존 source archive/resources/opaque bag에 그대로 보존한다.

## 의미와 식별자

- 원래 `CharacterStyleCatalogReader`, `ParagraphStyleCatalogReader`, paragraph→character border/fill 검증을 그대로 호출한다. reader 오류를 source-only fallback으로 숨기지 않는다. 원래 font/reference domains, 수치·enum·색·범위·count·dense ID 검사를 변경하지 않는다.
- named style은 원본 attribute 관찰과 source relationships다. named style 전체 business/type/lock/name 의미의 새 구현이나 cascade 완료를 주장하지 않는다.
- 세 정의 종류는 각각 별도 native numeric ID 공간이다. duplicate와 itemCnt 불일치를 거부하며 native number를 전역 logical ID로 사용하지 않는다. logical ID는 실제 document/package/part/span anchor에서 유도한다.
- named style의 `charPrIDRef`, `paraPrIDRef`, `nextStyleIDRef`가 실제 정의에 연결돼야 한다. next style은 다음 문단 관계이지 inheritance가 아니다. `Style.based_on`은 None이며 유효한 self/next 관계를 임의로 DAG로 바꾸지 않는다.
- 문단 `styleIDRef`는 그 문단의 `NodeCommon.style_refs`에 연결한다. `paraPrIDRef`는 원래 문단 properties에 source relation으로 추가한다. run `charPrIDRef`는 원래 run source anchor/inline segment에만 붙인다. run 글자 속성을 문단 전체 스타일로 적용하지 않는다.
- 없는 attribute에 0/default/caller 값이나 native inheritance를 추정하지 않는다. 지원 body parser의 foreign namespace 거부는 그대로 유지한다. 표·note·drawing의 typed 문단도 같은 actual anchor 규칙을 적용한다. opaque 아래 숨은 문단의 typed completeness는 주장하지 않는다.

## 검증과 제품 경계

whole fresh Source/body/forms/ranges/meanings/header/uses/typed reader 상태와 graph/receipt 전체 equality를 검증한다. 이번 추가만 제거하면 원래 graph 전체가 같아야 한다. 정의와 lookup은 기존 XML/domain 유한 한도 안에 있고, typed ID membership은 BTreeSet/Map으로 검사한다.

저장 경로는 원래 authenticated service verification을 생성 전·후 및 cached verification에서 재사용한다. tenant/subject/project/branch/document, ACL, scanner/quarantine, AEAD, digest, node/descriptor/head/source guards를 우회하지 않는다. 정상 READ audit 외 ingest/CAS/seal/publication을 하지 않는다. 반복 head read는 atomic lock/idempotency가 아니다.

새 profile/scope 각각은 단독으로도 full-document product context를 차단한다. 이 source 연결을 native formatting cascade/render/security/정식 Source-Result-IR lineage/issuer/ExecutionManifest/게시·복구 또는 P09 Gate로 승격하지 않는다. P26 failed_semantic_non_green, P62 UNRESOLVED, current admission INPUT_CHANGED_RE_ADMISSION_REQUIRED, full34 NOT_RUN/0green, Goal ACTIVE/no P10 경계를 유지한다.

한글·COM·UI·native dispatcher 및 접근 허용 창은 실행하지 않는다. 원본·실패 증거·사용자 dirty worktree를 보존하고 stage/commit/push/원본 삭제·이동/보호 설정 변경을 하지 않는다.
