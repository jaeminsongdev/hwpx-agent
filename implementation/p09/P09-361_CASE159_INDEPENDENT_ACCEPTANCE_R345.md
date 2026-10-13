# P09 case159 독립 전체 검증과 공식 승인

실제159 run001을 재실행하지 않고 별도 전체 read-only oracle과 독립 승인을 완료했다. 공식 원장은 152에서153으로 1회 전진했고, 잔여 개별 사례는96개, 다음 사례는160번이다. current-generation 승인은48개다. P09/A12/A13 Gate는 OPEN이며 full249-current와 signed16은 완료되지 않았다. P10 새 구현은 없다.

## 원래 전체 oracle 연결

current_successor_acceptance_prepare_v1.py는 원래 controller admission과 실제 manifest를 확인한다. 기대 범위는 정확한 이전158 runtime·authority152·독립 manifest admission으로부터 도출하며, 현재159 후보의 관측 frame을 복사해 기대값으로 만들지 않는다.

원래 scoped-validator를 semantic 범위에 먼저 연결하고, 이어서 같은 private Binding 타입의 physical oracle에 연결했다. frozen flat prepare 코드와 원래 Native·제품·Job·resource·두 byte 경계·cleanup·strict-window 검사 코드는 유지한다. 현재 controller·DATA와 alias/timing/failure source가 실제 frame 범위에 포함되어 있는지도 확인한다. 옛 source-stat DATA159를 만들거나 Native 입력을 소급 추가하지 않는다.

## 별도 read-only 검증

r751은 PASS_CURRENT159_SUCCESSOR_FULL_READ_ONLY_PREPARE_NOT_QUEUE_ACCEPTANCE다. 실제 ROOT 핀은 4580676bytes/SHA256090e2e069852a45d2db306f9968c2ca997962222e3bc622c7c10c7dee2d830d2이다. fresh213/final213, 전체CPU 최대39.63%, 최소 가용RAM58.56166%, cleanup true를 확인했다. 제품·Native 재실행과 원장 쓰기는 없었다.

## 공식 독립 승인

accept_case159_successor_run001_r345.py는 기존 optimized acceptance v1/v2/v3의 reader·원래 AST/bytecode·75% metadata warning·64KiB workspace·최종 fresh hash와 exclusive writer를 사용한다. 실행 중 r751의 상태·runtime 핀·source 핀을 다시 검증한 후 전체 prepare를 적용한다. 원래 legacy dependency는 별도 facade로 연결하고, generic runner가 부적합한 과거 DATA 경로를 사용하지 않도록 현재 prepare만 명시적으로 연결한다.

- 원장: implementation/p09/evidence/p09-361-case159-current-epoch-accept001.v1.json
- 크기436264bytes, SHA256be740fc83c883f3e07e010299a9f05955da728911ad3e1c36a02ce1688f7947e
- 상태PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE
- before152/after153/delta1/next160/current-generation48
- accepted index159 및 정확한 compiled 사례 actual_import::source_review_assembly::stored_review_assembly_rejects_each_provider_scope_substitution
- fresh1082/final1082, read2205/275181898bytes, 전체CPU 최대26.09%, 최소 가용RAM58.30663%, resource cleanup true
- diagnostic attempt001는 PASS_ORIGINAL_IMMUTABLE_ACCEPTANCE_WITH_QUALIFIED_METADATA_READER, 7012bytes/SHA2565a89cdf29320b56a0b59cfd9c4f180ad65e8de69a4ba912930c7149fe967bcd5, prepare 오류0/cleanup true

이 원장은 실제159 root의 동일 핀을 가리킨다. 성공159/158, 기존 authority152, 실패034 및 사용자 원본은 그대로 보존한다. 별도 승인 증거를 원래 Native 입력으로 소급 주장하지 않는다.

## 다음 단계와 보호 범위

160번의 실제 STEP와 authority153/root159에 연결된 입력 표현·controller·전체 oracle을 준비한다. 전체 current scope·비용·whole preflight가 통과한 뒤에만160번을 실행한다. 통과한159는 재실행하지 않는다.

기존 CPU/RAM/읽기 속도/600초/cleanup 보호와 원래 full249-current·signed16·P09 Gate 완료 조건을 유지한다. 현재 결과로 과거 PC 프리즈 원인이 해결됐다고 판정하지 않는다. P08/P17/공유 Rust 변경과 private 원본, 실패 증거는 보존하며, 한글·접근 허용·UAC 요청이나 OS/Defender/WSL 변경, 외부 프로세스 종료, 원본 삭제·이동, 원격 push는 하지 않았다.

근거는 implementation/p09/evidence 아래 p09-361-case159-successor-full-prepare-r751.v1.json, actual159 run001, optimized-acceptance-attempt001 및 current-epoch-accept001이다.
