# v1 → v2 갭 분석과 문서 매핑

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


| 영역 | v1 상태 | v2 보강 | 구현 문서 |
|---|---|---|---|
| 제품 범위 | 시험지·일반 문서 중심 | 한/글 메뉴/문서/자동화 기능 전체 inventory | `FEATURE_COVERAGE_MATRIX.*` |
| 문서 모델 | 최소 block/inline | graph, resources, controls, review, protection, accessibility | `docs/03_document_model/*` |
| 페이지 | paper/margin/columns | 사용자 정의 크기, 제본, 세로쓰기, 바탕쪽, 번호·줄번호, 구역별 설정 | `04_page_section_layout.md` |
| 표 | 일반 삽입 수준 | 구조 편집, 반복 머리행, 나눔, 수식, 셀 속성, 중첩·캡션 | `06_table_model.md` |
| 수식 | 강점, Tier A/B | parser provenance, AST version, typography, numbering, automation edit oracle | `07_equation_model.md` |
| 개체 | image 중심 | shapes, text box, WordArt, chart, OLE, multimedia, grouping, effects | `08_drawing_image_chart.md` |
| 필드/참조 | 거의 없음 | field, form, bookmark, hyperlink, cross-reference, mail merge, TOC/index/bibliography | `09_fields_controls_references.md` |
| 검토/보안 | 일반 security only | track changes, comments, compare, history, passwords, distribution docs, privacy protection | `10_review_protection_accessibility.md` |
| 자동화 | backend 추상화만 | Windows worker, action registry, modal control, health/recycle | `docs/05_backends/02_desktop_automation_backend.md` |
| WebHWP | 없음 | 선택 backend와 API 차이 검증 | `03_webhwp_backend.md` |
| 검증 | 단계 개념 | 기능별 evidence contract, layout metrics, oracle build pin, differential test | `docs/08_testing/*` |
| 플러그인 | Web/Codex 구분 | universal plugin + remote app + Codex local companion + MCP Apps UI | `docs/07_apps/*` |
| 운영 | 일반적 | Windows pool, fonts/printers, tenant cleanup, licensing, incident runbook | `docs/10_operations/*` |
| 로드맵 | P00–P12 | P00–P20, 기능 의존성·exit gate·artifact 정의 | `docs/09_roadmap/*` |

## 기존 파일 처리 방침

v1 문서를 직접 덧붙이지 않고 v2 규범 문서로 대체한다. 구현자는 v2만 읽어도 되며, v1의 중요한 결정은 `EXECUTIVE_REVIEW_AND_DELTA.md`와 ADR에 흡수됐다.
