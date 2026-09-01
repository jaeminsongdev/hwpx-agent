# 보존 편집과 round-trip 알고리즘

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 세 편집 모드

### normalized_authoring

새 문서 또는 제품이 소유한 문서를 IR에서 재생성한다. deterministic output과 style/resource dedup을 우선한다.

### surgical_preserve

기존 template의 미지 요소와 불변 part를 최대한 byte-preserve하고 지정 subtree만 수정한다.

### native_automation

문서를 실제 한/글에서 열어 allowlisted operation을 수행하고 저장한다. 한/글이 package를 광범위하게 normalize할 수 있으므로 output diff와 oracle provenance를 기록한다.

## surgical preserve data

- ZIP entry order/compression metadata snapshot.
- part checksum map.
- parsed token tree with source byte ranges where feasible.
- namespace/prefix map.
- relationship graph.
- numeric ID domains and allocators.
- opaque XML attributes/elements/comments/processing instructions.
- embedded binary inventory.

## patch algorithm

1. source package safety validation.
2. package/relationship graph와 typed IR 생성.
3. selector resolution 및 target subtree lock.
4. operation 적용 후 changed logical nodes 계산.
5. changed nodes에 연결된 최소 XML/resource closure 계산.
6. ID 충돌 없는 새 ID 할당.
7. 변경 part만 serialize; untouched entry는 원본 bytes 재사용.
8. content type/manifest/relationship consistency 갱신.
9. package reopen, semantic compare, preservation report.
10. 필요 시 Hancom open/save를 별도 normalization revision으로 생성한다.

## 보존 report

- byte-identical parts.
- semantically identical but rewritten parts.
- intentionally modified parts and reason.
- dropped/unknown elements: 반드시 0 또는 explicit waiver.
- new/deleted relationships/resources.
- ID remap table.

## 실패 조건

opaque subtree가 수정 target과 겹쳐 안전한 patch가 불가능하면 direct edit를 중단하고 automation route 또는 사용자 선택을 요구한다. 추정으로 재생성하지 않는다.
