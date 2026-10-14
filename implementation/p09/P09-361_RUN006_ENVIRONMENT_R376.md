# P09 실제 함수 환경 연결 수정과 별도 실행 준비

공식승인은153/249·잔여96·next160·generation48이며 P09/A12/A13은 OPEN이다. run004 Native제품성공과 독립검사 거부는 보존한다. run005는48.29초에 DEFERRED_NOT_STARTED/ENVELOPE_SCOPE_BINDING_MANIFEST_IN_FULL_SOURCE_SCOPE로 종료됐으며 product_body_observed=False, actual_product_child_executed=False, Native_source_frame_qualified=False, cleanup/owned_tree_empty=True이다. 원본126346bytes/SHA256 86f114fdae3632b223b3e8b7b98787952fec6537fc2530240dcd1fdbfaeeae45를 보존한다.

원인은 private namespace의 속성사전과 실제함수의 globals사전이 다르다는 점이었다. 일부함수는 복제되지 않아 실제binding이 이전환경을 참조했다. 사전검사는 새입력을 먼저읽어 차이를 가렸지만 실제실행은 binding부터 호출해 거부됐다. 함수의실제 globals사전을 기준으로 전체family를 복제하도록 수정했다. 실제binding·독립prepare의환경포인터를 직접확인하는2개회귀검사를 추가해 원22+초기읽기3+환경2=27개가 통과했다. bootstrap read와 원strictchecker는 유지한다.

새 entrypoint는 case160_attempt_controller.py이며 이번physicalrun은6, task는case160-current-r006-tests, 결과root는별도run006이다. run004/run005는 덮어쓰지 않는다. 초기검사에서 fullparent의고정task004가남아 preflight043은 EXACT_RUN004_TASK로 거부됐다. 해당문자열만새task로명시적metadata inverse 투영하여 정확한비교를 유지했다. 이전CODE/DATA/preflight도보존한다.

현재CODE는run006-controller-r376-run002, DATA044, preflight044이다. CODE27/fresh101-final101/helper62/시스템CPU29.16%·부모CPU1.4395153%·가용RAM45.8041206%·cleanupTrue로통과했다. 전체preflight044는2883inputs·fresh282/final282·import64·89.2685325초·예상전체runtime598.3306290초<원600·시스템CPU49.91%·가용RAM44.8755976%·cleanupTrue로통과했다. 실제실행이나독립oracle 승인으로확대하지 않는다.

원engine/worker/oracle 본체, Native600/shared720, 의미입력scope, 두실제바이트경계, decoder5·margin60·wire16384·helper64 및자원보호는 유지한다. 다음은단일run006·독립oracle·공식승인이다. 접근허용·OS변경·외부종료·삭제이동·원격push는없으며 PCfreeze해결은미증명이다.
