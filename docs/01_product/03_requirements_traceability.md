# 요구사항 추적성

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


각 요구사항은 `REQ-<domain>-NNN` 식별자를 갖고 capability, phase, schema, test에 연결한다.

| 요구사항 | 내용 | 대표 capability | 구현 phase | 검증 |
|---|---|---|---|---|
| REQ-PAGE-001 | A3/B4/8절 유사 크기와 사용자 정의 용지 | `page.paper_preset`, `page.paper_custom` | P05 | XML + actual page metric oracle |
| REQ-PAGE-002 | 구역마다 다른 방향·여백·다단 | `page.section_config` | P05 | two-section fixture |
| REQ-TABLE-001 | 표 생성·행열 편집·셀 병합/분할 | `table.*` | P06 | semantic + render |
| REQ-TABLE-002 | 셀 테두리·배경·여백·정렬·계산식 | `table.cell.*`, `table.formula.*` | P06 | formula readback |
| REQ-EQ-001 | native 편집 가능한 한컴 수식 | `eq.insert_native` | P07 | Hancom equation editor smoke |
| REQ-OBJ-001 | 그림·도형·글상자·캡션 | `object.*` | P08 | object tree + render |
| REQ-REF-001 | 각주/미주/책갈피/상호 참조/차례 | `reference.*` | P09 | update and reopen |
| REQ-REV-001 | 메모·변경 추적·비교 | `review.*` | P11 | automation + history evidence |
| REQ-SEC-001 | 암호/배포용/개인정보 보호의 정책적 처리 | `security.*` | P11 | authorization negative tests |
| REQ-X-001 | Web↔Codex 동일 project continuity | `project.*` | P14-P17 | cross-surface E2E |
| REQ-COMP-001 | 대상 버전 전체 기능 disposition 100% | registry completeness | P18 | registry lint |

상세 전체 목록은 `FEATURE_COVERAGE_MATRIX.csv`가 canonical이다.
