# ChatGPT Web 앱 설계

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 핵심 흐름

1. 사용자가 HWPX/HWP/템플릿 또는 요구사항을 제공.
2. skill이 `project_open/create`와 `document_inspect`를 선택.
3. `document_plan`으로 구조·수치·보존 정책을 확정.
4. mutation 실행 및 async job 추적.
5. widget에서 preview·diff·warning·revision을 표시.
6. validation gate 후 파일 artifact 제공.

## file input

업로드 파일은 서버 artifact store로 수집한 뒤 checksum, media-type sniffing, ZIP/XML limits, malware/OLE/script inventory를 수행한다. 파일명 확장자만 신뢰하지 않는다.

## 사용자 확인이 필요한 경우

- 원본 레이아웃이 바뀔 가능성이 큰 normalize.
- 서명 무효화 또는 보호 해제.
- 외부 서비스/네트워크/메일/인쇄.
- lossy format export.
- 폰트 substitution.
- 특정 한/글 build가 아닌 fallback renderer 사용.

## 대화 응답 계약

완료 메시지는 다음을 포함한다.

- 생성/수정된 revision과 파일.
- 적용된 핵심 변경.
- 검증한 항목과 미검증 항목.
- 경고와 예상 차이.
- 원본 보존 여부.

“완벽히 동일”이라는 표현은 target Hancom open/save/render evidence와 visual threshold를 모두 통과한 경우에만 사용한다.
