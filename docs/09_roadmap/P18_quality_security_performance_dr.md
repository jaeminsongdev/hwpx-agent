# P18 — Quality·Security·Performance·DR

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P12,P13,P16,P17`

## 목표

Quality·Security·Performance·DR를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P18-01` | Capability closure | 609 rows의 상태·fixture·evidence·제약을 audit한다. | `coverage dashboard` | missing required field 0 |
| `P18-02` | Fuzz/security | ZIP/XML/IR/protocol/widget/API/worker fuzz와 pentest를 수행한다. | `security report` | critical/high 0 |
| `P18-03` | Large document performance | page/object/table/equation scale별 benchmark와 limit을 확정한다. | `benchmark report` | SLO threshold |
| `P18-04` | Windows capacity | worker density, recycle, cold start, queue capacity를 측정한다. | `capacity model` | peak load simulation |
| `P18-05` | Chaos/retry | network/storage/worker crash/modal/DB failover를 주입한다. | `chaos evidence` | no partial/duplicate commit |
| `P18-06` | Backup/restore | DB/object/binding/evidence backup과 restore drill을 수행한다. | `DR report` | RPO/RTO met |
| `P18-07` | Privacy/retention | PII scan, data residency, purge/legal hold를 검증한다. | `privacy assessment` | deletion verification |
| `P18-08` | Supply chain | SBOM, provenance, signing, image scanning을 완성한다. | `release attestations` | policy pass |
| `P18-09` | RC gate | G0-G6와 blocker review를 수행한다. | `release candidate` | all mandatory gates pass |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P18-01` 산출물 `coverage dashboard` 존재, 검증: missing required field 0.
- [ ] `P18-02` 산출물 `security report` 존재, 검증: critical/high 0.
- [ ] `P18-03` 산출물 `benchmark report` 존재, 검증: SLO threshold.
- [ ] `P18-04` 산출물 `capacity model` 존재, 검증: peak load simulation.
- [ ] `P18-05` 산출물 `chaos evidence` 존재, 검증: no partial/duplicate commit.
- [ ] `P18-06` 산출물 `DR report` 존재, 검증: RPO/RTO met.
- [ ] `P18-07` 산출물 `privacy assessment` 존재, 검증: deletion verification.
- [ ] `P18-08` 산출물 `release attestations` 존재, 검증: policy pass.
- [ ] `P18-09` 산출물 `release candidate` 존재, 검증: all mandatory gates pass.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
