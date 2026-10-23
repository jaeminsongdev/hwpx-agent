# P09 filled review table v0 → v1

추가되는 source API는 ReviewTableCreationContext::lower_table_with_cells,
ReviewNewTableCell, immutable ReviewNewTableCells/ReviewFilledTableOutput/receipt다.
원래 blank table 및 existing cell-body APIs와 error/ID/reader/writer guards는 유지한다.
부모는 pub mod filled_output 선언1개만 추가하며 whole preimage/inverse로 확인한다.

호출자는 새 표의 좌표와 typed TextFlow 문단을 명시한다. 좌표 정렬, 중복/finite 입력
검사 후 원래 blank create와 원래 cell body output을 실제 package reimport로 조합한다.
원본 셀 anchor/offset/XML/caller authority/원본 native metadata는 받지 않는다.
필드·opaque structure 등 원래 cell-body가 거부하던 payload는 계속 거부한다.

blank_creation은 중간 단계라 최종 filled artifact의 digest/state가 아니다.
최종 package digest/bytes와 cell output chain은 별도다. final receipt의 full Flow 및
full comment acceptance flags는 false이고 출력 bytes accessor는 접근 권한이 아니다.
기존 stored provider/SQL/schema/운영 DB/설정/신뢰 상태 및 원본 HWPX에는 변경이 없다.

source archives, 초기 build/lint 실패 및 초기23 PASS executable을 보존한다.
초기 실행과 재사용 fixture15/native8 반복을 신규 작업 수로 더하지 않는다.
현재 component regression/Python whole-byte 검사만 이 receipt의 범위다.
native34 NOT_RUN/P09 OPEN/green0/P10 미시작과 모든 미완료 범위를 유지한다.
