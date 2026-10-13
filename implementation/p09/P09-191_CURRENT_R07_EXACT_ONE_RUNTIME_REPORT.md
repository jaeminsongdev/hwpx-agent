# P09-191 — current r07 exact-one 실행과 완료 재사용

## 결과

실제 현재 r07 테스트 1개가 정상 종료했고, 독립 전체 입력 closing까지 통과했다.
그 결과를 읽은 후속 실행 계획이 첫 테스트를 건너뛰고 index2를 선택하는 것을 확인했다.
현재 테스트 큐는 1/249 완료, 248 남음 = 일반 242 + corpus 묶음 6이다.
이 수치는 P09 전체 제품 잔여 작업 수나 완료율이 아니다.

full249/signed16/single-process 통합/SQL/native/product는 미수용이다.
P09/A12/A13 OPEN, 목표 active, P10 새 구현 없음.
원 P189 중단 결과의 부분48 카운트는 재사용 완료로 소급하지 않았다.

## 구현과 보호

`tools/p09/run_resumable_r07_case.py`는 다음을 연결한다.

- exact-one public test name, --exact, worker1/threads1/pretty/color-never/capture0.
- 기존 GO, 실제 Job membership, kernel limits readback, kill-on-close/no-breakaway.
- one affinity/BelowNormal, CPU hard6.25% machine, RAM hard8%/soft7%.
- .5초 sampling, systemCPU98%4회/여유RAM8%/commit95%/기존1200초/출력32768bytes.
- assertion/overflow 유지, 현재 EXE 사용, 새 Cargo compile 없음.
- 현재EXE와 모든non-EXE 입력1403개는 각case 전후 모든바이트 fresh 확인.
- 과거EXE67개만 준비/closing의 전체68EXE 보존 검사로 옮김.
- original source/corpus/fixtures를 줄이거나 검사를 생략하지 않음.
- 성공 후보를 독립 closing으로 수용하며 auto retry/parallel/다음case 자동 실행 없음.

완료 reuse는 원 P190 검증기로 실제 이름/정상exit/정확한 terminal/동일binding/
전후whole 입력/fresh 외부 receipt pin/cleanup을 모두 재확인한다.
별도 closing이 없는 부분 성공은 완료로 건너뛰지 않는다.

## 실제 증거

1. Preparation-run01: 142 contracts, whole1470/final fresh1470,
   read3125/964944329bytes,349.4339s, stop=null/cleanup=true.
2. Case001: actual_aead_tamper_cannot_be_reclassified_as_an_importer_or_policy_failure.
   exit0/1PASS/0failed/0ignored/0measured/248filtered,132.71초, 정상 정리.
   전후 각각1403readpasses/117816004bytes. stdout216/stderr0/capture error=null.
3. Closing-run01: whole original68EXE/Rust785/source249/59module,
   bound1472/final fresh1472/read3129/967383283bytes,351.1391s,
   stop=null/cleanup=true. 새 테스트 본문은 실행하지 않음.
4. Plan-run04: 완료case1을 실제로 skip하고 다음 index2/attempt1 선택.
   next는 actual_head_advance_invalidates_old_import_even_with_identical_result_bytes.
   이 read-only plan에서는 source/EXE whole을 새로 검사한 것이 아니다.

실제 최초case는 importer/policy와 구분한 stored-artifact tamper 거부를 검사한다.
fixture/in-memory stored-provider 경로의 검증이지 운영 SQL/원본 한글 수용이 아니다.
원 테스트 본문과 원본 HWPX/current EXE는 수정하지 않았다.

## 부하 관측과 한계

Case001 구간258samples: hostCPUmax100%,availableRAMmin47.040157%,
owned Job CPU합계0.328s/peak private32.29MiB. 지속CPU 보호 중단은 없었다.
host100%가 한 번도 없었다고 하거나 PC프리즈 원인이 해결됐다고 주장하지 않는다.
132.71초는 admission/전후hash/정리를 포함하며 테스트본문만의 시간은 아니다.

과거EXE67개의361560576bytes = 약344.81MiB는 매case의각hash pass에서 반복하지 않는다.
전후 두pass의723121152bytes를 batch 경계로 옮긴 구조적 변경이다.
다만 현재 최초1개 invocation은 whole preparation + case + whole closing이므로
전체 비용 감소/성능배수/CPU 감소율의 A/B benchmark가 아니다.
다음은 여러개의 순차 개별case가 준비/closing을 공유하도록 bounded continuation을 연결하는 것이다.
그 뒤 무거운6개의 내부 원본 반복을 원본별로 분할하며 모든assert/최종집계를 유지한다.

## 계약 검사와 사전 보완

원109 + P19022 + 새runtime adapter11 = 142 synthetic contracts PASS.
실제 실행과 synthetic/no-child 계약 검사를 구분한다.
최초141에는 원c.run의 상태명 기반 반환까지 다루는 검사가 없었다.
actual 시작 전에 반환값 문제를 보완하고 회귀1개를 추가했다.
이전helper/test 전체 및 light1/2를 source-archive에 보존했고 원 실패를 삭제하지 않았다.
latest light-run03은142 PASS다. 처음light를 최신수정 결과로 소급하지 않는다.

## 아직 남은 범위

일반242개 및 원본묶음6개는 pending이다. 추가case 실제 실행은 NOT_RUN.
묶음6개를 skip/ignored로 처리하지 않으며 원본별로 검증 가능하게 분할해야 한다.
완료1을 제품/Gate/full249/signed16 완료로 승격하지 않는다.
한글/접근허용/SQL/Git/Review/설치/다운로드/삭제·이동/전역 설정 변경 없음.

증거 파일:

- implementation/p09/evidence/p09-191-r07-resumable-run01.preparation.v1.json
- implementation/p09/evidence/resumable-r07/p190-case-001-attempt-001.json
- implementation/p09/evidence/p09-191-r07-resumable-run01.closing.v1.json
- implementation/p09/evidence/p09-191-r07-resumable-run04.plan.v1.json
