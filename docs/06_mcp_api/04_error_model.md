# 오류·경고·검증 모델

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## ErrorEnvelope

```json
{
  "schema_version":"hwpx-agent.error/v2",
  "request_id":"req_...",
  "error_code":"CAPABILITY_UNVERIFIED_FOR_TARGET",
  "category":"capability",
  "safe_message":"대상 한/글 빌드에서 이 기능의 실행 바인딩이 검증되지 않았습니다.",
  "retryable":false,
  "stage":"preflight",
  "details":{"capability_id":"...","target_profile":"..."},
  "recovery":[{"action":"choose_other_target"},{"action":"run_runtime_probe"}]
}
```

## category

- `input`: schema, unit, selector, source syntax.
- `capability`: unsupported, unverified, backend unavailable.
- `conflict`: stale revision, lock, concurrent edit.
- `document`: corrupt package, broken relationship, missing resource.
- `security`: permission, credential, policy, malware/OLE/script.
- `backend`: worker crash, modal, timeout, Hancom error.
- `validation`: reopen/render/semantic mismatch.
- `storage`: checksum, quota, commit.
- `external`: WebHWP/cloud/signing/provider failure.
- `internal`: invariant violation.

## 대표 코드

| 코드 | 의미 | 재시도 |
|---|---|---|
| `INPUT_SCHEMA_INVALID` | 요청 JSON 불일치 | 수정 후 |
| `SELECTOR_AMBIGUOUS` | 대상 노드가 여러 개 | selector 보강 |
| `REVISION_CONFLICT` | expected revision 불일치 | 최신 open 후 재계획 |
| `CAPABILITY_UNSUPPORTED` | 설계상 미지원 | 불가 |
| `CAPABILITY_UNVERIFIED_FOR_TARGET` | 버전 binding 미검증 | probe/다른 target |
| `BACKEND_UNAVAILABLE` | 필요한 worker 없음 | 가능 |
| `DOCUMENT_CORRUPT` | source package 손상 | repair 또는 교체 |
| `DOCUMENT_CREDENTIAL_REQUIRED` | 암호/보호 credential 필요 | credential 제공 |
| `EQUATION_LATEX_UNSUPPORTED` | 지원 밖 수식 문법 | source 수정/EqEdit |
| `HANCOM_MODAL_BLOCKED` | 예상치 못한 dialog | worker recycle 후 조사 |
| `VALIDATION_SEMANTIC_MISMATCH` | save/reopen 의미 불일치 | release 차단 |
| `VALIDATION_VISUAL_REGRESSION` | 허용치 초과 렌더 차이 | 검토 필요 |
| `POLICY_SCRIPT_EXECUTION_DENIED` | 스크립트 실행 금지 | 정책 변경 권한 필요 |

## warning

warning은 성공을 가장하지 않는다. `FONT_SUBSTITUTED`, `LAYOUT_REFLOWED`, `EXPORT_LOSSY`, `UNVERIFIED_RENDER`, `SIGNATURE_WILL_INVALIDATE`, `EXTERNAL_LINK_PRESERVED_NOT_FETCHED` 등을 receipt에 누적한다.

## 사용자 메시지

사용자에게 내부 COM stack trace, 로컬 경로, secret, tenant ID를 노출하지 않는다. 대신 무엇이 실패했고 문서에 변경이 커밋됐는지 여부, 안전한 복구 방법을 명확히 말한다.
