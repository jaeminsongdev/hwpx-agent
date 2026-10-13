# P09-198 — exact-one runtime 재개와 case005 실제 통과

2026-10-08. 목표active/P09·A12·A13 OPEN/product=false/P10 새 구현 없음.
compiled249=true/full249=false/signed16=false. 이번 정상 종료만으로 PC 프리즈 해결을 주장하지 않는다.

## 현재 큐와 판정 범위

P196의 실제 runtime 수용4를 재사용하고 case005만 추가 실행·closing했다.
runtime 수용5/249, 잔여244(일반238+corpus6), 미closing후보0, 다음index6이다.
244는 실제 미실행 테스트 수이며 P09 전체 작업 수/전체 완료율은 아니다.
원 whole 기준 수용3은 그대로다. whole reconciliation이 필요한 성공 body는
원 case004와 새 case005의2개다. 새로운 runtime 수용을 whole/Gate PASS로 바꾸지 않는다.
corpus6, full249, signed16, 실제 SQL/한글/native 제품 검증은 미완료 상태를 유지한다.

## 구현과 계약

run_runtime_resumable_r07_case.py와 test_runtime_resumable_r07_case.py를 추가했다.
P190/P191의 실제 terminal/capture/Job/전후source/cleanup 판정을 유지한다.
새 case는 evidence/runtime-r07/cases/에 쓰므로 원 legacy/P196 receipt inventory를
재작성하지 않는다. P198 progress는 원 runtime4와 새 receipt를 함께 검증한다.
당시 r66/P196 plan의4는 역사적 기록이며 현재5에 대한 권위 있는 큐는 P198 plan이다.

원runtime1403＋원scheduler2＋P198/P196/P193/P197 controller 각2=1413을 확인한다.
현재EXE와 모든 원non-EXE 입력을 보존하고 각 body의 실제 before/after byte read를
확인한다. P196 case_scope/validate에 새controller의 정확한 pin map을 전달하며
원 receipt의 read count/bytes를 줄여 보이게 하거나 투영하지 않는다.
별도 closing은 같은 원 P196 runtime 스키마/validator로 실제 모든 runtime byte를
다시 읽는다. sealed historical EXE67의 현재 fresh/Gate 확인 의무는 그대로 남는다.

현재 입력의 동일성이 검증된 실제 성공 body를 다시 실행하지 않는다. 성공 후
미closing 후보가 있으면 새 body를 막는다. stop/failure 뒤 자동 retry/next/closing은 없다.
`--mode close --run N --index I --attempt A`는 통과 body를 재실행하지 않고
독립 closing만 복구한다. corpus/수용된이름/임의case override/미완성인자를 거부한다.
이 복구 경로는 계약검사로 확인했으며 실제 복구가 필요하지 않아 실행하지 않았다.

one-affinity/BelowNormal/owned Job CPU·RAM 상한, .5초 표본/CPU98%4회/RAM·commit 비율,
원1200초body/600초reader/32768stream cap/정확한1PASS＋248filtered/exit0/cleanup을 유지한다.
P197의 제한된 read-only CPU 귀속을 parent 표본에 연결한다. 새 sampler thread나
외부 프로세스 변경/권한 상승/명령줄·경로 조회는 없다. 접근 거부 프로세스는0으로
가정하지 않는다. own CPU/RAM 및 기존 Job IO 관측을 그대로 남긴다.

light01 뒤 close-only 복구 및 whole 미확인 성공body 집계를 보완했다. 당시 전체source/test는
source-archive/p09-198-pre-recovery-cli/에 보존했다. light02는 기존188＋신규14=202
synthetic contracts PASS/stop=null/cleanup=true/IO.finished=true, next5를 실제 계산했다.
계약검사의 PASS를 실제제품/SQL/native/Gate PASS로 사용하지 않는다.

## 실제 case005 및 closing

```powershell
python -B tools/p09/run_runtime_resumable_r07_case.py --mode actual --run 1
```

테스트 이름: actual_import::field_ranges::actual_aead_tamper_is_original_service_failure_not_field_projection_failure.
저장소 서비스의 실제 import/field-range 검증 경로에서 fixture blob을 변조하고,
실패가 Artifact 원본 서비스 오류로 유지되며 새 range import도 거부되는지 확인했다.
실제 SQL 서버나 한글 GUI 경로는 아니다. 원 Rust 코드·원fixture·r07 EXE를 변경하지 않았다.

case005: exact1PASS/248filtered/exit0/stop=null/cleanup=true/owned_tree_empty=true,
elapsed133.83초(입력확인 포함), 원Runtime1413을2회117910771bytes씩 읽었다.
Job CPU0.188초/peakprivate28.85MiB, hostCPUmax61.36%, ownCPUmax0.919118%,
availableRAMmin48.71795689%. CPU귀속127 intervals/error=null. 원kernel Job 후손0으로 종료했다.

closing: PASS_EXACT_R07_RUNTIME_SOURCE_CLOSING_NOT_WHOLE_OR_GATE/exit0,
wall65.6251초/stop=null/cleanup=true/IO.finished=true/bound1414=fresh1414,
read237768033bytes. hostCPUmax41.86%, ownCPUmax0.970874%, ownprivate max48914432bytes,
availableRAMmin49.66912466%, CPU귀속63 intervals/error=null.
이후 plan01은 runtime5/잔여244/미closing0/next6/whole미확인성공2를 재계산했다.
한 실행에 실제 body는1개뿐이며 통과한1~4번을 재실행하지 않았다.

## 정확한 증거핀

경로는 implementation/p09/evidence/runtime-r07/ 기준이다.

| 파일 | bytes | SHA256 |
|---|---:|---|
| p198-runtime-resume-light-run02.v1.json | 49066 | 5c6db491340943f81cf01b4f28281817590de24f1e4adc76cb2fc06d6e17242f |
| p198-runtime-resume-preparation-run01.v1.json | 49141 | f149e0e90265def09eb8e92dc7ed12bde0317182c61af243d74d7eda975dbda8 |
| cases/p190-case-005-attempt-001.json | 936745 | cc19fbe61c82168ba7970dbea001b3f1690ddf29d12a9ddd4d3fb26acae2231f |
| p198-case-005-attempt-001-close-01.v1.json | 1135501 | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-runtime-resume-plan-run01.v1.json | 54301 | 8f4ef7accf5f9ea0710bcb8bebe7ebbc427006a12af9777c372df3d36c09abf1 |

CURRENT_STATE/P09-149의 r66 전체를 source-archive/p09-198-pre-single-runtime-progress/에 보존했다.
같은 r67 prefix를 추가하고 이전 본문의 byte를 그대로 유지한다. 이 문서는 실제 closing
후에 작성했으며 해당 closing의 입력이었다고 주장하지 않는다.

## 다음 exact task

next6를 동일한 `--mode actual --run 2`의1-case 실행으로 처리한다. source/EXE의
동일성이 맞지 않으면 수용/재사용하지 않는다. CPU/RAM 보호 stop이면 다음 테스트나
자동 retry를 하지 않는다. 역사적 전체검증/SQL/한글 접근허용/전체Gate는 별도 미완료다.
