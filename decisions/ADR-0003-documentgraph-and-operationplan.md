# ADR-0003 — DocumentGraph and OperationPlan

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


- 상태: Accepted
- 결정일: 2026-08-31

## 맥락

v1 설계를 “한/글 전체 기능” 수준으로 확장하면서 문서 포맷·편집기·배포 surface·검증의 경계를 명확히 해야 한다.

## 결정

LLM과 backend 사이 계약은 DocumentGraph IR과 typed OperationPlan이다.

## 결과

raw XML/COM coupling을 막고 diff, validation, multiple backends를 가능하게 한다.

## 변경 절차

이 결정을 바꾸려면 대체 ADR, migration plan, capability/fixture differential evidence가 필요하다.
