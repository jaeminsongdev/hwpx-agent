# 설계 검증 보고서

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`

## 판정

**설계 문서 세트는 구현 착수용 기준선으로 사용 가능하다.** 정적 구조·스키마·카탈로그 일관성 검증은 통과했다. 다만 이 판정은 제품 구현 또는 한/글 런타임 적합성 인증이 아니다.

## 자동 검증 범위

`tools/design-validation/validate_design.py`가 다음을 검사한다.

1. 모든 JSON/YAML 파일의 구문 파싱.
2. `FEATURE_COVERAGE_MATRIX.csv`와 JSON 원본의 완전 동일성.
3. feature ID와 capability ID 중복 여부.
4. 609개 feature row의 JSON Schema 적합성.
5. 609개 generated capability contract의 JSON Schema 적합성 및 순서 일치.
6. 190개 WBS task ID 중복 여부.
7. OperationPlan 예제의 v2 schema 적합성.
8. root skill의 YAML frontmatter 필수 필드.
9. 모든 Markdown code fence 짝수 여부.

추가 봉합 검사는 다음을 확인한다.

- plugin blueprint의 `plugin.json`, `.app.json`, `.mcp.json` 구문.
- manifest가 참조하는 skill/assets/apps 경로의 존재.
- 기능 계약 Markdown의 feature heading 수가 609개인지 여부.
- phase 문서 P00~P20과 WBS phase/task의 일치.
- Markdown 내부 상대 경로가 실제 파일을 가리키는지 여부.
- 최종 ZIP 무결성 검사.

## 최종 수치

- 전체 파일: `278`
- Markdown 문서: `231`
- Markdown 단어 수: `221712`
- feature baseline: `609`
- capability contract: `609`
- 기능 영역: `16`
- roadmap phase: `21` (`P00`~`P20`)
- WBS task: `190`
- root workflow skill: `9`
- OperationPlan 예제: `6`
- 정적 검증 오류: `0`

## 기능 매트릭스 분포

지원 수준은 현재 설계 baseline의 **의도된 구현 경로**이며, 실제 지원 인증이 아니다.

- `HYBRID`: 345
- `AUTOMATION_FULL`: 191
- `DIRECT_FULL`: 28
- `OPTIONAL_EXTERNAL`: 37
- `READ_ONLY`: 3
- `PRESERVE_ONLY`: 2
- `DISABLED_BY_POLICY`: 2
- `UNSUPPORTED`: 1

## 검증하지 않은 것

이번 산출물은 설계 문서다. 다음은 아직 증명되지 않았다.

- 실제 HWPX writer/editor 구현 및 생성 파일.
- 한/글 대상 build에서의 COM/Automation action 실행.
- ActionTable/ParameterSetTable의 구체 이름과 버전별 binding.
- native equation의 실제 편집기 round-trip.
- 표/사용자 정의 용지/다단/객체의 실제 렌더링 일치.
- `.hwp`, PDF, 인쇄 변환 결과.
- Windows worker의 장시간 안정성, modal 처리, crash recovery.
- ChatGPT Web/Codex 실제 설치·인증·MCP E2E.
- 상업용 한컴 오토메이션/WebHWP 라이선스 승인.

따라서 문서에서 target evidence가 없는 capability는 `implemented_unverified` 또는 그보다 낮은 상태로 유지해야 하며, 실제 사용자에게 “완전 지원”으로 표시하면 안 된다.

## 구현 전 필수 확인

P00에서 대상 한/글 exact build, Windows image, font set, 상업 라이선스, 공식 manual/schema source lock을 먼저 확정한다. P02/P10에서 공식 자료와 runtime probe를 결합하여 signed target binding을 생성한 뒤에만 구체 HAction/ParameterSet을 실행한다.

## 재현 명령

```bash
python tools/design-generation/generate_capability_contracts.py
python tools/design-generation/generate_wbs.py
python tools/design-validation/validate_design.py
```

생성기 재실행 후 generated 파일에 diff가 생기면, 원본 matrix/WBS와 함께 검토하고 다시 검증한다.
