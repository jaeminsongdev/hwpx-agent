# P09-204: 실행용 r07 worker 분리 및 제품 실행 전 입력 확인

## 구현과 실제 확인 범위

2026-10-08. `tools/p09/minimal_r07_worker.py`를 추가했다. 과거 보고·검증 모듈을 실행용 worker에서 import하지 않고, 고정 SHA로 확인한 기존 `conservative_maintenance.py`와 `audit_evidence_io.py`만 source에서 불러온다. 기존 worker의 GO 승인과 실제 Job 소속 확인 함수를 그대로 호출하며 현재 고정 EXE에 원 단일 테스트 이름·`--exact`·`--test-threads=1`·출력 형식을 전달한다. 원 실행 환경과 priority/creation flags를 유지하고 corpus6은 분할 대기 상태로 남긴다.

새 worker의 실제 부모/Job 연결 및 제품 body 실행은 아직 **NOT_RUN**이다. 원 actual runner와 입력 범위를 바꾸지 않았으며 기존 성공 body를 재실행하지 않았다. 실행용 import 분리는 구현했지만 실제 제품 실행의 성능 향상이나 프리즈 해결을 증명한 것은 아니다.

`python -B tools/p09/audit_minimal_worker_inputs.py --run 1 --index 11`은 terminal exit0으로 완료했다. 신규20계약 PASS, stop=null/cleanup=true, IO finished=true/bound21=fresh21이다. 제품 실행 전 import/선택 단계에서 저장소 코드3개와 compiled 목록 JSON1개를 관측했다. 외부 runtime 코드 이름·환경·내용은 저장하지 않는다.

선택한 다음 테스트는 `actual_import::field_ranges::stored_range_debug_and_receipt_do_not_disclose_cached_field_content`다. 원 queue index11과 이름/argv가 정확히 같다. 실제 프로세스 생성 API를 호출하지 않았고, `sys.audit`로 만든 합성 subprocess 이벤트1개가 차단되는지만 확인했다. 회귀 검사의 GO/Job은 mock이며 실제 Job 검증으로 승격하지 않는다.

## 입력·비용·안전 경계

관측된 저장소 코드는 새 worker, 원 maintenance 29237bytes, 원 evidence reader 5653bytes다. 직접 데이터는 P186 compiled 목록 339893bytes, SHA-256 `7b06997d3b8090967597fad1d12b94446e20e3a17ba206233ae8711fdb1d455d`다. 세 코드의 실행 당시 pin과 종료 fresh pin을 확인했다. 저장소 `.pyc`/EXE 읽기를 probe에서 거부하고 원 source를 compile했다. protected cache나 원본 EXE를 수정하지 않았다.

probe 구간의 open 이벤트는9개이고 파일 크기 합계는503530bytes다. 이는 열린 파일의 선언 크기이며 실제 소비 byte나 physical disk IO가 아니다. 이후 계약/원 baseline 대조까지 포함한 paced logical read는48회12659464bytes다. 실제 제품 준비/전후 closing의 IO 감소 수치와 혼동하지 않는다.

원 sampler를 재사용한8표본에서 hostCPUmax21.63%, ownCPUmax0.56926%, ownprivate최대31748096bytes(약30.28MiB), availableRAM최저47.54339386456884%였다. 표본은 import/selection 이후 계약·metadata 확인 구간이며 전체 startup이나 다른 run의 성능 대비를 증명하지 않는다. 프리즈 원인·해결은 미확정이다.

이 관측은 Python audit 이벤트 범위이며 모든 native DLL/product IO closure가 아니다. Python 공식 문서도 audit hook을 보안 sandbox로 사용하지 말라고 명시한다. [sys.addaudithook](https://docs.python.org/3/library/sys.html#sys.addaudithook), [SourceFileLoader](https://docs.python.org/3/library/importlib.html#importlib.machinery.SourceFileLoader). 실제 GO/Job/limit/cleanup은 이후 부모 연결의 실제 증거로 별도 확인해야 한다. current EXE hash, Cargo/build/SQL/Hangul/접근허용/Git/Review/부하재현/OS·Defender·WSL 변경은 없다.

## 유지한 제품 standing과 다음 작업

기존 제품 큐224계약을 재사용한다. runtime 수용10/249·잔여239(일반233+corpus6)·미closing후보0·다음index11, 원 whole 수용3/whole미확인성공7, compiled249=true/full249=false/signed16=false다. 신규20계약은 worker 입력·선택 검사이지 제품 테스트20건이 아니다. whole/Gate 미수용, product=false, P09·A12·A13 OPEN, 목표active/P10 새 구현 없음. 249는 r07 큐의 분모이지 P09 전체 분모가 아니다.

다음은 경량 worker를 기존 실제 부모 감독에 연결하고, P203에서 확인한 고유 fixture38개를 포함한 live 입력과 historical 보존 참조를 분리하는 실행 경로 구현이다. 이 단계에서는 원1470 manifest나 실제 runtime source scope를 줄이지 않았다. 최종 whole reconciliation/signed16/Gate 의무와 원 실패를 보존한다.

## 정확한 증거와 문서 확인

worker proof: `implementation/p09/evidence/runtime-r07/p09-204-minimal-worker-input-probe-run01.v1.json`, 19273bytes, SHA-256 `e961b7b0f5777ba84cfb55205474d09ae26b60f9671d4b40868b955abae5c821`.

재사용 큐 proof: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-light-run07.v1.json`, 224계약, 88896bytes, SHA-256 `3146b518664ef4d02608b53771a0b43924fec2f8812c713f41fa39619934db4f`.

현재 runtime 수용에 사용하는 closing은 `implementation/p09/evidence/runtime-r07/` 아래다.

| closing | SHA-256 |
| --- | --- |
| p196-case-004-attempt-001-close-01.v1.json | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| p198-case-005-attempt-001-close-01.v1.json | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-case-006-attempt-001-close-02.v1.json | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| p198-case-007-attempt-001-close-03.v1.json | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-case-008-attempt-001-close-04.v1.json | e04e457e974217bb9bec4b50b286aa20ea1edca6f5cb2b8bbafdf6f47c621a54 |
| p198-case-009-attempt-001-close-05.v1.json | 08dd6dbf07f2de549d2bb1f57a6260f86ce5c619e9273bb56564252824119d29 |
| p198-case-010-attempt-001-close-06.v1.json | cfa19969a89e822e38b9b8e9094b3cfdcc6f9cde0dbf3cf0ef5fc4d300e24218 |

두 상태 문서는 동일 r73 prefix를 추가하고 이전 r72의 모든 byte를 `source-archive/runtime-progress-r72/`에 보존한다. checker 변경 전 원본도 `source-archive/p09-204-doc-checker-preimage/`에 보존했다. doc-sync는 현재224계약 controller pin/원 runtime validator와 새20계약의 tested helper/executed source pin/선택·범위 제한을 확인한다. 별도 terminal PASS가 있어야 문서 동기화 완료이며 제품/whole/Gate PASS가 아니다.
