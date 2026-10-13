# P09 r341 — 실제159 manifest·20쌍 worker 캡슐·상속 범위 비용

## 공식 상태

152/249, 잔여97, next159, generation47. P09/A12/A13 OPEN, P10 새 구현0, P09~P20 목표 ACTIVE. 실제159 제품·Native·독립승인·전체controller GO는 실행/자격 부여하지 않았다. 성공158 및 권위152는 보존하고 재실행하지 않았다.

## 실제 manifest023

`runtime_successor_manifest_v1.py`와 실제 `p09-361-case159-source-manifest023.v1.json`을 추가했다. 이전 placeholder를 실제 manifest 입력으로 사용하지 않는다.

- 별도의 이전158 그래프에서 원 manifest022 `load`를 그대로 호출하여 old16 source/producer/qualifier/failure/authority와 original/physical byte 핀을 재검증한다. 원158 manifest의 index/before 및 실패 상태를159로 고치지 않는다.
- 새private159 그래프에 원16개의 pin을 보존하고 descriptor의 명시적 next159 context만 연결한다. r728 실제 파생4개를 추가하여20쌍 구성. 기존 original scope, 실제 prior158의 semantic scope, authority152/root158/actual manifest 핀을 충돌 재작성 없이 합친다.
- 정확한 case159/before152/schema/closed keys/양쪽 graph 분리/CODE9/r729/실제producer/r728와selector/r727/모든현재source를 확인한다. 이전실패003004를 별도의 prior_failure_lineage로 새로 확인하며 제품으로 승격하지 않는다.
- r731: CODE4 4/4 및 실제 complete old admission+new20 PASS, fresh130/final130, CPU40.68%, 가용RAM19.70909%, cleanup True. 전체159 runtime scope나 GO가 아니다.

## worker 캡슐 v2

기존 worker v1은 wire에authority151_pin/actual157_pin과158/151을 고정했다. 새 `runtime_successor_worker_capsule_v1.py`는 명시적159/152/실제158 ROOT와 새 `authority_pin`/`prior_runtime_pin`을 쓰는 closed wire/v2를 연결한다.

- Encoder/decoder의 닫힌 metadata constants만 project하고 역변환 시 전체 원 code object와 동일한지 확인한다. 원 defaults/closure 및 worker dispatch bytecode를 유지한다. 새 권위를 옛151/157로 잘못 표기하지 않는다.
- source Binding은 정확한 private159 type으로 부모 측 객체와 decoder가 공유한다. 원16KiB 상한·strict schema/hash/type/cursor/guard/once-only worker 조건 유지. 원 default module 변경0.
- r732: CODE6 중 roundtrip 한 건 error. Python closed key set이 frozenset constant인 것을 tuple/string과 함께 변환하지 못한 원인이다. 실패 보존 후 키 검사를 제거하지 않고 frozenset metadata projection과 inverse equality를 추가했다.
- r732 실패 실행은 source pin을 출력하지 않았다. 보존한 수정 전 source는 현재 코드에서 해당 수정 한 줄을 역변환해 재구성한 자료이며, 실패 실행의 직접 source-pin 증거로 취급하지 않는다.
- r733: CODE6 6/6 및 실제20쌍 encode/decode PASS, fresh134/final134, CPU43.95%, 가용RAM18.74810%, cleanup True. 실제 worker dispatch/제품은0.
- canonical wire11,019bytes/SHA `2513e092c8716e0f40c02ab424cc58393bff2fa058e63d9c4efa8fe2abbbe028`, LF포함실제file11,020bytes/SHA `307eb20b57ed084f01cd69ae5d20b8a5f8e45ef71a363306f12e98a041a2c0f8`를 구분했다. 실제 capsule001.v2 파일은16KiB 미만이다.

## 비용 경계

r734는 새 실제 manifest의 상속 원본+현재 admission reader에 결속된 입력을 새private20쌍 Binding으로 물리 투영하여 기존 complete budget 식으로 계산했다. 옛case158의597초 모델을 복사한 것이 아니다.

- 입력2,679/dirs372, binary28,433,408bytes/other223,139,442bytes, 물리총251,572,850bytes.
- semantic2,679/286,062,268bytes, 원본 scope 제외0.
- baseline predicted_runtime_combined_seconds594.863348 <600, unallocated margin60, acquire14/s/byte20/s, capture15초, aggregate decoder5초, 모든원 rate/guard/actual two reads 유지.
- fresh130/final130, CPU45.11%, 가용RAM17.17587%, cleanup True.
- **아직159 controller/DATA/imports/current Rust inventory/전체 scope가 완성되지 않았으므로 이 값은 baseline이며 전체159 GO가 아니다.** 새 전체 preflight에서 최종 scope/cost를 다시 확인해야 한다. actual_completion_guaranteed False, PC_freeze_resolved False.

## 다음 실제 작업

private core parent/worker/full-oracle가 같은159 Binding을 사용하도록 실제 통합 그래프를 연결하고, 엄격한15초capture·원Native timing·원전체독립acceptance를 포함한 새159 controller/DATA/complete current scope·cost·wholepreflight 자격을 확보한다. 통과 후159만 한 번 실제 실행하고 독립승인을 진행한다. fixture/manifest/capsule/baseline PASS를 제품이나P09 Gate PASS로 승격하지 않는다.

접근허용/한글/UAC, OS·Defender·WSL 변경, 외부process 종료, 원본삭제·이동, 원격push 없음. 과거CPU폭증·PC프리즈 원인/해결은 미증명이다.
