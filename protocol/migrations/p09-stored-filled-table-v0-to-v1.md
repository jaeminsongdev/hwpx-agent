# P09 stored filled table v0 → v1

추가되는 prepare_filled_table 경로는 actual imported review와 실제 저장 template의
동일 actor/독립 scope checks를 P09-106 typed cell package composition에 연결한다.
원래 blank table request/limits/closed errors와 original fresh source checks를 재사용한다.
original source service, native builder, reader/writer, guards, SQL/schema/DB/설정은 그대로다.

새 request는 원래 selection plus immutable ReviewNewTableCells이며 raw bytes/XML/
offset/native metadata/임의 source hash/승인 비트를 받지 않는다. 새 prepared object와
receipt는 request/actual output을 변경 불가능하게 보관하고 verify 시 deterministic
filled output과 양쪽 current source access를 replay한다. consumer 이전 오류는 callback을
막지만 성공한 반복 reads가 이후 atomic lease/publication을 승인하지는 않는다.

신규 모듈1개와 테스트 child module1개만 기존 부모2개에 선언하며 whole preimage 및
전체 inverse로 확인한다. 기존 original native fixture는 중복 module loading 없이
이전 test module의 private helper를 child에서 재사용한다. 원래 test body/guards는 수정하지 않는다.

중간 blank receipt와 final filled digest/chain을 구분한다. product route는 fresh failures
우선 검사 뒤에도 RouteUnqualified다. 실제 SQL/issuer/원자적 실행·저장/native 검증은
미완료이며 component/fixture PASS를 native34/P09 Gate/P10 승격으로 쓰지 않는다.
기존 실패/private/native/user-owned evidence와 PLANS 삭제 상태를 보존한다.
