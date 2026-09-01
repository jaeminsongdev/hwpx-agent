# DirectHWPXBackend

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 역할

Rust로 HWPX package를 안전하게 읽고, DocumentGraph로 변환하고, normalized/surgical 모드로 작성한다. deterministic authoring과 대량 처리의 기본 경로다.

## 모듈

- ZIP package guard and part store.
- XML bounded parser and namespace-aware token store.
- schema-derived typed models.
- relationship/resource graph.
- source-preserving syntax tree.
- DocumentGraph mapper.
- ID allocator per domain.
- lowerers by capability.
- serializer/package builder.
- semantic snapshot/diff.

## schema workflow

1. 공식 OWPML/HWPX schema snapshot을 `schemas/source/<version>`에 저장.
2. license와 checksum 기록.
3. XSD graph를 분석해 generated Rust types 또는 validated intermediate representation 생성.
4. generated code를 직접 수정하지 않고 `overrides/`로 enum aliases, constraints, version differences를 보강.
5. schema version별 parser/writer conformance fixture 생성.

## writer 규칙

- unknown content 보존.
- deterministic ordering은 normalized mode에만 적용.
- surgical mode는 source order/prefix/whitespace를 가능한 한 유지.
- resource dedup은 content hash와 semantic reference를 모두 확인.
- missing relationship와 dangling reference는 publish gate 실패.

## 성능 목표

- 100MB/1,000페이지 문서 outline inspect 시 peak memory bounded.
- streaming binary copy.
- unchanged part copy-on-write.
- parallel validation은 가능하되 deterministic commit 순서를 유지.
