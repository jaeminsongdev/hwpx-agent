# 플러그인 Skills 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 공통 skill 규칙

- 사용자가 어떤 문서를 원하는지 먼저 구조화한다.
- 기존 파일은 inspect 없이 수정 계획을 만들지 않는다.
- 용지·표·수식·레이아웃 수치는 exact unit으로 내려간다.
- mutation 전 plan/dry-run, 후 validation.
- 지원하지 않는 기능은 조용히 대체하지 않는다.
- 결과에는 파일과 검증 상태를 함께 반환한다.

## skills

### `create-hancom-document`

새 보고서, 학습지, 시험지, 공문, 양식. 용지/구역/style system을 먼저 정하고 content를 채운다.

### `edit-hancom-document`

source inspect → edit mode 선택 → stable selector → transaction → preservation report.

### `compose-math-exam`

시험지 page profile, 문제 block, native equation, 표/그림, keep/split, 정답지 분리, 배점 검증.

### `validate-hancom-document`

요구 gate를 선택하고 evidence 없는 pass를 금지한다. 페이지 잘림/문항 분리/폰트/수식 native 여부를 특별 검사한다.

### `resume-hancom-project`

`project_open` 결과의 head/warning/next actions를 기반으로 이어서 작업한다. 대화 메모리만으로 상태를 재구성하지 않는다.

## skill 평가

각 skill은 positive prompt, ambiguous prompt, unsupported feature, malicious document, stale revision, retry case를 포함한 eval set을 갖는다.
