# P09 r89: formula_policy 11개 개별 runtime 수용과 CPU peak 검토

2026-10-08. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용43/249 · 잔여206(일반200+corpus6) · 미closing후보0 · 다음index44.
whole 수용3 / 통합 성공본문whole재조정대기40. 원 legacy pending1은 별도다.
원 STOP/FAILED 보존. compiled249=true/full249=false/signed16=false, Gate 미승격.
PC 프리즈 원인·해결 미확정. 43/249는 고정 r07 개별 runtime 큐이며 P09 전체 완료율이 아니다.

## 제품 검사와 수용 범위

r88 최신 문서 receipt의 runtime38/다음39/bound115=fresh115/finished/cleanup/원 bytes와
실패 보존을 확인한 뒤 같은 P222로39→40→41→42→43을 직렬 실행했다.
기존 성공1~38 본문/원 P220/P222 driver·tests/P221 helper/P219 compact/원 P208
parent·strict validator/Native pressure source는 수정·재실행하지 않았다.
매 실행88계약 PASS이며 서로 다른440개 계약이라는 뜻은 아니다.

- case039/run005: target 순서 변경 뒤 동일 target binding digest와 다른 policy raw digest를
  확인하며, 최신 version/generation으로 옛 bound 정책·cached byte 소비가 Drift로 거부된다.
  최신 정책의 새 준비는 허용되고 철회 후 다시 거부된다. 원 정책으로 fallback하지 않는다.
- case040/run006: binding 도중 철회와 callback 직전 다섯 번째 repository guard에서
  철회를 거부한다. callback 미호출/정확한 추가5조회/공개 경계를 검사한다.
- case041/run007: unknown 필드·중복/Unicode alias 키·boolean coercion·object 대신 positional
  array·추가 JSON·잘못된 JSON·빈/1MiB+1 입력 등29개 payload가 권한이 되지 못한다.
- case042/run008: caller policy/issuer/approval/expected_results/artifact_id 주입5종과
  잘못된 operation3종을 거부한다. 정책 repository 조회0회/audit 불변/no_publication 확인.
- case043/run009: target coverage/중복/외부 ID/anchor/AST/graph/정책 generation 변형10종과
  tenant~정책 digest source binding 변형15종을 거부한다.

고정 compiled 목록에서 actual_import::formula_policy:: 그룹은11개(33~43)이며
이제 해당 그룹의11개가 개별 runtime 큐에 수용된다. 합성 fixture의 DATA 정책 검사이지
실제 issuer/SQL/native/전체 제품 인수가 아니다. case043 이름의 whole도 fixture target
전체 범위이며1470 source whole 재조정 또는 full249/Gate PASS라는 뜻이 아니다.
qualification의 NOT_trusted_issuer/full_import/SQL/transport/atomic_execution/native/Gate
경계는 그대로 유지한다. 다음44는 formula_policy_issuer 그룹이다.

실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결을 유지했다.
각 exact1 PASS/248 filtered/exit0/COMMITTED, 전후1503입력 각118841107bytes 일치.
잠금1809/복제stream3006 모두close/잔여0/close 실패0; Job active0/tree empty=true.
원 Rust785/고정EXE/두 전체 실제 byte 읽기/identity/seek/최종 fresh hash/CPU·RAM·commit
보호/affinity1/BelowNormal/Job·GO·정리/600초/32open/s/no burst/binary1·other2MiB/s 불변.
별도 sampler/Git/build/SQL/한글 접근 허용/Defender·WSL·OS 설정 변경은 없다.

## 추가 코드 검토

source_policy/formulas/wire.rs의 descriptor·실제 byte 1MiB 상한, object-only decode,
deny_unknown_fields, d.end() 및 target 최대4096 경계를 확인했다.
stored_operations/policy.rs는 request 분류·검사를 source import/policy binding보다 먼저 수행한다.
원 guarded sampler와 IO·Native pressure/정리 구조를 유지했다. 이번에 CPU STOP은 없었다.
전체249의 결합 시간·600초 reader/1440표본 예산 충분성은 여전히 미수용이다.

## 자원 관측

|관측|case039|case040|case041|case042|case043|
|---|---:|---:|---:|---:|---:|
|시스템 CPU 최고(%)|27.88|42.58|65.22|33.95|100.00|
|제어 CPU 최고(머신 분모 %)|1.158301|1.158301|1.223776|1.356589|1.272727|
|제어 private 최고 bytes|40652800|39809024|40230912|40628224|42176512|
|RAM 여유 최저(%)|42.0174|40.9986|40.2724|42.0093|41.5588|
|제품 Job CPU 누적 초|6.297|7.281|1.078|0.234|2.594|
|제품 Job peak private MiB|33.86|32.19|24.62|22.66|23.55|
|원 parent elapsed 초|307.42|211.17|248.4|222.43|289.2|
|원 완료 자원 표본 수|865|679|763|701|864|
|준비 bound/fresh/finished|106/106/true|108/108/true|110/110/true|112/112/true|114/114/true|
|준비 실제 읽기 bytes|166543085|168292590|169932675|171608648|173255649|
|Native warning / pause windows|0/0|0/0|0/0|0/0|0/0|
|CPU STOP / cleanup|null/true|null/true|null/true|null/true|null/true|

각 peak는 서로 다른 workload/호스트 상태의 관측이다. elapsed/CPU 차이를 동일 workload
성능 개선으로 계산하지 않는다. root는 원 resource cleanup 뒤 terminal lifecycle 검사로
저장하므로 위 표본이 root 저장 전체를 감시했다는 뜻도 아니다.

## 시스템 CPU 100% 표본 조사와 진단 보정

case043에서 시스템 CPU 100% 표본2회 연속이 기록돼 다음 제품 실행을 하지 않고 조사했다.
P223은 원 보호 Reader로 고정 case043 root/body를 재읽고 전체 raw 로그/표본 대신
bounded 수치 요약만 남겼다. 최대 연속98% 이상2표본이라 원4회 연속 hard STOP에는
도달하지 않았다. Native·두 byte 읽기 pressure warning0과 모순되는 것으로 단정하지 않는다.

원 parent의 두 hot 표본에는 Job active_processes=4가 있으며 Job elapsed 약160초다.
그 구간 Job CPU 최대0.4836653651%/제어 CPU 최대0.177936%(모두 머신 분모)다.
root의 phase_at_sample=admission은 caller scope 태그이며 실제 startup/CPU 원인 표시가 아니다.
따라서 root 태그만으로 제품 실행 전 CPU peak라고 해석하지 않는다.

Job 값 없음은 0이 아님. P223의 root Job peak0은 필드 부재를 기본0으로 처리한 진단
표현 문제였으며 실제 Job CPU 0의 증거로 쓰지 않는다. P223 원본/소스/receipt는 보존했다.
P224 보정 진단은 missing 값을 null/관측 수0으로 구분하고 실제 parent의 두 Job 표본/
active4를 별도 기록한다. missing·observed zero·2/4 hot windows·예산/NaN/출력 제한8계약
PASS, 원 입력6bound=fresh/finished/cleanup=true/오류·stop=null이다.
P224 최초 명령은 진단 출력 경로 선택 오류로 기존 P223 fresh-only 보호에 막혔다.
owner·제품 실행/기존 파일 변경 전이었고 경로 보정 후 별도 P224 새 원장을 생성했다.
제품 body를 재실행하거나 기존 보호를 완화하지 않았다.

직접 CPU 측정은 낮지만 검증이 간접 OS/Defender 부하를 유발했는지와 외부 PID는
조사하지 않았다. 원인 미확정/PC 프리즈 해결 미확정이며 외부 탓 또는 해결 완료로 단정하지 않는다.
진단 개선은 원인을 0/잘못된 phase로 잘못 해석하지 않기 위한 것이며 CPU 성능 개선 증거가 아니다.

## 동일 JSON 표현 크기와 다음 consumer 비용

|동일 JSON 값|원 compact bytes|실제 carrier bytes|크기 감소|
|---|---:|---:|---:|
|39 root|1753322|584156|66.6829%|
|39 body|887064|193731|78.1604%|
|40 root|1594975|566616|64.4749%|
|40 body|644686|168951|73.7933%|
|41 root|1667968|576664|65.4272%|
|41 body|681972|174215|74.4542%|
|42 root|1614397|568736|64.7710%|
|42 body|644311|169843|73.6396%|
|43 root|1754706|585368|66.6401%|
|43 body|795536|186055|76.6126%|

모든 필드·표본 보존/semantic_fields_removed=0/original_files_rewritten=false.
원16MiB carrier/해제 cap·64KiB inflate·외부 pin/내부 길이/SHA/canonical/EOF 검사를 유지한다.
크기 감소만으로 CPU 개선을 주장하지 않는다.

|준비 단계|실제 증가 bytes|원 fresh 읽기 대조|
|---|---:|---|
|38→39|1615353|2×562368+3×163539|
|39→40|1749505|2×584156+3×193731|
|40→41|1640085|2×566616+3×168951|
|41→42|1675973|2×576664+3×174215|
|42→43|1647001|2×568736+3×169843|

각 증가량은 이전 packed root2회+body3회의 실제 크기와 일치하며 원 read/final fresh 횟수는
생략하지 않았다. 미래 전체249 시간·표본 예산이 충분하다는 증거는 아직 아니다.

## 증거 pin

경로 기준 implementation/p09/evidence/locked-r07/.

|파일|bytes|SHA256|
|---|---:|---|
|p222-case-039-run005.v1.json|584156|511b49513d45fcd9beba401fe6784c3cf6c1e89654d22e1db0bc5a4d5f02f5c4|
|cases/p222-case-039-run005.json|193731|3bbc3d246c2fbf0a2b73378294b86166dba205396d09dc9d023cba02c52e5668|
|p222-case-040-run006.v1.json|566616|976a043fc22de9faba59a1cd284559a1cdfd57e5bf3b5097aa6be2e3159e4583|
|cases/p222-case-040-run006.json|168951|a48d9ab702075b4cb2107b225366f0cf6728091b03284f02dabf6776f2e2e374|
|p222-case-041-run007.v1.json|576664|b17170c72ed979c46b54f47f2e7adcc2449d93ff295af43978bf78c4c2802c62|
|cases/p222-case-041-run007.json|174215|c09dc5f9352a061143daf1c2c232a264435e8d874bf5684abe2080b5377c04d1|
|p222-case-042-run008.v1.json|568736|322a2d5066ed9d79809929662f5e035f1a33c68aa61911d1c6a8814231d3dcdc|
|cases/p222-case-042-run008.json|169843|5b1da18d03160ad8484706e5e848e75832994883f295f1dc9eda25800f90b923|
|p222-case-043-run009.v1.json|585368|36139bea1c5a9c7e128485d9350b3c9eeaa439392498be9b0ffe9c5869c59c06|
|cases/p222-case-043-run009.json|186055|de8ecef23d916b34a113b8b6882e5c3fc9030c85b3878c522f785a69a5b8fc49|
|p223-cpu-peak-review-run01.v1.json|7375|353f471e9acb4beef62dc505fd6ebc9d46650fcd15b5bd73d07085e1261a4348|
|p224-cpu-peak-review-run01.v1.json|8727|659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254|

## 문서 동기화와 다음 경계

r88 두 문서의 기존 receipt pin/길이/SHA를 대조해 evidence/runtime-progress-r88/에 복사했다.
동일 r89 prefix 추가와 원 byte suffix 보존을 수행한다.
새 P225 문서 provider는 원 P222/P216 문서 검사와 runtime88+문서8계약을 유지하고
고정 P224 진단8계약 receipt/6입력/unknown과 observed Job 값/원 P222 문서 provider pin을
추가 fresh 대조한다. 제품/frame 재실행 없이 새 pair5개/전체 final fresh/cleanup/
문서 bytes·실패 보존/오류·stop=null/Gate OPEN일 때만 terminal r89 문서 동기화를 수용한다.
보고서 작성 자체는 문서 PASS가 아니다.

CPU 보호 중단 시 자동 재시도 금지. 실패/CPU STOP/부분 원장/정리 실패는 재개를 막는다.
원본 보존→관련 코드·관측 검토→안전한 최적화·검증 뒤 다음 미수용 항목을 진행한다.
다음은 같은 P222의 index44이며 성공1~43 본문은 재실행하지 않는다.
P09 Gate가 권위 있게 닫히기 전 P10 새 구현으로 넘어가지 않는다.
