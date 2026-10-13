# P09 case158 run002 전체 연결과 사전검증 — r332

공식 승인151/249·미완료98·next158·현재 generation 개별46.
P09/A12/A13 OPEN, P10 새 구현0, 목표ACTIVE. 이번 제품 승인 증가0.

## 변경 범위

- 원 V19 및 성공157/권위151·실패run001 보존. 새 V20에만 명시 run002를 연결했다.
- reviewed_case158_attempt_v4는 V3 단일 인자 adapter를 유지하며 원 root_path/task/public_run/validate_actual 함수 code/default/closure를 그대로 사용한다. 실제 기록의 경로·task를 사후 재라벨링하지 않는다.
- V20 전체 source.prepare root 경로, worker task, public run2→qualification1, 실제 template physical2 및 full candidate identity가 일치한다. 원 preflight/whole oracle/원 worker/GO/Job/입력 보호 범위를 유지했다.
- qualifier는 원 자원 admission 이후 현재 controller를 import한다. 이전 startup resource failure가 원인 확정이나 제품 실행 증거였다고 주장하지 않는다. 같은 원 sampler의 실패 stage/표본도 보존하도록 했다.

## 코드 자격

CODE20/r670:20/20 PASS·fresh10/final10·CPUmax8.77%·가용RAMmin69.62279%·cleanupTrue.
새 source5개는 p361-r332-qualified에 exact archive. 구성요소 자격은 실제 제품/Native/GO 증거가 아니다.
초기 private namespace 속성 대신 cloned template globals를 읽어야 하는 연결 오류를 수정했다.
그 이전 source와 import 실패r671을 보존했다. resource STOP r672 및 당시 qualifier source도 보존한다.

## 전체 사전검증

run002 preflight027:PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE.
235.5462375초·원 metadata 계약10·compiledRust787·imports63.
fresh926/final926·1856 read passes·298149686 bytes.
raw representations2617/283435598 bytes; budget physical2606/258934358 bytes.
원 scope/두 실제 읽기/14 acquisition·20 open ceiling·1/2MiB read rate·600 lock limit·60 margin·15 product window·decoder5 유지.
보수적 predicted_runtime_combined_seconds596.6695435<600. 실제 완료 보장은 아니다.
CPUmax32.39%·가용RAMmin64.14556%·cleanupTrue.
터미널 관측r673은 원 preflight027을 대체하지 않는다.

## 실제 run002와 독립 STOP 검토

실행1회, terminalexit1/DEFERRED_NOT_STARTED/STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME.
실패 root21201bytes/SHA956dbb5fb6723eeaac4b59ad6d4ffa7965583c17adcee318385f462d96b36dd4 보존.
경과4.23초·worker/job/제품본문 false·source_frame null/source_freeze []·Native qualification false·cleanupTrue·owned tree empty.
원 기록은 실패로 유지한다. V2 receipt writer의 실제 Native-latch 실패 분기까지 자격이 입증됐다는 뜻은 아니다.

CODE7+실제 exact STOP 독립 검토/r675 PASS:root source/코드2 fresh3/final3.
실제 시스템CPUmax76.17%·parentCPUmax0.1943722%·private max45.8828MiB·가용RAMmin63.21892%.
원 표본의 최소 간격0.502446초:이번 receipt에서 short forced interval은 관측되지 않았다.
metadata23 reads/3087483bytes·source_requests23·64KiB workspace1·모든 lease반환.
metadata warning75에서 one-way latch1/추가 cooling0/원callback복구·중복hard callback305회 회피가 기록됐다.
Defender/다른프로세스의 인과·PC프리즈 해결은 미증명이다.
STOP review code 최초fixture의 parent_private_percent 누락 오류r674 및 source를 보존한 뒤 공통fixture를 수정했다.
검토 자체CPUmax0.98%·가용RAMmin67.02047%·cleanupTrue.

## 다음 경계

run001/002 재실행·덮어쓰기 및 통과157 제품 replay를 하지 않는다.
실패002 원source와 binding 초기 IO를 검토하고 필요한 최적화만 수행한다.
다음 실제 시도는 검토된 실패002와 분리된 identity, 현재 source/DATA/whole preflight 자격을 요구한다.
실제158 전체 product/Native COMMITTED 및 독립 승인 전151/249를 늘리지 않는다.
접근허용/한글/UAC/OS·Defender·WSL 설정/다른 앱 종료/Git/삭제·이동0.

## 근거

- evidence/p09-361-case158-envelope-controller-run002-code20-r670.v1.json
- evidence/p09-361-case158-envelope-controller-data026.v1.json
- evidence/p09-361-case158-envelope-controller-run002-preflight027.v1.json
- evidence/p09-361-case158-current-runtime-run002.v1.json
- evidence/p09-361-case158-run002-metadata-stop-review-code7-r675.v1.json
