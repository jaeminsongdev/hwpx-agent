# ADR-0015 — C#/.NET Windows Hancom Worker

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 결정

한/글 COM/Automation과 직접 상호작용하는 프로세스는 C#/.NET STA worker로 구현한다. Rust는 control plane, direct HWPX engine, capability routing을 소유한다.

## 이유

COM apartment, event sink, Windows message pump, process/desktop 제어, typed parameter model을 Windows 전용 경계에 가둔다. Rust core에 COM 세부사항이 누출되지 않으며 worker 교체가 가능하다.

## 결과

- C# worker는 semantic protobuf command와 signed binding만 실행한다.
- public generic action executor는 없다.
- Python automation은 fixture 탐색/호환 adapter로만 허용하고 production 기본 경로가 아니다.
