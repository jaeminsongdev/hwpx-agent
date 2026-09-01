# MCP 도구 계약 상세

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 공통 요청 문맥

```json
{
  "project_id": "prj_...",
  "expected_revision": "rev_...",
  "idempotency_key": "uuid",
  "client_surface": "chatgpt_web|codex_remote|codex_local",
  "target_profile": "hancom-2024-13.x-ko-KR",
  "locale": "ko-KR",
  "request_id": "req_..."
}
```

mutation은 `expected_revision`과 `idempotency_key`를 MUST로 요구한다. 새 프로젝트 첫 revision은 `expected_revision=null`을 명시한다.

## `capability_check`

**Use this when** 요청한 한/글 기능이 특정 버전·배포·보안 정책에서 가능한지 실행 전에 확인해야 할 때.

입력:

```json
{
  "capabilities": ["page.paper_preset", "table.merge_cells", "eq.insert_native"],
  "document_ref": {"revision_id":"rev_..."},
  "requirements": {
    "preserve_unknown": true,
    "native_editability": true,
    "required_validation": ["hancom_save_reopen"]
  }
}
```

출력은 capability별 `supported`, `support_level`, `selected_backend`, `constraints`, `permissions`, `estimated_job_class`, `unverified_reasons`를 제공한다.

Annotations: `readOnlyHint=true`, `destructiveHint=false`, `openWorldHint=false`.

## `document_plan`

자연어/간소화 spec을 `OperationPlan v2`로 변환한다. `compile_only=true`이며 artifact를 바꾸지 않는다. 출력에는 validation errors, resolved defaults, ambiguities, risk summary, backend plan, estimated page/layout effects가 포함된다.

중요 규칙:

- 모호한 수치 단위는 추정하지 않고 `needs_resolution`으로 남긴다.
- “8절지 느낌”처럼 물리 규격이 모호한 표현은 preset 후보와 exact mm를 함께 제시한다.
- 수식은 LaTeX/EqEdit/MathML/AST 중 source를 하나만 허용한다.
- 표 병합 범위는 겹침/비직사각형 여부를 정적으로 검사한다.

## `document_create`

입력은 `DocumentGraph` 또는 `OperationPlan`과 선택적 `template_artifact_id`다. 생성 모드는 `normalized_authoring`, `surgical_preserve`, `native_automation` 중 하나다.

출력:

```json
{
  "job_id": "job_...",
  "revision_id": "rev_...",
  "artifact": {"artifact_id":"art_...","media_type":"application/hwp+zip"},
  "capability_receipt": [],
  "validation_summary": {"state":"verified|partial|failed"}
}
```

## `document_inspect`

selectors:

- `outline`
- `sections`
- `range`
- `node_ids`
- `styles`
- `tables`
- `equations`
- `drawings`
- `fields_references`
- `review_security`
- `package_parts`
- `capability_usage`

`materialization=summary|properties|full`을 지원한다. 대형 결과는 cursor와 snapshot artifact를 반환한다.

## `document_edit`

입력은 source revision과 validated `OperationPlan`이다. 실행 전에 `dry_run=true`로 semantic diff와 예상 backend를 받을 수 있다.

transaction 단계:

1. revision precondition 확인.
2. source artifact checksum 확인.
3. capability·permission·document-state preflight.
4. isolated working copy 생성.
5. operation DAG 실행.
6. package/semantic/backend validation.
7. artifact immutable commit.
8. metadata/revision CAS commit.
9. receipt/audit append.

부분 성공은 기본적으로 허용하지 않는다. `best_effort=true`는 read-only extraction이나 사용자가 명시한 일괄 변환에만 허용한다.

## `document_transform`

지원 job:

- 문서 병합/분할.
- 서식 일괄 교체.
- 표/수식/그림 목록 정규화.
- 스타일 dedup 또는 template style mapping.
- 개인정보·메타데이터 sanitize.
- 형식 변환 전 preflight.

각 transform은 `preview_diff`를 제공하고, 원본 revision을 변경하지 않는다.

## `template_analyze`

출력 `TemplateContract`:

- immutable regions.
- fillable slots and expected content types.
- named styles and page/section assumptions.
- repeating blocks/table rows.
- header/footer/master page anchors.
- unknown/control/script/OLE inventory.
- permitted operations and preserve policy.

## `document_validate`

요청 level:

`input`, `package`, `schema`, `relationships`, `semantic`, `reopen`, `hancom_open`, `hancom_save_reopen`, `render`, `visual_diff`, `print_export`, `accessibility`, `security`.

실제 수행하지 않은 level은 `unverified`로 남는다. backend가 없다고 pass로 간주하지 않는다.

## `document_render`

입력은 page range, dpi, output(`png|webp|pdf`), render backend, crop/bleed option. 출력은 page tile refs, page dimensions, font substitution, backend build, render timestamp를 제공한다.

## `document_export`

출력 형식마다 capability binding을 resolve한다. `.hwp` 또는 한/글 고유 변환은 desktop/WebHWP 경로를 우선한다. 변환 결과는 원본과 별개 artifact이며 semantic loss report를 MUST로 생성한다.

## 프로젝트/작업/아티팩트 도구

- `project_create`: tenant와 ACL을 생성하고 initial empty revision pointer를 반환.
- `project_open`: head, checkpoints, warnings, lock/conflict, capability target, recent artifacts, recommended actions 반환.
- `project_history`: revision DAG와 semantic diff cursor 반환.
- `project_checkpoint`: immutable label; 동일 idempotency key 재시도 시 동일 결과.
- `project_publish`: required gates가 pass인 revision만 publish tag 부여.
- `job_get`: state, stage, progress, retry count, worker, evidence/artifacts 반환.
- `job_cancel`: queued는 즉시, running은 safe cancellation point에서 중단.
- `artifact_get`: ACL 확인 후 attachment 또는 짧은 수명의 signed URL 발급.
