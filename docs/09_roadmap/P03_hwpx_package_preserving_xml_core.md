# P03 — HWPX Package·Preserving XML Core

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P02`

## 목표

HWPX Package·Preserving XML Core를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P03-01` | Bounded ZIP reader | 크기/entry/압축률/path 제한을 적용한다. | `hwpx-package reader` | malicious ZIP corpus pass |
| `P03-02` | Package graph | mimetype/container/manifest/relationships/part graph를 구축한다. | `PackageGraph` | dangling/duplicate relationship tests |
| `P03-03` | XML safety parser | DTD/entity/network off, depth/node/text limit을 구현한다. | `safe XML reader` | XML bomb/invalid namespace tests |
| `P03-04` | Preserving tokenizer | byte span·namespace-aware token/tree를 만든다. | `hwpx-xml token model` | parse-serialize untouched equality |
| `P03-05` | Part preservation map | byte/token/semantic/opaque/rejected 등급을 계산한다. | `PreservationReport` | known fixture expected map |
| `P03-06` | ID/reference index | part별 ID namespace와 cross-reference를 색인한다. | `IdIndex` | duplicate/dangling/wrong-type detection |
| `P03-07` | Patch engine | 제한된 PatchIntent와 overlap/conflict 검사를 구현한다. | `preserving patcher` | property/random patch tests |
| `P03-08` | Atomic ZIP writer | deterministic normalized writer와 preserve writer를 분리한다. | `package writer` | crash/no partial output tests |
| `P03-09` | Round-trip·repair | 100+ fixture reopen, repair diagnostics, fuzz baseline을 만든다. | `roundtrip CLI/evidence` | untouched policy 위반 0 |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [x] `P03-01` 산출물 `hwpx-package reader` 존재, 검증: malicious ZIP corpus pass.
- [x] `P03-02` 산출물 `PackageGraph` 존재, 검증: dangling/duplicate relationship tests.
- [x] `P03-03` 산출물 `safe XML reader` 존재, 검증: XML bomb/invalid namespace tests.
- [x] `P03-04` 산출물 `hwpx-xml token model` 존재, 검증: parse-serialize untouched equality.
- [x] `P03-05` 산출물 `PreservationReport` 존재, 검증: known fixture expected map.
- [x] `P03-06` 산출물 `IdIndex` 존재, 검증: duplicate/dangling/wrong-type detection.
- [x] `P03-07` 산출물 `preserving patcher` 존재, 검증: property/random patch tests.
- [x] `P03-08` 산출물 `package writer` 존재, 검증: crash/no partial output tests.
- [x] `P03-09` 산출물 `roundtrip CLI/evidence` 존재, 검증: untouched policy 위반 0.
- [x] 새 capability/contract/schema에 migration과 negative test가 있다.
- [x] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [x] source artifact를 in-place로 수정한 경로가 없다.
- [x] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
