# P09-205: 경량 worker의 실제 단일 테스트 실행 연결

## 구현과 실제 제품 경로 확인

2026-10-08. `tools/p09/run_minimal_runtime_r07_case.py`를 추가해 P204 source-only worker를 기존 exact-one 부모 감독에 연결했다. 부모의 실제 `c.run`은 그대로이며 child 경로와 task만 정확하게 매핑한다. 기존 GO 전 Job 할당, child의 실제 Job 소속 확인, CPU/RAM hard limit/readback, 1200초 deadline, bounded capture, owned cleanup을 유지했다. 과거 성공 case 세대8/10/12-controller와 새16-controller를 명시적으로 구분한다. 새 controller는 실행 전후 fresh 입력과 별도 closing에 포함된다.

원1470 manifest는 수정하지 않았다. 과거67 EXE의 최종 whole 확인 의무도 유지한다. 실제 runtime 입력은 이전 모든 입력에 새 worker/worker test/연결기/연결 test4개를 추가한1421개117955529bytes다. 경량 import 연결 외에 원 historical evidence를 제거하거나 입력 freshness를 약화하지 않았다.

기존224 + worker12 + 연결10 = **246계약 PASS**다. 실제 제품 경로 검증은 `python -B tools/p09/run_minimal_runtime_r07_case.py --mode actual --run 7`로 다음 미실행 case011 하나만 수행했다. session은 terminal exit0이며 성공 body1~10을 재실행하지 않았다. corpus6/SQL/Hangul/접근허용/Git/Review/Cargo/build/설치/삭제·이동/OS·Defender·WSL 변경은 없다.

case011: `actual_import::field_ranges::stored_range_debug_and_receipt_do_not_disclose_cached_field_content`. 현재 고정 EXE에 정확한 이름과 `--exact --test-threads=1 --format=pretty --color=never`를 전달했다. 결과는 passed1/failed0/ignored0/measured0/filtered248, exit0, stop=null, capture error=null다. 실제 Job 소속 및 limit 확인이 true이며 cleanup/owned_tree_empty=true, 최종 active0/owned[]다. 직접 기록된 task는 `p204-r07-case-011-tests`, 원 부모 task는 `p191-r07-case-011-tests`다.

실제 source before/after 각1421개117955529bytes가 같았다. body132.97초는 입력 확인·worker·제품 테스트·정리를 포함하며 제품 테스트 자체 시간으로 표현하지 않는다. 이어진 독립 runtime closing은 PASS/stop=null/cleanup=true/bound1422=fresh1422/read237896225bytes/wall65.8964초다. 원 runtime validator를 적용했고 전체249/whole/Gate PASS로 승격하지 않았다.

## CPU/RAM 관측과 남은 최적화

body256표본: hostCPU최대50.38%, 95% 이상 표본0, JobCPU최대5.39743164917723%, RAM여유최저47.674885779808356%. Job CPU 누적0.141초, peak private17.77MiB였다. 독립 closing의 hostCPU최대66.99%, ownCPU최대1.405622%, ownprivate최대54878208bytes였다. 이는 해당 run의 표본이며 원인 귀속, 다른 run과의 인과적 성능 비교 또는 PC 안전성 증명이 아니다. 프리즈 원인·해결은 미확정이다.

P204의 import/선택 확인만으로 미검증이던 실제 부모/GO/Job/제품 body 연결을 이번 run에서 확인했다. 반면 전후 약118MB와 closing 약238MB의 기존 입력 확인 비용은 여전히 남아 있다. 다음 최적화는 P203의 명시 fixture38개를 포함한 live 입력과 historical 보존 참조 분리다. 이름만 보고 evidence를 제외하지 않고 실제 의존성과 검증 의무를 구분해야 한다.

## 현재 큐와 수용 경계

성공 body를 재실행하지 않은 별도 light-run09에서 원 validator와 closing을 다시 확인하고, **runtime 수용11/249·잔여238(일반232+corpus6)·미closing후보0·다음index12**를 확인했다. 다음 미실행 항목으로 넘어가는 재사용 판단만 확인했으며 case012 body는 실행하지 않았다.

원 whole 수용3/whole미확인성공8, compiled249=true/full249=false/signed16=false다. whole/Gate 미수용, product=false, P09·A12·A13 OPEN, 목표active/P10 새 구현 없음. 246은 controller 회귀 계약 수이며 제품 테스트246건을 새로 통과한 의미가 아니다. 249는 r07 큐이지 P09 전체 완료율의 분모가 아니다. 이전 실패 및 P200 hostCPU100% 기록을 보존한다.

## 정확한 증거와 문서 동기화

- body: `implementation/p09/evidence/runtime-r07/cases/p190-case-011-attempt-001.json`, 933704bytes, SHA-256 `6d8ad0af9c5e12bd178b94cb28735200b611ca6b288165fcc7eaa7052c02877d`.
- 새 closing: `implementation/p09/evidence/runtime-r07/p198-case-011-attempt-001-close-07.v1.json`, 1145043bytes, SHA-256 `23f0505522ea72495377986ed944bf9adc2c967d195ef56a291fb79829f4c5ae`.
- 246계약과 현재 큐: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-light-run09.v1.json`, 98936bytes, SHA-256 `e99ccd6cb000561460403c48522250299f39d6a14ff27cc34e4ac6165ec45b14`.

기존 수용 closing7개도 계속 사용하는 원본이다. 경로는 `implementation/p09/evidence/runtime-r07/` 아래다.

| closing | SHA-256 |
| --- | --- |
| p196-case-004-attempt-001-close-01.v1.json | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| p198-case-005-attempt-001-close-01.v1.json | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-case-006-attempt-001-close-02.v1.json | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| p198-case-007-attempt-001-close-03.v1.json | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-case-008-attempt-001-close-04.v1.json | e04e457e974217bb9bec4b50b286aa20ea1edca6f5cb2b8bbafdf6f47c621a54 |
| p198-case-009-attempt-001-close-05.v1.json | 08dd6dbf07f2de549d2bb1f57a6260f86ce5c619e9273bb56564252824119d29 |
| p198-case-010-attempt-001-close-06.v1.json | cfa19969a89e822e38b9b8e9094b3cfdcc6f9cde0dbf3cf0ef5fc4d300e24218 |

동일 r74 prefix를 두 상태 문서에 추가하며 r73 이하의 모든 byte를 `source-archive/runtime-progress-r73/`와 대조한다. checker 변경 전 byte는 `source-archive/p09-205-doc-checker-preimage/`에 보존했다. doc-sync는 246계약16-controller의 현재 pin과 실제 새 body/closing 및 기존 원 validator/whole·Gate 경계를 확인한다. doc-sync terminal PASS가 있어야 문서 동기화 완료이며 제품 전체 수용이나 프리즈 해결 증거는 아니다.
