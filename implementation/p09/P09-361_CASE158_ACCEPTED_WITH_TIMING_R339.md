# P09 r339 — case158 실제 제품 통과와 독립 승인

## 공식 결과

- **152/249**, 잔여 **97**, 다음 **159**, current-generation 개별 47.
- 권위: `p09-361-case158-current-epoch-accept001.v1.json`, 396,156 bytes, SHA256 `ae5968271c2529880cb562a1ae3a48621af39d2af8d747d1ef77f6c245794f34`.
- state `PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE`, before151/after152/delta1, resource cleanup True.
- P09/A12/A13 OPEN. full249_current_qualified False, signed16_current_qualified False. P10 새 구현 0. P09~P20 전체 목표 ACTIVE.
- 성공157, 실패001~004, superseded/failed qualification 및 기존 사용자 변경을 보존했다. 승인된 run005를 다시 실행하지 않는다.

## 입력 제외 없이 준비 IO 감소

1. r713: 원157 whole scope에 포함된144/145/146의 현재 byte/SHA 핀 확인, 원 guarded reader와 final fresh 유지. Native/제품 재실행 0.
2. r714: 기존 CODE13 writer/codec 사용, 세 원본 8,024,854 bytes → 새 표현 2,095,289 bytes, 절감 5,929,565 bytes. 실제 six fresh decodes exact, 2MiB/s publisher/flush/fsync/exclusive 생성, 원본 변경·삭제 0. CPU26.81%, 가용 RAM25.82308%, cleanup True.
3. r715: 정확한 failed004 ROOT + 독립r703 + 현 reviewer source 조건의 새 실패 역할 CODE9 9/9. 이미 연결된failed003 역할은 보존하며 새private graph descriptor만 추가. 새 representation에 failed004 provenance를 명시한다. 제품/COMMITTED/GO 승격 0.
4. r716: failed004 원본2,287,363 bytes → 물리941,783 bytes, SHA `499ccdf18e6178d6a6e49a9849fe1424e8c0e20cab39900201ca12d833b7259f`. 두복원 exact, exclusive publisher, fresh23/final23, CPU25.38%, 가용 RAM24.80986%, cleanup True.
5. manifest022: 원manifest021의12쌍 + 실패004 1쌍 + prior144~146 3쌍 =16. 원 producer/qualifier/authority/reviewer 검증과 original/physical fresh 핀, 모든 semantic 입력 유지.
6. r717: manifest CODE4 4/4 및 실제 complete admission PASS, fresh110/final110, CPU41.1%, 가용 RAM22.36410%, cleanup True. Native/제품 증거가 아니다.
7. r718: 같은private Binding type으로16쌍 worker capsule encode/decode PASS. canonical8,973 bytes와 LF포함파일8,974 bytes를 구분했다. 실제 capsule003 파일 SHA `2bca52eab846a58415d5610f51a06077db8de5cb946c4728ba6141409774273a`, 기존16KiB 상한 유지. 실제 worker dispatch는 이 단계에서 실행하지 않았다.

## 새 controller·attempt·사전검증

- V7 attempt: 원 identity/worker/단일 adapter code를 유지하고 physical5/task005/root005로 명시적 연결. 실패001/002/003/004 및 독립검토를 검증하며 기존 attempt/relabel/overwrite 거부.
- V25/DATA031: core16 + 역할4 + timing3 private namespace. 실패003/004 각각 같은 reader의 선언만 재사용하고 원 final fresh/Native2byte/600초/60초 margin/15초 capture/decode5/rates/warning/Job 보호 유지. 원 V24 등 historical source를 변경하지 않았다.
- r719 bootstrap: 단일 역할을 전제한 namespace identity 체크가 새 두 역할과 불일치해 STOP. 원 source 보존. cleanup receipt는 출력되지 않았으므로 별도 성공으로 만들지 않았다.
- r720 qualifier: 오래된 attempt chain 속성 접근 AttributeError, tests 전 STOP/cleanup True. 명시적 ATTEMPT_PINS 전체 검증으로 경로를 수정했다.
- r721: CODE27의 과거 실패역할 시험 routing 한 건 실패. old role은manifest.original.failed, 새 역할은manifest.failed 각각 검증하도록 수정했다.
- r722: 27/27 통과지만 state label에 RUN004가 남아 superseded로 보존. 현재 RUN005 label/source 다시 자격 확인.
- r723: CODE27 27/27, fresh34/final34, CPU21.86%, 가용 RAM22.69982%, cleanup True. 아직 제품/GO 증거는 아니었다.
- wholepreflight033 PASS: 251.58247초, raw2,681/292,213,238bytes, Rust787/import63, fresh992/read1,994/324,736,759bytes/final992, CPU35.67%, RAM20.81787%, cleanup True.
- 새 physical scope2,665/255,190,755bytes, semantic2,665/281,194,120bytes, dirs372. 완전 모델597.313651초 < 원600초. 모델은 실제 완료 보장이 아니고 unknown pressure/OS latency를 0으로 주장하지 않는다.

## 실제 run005

`p09-361-case158-current-runtime-run005.v1.json`

- 4,404,465 bytes, SHA `34db0892a40886196a3307ba21decfdcb7ecdede4e6e02feb48422636a54ded4`.
- PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE, 644.03초. 이 값은 bootstrap을 포함한 전체 elapsed이며 Native 잠금600초를 늘린 값이 아니다.
- 실제 test1 passed/0 failed/0 ignored/248 filtered: `actual_import::source_review_assembly::stored_assembly_retains_complete_source_raw_typed_review_and_old_branches_without_publication`.
- Frame COMMITTED, 실제 whole byte boundaries2, input handles3,037 opened=3,037 closed, remaining0, cleanup True/owned tree empty True.
- 원 Native clock: after_acquire221.013842초, before_parent360.631633초, after_parent/before_release508.973422초 < 원600초. 첫 lock error 없음.
- strict GO→complete capture1.545879초 <15, 실제 GO1/capture1. aggregate16×2=32decodes,0.434143초 < shared5초.
- 전체CPU 최대32.83%, 가용RAM 최저20.81828%, parent CPU 최대5.79596%, parent private 최대49.23047MiB.
- Native timing reserve/checkpoint:3,037/3,037, 총219.322843초·최대0.234912초. 순수CreateFileW:3,037/3,037, 총0.552143초·최대0.015838초. unknown0/accounting_unavailableFalse.
- 정상 실행의 분리 계측일 뿐 이전 CPU98%/commit 폭증/PC freeze의 인과를 특정하거나 해결됐다고 주장하지 않는다.

## 독립 승인 연결 수정과 결과

제품을 재실행하지 않고 기존 qualified optimized acceptance v1/v2/v3, 같은 원 전체 frozen oracle/AST/guard/reader/64KiB workspace/fsynced exclusive writer를 사용했다.

- acceptance diagnostic001/002 FAILED, delta0/cleanup True. 안전한 오류 frame 조사로 `sql_source_link_or_missing` 확인: 과거 source-stat per-case DATA158를 찾는 경로였으며 파일이 없고 실제 run005 Native scope에도 없었다.
- 과거 DATA를 만들어 Native 입력인 척하지 않았다. 별도 `current_envelope_acceptance_prepare_v1.py`는 current controller admission과 독립 inherited scope를 확인하고, 원 frozen flat prepare AST와 모든 Native/제품/Job/resource/cleanup oracle을 current root/context로 실행한다.
- r724 읽기전용 probe는 inherited compose를 물리 투영 후 wrapper에 적용해 ORACLE_SCOPE KeyError. 실패 보존 후 순서를 의미상 원본 compose → qualified physical projector로 바로잡았다. V25 및 run005는 수정하지 않았다.
- r725 실제 complete read-only prepare PASS, fresh222/final222, CPU47.85%, 가용RAM21.43887%, cleanup True, acceptance publication/Native/제품 재실행0. 원 acceptor/oracle AST restoration과 모든원 predicate/cost/source check 유지가 기록됐다.
- acceptance diagnostic003은 r725 state/root/code pins를 fresh 확인한 뒤 실제 full prepare·final boundary·epoch write 수행. PASS_ORIGINAL_IMMUTABLE_ACCEPTANCE_WITH_QUALIFIED_METADATA_READER, delta1, cleanup True. canonical152 권위 파일을 직접 확인했다.

## 다음 경계

case159에는 실제 case158의 권위/root를 사용한 새 immutable STEP/DATA/controller/full current scope·cost·사전검증이 필요하다. case158을 다시 실행하거나 old597초 모델을 새 case의 모델로 사용하지 않는다. 이후 159 한 건의 실제품과 독립승인을 진행한다. 잔여97은 개별 queue 잔여이며 P09 전체 완료율이 아니다. 전수249-current/signed16/whole reconciliation 및 P09 Gate는 별도 미완료다.

이번 작업에서 접근허용/한글/UAC, OS·Defender·WSL 변경, 외부process 종료, 원본 삭제·이동, 원격push 없음.
