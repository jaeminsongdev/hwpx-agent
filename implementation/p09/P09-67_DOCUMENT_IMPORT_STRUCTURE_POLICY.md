# P09-67 실제 원본 기반 본문 구조 importer 정책

- 범위: actual HWPX source → partial source-backed `DocumentGraph`. 전체 typed 문서 importer 또는 제품 실행 승인이 아니다.
- 공개 profile: `hwpx-agent.document-import-structure/partial-v1`; scope: `source_backed_body_structure_not_complete_typed_document`.
- 입력은 P66 `ImportedSourcePackage`가 실제 ZIP·모든 part·namespace-aware XML·whole SHA·원본 anchor를 검증한 immutable source뿐이다. caller 그래프나 native 숫자 ID를 원본 위치로 가정하지 않는다.
- 출력은 immutable source와 검증된 IR를 함께 소유한다. 모든 node는 실제 원본 element anchor와 part resource에 연결된다. anchor/논리 ID는 이 문서·원본 버전에 종속되며 cross-revision persistent identity를 의미하지 않는다.

## 변환과 보존

1. 실제 spine에서 section namespace `sec`만 본문 section으로 변환한다. header 등 non-section spine part는 완전한 source/resource/opaque bag에 보존하며 본문으로 꾸며내지 않는다.
2. 기존 문단 validator를 실제 immutable token tree에 적용한다. Unicode·참조 디코딩·run/text 경계·tab/line break·원본 속성·inline 객체 순서를 보존한다. 원본 anchor를 임의 XML 재작성으로 만들지 않는다.
3. 기존 table grid validator를 동일 tree에 적용한다. 행·열·병합 span·cell `subList`·중첩 표·실제 객체 위치를 변환하고 domain graph에서도 재검증한다. 기존 공개 table reader/lowerer의 허용 조건은 변경하지 않는다.
4. 미지원 의미는 실제 source-backed XML `EmbeddedObject`로 보존한다. 폼·필드·노트·참조·layout/catalog/security 의미 변환 완료로 집계하지 않는다. 손상된 지원 구조는 opaque fallback으로 통과시키지 않는다.
5. 실제 저장본의 parameterized field를 읽기 위해 **private SourcePreserving profile**만 추가한다. 기존 공개 typed paragraph reader와 writer는 그대로 TypedParagraph로 동작한다. 기존 field header/type/numeric/bool 및 duplicate/mismatch/unclosed/depth 검증을 그대로 실행하고, 단일 native `parameters` container와 `cnt`/direct child count·속성·whitespace·budget을 검증한다. 그 내부의 안전한 미지원 parameter semantics는 exact opaque로 보존한다. 수식 평가나 parameter 의미가 검증됐다고 주장하지 않는다. 이 profile의 field payload는 typed lowering으로 승격되지 않는다.
6. 모든 part의 raw SHA/length/media를 IR descriptor와 opaque bag에 연결하고, 실제 원본 bytes는 importer가 소유한다. `ArtifactRef` descriptor를 실제 ArtifactService에 ingest된 object라고 부르지 않는다. IR JSON만으로 모든 원본 bytes를 복원할 수 있다고 주장하지 않는다.
7. security-state 기본 bool은 잠금 해제/보호 부재 attestation이 아니다. qualification을 `native_security_unqualified_no_unprotected_attestation`으로 명시한다.

## 검증과 제품 경계

- source의 whole reimport 및 graph 전체 재구성 결과를 비교한다. receipt만 비교하는 재검증으로 대체하지 않는다.
- partial source profile 또는 scope 중 하나라도 있으면 기존 full-document form context가 `Projection`으로 거부한다. marker 검사는 importer issuer signature나 임의 caller graph의 권위 증명이 아니다. signed 실행·publication은 여전히 승인되지 않았다.
- 실제 locked P09 form10과 기존 P06 generated/saved table16을 모두 읽는다. table16의 historical grid oracle 및 모든 node anchor/fresh graph를 확인하되, 과거 native receipt를 이번 native 실행 증거로 재사용하지 않는다.
- 합성 병합/중첩 표와 실제 saved aggregate 표 증거를 구분한다. 실제 saved merged/nested corpus까지 검증한 것으로 일반화하지 않는다.
- 실패한 source와 원본·private 증거를 보존한다. predecessor whole CLI replay/current admission·P62 미해결 실패·full34 native·P09 Gate는 별도로 유지한다.
- 한글/COM/UI/접근 허용창·DB 생성·dependency 변경·commit/push·P10 구현 없이 이 단계만 수행한다.
