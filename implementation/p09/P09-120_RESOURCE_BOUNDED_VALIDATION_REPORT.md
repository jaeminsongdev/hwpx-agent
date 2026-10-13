# P09-120 — 자원 제한 및 검증 실행 최적화

## 목적과 범위

2026-10-05 사용자가 PC CPU 과부하로 중단한 stored225 검증을 재개하기 전에 실행 비용과
병렬 부하를 제한한다. 기존 제품 Rust source, 검증 사례, 보안 guard, 원본 HWPX 및 기존 실행
파일은 변경하지 않는다. 전체 P09/P09~P20 완료나 성능 Gate 통과로 해석하지 않는다.

## 확인된 상태와 원인 구분

이전 실행에는 `--test-threads` 지정이 없었고 PC 논리 CPU는16개다. 기본 병렬 테스트 실행이
과부하의 주요 원인이라는 판단은 실행 방식과 당시 증상에 근거한 추론이며 CPU profiler의
함수별 병목 판정은 아니다. 이번 작업 시작의 live 관측은 CPU10%/RAM31.11GiB/여유13.94GiB였다.

## 구현

- `tools/p09/run_resource_bounded_tests.ps1`: 실제 binary를 직접 실행하되 test worker1,
  허용된 logical CPU2, BelowNormal 우선순위를 적용하고 적용 상태를 실행 중 재확인한다.
- `tools/p09/resource_bounded_test_support.ps1`: CPU/RAM 관측, 중단 조건, 안전한 test 출력
  projection을 제공한다. package/claim/key/raw stdout/stderr는 기록하지 않는다.
- `tools/p09/build_resource_optimized_tests.ps1`: 별도 target에서 offline/locked build,
  cargo jobs1, opt-level1/codegen-units1/debug-assertions true/overflow-checks true를
  해당 자식 프로세스의 환경에만 설정한다. 운영/사용자 설정은 바꾸지 않는다.
  Cargo 소유 자식의 CPU affinity/우선순위도 관측·제한한다.
- `tools/p09/tests/test_resource_bounded_test_support.ps1`: 정책/negative/출력 privacy 검사를 수행한다.

실행 전과 후에는 P120 Rust/module/Cargo source11의 크기/SHA를 대조한다. 이전 CPU 과부하
실행 파일은 그대로 보존하고 새 build는 `target/p09-120-resource-optimized`만 사용한다.
검증 범위 감소, guard 제거, fake approval, cache를 통한 보안 재검증 우회는 없다.

## 보호 조건

5초 간격 관측이며 시스템 CPU85% 이상이3회 연속이면 해당 작업만 중단한다. RAM 여유가
4096MiB 미만이면 즉시 중단한다. 테스트 process working set이2048MiB를 초과하거나 실행
시간 제한을 넘겨도 중단한다. 측정/affinity 적용 실패도 fail-closed로 중단한다.
시작 전 과부하이면 아예 실행하지 않는다. build RAM 샘플의 process working set은 Cargo
root 값이고 child 합계가 아니며, 시스템 available RAM 및 별도 child 관측을 함께 사용한다.
다른 사용자 앱은 종료하거나 우선순위를 바꾸지 않는다. affinity는 CPU hard-quota 백분율이나
PC 전체 CPU 제한과는 다르다. 모든 샘플은 runtime JSON에 남기되 콘솔은 약30초마다 요약한다.

## 현재 검증

8abcaa: 초기 정책 assertions15/DryRun PASS. 최초 smoke8374d5는 시작 전 resource pressure로
test process를 시작하지 않았다. 99a2b9 재측정 CPU24%/여유12889MiB. 이후 policy/출력 privacy
assertions16 및 PowerShell parse4는4e3ae6/exit0 PASS다.

제한 smoke의 실행 session은64864/PID10720이다. 실제 process readback으로
affinity3/BelowNormal/RAM21.43MiB 확인. d0fd7c 실측2초에서
test CPU5.8%/RAM27.2MiB였다. 다른 앱 CPU도 존재했으며 사용자 앱에는 조치하지 않았다.

제한된 unoptimized smoke는40ecb7/exit1에서301.15초 duration limit으로 중단했다.
실제 receipt: `target/p09-120-signed-original-corpus/resource-bounded-smoke-20261005-b.json`.
샘플55개, RAM 여유 최소12534MiB, test RAM 최대29.68MiB, 마지막 test CPU257.95초,
source11 exact_after=true. terminal test summary가 없으므로 해당1 test PASS나225 PASS가 아니다.
resource 제한은 적용됐지만 연산 비용 최적화 효과를 이 결과만으로 주장하지 않는다.

aa1657/session23682: 최적화 빌드 시작, Cargo root PID20128. bf450f에서 소유 child Cargo/conhost의
affinity3/BelowNormal 확인. 65379a에서 실제 rustc PID15124 affinity3/BelowNormal/RAM347.4MiB와
compiler opt-level1/debug-assertions=on/codegen-units1 확인. overflow checks는 명시적 process
환경 true이며 해당 observation에서 compiler의 explicit overflow flag는 관측되지 않았다.
build receipt 예정: `target/p09-120-resource-optimized/build-resource-20261005-a.json`.

## 다음 경계

최적화 빌드는 a5a3d9/exit0으로 PASS_BUILD_NOT_TEST_EXECUTION이다.572.9초/source11 exact,
소유 child affinity/priority observations284/샘플96/RAM 여유 최소6117MiB다.
새 binary는 `form_stored_provider-658c5ea10a96d565.exe`/10643456bytes/SHA
`e479511dc76564e032f23f9e6019ba2e37816a44e874307672344824e481bad9`이다.
ce27fe/exit0 동일 제한 smoke는1 PASS/0failed/0ignored/224filtered/41.39초였다.
이는 동일 사례가 unoptimized301초 미완료였던 것과 구분되는 실제 완료 결과다. 최초 실행은
timeout으로 종료됐고 PC의 다른 작업 부하도 변동하므로 정확한 배속/전체 성능 PASS로 확대하지 않는다.

전체225는 c38830/session51730/PID12640 →dfbc2d/exit0으로225 PASS/0failed/0ignored/0filtered,
544.01초다. 원본36/current16/protection32를 같은 자원 보호 조건으로 포함한다. 새3 test는
전체225에 포함되며 추가 합산하지 않는다. source11 전후 exact,98 resource samples,
system CPU max60%, available RAM min17635MiB, test RAM max27.17MiB다.
원본 수식16은 Changed0/NoChange16이며 full product/native/trust/SQL/Gate 완료가 아니다.
기존 CPU 중단과 미완료 smoke를 보존하고, native/SQL/접근허용/UI는 실행하지 않는다.
P09 Gate OPEN/P10 미착수/product false/full goal active를 유지한다.

최종 source/current byte guard 및 predecessor 보존은 e99d57 PASS, 확장 Python negative10은
e20452 PASS다. resource policy assertions16도 실제 통과했다. 원장 검사에서 single-worker,
affinity/priority/RAM guard/debug·overflow 설정 누락, filtered 실행, corpus/도구 hash 변조,
원본36 누락 및 unsupported product/Gate 승격은 거부된다.
