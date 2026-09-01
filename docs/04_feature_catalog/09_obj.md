# 그림·도형·개체·차트 기능 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 구현 원칙

그림·도형·차트·미디어를 asset relationship와 geometry/anchor/wrap 그래프로 관리한다.

## 공통 처리 순서

1. capability lookup과 target version 확인.
2. selector/입력 schema 검증.
3. dry-run에서 route·위험·보존 영향 계산.
4. isolated output/session에서 실행.
5. domain-specific semantic readback.
6. 필요 시 실제 한/글 open/save/render.
7. evidence와 새 revision 또는 session receipt commit.

## 기능 목록 (58개)

| ID | 기능 | capability | 범위 | 지원 | backend | phase | 검증 |
|---|---|---|---|---|---|---|---|
| OBJ-001 | 도형 삽입 | `obj.shape_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-002 | 그림 삽입 | `obj.image_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-003 | 그리기마당 개체 삽입 | `obj.drawing_gallery` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-004 | 스크린 샷 삽입 | `obj.screenshot_insert` | `artifact_semantics` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_oracle·manual_e2e |
| OBJ-005 | 그림에서 글자 가져오기 | `obj.ocr_image_text` | `artifact_semantics` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_oracle·manual_e2e |
| OBJ-006 | 차트 삽입 | `obj.chart_insert` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-007 | 글상자 삽입 | `obj.textbox_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-008 | 멀티미디어 삽입 | `obj.multimedia_insert` | `artifact_semantics` | `OPTIONAL_EXTERNAL` | `desktop_automation` | P11 | provider_oracle·manual_e2e |
| OBJ-009 | 글맵시 삽입 | `obj.wordart_insert` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-010 | 그리기 개체 삽입 | `obj.drawing_object_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-011 | OLE 개체 삽입 | `obj.ole_insert` | `artifact_semantics` | `PRESERVE_ONLY` | `desktop_automation` | P11 | binary_preservation·security_scan |
| OBJ-012 | 양식 개체 삽입 | `obj.form_object_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-013 | 개체 캡션 넣기 | `obj.caption_insert` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-014 | 문단 띠 개체 | `obj.paragraph_band_object` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-015 | 개체 위치 | `obj.position` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-016 | 개체 크기 | `obj.size` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-017 | 글자/문단/쪽 기준점 | `obj.anchor` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-018 | 개체 주위 글 배치 | `obj.wrap` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-019 | 개체 여백·캡션 | `obj.margin_caption` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-020 | 선 모양·색·두께·화살표 | `obj.line_style` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-021 | 단색 채우기 | `obj.fill_solid` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-022 | 그라데이션 채우기 | `obj.fill_gradient` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-023 | 무늬 채우기 | `obj.fill_pattern` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-024 | 그림 채우기 | `obj.fill_image` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-025 | 글상자 내부 여백·정렬 | `obj.textbox_properties` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-026 | 개체 그림자 | `obj.shadow` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-027 | 그림 반사 | `obj.reflection` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-028 | 네온/광선 | `obj.glow` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-029 | 옅은 테두리 | `obj.soft_edge` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-030 | 그림 확대·축소·해상도 | `obj.image_properties` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-031 | 그림 자르기 | `obj.crop` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-032 | 개체 회전 | `obj.rotate` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-033 | 개체 뒤집기 | `obj.flip` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-034 | 투명도 | `obj.transparency` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-035 | 밝기·대비·색조 보정 | `obj.color_adjust` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-036 | 개체 묶기 | `obj.group` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-037 | 개체 풀기 | `obj.ungroup` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-038 | 맨 앞/뒤·앞/뒤로 | `obj.z_order` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-039 | 개체 맞춤 | `obj.align` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-040 | 개체 간격 동일하게 | `obj.distribute` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-041 | 연결선 | `obj.connector` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-042 | 자유형 도형 | `obj.freeform` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-043 | 도형 점 편집 | `obj.shape_edit_points` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-044 | 가로세로 비율 유지 | `obj.aspect_lock` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-045 | 개체 보호 | `obj.object_protect` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-046 | 인쇄 여부 | `obj.printable` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-047 | 대체 텍스트 | `obj.alt_text` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-048 | 개체 하이퍼링크 | `obj.object_hyperlink` | `artifact_semantics` | `HYBRID` | `direct_hwpx` | P08 | resource_integrity·semantic_reopen·hancom_open·object_bounds·render_diff |
| OBJ-049 | 차트 종류 | `obj.chart_type` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-050 | 차트 데이터 | `obj.chart_data` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-051 | 계열 설정 | `obj.chart_series` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-052 | 축 설정 | `obj.chart_axis` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-053 | 범례 | `obj.chart_legend` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-054 | 데이터 레이블 | `obj.chart_labels` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-055 | 차트 제목 | `obj.chart_title` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-056 | 차트 스타일 | `obj.chart_style` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |
| OBJ-057 | OLE 속성 | `obj.ole_properties` | `artifact_semantics` | `PRESERVE_ONLY` | `desktop_automation` | P11 | binary_preservation·security_scan |
| OBJ-058 | 글맵시 속성 | `obj.wordart_properties` | `artifact_semantics` | `AUTOMATION_FULL` | `desktop_automation` | P11 | hancom_open·property_readback·render_diff |

## 상세 구현 계약

각 기능의 selector·args schema·direct/automation 알고리즘·검증·오류는 `contracts/09_obj_contracts.md`에 있다.

## 완료 체크리스트

- [ ] 모든 기능에 operation schema 또는 명시적 제한 사유가 있다.
- [ ] target build binding과 source checksum이 기록됐다.
- [ ] 정상·경계·오류·보안/preservation fixture가 있다.
- [ ] direct/automation 차이를 differential test로 기록했다.
- [ ] 사용자 warning/degradation 문구가 정의됐다.
