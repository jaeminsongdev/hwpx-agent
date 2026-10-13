# P09-190 문서 배치 실패와 별도 재검증

첫 문서 sync-run01은 `RESUME_DOC_WHOLE_PRIOR_DOC_SUFFIX`로 실패했다.
원인은 context 없는 추가 패치가 새 내용을 문서 처음이 아니라 끝에 붙인 것이다.
보존본과의 비교에서 두 파일 모두 원래 전체 문서가 index0에 그대로 있었고,
삭제/변조가 아니라 새 상태 문단의 위치가 잘못됐음을 확인했다.

명시적인 기존 첫 줄 context를 사용하여 동일 새 문단을 앞에 배치하고 끝의 중복 문단을 제거했다.
기존 전체 바이트는 archive와 동일한 suffix로 유지했다. 검사 조건을 약화하지 않았다.
원 sync helper와 실패 receipt는 수정하지 않았다.

같은 검증 함수에 새 출력 경로만 지정하여 sync-run02를 별도로 실행했다.
`PASS_R07_RESUMABLE_PLAN_AND_TERMINAL_STOP_DOC_SYNC_ONLY_NOT_RUNTIME_OR_GATE`,
22 contracts, stop=null, cleanup=true다. 원 sync-run01 실패는 성공으로 소급하지 않는다.

증거:

- `implementation/p09/evidence/p09-190-resumable-progress-sync-run01.v1.json`
- `implementation/p09/evidence/p09-190-resumable-progress-sync-run02.v1.json`
- `implementation/p09/source-archive/p09-190-pre-resumable-progress/document-preimages.v1.json`

실제 제품 테스트나 source/EXE whole 재감사를 새로 수행한 것이 아니다.
