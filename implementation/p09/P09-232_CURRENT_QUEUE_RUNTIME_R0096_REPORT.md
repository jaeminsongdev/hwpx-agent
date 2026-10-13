# P09 r96: provision 잔여4개 실제 수용과 case64 순간 CPU 피크 검토

2026-10-09. 목표 active. P09·A12·A13 OPEN, product=false. P10 새 구현 없음.
runtime 수용61/249 · 잔여188(일반182+corpus6) · 미closing후보0 · 다음index68.
whole재조정대기58. 원 STOP/FAILED 보존. PC 프리즈 원인·해결 미확정.
현재 수는 고정 r07 개별 runtime 큐이며 P09 전체 잔여 작업 수·완료율이 아니다.

## 실제 검증 범위

기존 수용57개 본문은 재실행하지 않고 원장·source 동일성을 대조했다.
원 P230 caller로64/run004→65/run005→66/run006→67/run007을 각각 한 번씩,
앞 사례의 정리·CPU/RAM 확인 후 다음 사례를 실행했다.
64 피크 요약 확인 시65는 이미 시작됐으며 이후66 전에는 별도 피크 검토를 완료했다.
64의 통과를 CPU 중단으로 오인하거나 실패를 PASS로 바꾸지 않았다.

64: 루트 scope/시간/generation/key/tenant/preflight8개 오류와 읽기 권한 부족을
artifact/registry 생성 전에 거부하고 증거 수 불변/root_writes0/no_publication 검사.
65: signer hook 동안 같은 generation의 root/policy drift를 만든2개 fixture에서
approval artifact 없음/approval_writes0/no_publication 검사.
66: scanner 미검증과 AEAD 변조2개 fixture의 ArtifactReadback 거부/
실패 artifact identity 보존/NotAttempted/root_writes0/no_publication 검사.
67: signer/key/signature/수명/clock/preflight8개 fixture 실패를 승인 쓰기 전 거부/
artifact 없음/NotAttempted/approval_writes0/예상 signer 호출 수/no_publication 검사.
합성 registry fixture이며 운영 SQL 등록·생산 키 custody·실제 issuer 운영 인수가 아니다.

고정 inventory339893bytes/SHA7b06997d3b8090967597fad1d12b94446e20e3a17ba206233ae8711fdb1d455d와
case67 root를 원 Reader로 새로 읽어 provision group required8/accepted8/missing[]를 확인했다.
이 읽기 census는2bound=fresh/finished/cleanup/stop=null이고 제품 실행·Gate 인수가 아니다.
원 P22860/P23061~67의 개별 수용으로 provision8개가 채워졌다는 범위만 인정한다.
다음index68:
actual_import::formula_policy_issuer::public_request_cannot_supply_issuer_approval_keys_clock_or_signature_before_server_reads.

## 자원 및 개별 증거

전체/자체 CPU는 원 watcher 표본 최대값이다. own CPU는 전체 machine 대비 값이며
CPU 원인 귀속이나 전 PC의 무중단 보장이 아니다. 최종 root 쓰기는 owner 종료 이후여서 이 표본 밖이다.

| index | parent초 | 전체CPU최대% | 자체CPU최대% | 가용RAM최소% | Job CPU초 | Job peak MiB |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 64 | 197.29 | 100 | 2.901354 | 41.31680724143448 | 0.141 | 17.5 |
| 65 | 200.53 | 57.64 | 2.5878 | 41.31730991449041 | 1.641 | 23.52 |
| 66 | 197.13 | 51.66 | 3.001876 | 40.8564935857079 | 0.156 | 17.62 |
| 67 | 202.93 | 52.17 | 2.979516 | 40.98711501833837 | 6.344 | 26.23 |

### 64 / run004

actual_import::formula_policy_issuer::provision::provision_root_scope_time_and_generation_fail_before_artifact_or_registry.
root 574668bytes/SHA31c661809288bd35b03361bbce41e7d3784c7c47187f6831be016411a99e1150.
body 165831bytes/SHA750a3e0f8c95195b88768df78da6ced1db5b0a95591085785e4b99e9453f7ea2.
prep167bound=fresh/finished/read201136999bytes/
697표본/private최대42434560bytes.
지원156/exact1PASS/248filtered/exit0/COMMITTED/Job active0/owned tree empty/stop=null.
Native warning1/pause2windows/
요청1초, 원 hard guard 불변.

### 65 / run005

actual_import::formula_policy_issuer::provision::provision_same_generation_root_or_policy_drift_stops_before_approval_ingest.
root 574964bytes/SHAfaa4c41c3f2d90a43ffcb08241212fb9907a2b030af1b115478af614fe6c8b00.
body 166735bytes/SHA555aa23392cc17f759d5083b81fa7114feb6f972e05ab783126c8e64a64b2ccd.
prep169bound=fresh/finished/read202783828bytes/
702표본/private최대41267200bytes.
지원156/exact1PASS/248filtered/exit0/COMMITTED/Job active0/owned tree empty/stop=null.
Native warning0/pause0windows/
요청0초, 원 hard guard 불변.

### 66 / run006

actual_import::formula_policy_issuer::provision::provision_scanner_and_aead_failures_never_register_root.
root 576904bytes/SHA05e5614e2e3c89e7de1d0a1f25501cde5a233c891274179686eddf83d70860ee.
body 166563bytes/SHA8bce97de75434f1c644326dd542870e70184a2c3f4f0fdf0292a8e40b2480a6f.
prep171bound=fresh/finished/read204433961bytes/
698표본/private최대42799104bytes.
지원156/exact1PASS/248filtered/exit0/COMMITTED/Job active0/owned tree empty/stop=null.
Native warning0/pause0windows/
요청0초, 원 hard guard 불변.

### 67 / run007

actual_import::formula_policy_issuer::provision::provision_signer_key_signature_lifetime_and_clock_fail_closed_before_approval_write.
root 576676bytes/SHA2d8d7e3d3dbd4a03012369a4ed1f035a444d84195d4fc549e0eedc8c45c5bfc1.
body 167543bytes/SHA4f4acefc745bd734bd2fa6bdc118e83d12effba732f0eae6c29e95c5a758fc3b.
prep173bound=fresh/finished/read206087458bytes/
713표본/private최대43393024bytes.
지원156/exact1PASS/248filtered/exit0/COMMITTED/Job active0/owned tree empty/stop=null.
Native warning0/pause0windows/
요청0초, 원 hard guard 불변.

네 사례 공통: 전후1512입력 각118919360bytes/원 Rust785·고정 EXE 불변/
잠금1818·복제3024 모두close/잔여0/close실패0/resets3024/
directory306/ancestor305/별도 pathname reopen0/원 cleanup 전 release 금지.
원 두 전체 실제 byte 읽기/held identity/finalfresh/cleanup 유지.
실제 Native pressure frame 연결 및 실제 packed parent/root writer 연결 유지.
Job CPU6.25%/affinity1/BelowNormal/RAM percent/GO 뒤 실행/한 watcher/
Native32open/s/no burst/600초/1440표본/원98x4 hard STOP는 바꾸지 않았다.
JSON 필드 제거0/기존 원장 재작성false/new sampler false/CPU 성능 개선 주장false.

## case64 순간 100% 추가 검토

P233 review_current_queue_peak.py는 원 Reader 및 검증된 P224 null-safe 요약기를 사용한다.
P224 지원8727bytes/SHA659a277ae8be29c1ca60b7b76c3df4a445008145fd6fabee2fd66f72bb12a254의
literal pin/PASS/6fresh/cleanup 및 기존 요약기·test source pins를 확인했다.
case64 root/body의 exact pin/PASS/Job active0를 읽고8계약/6bound=fresh/finished/cleanup/stop=null 통과.
새 검토 원장7797bytes/SHA410a539b8cf874479a3d715456d016a8185fd0cc2e8f90c1b0257ddd899aa85e.
본문 재실행/원장 재작성/전체 표본·로그 출력/외부 PID 귀속은 하지 않았다.

root697표본 중95이상1/98이상1/최대연속98표본1, caller 태그metadata_hash.
해당 표본 자체CPU0.189394%/audited logical read delta0,
Job CPU 관측 수0/값null: 누락값을0으로 해석하지 않았다.
첫 경고 주변 전체CPU57.23→100→60.55이며 이3개 숫자만 제한 요약했다.
원 parent385표본의 최대45.12%,95이상0/98이상0.
Native backpressure warning1/pause2windows/1초로 신규 reservation을 대기했고
원 hard98x4/IO·잠금 deadline은 그대로였다.
태그는 호출 범위이지 정확한 CPU 원인·코드 위치·외부 PID 증거가 아니다.
낮은 자체 CPU는 간접 유발 부하를 배제하는 근거가 아니며 프리즈 원인·해결은 미확정이다.

Native open/read pressure 코드도 읽어 기존 owner 표본 재사용,
매 대기마다 원 guard 호출/최대8windows/sleep/두 distinct cool 표본/
cleanup은 pressure guard로 막지 않는 연결을 확인했다.
이번 기록에서 바쁜 대기·새 sampler·무제한 재시도·새 지속 CPU 중단은 확인되지 않았다.
보호 기준 완화·원 입력 제외·수용된 코드 변경을 CPU 최적화로 대신하지 않았다.
이번 신규 코드는 읽기 전용 피크 검토 지원이며 CPU 성능 향상 측정 결과는 아니다.

## 문서 전이와 남은 경계

이전 r95 원장306743bytes/SHAa9d3da0d16226678d9e27fa2e5587cc36f592bc6c4beb3985e3352a2d37a37be/
수용57/next64/179fresh/cleanup와 실제 pin을 대조했다.
rootdoc 사본은 runtime-progress-r95에 크기·SHA 일치/덮어쓰기 없이 보존한다.
CURRENT_STATE.md 437436bytes/SHA61c2439fd8916cfaeb5bd1b2a023adbab03865303798ca61dc5ca829af9fd387.
P09-149_CONSERVATIVE_OPTIMIZATION_PROGRESS.md 531068bytes/SHAb064cffef7af94d25ef06bc335ae2312e526817ef83b014917444908c269bd0c.
원 P232 재사용 verifier를 수정 없이 r96에 사용하여 현재156+문서24계약,
새 actual pair4개와 증가량4/동일 prefix/이전 전체 byte suffix/finalfresh/cleanup을 대조한다.
문서 검증 자체는 새 EXE·GO·full source frame을 실행하지 않는다.

CPU 보호 중단 시 자동 재시도 금지: 해당 경로·Job·CPU/RAM·핸들·최종 쓰기/정리 증거를 검토하고
가능한 개선을 새 버전으로 검증한 후 재개한다. 이번4건은 CPU STOP 없이 수용됐다.
실제 CPU STOP 재현은 NOT_RUN. 새 실제 STOP sidecar 기록이나 PC 프리즈 해결을 주장하지 않는다.
원 P222 STOP root SHA78c11517c8bb36289de5b9ade68f0910c2e583c5cba1058895a38b81bb4ff9b0 및
0byte body SHAe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855를 보존한다.
P227 합성 parent STOP 연결 지원 SHA3e980627f22938f16a9fc46f14b1fa1cf3fe8b63fa7907e73333bc93e1f60c68도 보존한다.
full249/whole1470/historical67/signed16/실제 SQL/생산 issuer/한글 접근허용 UI/
통합·제품 Gate는 별도 미완료다. 목표 active, P09·A12·A13 OPEN 유지.
