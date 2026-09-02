# P02 Official Catalog Importer and Capability Registry Gate Report

- Generated: 2026-09-02
- Audited source commit: `7b63d0ede07ea116e64d084fa00015a0fefb4ec3`
- Audit mode: `STRICT / max`
- Overall state: `pass_scoped_current_pc_local`
- P03 authorization: `authorized_current_pc_local_only`

P02-01~09를 현재 PC의 정품 한글 2020 `11.0.0.9136` x86 범위에서 구현하고 재현했다. 공식 source records, semantic review와 complete binding coverage를 actual restricted outputs로 검증했고, disposable runtime probe와 signed registry를 exact target evidence에 연결했다. 결과 registry는 부분 qualification이며 public routing은 활성화하지 않는다.

## Gate criteria

| Criterion | State | Evidence | Remaining boundary |
|---|---|---|---|
| P02-01 SourceRecord | `pass` | 5 valid kinds, 10 negative cases, schema/codegen and clean-clone checks | New source kinds require additive migration |
| P02-02 Help extractor | `pass` | locked help snapshot, 4 actual records, locator/hash verifier errors 0 | Restricted actual output stays local |
| P02-03 Automation extractor | `pass` | 4 locked PDFs, 2,532 actual records, field/source verifier errors 0 | Raw identifiers stay restricted |
| P02-04 OWPML extractor | `pass` | authoritative XSD/package data, 1,144 actual records, namespace 7/7 | 2024 schema metadata is not 2024 runtime support |
| P02-05 candidate graph | `pass` | 3,680 nodes, 3,811 review edges, auto-merge 0 | Similarity never grants support |
| P02-06 semantic review | `pass` | node 3,680/3,680 and edge 3,811/3,811 dispositions, unresolved 0 | Ignored is not permanent unsupported |
| P02-07 binding model | `pass` | 536/536 required bindings, candidate 32, unavailable 504, routing/runtime-qualified 0 | Missing reviewed mapping remains unavailable |
| P02-08 runtime probe | `pass_scoped` | exact x86/STA trace, safe canaries 2, default-read failure 1, risk-blocked 17, not-run 12, save/reopen exact, Hwp remainder 0 | Only two canaries are verified for this target |
| P02-09 signing/drift | `pass_scoped` | Ed25519 envelope and independent receipt, deterministic/no-overwrite, tamper/rollback/drift tests | Actual other-build baseline is unavailable |
| Common phase constraints | `pass` | migration and negative tests, unexecuted states preserved, source in-place writes 0, failure/handoff recorded | Production and other versions remain deferred |

## Actual current-target evidence chain

```text
locked official sources
  -> SourceRecord outputs
  -> 3,680-node reviewed catalog
  -> 536-binding exact-2020 private registry
  -> P02-08 request/trace/receipt
  -> independent runtime verification
  -> P02-09 signed private registry
  -> independent signature/evidence verification
```

- Source registry SHA-256: `986953421c74d033bcb17dbd763eb6daa0b06c1a5a8b9e3720951fc674d6fd48`.
- Runtime trace SHA-256: `7cea2ff287df3de356462df73048b59ec02695521943d23ba0ab73baa9689246`.
- Signed envelope SHA-256: `97c86645a4bf0696474cb6815699a2e4b012f650ae09ef81c582b672580b85e4`.
- Independent signed-registry verifier: state `pass`, signature/runtime evidence valid, errors 0, raw identifier leak 0.
- Drift report: `baseline_unavailable`; actual cross-build comparison is not claimed.

## Validation summary

- Current Windows P02 suite: `61/61` passed; PowerShell P02-08 static suite: `31/31` passed.
- Official Python 3.13.13 Linux read-only source lane: `61/61` passed.
- Current repository and clean clone FULL bootstrap: each `5/5` lanes passed; clean-clone post-run status changes 0.
- Rust format/clippy/test, C# format/build/smoke, TypeScript format/typecheck/build/test, schema/codegen drift, docs/design and Python compileall all passed.
- Secrets, vulnerabilities and forbidden licenses 0; SBOM components 148.
- Actual runtime/signing evidence and private key remain Git-ignored; user documents and the original design ZIP remain unmodified.

## Strict review

- Change risk: `high`, covering restricted official-source parsing, runtime COM evidence, cryptographic signing, rollback and generated support claims.
- Verdict: `approve_scoped_current_pc_local`.
- Blocker/major/minor findings after remediation: `0/0/0`.
- Synthetic drift tests are not represented as an actual cross-build comparison.
- A signed candidate is not automatically routable. Exactly two bindings have verified current-target evidence and registry routing count remains zero.
- GitHub-hosted scheduler, clean immutable worker, other PCs, Hancom 2022/2024 and production/provider use are not claimed.

## Failure fixtures and residual risks

- The exact 2020 `edit.go_to` default-ParameterSet read failed and remains typed/hashed negative evidence; its action was not run and the binding was not promoted.
- Modal, clipboard, security, external and high-risk candidates remain policy-blocked; 12 candidates remain not run and 504 required bindings remain unavailable for lack of reviewed mapping.
- Tampered payload/source/signature/trust-anchor, overwrite, non-monotonic sequence and wrong-parent lineage cases remain negative tests.
- The first Linux container attempt used non-executable tmpfs and failed before test import; the corrected executable-tmpfs run is the authoritative Linux result.
- The first actual build has no prior signed baseline. P02 proves the drift mechanism and honestly emits `baseline_unavailable`; later exact builds must supply their own signed evidence before comparison.

## Next exact task

Start `P03-01 Bounded ZIP reader` in Rust. Lock bounded archive/entry/expanded-size/compression-ratio/name/path/nested-archive policy first, then implement streaming reads and a generated malicious-ZIP corpus without opening user documents. Use reasoning effort `max`; P03 final Gate also requires `max`.
