# P09-195 — case004 독립 closing 복구와 IO 범위 조사

2026-10-08. 목표active/P09·A12·A13 OPEN/product=false/P10 새 구현 없음.
compiled249=true/full249=false/signed16=false. PC 프리즈 원인·해결을 확정하지 않는다.
이번 단계에 case004 재실행/새 product EXE/Cargo/SQL/Hangul/접근허용/OS 설정 변경은 없다.

## 현재 큐와 경계

원 통과3의 수용은 그대로 유지한다. case004는 1PASS/exit0/owned cleanup이 검증된 통과후보1이나
별도 whole closing은 미수용이다. 수용3/249, 잔여246(일반240+corpus6), 실제미실행245(일반239+corpus6).
다음미실행index5지만 원후보 closing 전에는 기존 runner가 다음 case를 시작하지 않는다.
이 수치를 P09 전체 완료율로 사용하지 않는다. 성공 body를 자동 재실행하지 않는다.

## 독립 복구 구현

recover_r07_case004_closing.py와 test_r07_independent_closing.py를 추가했다.
원 run_shared_resumable_r07_batch.close(5)의 전체 판정 body를 유지한다.
fresh 출력 요청만 새 p09-195-independent-case004-recovery-closing-runNN.v1.json으로 돌리고,
원 p09-191-r07-resumable-run05.closing.v1.json의 실패 byte는 그대로 둔다.
PASS 복구만 원 closing reference에 명시적으로 연결하도록 별도 validate_recovery/progress를 구현했다.
현재 PASS 복구가 없으므로 해당 alias가 실제 수용됐다고 주장하지 않는다.

binary 읽기를2.5→1.5MiB/s로 낮췄다. 일반파일4MiB/s/64KiB burst/16MiB parse cap,
원 .5초 수동표본/one-affinity/BelowNormal/98%4회/freeRAM8%/commit95%/600초scope는 유지한다.
모든 원 읽기와 마지막 전체 fresh hash를 수행하는 구조이며 stat/cache로 대체하지 않는다.
원1470 입력의 byte 합은 binary375777280/other103599300이다.
2회 읽기의 속도 하한527.2255초, metadata32MiB와40초 여유를 포함한 추정575.2255초다.
시간이 맞을 가능성만 확인한 것으로 완료를 보장한 계산이 아니다.

P193 ownCPU/ownmemory 관측을 기존 표본에 연결했다. 새 sampler thread/외부 PID 조회는 없다.
단계와 논리read counter를 저장하되 외부 원인/실제 디스크IO를 입증한 것으로 취급하지 않는다.
controller6개source를 입력과 최종 fresh hash에 추가하고 원baseline identity는 바꾸지 않는다.

## 계약검사 및 래퍼 수정

light-run04는 기존154＋P193 관측10＋신규12=176 synthetic contracts PASS, stop=null/cleanup=true다.
기존 fixture reader는 원 구현에 위임하고 실제 소유자만 새 관측reader로 바꾼다.
초기 관측 누락 시 실패 receipt를 쓰지 못할 수 있는 경로는 보완했고, missing을0 사용량으로 바꾸지 않는다.
배열/null/string JSON은 그대로 통과시키도록 dump observer를 보완했다.

recover-run01/02는 whole 확인 전 래퍼 오류로 FAILED_NOT_ACCEPTED, stop=null이다.
run02의 값 없는 closed diagnostic은 TypeError 및 공개 코드 module/function/line만 남겼다.
CLI의 __main__과 계약검사의 canonical import가 다른module을 만들어, 역할patch 중 재import된
Reader base가 factory 함수로 바뀐 것이 오류 위치에서 확인됐다.
sys.modules alias를 등록해 같은 원 class/module을 사용하게 하고 해당 경로 계약검사를 추가했다.
run01은 상세가 남지 않아 동일 원인이라고 확정하지 않는다.
수정 전 source/test 전체는 pre-failure-observation-repair, pre-json-observer-repair,
pre-canonical-import-repair source-archive에 각각 보존했다. 모든 초기 receipt도 보존한다.

## 실제 복구 run03 — 낮춘 속도에서도 CPU STOP

FAILED_NOT_ACCEPTED, error=resource_stop_reason=STOP_SUSTAINED_SYSTEM_CPU,
wall214.5276초/cleanup=true/실행핸들exit1, candidate_body_reexecuted=false/additional_product_child=false.
IO bound1271/read1281/357417924bytes/final fresh0/finished=false.
원1470 전체 fresh 완료나 case004 수용으로 승격하지 않는다.

interrupted protected EXE:
target/p09-150-signed-durable/build/debug/examples/formula_issuer_product_postgres_probe-p150-r05.exe.
이 파일을 실행한 것이 아니라 첫 whole byte hash를 읽던 중이다.
직전 P194 STOP의 p151 EXE와 다른 historical artifact에서 발생했다.

410완료표본: hostCPUmax100%, ownCPU(machine)max2.073598%,
ownprivate max40091648bytes(약38.23MiB), ownworking-set max50872320bytes(약48.52MiB),
availableRAMmin29.636965840913785%.
마지막4표본 host98.97/99.93/100/100%, ownCPU 모두0%, availableRAM30.21~30.80%.
직접 reader의 CPU/RAM 독점이 아니라는 구간 관측은 있지만 간접IO부하/Defender/다른프로세스/
프리즈 원인은 특정하지 않는다. 속도 감소만으로 문제가 해결됐다고 주장하지 않는다.
이후 같은 heavy 확인을 다시 시작하지 않았다.

## 별도 IO 범위 조사 — metadata만 읽음

audit_r07_closing_workload.py와 test_r07_closing_workload.py를 추가했다.
기존 worker의 단일 현재EXE 호출/원runtime_scope/원source_extension/실제case004 전후 증거를 확인했다.
모든 non-EXE 입력을 보존하는 scope가1403＋scheduler2=1405임을 검증했다.
원 sealed prep의 historical67개는 현재 byte를 다시 읽지 않고 참조 정보로만 분류했다.
원176 계약검사의 byte 동일성을 확인해 재사용하고 신규 분류4 계약검사 PASS.
inventory bound32/fresh32/24112015bytes, stop=null/cleanup=true. EXE byte rehash/새 closing/새 child 없음.

| 범위 | 입력 수 | 1회 전체 byte 읽기량 |
|---|---:|---:|
| 현재 case의 runtime＋scheduler | 1405 | 117837770 |
| 원 whole baseline | 1470 | 479376580 |
| 추가 historical EXE만 | 67 | 361560576 |

현재EXE는14216704bytes이고 historical만2회723121152bytes(약689.62MiB)다.
역사적EXE가 whole binary byte의96.2167%를 차지한다.
이것은 반복 확인 비용의 정량 근거이며 해당 파일의 현재 상태/Gate 확인을 생략해도 된다는 판정이 아니다.
다음은 실제 runtime 입력의 closing과 역사적 whole Gate 확인을 명시적으로 분리할 수 있는지
요구사항/계약을 점검하는 작업이다. 가능하더라도 원실패의 PASS 변조, whole 미검증의 완료 승격,
source/EXE freshness 누락이나 CPU 보호 완화는 금지한다.

## 정확한 최신 증거핀

아래 경로는 implementation/p09/evidence/ 기준이다.

| 경로 | bytes | SHA256 |
|---|---:|---|
| p09-195-case004-recovery-light-run04.v1.json | 28959 | a4a8803485e247713079adadd6e66d908708a945cee07b914429beddf09ca338 |
| p09-195-independent-case004-recovery-closing-run01.v1.json | 13087 | 905fcee313d88afc1b9cf8b765f305222c91fd9eb09a9d135fd5a55c7a1f4a58 |
| p09-195-independent-case004-recovery-closing-run02.v1.json | 13981 | 4d8e3034f3616ed5ea98ab17dee9a8a9087c3b384f7293a06bde7fdce2ea1367 |
| p09-195-independent-case004-recovery-closing-run03.v1.json | 758505 | 070c8087d9cc548a33faeaefd407fd0858a5691e7f33d3fd2d8b7214a9f527bf |
| p09-195-closing-workload-inventory-run01.v1.json | 18179 | ca8d0fa757a27069ba96ce5f4b416adcd387705f9b0cd071c81276e8a3af30a5 |

CURRENT_STATE.md/P09-149의 이전r64전체를 source-archive/p09-195-pre-recovery-progress/에 보존했다.
같은 새r65 prefix만 추가하며 이하 과거 기록을 그대로 유지한다.
이 보고서와 r65 문서는 위 inventory/closing 검사 완료 뒤 작성되며, 그 검사의 입력이었다고 주장하지 않는다.
