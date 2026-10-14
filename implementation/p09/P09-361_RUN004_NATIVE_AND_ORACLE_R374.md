# P09 실제 실행 성공과 독립 검사 미승인

공식 승인은153/249, 잔여96개, next160, generation48이다. 새run004의 실제제품 테스트는 통과했지만 독립검사가 거부했으므로 공식승인은 증가시키지 않았다. P09/A12/A13은 OPEN이고 P10은 시작하지 않았다.

## 실제 실행

새 controller의 CODE22 및 preflight041 통과후 사례160만 한번 실행했다. p09-361-case160-current-runtime-run004.v1.json은4385867bytes, SHA256 0c75fc523072db2c4e27ca23178ccd848e440900bf583b2f015ead3664413087이다. 상태는 PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE, task case160-current-r004-tests, 제품테스트1개 PASS, 경과568.98초이다.

실제 Native frame은 COMMITTED, 바이트경계2개, 전체물리입력2845개이며 잠금핸들잔여0이다. decoder68회가 두경계의 단일5초예산에서0.8449206초에 완료됐다. cleanupTrue/owned_tree_emptyTrue이다. 1109개 자원샘플에서 시스템CPU최대65.23%, 검증부모CPU최대1.8441647%, 가용RAM최소42.1517594%, 검증부모private최대54.015625MiB였다. 이 결과만으로 PCfreeze가 해결됐다고 주장하지 않는다.

## 독립 결과 검사

qualify_case160_run004_readonly.py는 제품이나 Native를 재실행하지 않고 원 frozen prepare와 전체독립oracle을 호출했다. 검사스크립트는 실제Native 입력에 사후삽입하지 않고 별도reader로 전후바이트를 확인하도록 구성했다. 공식queue쓰기 API는 여전히 차단돼 있다.

p09-361-case160-run004-independent-oracle-r374.v1.json은 CURRENT_EPOCH_ACCEPT_BOOTSTRAP_CONTROLLER로 실패했다. fresh입력207개·읽기220회·52077406bytes 단계에서 거부됐고 최종fresh완료나독립PASS를 주장하지 않는다. 경과36.8465103초, 시스템CPU42.5%·부모CPU4.5987758%·가용RAM43.9978079%·부모private52.59765625MiB·cleanupTrue이다.

초기bootstrap_metadata.input_pins는276개였다. 원checker가 요구하는 qualifiedCODE_PINS/native.SOURCES 중 아래2개가 초기읽기목록에 없었다. 두파일은 전체Native source_freeze에는 포함되어 실제두바이트경계에서 확인됐지만, 별도의초기읽기조건은 충족하지 않는다.

- tools/p09/tests/test_case112_current_stored_runtime.py
- tools/p09/tests/test_current_stored_native_bridge.py

현재controller·DATA041·preflight041은 초기목록에 있다. 원본실행결과·bootstrap목록을 덧붙이거나 checker조건을 제거하여 승인하지 않는다. 성공한run004와 독립실패는 함께보존한다.

## 다음 실행 조건

다음별도물리attempt는 위2개의 원qualified byte pin을 bootstrap 반환전 fresh읽기에 포함해야 한다. 원scope·체커·600/720·자원보호는 유지하고 새identity·DATA·CODE·전체preflight를 검증한다. 기존run004를 덮어쓰거나 재실행하지 않는다. 새로운실제성공candidate의 독립oracle까지 통과해야 공식승인을153→154로 갱신할 수 있다.
