# P09 case160 STEP와 무손실 입력 준비

160번의 실제 STEP를 authority153과 승인된159 runtime에 연결했다. 큰 과거 결과140/135/139 및 실제159 결과를 원본 그대로 보존하면서 추가 무손실 표현4개를 생성·검증했다. 공식 승인 수는153/249, 잔여96개, 다음160이며 current-generation48이다. 이 결과는 입력 준비이지160번 controller·전체 비용·Native·제품·독립 승인 또는 P09 Gate 통과가 아니다.

## 정확한 STEP와 원본 선택

r753은 실제436264bytes/SHA256be740fc83c883f3e07e010299a9f05955da728911ad3e1c36a02ce1688f7947e인 authority153과 4580676bytes/SHA256090e2e069852a45d2db306f9968c2ca997962222e3bc622c7c10c7dee2d830d2인 actual159 run001을 새로 읽어 확인했다. 원장의 next160/delta1/cleanup 및 원래 COMMITTED frame과 전체byte2 경계를 확인하고 compiled roster249에서160번 사례를 선택했다.

새 STEP의 index160/before153과 prior_queue_pin/prior_candidate_pin은 위 실제 원본이다. 사례는 actual_import::source_review_cell_output::cached_body_callback_rechecks_actual_aead_acl_regrant_and_advanced_head이다. 기존 runtime159의 semantic 입력에서 이미 표현된20쌍을 제외한 큰 prior 결과140/135/139를 선택했고159 결과를 추가했다. 159번 제품은 다시 실행하지 않았다.

r753 상태는 PASS_ACTUAL153_SUCCESSOR160_STEP_AND_FOUR_RECEIPT_SELECTION_NOT_RUNTIME_OR_GO이며 전체CPU 최대29.03%, 최소 가용RAM58.06747%, cleanup true다.

## 무손실 표현4개

r754는 원래 검증된 publisher CODE13, codec, 2MiB/s write pacing과 exclusive xb/flush/fsync 경로를 그대로 사용했다. 원본12,164,765bytes를 새 표현3,696,244bytes로 생성하여8,468,521bytes의 표현 차이가 있다. 원본을 삭제하거나 디스크 전체를 그만큼 정리한 것은 아니다.

추가 파일은 implementation/p09/evidence/p361-lossless-runtime-inputs 아래 case140-runtime-run001.envelope.v1.json, case135-runtime-run001.envelope.v1.json, case139-runtime-run001.envelope.v1.json, case159-runtime-run001.envelope.v1.json이다. 각 출력은 next_case160의 typed descriptor로 연결한다. 네 원본과 네 표현을 두 번 fresh decode하여 정확한 모든 원본 byte 일치를 확인했다.

r754 상태는 PASS_FOUR_SUCCESSOR160_EXCLUSIVE_LOSSLESS_RECEIPTS_NOT_CURRENT_RUNTIME_OR_GO이다. decode8/fresh27/final27, 전체CPU 최대34.66%, 최소 가용RAM58.24709%, cleanup true를 확인했다. 원본 rewrite·삭제·이동 및 실제 제품·Native 실행은 없었다.

## 다음 검증과 보호 조건

다음은 실제160 manifest와24쌍 Binding, authority153/root159 worker capsule 및 parent/full oracle, 이전159 전체 독립 검증, 새 controller/DATA를 연결하는 작업이다. 그 후 현재 source/import/Rust inventory를 포함한 전체 비용과 whole preflight를 통과한 뒤 실제160을 단일 실행한다. 기존159 모델이나 이번 STEP/codec PASS를 실제160 GO 근거로 사용하지 않는다.

P09/A12/A13 Gate는 OPEN이고 full249-current와 signed16은 미완료다. P10 새 구현은 없다. 기존 CPU/RAM/읽기 속도/600초/cleanup 보호를 유지하고 과거 PC 프리즈 해결을 주장하지 않는다. 성공159/158과 authority153/152, 실패034 및 P08/P17/공유 Rust 사용자 변경·private 원본을 보존했다. 한글·접근 허용·UAC 요청, OS/Defender/WSL 변경, 외부 프로세스 종료, 원본 삭제·이동, 원격 push는 하지 않았다.

근거는 implementation/p09/evidence 아래 p09-361-case160-step-config001.v1.json, p09-361-case160-step-and-lossless-selection-r753.v1.json, p09-361-case160-four-envelope-producer-r754.v1.json이다.
