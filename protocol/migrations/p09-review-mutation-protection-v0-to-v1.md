# P09-111 관측 review mutation 보호

공개 request/API/직렬화/DB schema 변경은 없다. 기존 actual-source body/paragraph/cell
교체와 review wrapper 삭제가 원래 ancestor 보호와 실제로 사라지는 subtree의 표·셀 보호를
함께 검사한다. protected consumed tc/tbl/sz가 있거나 삭제 target 중 하나라도 보호되면
Selection을 반환하며 부분 출력/삭제는 반환하지 않는다. Source drift 우선순위는 그대로다.

기존 helper/target selection/ID/style/opaque/budget/원본 외부 영역 보존/native boolean 규칙을
유지한다. 관련 없는 protected peer는 원본 전체 part byte 비교로 보존한다. 반대편의 잠긴
review 때문에 보호 없는 별도 문단 편집을 문서 전체 단위로 거부하지 않는다.

원래 source4 whole preimage와 정확히 선언한 private helper/단일 call 변경의 inverse를
검증한다. 최초 실패 회귀 source/executable, 초기 lint source/21 실행 파일과 빈 checker
진단 자료를 별도 경로로 보존한다. 진단 inventory의 파일 수를 최종 성공 실행 수로 세지 않는다.
원래 guard를 되돌리면 보호된 descendant 삭제·교체가 다시 허용될 위험이 있으므로 자동
rollback은 수행하지 않는다. 사용자 dirty source나 실패 증거를 덮어쓰지 않는다.

공용 memoPr 보호 의미/native author/time/state/source-full-comment mapping/actual SQL
내구 통합/trusted issuer/atomic execution/publication 및 actual native Gate는 미완료다.
P09 OPEN/native34 NOT_RUN/P84_SQL UNRESOLVED/no P10/전체 목표 active 상태를 유지한다.
