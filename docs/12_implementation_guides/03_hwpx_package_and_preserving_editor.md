# HWPX 패키지 파서·작성기·보존 편집기 구현

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 두 개의 writer를 분리한다

- `NormalizedWriter`: 새 문서 또는 명시적 정규화 모드. 내부 IR에서 일관된 HWPX를 생성한다.
- `PreservingEditor`: 기존 문서/학교 양식. 원본 part·token·namespace·unknown extension을 최대한 그대로 두고 semantic patch만 적용한다.

두 경로를 하나의 DOM serializer로 합치면 템플릿의 미지 XML, ID 순서, 관계, 압축 특성이 대규모로 바뀌므로 금지한다.

## PackageReader 단계

1. 입력 전체 크기, entry 수, 압축률, nested archive 정책 검사.
2. canonical path 정규화 후 traversal, absolute path, duplicate/case collision 거부.
3. `mimetype`와 container/manifest/relationship를 읽고 part graph 생성.
4. XML은 DTD/entity/network를 끄고 depth/node/text/attribute limit을 둔다.
5. 모든 part에 raw bytes hash와 parsed representation 상태를 기록한다.
6. binary asset은 stream hash와 MIME sniffing을 수행한다.

## PartRecord

```rust
struct PartRecord {
    path: PackagePath,
    media_type: MediaType,
    raw_sha256: Digest,
    raw_bytes_ref: BlobRef,
    parse_state: ParseState,
    relationships: Vec<Relationship>,
    preservation: PreservationClass,
}
```

`PreservationClass`는 `ByteExact`, `TokenStable`, `Semantic`, `Regenerated`, `Opaque`, `Rejected`다.

## XML 보존 계층

일반 DOM과 별도로 token span을 유지한다.

```text
XML bytes
 -> namespace-aware tokenizer (byte spans)
 -> lightweight tree/index
 -> semantic node bindings
 -> PatchIntent[]
 -> overlap/dependency check
 -> byte-range/token rewrite
 -> parse again + relationship validation
```

`PatchIntent`는 `ReplaceAttribute`, `ReplaceText`, `InsertSibling`, `DeleteSubtree`, `ReplaceSubtree`, `AllocateId`, `AddRelationship`, `AddPart`로 제한한다. 서로 겹치는 patch는 자동 순서 추정 대신 conflict로 실패한다.

## ID allocator

- part별 ID namespace와 cross-part reference를 index한다.
- 기존 ID를 재번호화하지 않는다.
- 새 ID는 target schema 범위 안에서 deterministic reservation block을 사용한다.
- transaction rollback 시 reservation을 폐기한다.
- duplicate, dangling, wrong-type reference를 validator가 검출한다.

## Relationship closure

part 추가/삭제 시 다음을 원자적으로 처리한다.

```text
source XML reference
+ relationship entry
+ target part
+ manifest/content type
+ binary asset
+ inverse index
```

하나라도 빠지면 commit하지 않는다. 외부 relationship는 policy에 따라 preserve/block/strip-explicit 중 하나다.

## ZIP writer

- deterministic order와 normalized timestamps는 normalized mode에만 적용한다.
- preserve mode에서 untouched entry bytes/compression metadata를 가능한 한 유지한다.
- temp file에 완성한 뒤 fsync/checksum/atomic rename한다.
- output을 다시 PackageReader로 열기 전에는 success가 아니다.

## Diff report

- touched/untouched/new/deleted part.
- byte diff와 semantic diff 분리.
- namespace/attribute order 변경 사유.
- relationship 변화.
- unknown XML preservation state.
- render/oracle 필요 여부.

## 필수 fuzz/property test

- malformed ZIP, zip bomb, overlapping entry, duplicate path.
- namespace prefix variation, unknown extension, huge attributes, invalid UTF.
- random safe patch sequence 후 reopen.
- untouched part byte equality.
- interrupted write에서 원본 불변.
