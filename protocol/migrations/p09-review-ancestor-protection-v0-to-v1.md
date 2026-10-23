# P09 관측 댓글 상위 보호 — 기존 경로 보완

버전: P09-110 source progress v1. 공개 request/API/직렬화/DB schema는 변경하지 않는다.
`ImportedDocumentReviewBodies`의 기존 전체 본문, 개별 문단, 기존 셀 출력 및 표 삽입 위치
선택이 실제 댓글 밖의 MAIN 표·셀 조상에서 관측된 기존 보호 flag를 검사한다.

이전에 body 경계 밖이라는 이유만으로 통과하던 protected ancestor 입력은 이제 Selection으로
거부한다. source drift는 여전히 Source가 우선한다. 거부 후 부분 artifact를 반환하지 않는다.
보호되어 있지 않은 기존 허용 입력의 출력 보존 계약은 그대로다. 기존 importer가 이미 거부하던
native boolean/필수 속성 입력을 허용으로 바꾸지 않는다. 누락 속성은 전체 보호 자격이 아니다.

원래 부모 source 3개와 실패 테스트/실행 증거는 implementation/p09/source-archive 및
target/p09-110-review-ancestor-protection의 분리된 파일로 보존한다. 사전 source의 byte/SHA256,
guard의 정확한 추가 역변환, 이전 qualification과 원본 테스트의 독립 재검증을 기록한다.
되돌릴 경우 이 추가 guard만 검토 대상으로 삼는다. 사용자 dirty 변경이나 과거 원본을
덮어쓰지 않고, 보호 우회가 다시 생기는 위험을 명시해야 한다. 자동 rollback은 수행하지 않는다.

권위 있는 actual native/SQL/product/Gate 완료 상태는 변경하지 않는다. P09 OPEN,
native34 NOT_RUN, P84_SQL UNRESOLVED, P10 미착수 및 전체 P09~P20 active 목표를 유지한다.
