# P09-202: 반복 입력 읽기의 역할 조사 및 동적 fixture 경계

## 실제 수행과 현재 상태

2026-10-08. `tools/p09/audit_runtime_input_roles.py`로 기존 compiled manifest의 Rust 입력785개를 실제 fresh 읽고 최종 hash를 다시 확인했다. 12개 조사 계약이 통과했고 audit-run02는 exit0/stop=null/watcher cleanup=true/IO finished=true/bound802=fresh802로 종결됐다. 원 manifest1470의 path·bytes·SHA-256은 그대로 보존했다. current/historical EXE의 내용은 읽거나 재해시하지 않았다.

기존 제품 큐 계약224 및 runtime 수용10/249·잔여239(일반233+corpus6)·미closing후보0·다음index11은 그대로다. 원 whole 수용3/whole미확인성공7, compiled249=true/full249=false/signed16=false, whole/Gate 미수용, product=false, P09·A12·A13 OPEN이다. 조사12계약은 제품224계약과 별도 범위이며 제품 실행12건이 아니다. 목표active/P10 새 구현 없음. 249는 r07 regression 큐의 분모이며 P09 전체 작업 분모가 아니다.

## 원1470 입력의 보수적 역할 구분

| 역할 | 파일 수 | bytes | 판정 |
| --- | ---: | ---: | --- |
| 원 non-EXE 입력 유지 | 1127 | 22077231 | 현재 범위 유지 |
| 과거 evidence/archive 후보 | 272 | 81053063 | 미사용 미증명, 유지 |
| Rust 경로/파일명 참조 후보 | 2 | 129113 | 보수적으로 보호 |
| worker가 직접 읽는 compiled inventory | 1 | 339893 | 필수 유지 |
| 현재 EXE | 1 | 14216704 | 필수 유지 |
| 과거 EXE | 67 | 361560576 | 최종 whole reconciliation 의무 유지 |
| 합계 | 1470 | 479376580 | 원 manifest 불변 |

Rust 참조 후보 두 개는 P77 source manifest(112797bytes)와 source-archive 아래 과거 `actual_import.rs`(16316bytes)다. P77 manifest는 실제 Rust 입력 함수가 읽는다. 두 번째는 파일명 문자열의 보수적 일치이므로 그 archive 파일을 실제 실행이 읽는다고 확정하지 않는다. 파일명만으로 놓치는 경우를 줄이기 위해 과잉 보호한 결과다.

272개81.1MB는 반복 확인 분리의 후보이지 제외 승인 목록이 아니다. Python import/call graph, 간접 경로, 동적 입력 및 최종 보존 검증을 조사하기 전에는 미사용으로 승격하지 않는다. `safe_runtime_exclusions=[]`, exclusions_authorized=false, reduced_scope_runtime_qualified=false이다. 실제 runner의 source scope는 수정하지 않았다.

## 추가 발견: 동적 fixture가 기존 Python freeze 밖에서도 읽힘

Rust 코드와 두 manifest의 실제 hash를 대조했다. P77 manifest SHA와 form matrix manifest SHA는 각각 Rust에 고정된 값과 일치했다. 실제 HWPX 문서 내용은 이번 조사에서 읽지 않았다.

| manifest 가족 | 선언 문서 수 | 선언 bytes 합계 | 기존 case010 Python freeze에 있는 문서 수 |
| --- | ---: | ---: | ---: |
| P77 source corpus | 36 | 510909 | 1 |
| P09-42 form matrix(5case × source/output) | 10 | 159833 | 0 |

P77 manifest 자체는 기존 freeze에 있고, form matrix manifest(7471bytes) 자체는 그 목록 밖이다. 따라서 기존 Python freeze는 제품의 모든 동적 파일 I/O 의존성 목록이라고 주장할 수 없다. 다만 Rust 입력 함수는 manifest의 고정 SHA, 각 문서의 길이·SHA 및 경로 조건을 읽을 때 검사한다. 이 조사만으로 기존 성공 body를 실패로 바꾸거나 runtime 수용을 취소하지 않는다.

원 코드 근거:

- `crates/hwpx-package/tests/support/document_import_settings_inputs.rs`: 고정 P77 manifest 및36개 actual_inputs 읽기·검사.
- `crates/hwpx-package/examples/document_import_form_policies_support/mod.rs`: 고정 matrix manifest와 source/output 문서별 읽기·검사.
- `tools/p09/run_resumable_r07_case.py`: worker의 직접 compiled inventory 읽기 및 exact-one EXE 실행.

정확한 숫자·metadata pin은 `implementation/p09/evidence/runtime-r07/p09-202-dynamic-fixture-boundary-inspection.v1.json`에 기록했다. 이는 선언 metadata 관측이며 실제 문서 byte의 신규 검증 PASS가 아니다. 동적 의존성 closure는 미완료다.

## 다음 구현 경계

먼저 실제 r07 test target이 읽는 동적 manifest/문서와 worker 입력을 명시적 실행 입력 목록에 포함하고, 모든 입력의 범위·중복·digest 및 변조 거부 계약을 확립한다. 그 뒤 원본 보존용 과거 증거를 별도 phase/batch 경계에서 확인하는 분리를 구현한다. 범위를 분리해도 원1470 whole reconciliation은 미검증으로 유지하며 최종 확인 의무를 삭제하지 않는다.

이번에는 파일명 기반 대량 제외, 검증 skip, 새 제품 테스트, 고부하 재현, Git/Cargo/SQL/Hangul/접근허용, OS·Defender·WSL 변경, 삭제·이동이 없다. 프리즈 원인·해결은 미확정이다. 조사 run의 hostCPUmax7.8%·ownCPUmax4.496301%·ownprivate48586752bytes·availableRAMmin49.79782121881052%는 해당 경량 조사 표본이며 안전성·인과적 개선율 증명이 아니다.

## 실패 보존과 정확한 증거

최초 launch-run01은 결과 dict의 중복 필드 초기화 오류로 계약/소스 조사를 시작하기 전에 exit1로 끝났다. 실패 기록 `p09-202-input-role-audit-launch-failure-run01.v1.json`과 수정 전 소스 `source-archive/p09-202-pre-output-flag-repair/`를 보존했다. 이 실패를 PASS로 재분류하지 않았다.

실제 조사: `implementation/p09/evidence/runtime-r07/p09-202-input-role-audit-run02.v1.json`, 714135bytes, SHA-256 `a3a90ee153da37f1cdb2128c002f5137c1725db6e0e5915099c8ed224f84336d`. IO read2393/61238521bytes/bound802=fresh802. 12개 계약과 실제785개 소스 조사는 구분한다.

재사용한 제품 큐 계약: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-light-run07.v1.json`, 224계약 PASS, 88896bytes, SHA-256 `3146b518664ef4d02608b53771a0b43924fec2f8812c713f41fa39619934db4f`.

현재 runtime 수용의 원 closing은 모두 `implementation/p09/evidence/runtime-r07/` 아래다.

| closing | SHA-256 |
| --- | --- |
| p196-case-004-attempt-001-close-01.v1.json | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| p198-case-005-attempt-001-close-01.v1.json | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-case-006-attempt-001-close-02.v1.json | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| p198-case-007-attempt-001-close-03.v1.json | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-case-008-attempt-001-close-04.v1.json | e04e457e974217bb9bec4b50b286aa20ea1edca6f5cb2b8bbafdf6f47c621a54 |
| p198-case-009-attempt-001-close-05.v1.json | 08dd6dbf07f2de549d2bb1f57a6260f86ce5c619e9273bb56564252824119d29 |
| p198-case-010-attempt-001-close-06.v1.json | cfa19969a89e822e38b9b8e9094b3cfdcc6f9cde0dbf3cf0ef5fc4d300e24218 |

CPU 원 관측은 `implementation/p09/evidence/runtime-r07/p09-200-case010-cpu-spike-inspection.v1.json`을 유지한다. 문서 확인은 r70 원 byte 보존, 현재224계약 controller pin, 저장된 runtime 원 validator, 조사 receipt의 원1470 역할 합계/12계약/source pin, 두 동적 manifest의 SHA·선언 수·기존 freeze 포함 수를 대조한다. 별도 doc-sync의 실제 terminal PASS가 있어야 동기화 완료로 판단하며 제품 실행이나 전체 Gate 수용으로 승격하지 않는다.
