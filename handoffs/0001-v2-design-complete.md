# HANDOFF 0001 — v2 설계 완료 및 구현 착수 기준선

> 작성일: 2026-08-31  
> 상태: `DESIGN_COMPLETE_FOR_IMPLEMENTATION`  
> 다음 phase: `P00_SOURCE_LICENSE_TARGET_FREEZE`

## 이번 세션에서 완료한 일

- 업로드된 v1 설계를 전수 검토하고 v2 문서 체계로 재구성했다.
- HWPX 단일 authoring 경로를 capability-driven multi-backend 구조로 변경했다.
- Rust control plane/direct HWPX backend와 C#/.NET STA Windows automation worker 경계를 고정했다.
- 한/글 기능을 16개 영역, 609개 baseline feature로 정리했다.
- 각 feature에 대한 기계 판독 capability contract와 영역별 인간용 계약서를 생성했다.
- P00~P20, 총 190개 WBS task와 phase hard gate를 작성했다.
- 표, 사용자 정의 문서 크기, native 수식을 VS-1 필수 gate로 지정했다.
- ChatGPT Web universal package, Codex remote/local companion blueprint와 9개 skill을 추가했다.
- JSON Schema, OperationPlan 예제, 생성기, 설계 검증 스크립트를 추가했다.

## 검증 상태

- 설계 파일 JSON/YAML 구문 검증: 통과.
- feature CSV↔JSON 동일성: 통과.
- 609개 feature ID/capability ID 중복 검사: 통과.
- 609개 generated contract schema 검사: 통과.
- 190개 WBS task ID 중복 검사: 통과.
- OperationPlan 예제 schema 검사: 통과.
- Skill frontmatter/Markdown fence 검사: 통과.
- 실제 제품 코드 빌드, 한/글 COM 실행, HWPX 생성, 렌더링, Action/ParameterSet binding 실험: 아직 수행하지 않음.

## 다음 실행 순서

1. `docs/09_roadmap/P00_source_license_target_freeze.md`의 P00-01부터 P00-09까지 수행한다.
2. 대상 한/글 제품과 정확한 build, Windows image, font set을 확정한다.
3. 상업용 오토메이션 및 필요 시 WebHWP 라이선스 범위를 서면 확인한다.
4. 공식 manual/schema/help 원본을 source lock에 고정한다.
5. P01 monorepo를 만들고 P02 catalog importer와 target binding generator를 구현한다.
6. 구체 HAction/ParameterSet 이름은 P02/P10의 공식 자료 파싱·runtime probe 결과로만 채운다.

## 현재 blocker

- target 한/글 version/build 미확정.
- 상업용 automation 라이선스 미확정.
- production Windows interactive worker 운영 방식 미확정.

## 핵심 진입점

- `00_START_HERE.md`
- `IMPLEMENTATION_PLAYBOOK.md`
- `FEATURE_COVERAGE_MATRIX.csv`
- `WORK_BREAKDOWN_STRUCTURE.csv`
- `docs/09_roadmap/00_master_roadmap.md`
- `docs/12_implementation_guides/`
- `DESIGN_VALIDATION_REPORT.md`
