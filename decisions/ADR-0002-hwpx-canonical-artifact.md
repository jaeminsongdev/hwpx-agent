# ADR-0002 — HWPX canonical artifact

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


- 상태: Accepted
- 결정일: 2026-08-31

## 맥락

v1 설계를 “한/글 전체 기능” 수준으로 확장하면서 문서 포맷·편집기·배포 surface·검증의 경계를 명확히 해야 한다.

## 결정

새 revision의 canonical 한컴 artifact는 HWPX다. HWP는 import/export/automation 경로로 처리한다.

## 결과

개방형 package의 보존·검증·diff가 가능하고 HWP binary writer를 핵심 경로로 떠안지 않는다.

## 변경 절차

이 결정을 바꾸려면 대체 ADR, migration plan, capability/fixture differential evidence가 필요하다.
