# MCP 도구 표면

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 설계 원칙

공개 MCP는 HWPX 태그, COM `HAction`, `ParameterSet`, 메뉴 ID를 노출하지 않는다. 도구는 **사용자 목적 단위**로 나누고, 실제 기능 선택은 `CapabilityRouter`가 맡는다. OpenAI 플러그인 지침에 따라 각 도구는 명확한 사용 시점, 입력·출력 스키마, 권한, 안전 annotation을 갖는다.

## 공개 도구 18개

| 도구 | 목적 | 성격 | 비고 |
|---|---|---|---|
| `capability_check` | 요청 기능의 버전·백엔드·권한·제약 확인 | read-only | 실행 전 계획 근거 |
| `document_plan` | 자연어 요구를 검증 가능한 OperationPlan으로 컴파일 | read-only | 파일 변경 없음 |
| `document_create` | 빈 문서 또는 구조화 계획으로 새 문서 생성 | mutation | async 가능 |
| `document_inspect` | 문서 구조·스타일·개체·보안·기능 사용 현황 검사 | read-only | 범위 기반 partial inspect |
| `document_edit` | 기존 revision에 원자적 편집 적용 | mutation | expected revision 필수 |
| `document_transform` | 일괄 변환·정규화·문서 결합/분할 | mutation | long-running job |
| `template_analyze` | 템플릿 slot·고정 영역·보존 규칙 추출 | read-only | template contract 생성 |
| `document_validate` | schema·semantic·한/글·visual 검증 | read-only/job | evidence만 보고 |
| `document_render` | 페이지 이미지/PDF 미리보기 생성 | read-only/job | renderer provenance 포함 |
| `document_export` | HWP/PDF/DOCX/RTF/TXT/HTML/DAISY/점자 등 내보내기 | mutation/job | capability에 따라 route |
| `project_create` | 영속 프로젝트 생성 | mutation | 프로젝트 단위 권한 |
| `project_open` | 현재 head·경고·아티팩트·다음 행동 조회 | read-only | cross-surface resume |
| `project_history` | revision DAG·diff·checkpoint 조회 | read-only | paging |
| `project_checkpoint` | immutable checkpoint/label 생성 | mutation | 문서 bytes 변경 없음 |
| `project_publish` | 검증된 revision을 사용자 전달본으로 승격 | mutation | publish gate |
| `job_get` | 비동기 작업 상태·로그 요약·결과 조회 | read-only | cursor/event 지원 |
| `job_cancel` | 취소 가능한 작업 중단 | mutation | best-effort + receipt |
| `artifact_get` | 다운로드/preview용 artifact 참조 획득 | read-only | signed URL 또는 attachment |

## 내부 API와 공개 도구 분리

내부에는 수백 개 semantic operation이 있어도 공개 도구 수는 늘리지 않는다. `document_edit`가 받는 `OperationPlan` 안에서 `page.paper_preset`, `table.merge_cells`, `eq.insert_native` 같은 capability를 조합한다. 다만 모델이 한 번에 거대한 자유 형식 JSON을 만들지 않도록 `document_plan`이 먼저 typed plan을 생성하고 서버가 재검증한다.

## 기본 호출 순서

```text
capability_check (필요 시)
        ↓
document_plan
        ↓
사용자 intent가 파괴적/비가역/외부효과면 확인
        ↓
document_create | document_edit | document_transform | document_export
        ↓
job_get (비동기인 경우)
        ↓
document_validate
        ↓
project_checkpoint / project_publish
```

## 반환 원칙

- `structuredContent`: 모델과 UI가 재사용할 짧은 구조화 결과.
- `content`: 사용자가 이해할 수 있는 요약.
- `_meta`: widget 전용 대형 payload, cursor, preview tiles, non-model data.
- 문서 본문 전체나 파일 bytes는 응답에 직접 싣지 않고 `ArtifactRef`로 반환한다.
- 오류에도 `request_id`, `error_code`, `retryable`, `safe_message`, `details`를 포함한다.
