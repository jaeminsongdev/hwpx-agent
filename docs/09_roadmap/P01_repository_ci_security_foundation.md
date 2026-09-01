# P01 — Repository·CI·Security Foundation

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 선행 조건

`P00`

## 목표

Repository·CI·Security Foundation를 문서상 계획이 아니라 **재현 가능한 산출물과 검증 증거**로 종료한다. 다음 phase는 아래 hard gate가 충족되기 전 시작할 수 없다.

## 작업 분해 구조 (9개)

| Task | 작업 | 구현 내용 | 산출물 | 검증 |
|---|---|---|---|---|
| `P01-01` | Monorepo 생성 | Rust/C#/TypeScript workspace와 경계를 생성한다. | `buildable repository` | clean checkout build |
| `P01-02` | 도구체인 lock | Rust/.NET/Node/protobuf/schema 도구를 lock한다. | `toolchain manifests` | CI와 local version 일치 |
| `P01-03` | Schema·protobuf generation | JSON Schema와 proto codegen을 단일 명령으로 만든다. | `generated model packages` | breaking/schema compile test |
| `P01-04` | CI matrix | Linux core, Windows worker, widget, docs, security job을 구성한다. | `CI workflows` | 각 job 최소 smoke pass |
| `P01-05` | Secure workdir | temp/staging/quarantine/atomic output 규칙을 구현한다. | `workspace utility` | path traversal·interruption tests |
| `P01-06` | Dependency security | SBOM, license allowlist, vulnerability/secret scan을 추가한다. | `SBOM/security reports` | 금지 라이선스·secret 0 |
| `P01-07` | Logging baseline | request/job/trace ID, redaction, structured logging을 정의한다. | `logging crate/package` | PII/secret redaction tests |
| `P01-08` | Fixture policy | synthetic/licensed-private/malicious fixture manifest 규칙을 만든다. | `fixture manifest schema` | 라이선스/PII 필드 누락 시 CI fail |
| `P01-09` | Bootstrap docs | 개발 환경과 한 명의 새 개발자 smoke 절차를 작성한다. | `bootstrap script/runbook` | 새 환경 재현 성공 |

## 구현 순서와 병렬화

1. 첫 task에서 source/contract/실패 조건을 고정한다.
2. schema·pure model·negative test를 backend 연결보다 먼저 만든다.
3. 같은 phase 안의 독립 adapter/fixture 작업은 병렬화하되 generated contract와 target profile은 공유한다.
4. backend 연결 후 semantic readback과 required target evidence를 수집한다.
5. 마지막 task에서 registry, ROADMAP_STATUS, CURRENT_STATE, handoff를 함께 갱신한다.

## Phase hard gate

- [ ] `P01-01` 산출물 `buildable repository` 존재, 검증: clean checkout build.
- [ ] `P01-02` 산출물 `toolchain manifests` 존재, 검증: CI와 local version 일치.
- [ ] `P01-03` 산출물 `generated model packages` 존재, 검증: breaking/schema compile test.
- [ ] `P01-04` 산출물 `CI workflows` 존재, 검증: 각 job 최소 smoke pass.
- [ ] `P01-05` 산출물 `workspace utility` 존재, 검증: path traversal·interruption tests.
- [ ] `P01-06` 산출물 `SBOM/security reports` 존재, 검증: 금지 라이선스·secret 0.
- [ ] `P01-07` 산출물 `logging crate/package` 존재, 검증: PII/secret redaction tests.
- [ ] `P01-08` 산출물 `fixture manifest schema` 존재, 검증: 라이선스/PII 필드 누락 시 CI fail.
- [ ] `P01-09` 산출물 `bootstrap script/runbook` 존재, 검증: 새 환경 재현 성공.
- [ ] 새 capability/contract/schema에 migration과 negative test가 있다.
- [ ] 실제 수행하지 않은 검증은 `unverified`로 남았다.
- [ ] source artifact를 in-place로 수정한 경로가 없다.
- [ ] phase handoff에 실패 fixture와 다음 exact task가 기록됐다.

## 금지

- hard gate를 “나중에 테스트”로 넘기지 않는다.
- raw XML/action 문자열을 public API 또는 LLM 출력에서 실행하지 않는다.
- 라이선스·보안·보존 blocker를 기능 fallback으로 숨기지 않는다.
