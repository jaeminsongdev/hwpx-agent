# P09-207: 잠금 수명 보완과 전체 입력 native qualification

## 결론과 범위

2026-10-08. 잠금 코드의 추가 수명/정리 누락을 보완한 뒤 **전체1467입력·306디렉터리·118581555bytes의 native qualification을 terminal exit0으로 완료**했다. 원 runtime1421개를 그대로 유지하고 명시 fixture38개·manifest·helper를 합친 범위다. 원 product 입력 집합은 변경하지 않았다.

판정은 `PASS_FULL_RUNTIME_AND_KNOWN_FIXTURE_READ_LOCKS_NOT_SHARED_FRAME_PRODUCT_OR_GATE`다. 이것은 전체 입력의 일반 Windows 읽기 전용 handle과 전후 실제 byte/identity 확인에 대한 결과다. 실행용 shared frame, 새 제품 body, whole1470·과거67EXE·full249·signed16·P09 Gate의 통과가 아니다. 원 full run01의 CPU 중단/FAILED_NOT_ACCEPTED는 그대로 보존한다. 프리즈 원인·해결은 미확정이다.

## 추가로 수정한 문제

- 권한 취득만 하는 probe handle도 Native 소유 목록에 등록한다. close가 false/예외이면 목록에 보존하고 오류를 반환하며, InputLocks의 최종 cleanup에서 이 handle도 전수 정리한다. 본 잠금을 해제한 뒤 시행하는 probe의 실패도 cleanup=false에 반영한다. 실패한 close를 성공으로 포장하거나 이미 닫힌 handle을 반복해 닫지 않는다.
- 실제 열린 byte stream의 수명을 별도로 센다. reader adapter 연결이 먼저 끝나더라도 stream이 열려 있으면 잠금 해제를 막는다. 연결이 끝난 source proxy로 새 stream을 열려고 하면 파일 open 전에 실패한다.
- 이전 공통 ancestor 메모화, close 예외 후 나머지 정리, reader 중첩 거부, 잘못된 경로 조기 거부, 동일 stream identity, 원 CPU/RAM/deadline/pacing 검사는 유지한다.

관련8개 계약을 기존35개에 추가해 **잠금/qualification43계약 PASS**를 얻었다. 현재 전체 결과를 독립적으로 판정하는8개 계약도 추가했다. 후자의 계약은 scope 누락/중복/다른 pin, 불완전 final hash, 한 번만 읽기, probe/stream 누수, 잘못된 open accounting, guard 완화, 쓰기 허용, 제품/Gate 승격을 거부한다. 기존 제품 준비246계약과는 별도다.

수정 전35계약 당시4개 helper와 doc checker는 `implementation/p09/source-archive/p09-206-contract04-preimage/`에 보존했다. 이전 두 원장의 r75 byte는 `implementation/p09/source-archive/runtime-progress-r75/`에 보존했다. 원 full 실패와 이전 probe/29계약 버전의 preimage도 유지한다.

CloseHandle 성공은 nonzero, 실패는 zero이며 실패를 성공으로 간주하면 안 된다. [Microsoft CloseHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-closehandle). FILE_SHARE_READ는 일반 쓰기·삭제 접근 공유를 허용하지 않는 방식이다. 속성/확장 속성 접근이나 보안 sandbox·kernel/악성 우회 방지를 보장하는 의미는 아니다. [Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

## 실제 검증

1. `python -B tools/p09/qualify_locked_runtime_inputs.py --run 5 --scope contracts-only`: 43계약 PASS/exit0/stop=null/cleanup=true/bound5=fresh5. 실제 native 입력 잠금이나 제품 실행은 없다.
2. `python -B tools/p09/qualify_locked_runtime_inputs.py --run 6 --scope probe-only`: 새 helper/자체 fixture5개의 제한된 실제 API 확인. 잠금10/close10/잔여0, byte stream identity10, probe3/close3/잔여0이다. 이 결과를 전체 검사 성능이나 프리즈 해결로 사용하지 않았다.
3. 전체 범위를 기존 reader/원 validator로 구성한 read-only 사전 비용 계산은1467개·306디렉터리·118581555bytes, 필수2회 읽기와 scope open4707개였다. byte pacing과 open 간격을 직렬 합산한 모델은273.70878887176514초이며, bootstrap/metadata/guard 대기/실제 스케줄링을 포함한 완료 시간 보장은 아니다. 600초 한도를 늘리지 않았다.
4. `python -B tools/p09/qualify_locked_runtime_inputs.py --run 7 --scope full-runtime`: 아래 전체 결과로 terminal exit0. 병렬 검증·자동 재시도·제품 child 실행은 없다.

| 전체 run07의 확인 항목 | 실제 결과 |
| --- | --- |
| 잠금 파일/디렉터리 | 1467 / 306 |
| 취득/해제/잔여 잠금 handle | 1773 / 1773 / 0 |
| 취득/해제/잔여 probe handle | 3 / 3 / 0 |
| 활성 reader / 열린 byte stream / close 실패 | 0 / 0 / 0 |
| 공통 ancestor 순회 | 305회; 모든306디렉터리 handle 유지 |
| 전후 byte stream identity 확인 | 2934회 = 모든1467입력 × 2 |
| held/stream metadata 확인 | 6480회 |
| 별도 pathname 재열기 | 0 |
| 공유 open pacing 예약 | 4713 = scope4707 + 권한시험/최종 자체파일 읽기6 |
| 전체 reader logical IO | 2995회 / 253370185bytes |
| bound / final fresh / finished | 1472 / 1472 / true |
| CPU/RAM 보호 중단 / watcher cleanup | null / true |

원 EXE는 실행하지 않고 기존 현재 EXE14216704bytes를 전후 hash용으로 읽었다. binary logical byte28433408은 정확히2회 읽기에 대응한다. 과거67EXE는 읽거나 수용하지 않았다. bootstrap·기준 receipt의 읽기와 마지막 fresh 때문에 전체 reader bound/IO는 잠금 입력 수/byte보다 크며, 전후 identity 확인 대상1467개를 줄인 것이 아니다.

자체 작은 probe 파일에서 잠금 중 READ 권한 취득은 허용, WRITE/DELETE 권한 취득은 error32로 거부됐다. 해제 후 두 권한 취득은 복구됐고 동일 byte도 재확인했다. OPEN_EXISTING으로 권한 취득만 시도했으며 WriteFile·truncate·DeleteFile·rename·속성 변경은 하지 않았다.

## CPU/RAM 관측의 해석

전체 run07의 완료 표본은502개다. hostCPUmax92.99%, ownCPUmax0.954198%, ownprivate최대31174656bytes(약29.73MiB), RAM여유최저38.859128328140066%다. reader95% 경고 진입0/보호 중단null이었다. native open 요청 대기113.54978060084977초는 요청한 sleep 합계이며 실행 시간이나 CPU 개선량이 아니다.

이번 최적화 버전은 전체 검사를 끝까지 통과했지만 이전 실패와 통제된 A/B 실험을 수행한 것은 아니다. CPU·RAM 개선 비율, 전체 PC 프리즈 해결, 외부 프로세스 원인 귀속을 주장하지 않는다. 프리즈 원인·해결은 미확정이다. Defender·WSL·시스템 설정은 바꾸지 않았다.

## 제품 standing과 다음 경계

기존246계약·runtime 수용11/249·잔여238(일반232+corpus6)·미closing후보0·다음index12는 그대로다. whole 수용3/whole미확인성공8, compiled249=true/full249=false/signed16=false, whole/Gate 미수용, product=false/P09·A12·A13 OPEN/목표active/P10 새 구현 없음이다. 249는 r07 큐이며 P09 전체 작업의 분모가 아니다.

다음은 이번에 실제 자격을 확인한 잠금을 실행용 shared frame의 수명·소유·등록·예외/중단 cleanup 계약에 연결하는 것이다. 아직 이를 실행용 worker에 연결하지 않았고, 필수 source byte 확인을 생략하거나 cached pin으로 대체하지 않았다. 기존 성공 제품 body1~11을 재실행하지 않았다. 접근허용/Git/Review/Cargo/build/SQL/Hangul/OS 변경은 없다.

## 증거와 문서 검증

- 원 full 실패 run01: `implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run01.v1.json`, 344819bytes, SHA `a71f78acdeb3a0d86a5c9798415be2c374fa4cf97142f9e011de749094e2a43a`.
- 최신43계약 run05: `implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run05.v1.json`, 10065bytes, SHA `4ab8512460bdba02d183cb920d5f6436ce20f67f3ffac8817e2d0054a7a81c02`.
- 최신 제한 API run06: `implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run06.v1.json`, 12799bytes, SHA `0e37b213ba4f2be9dca66bb5780589add201517ca0190100850528d825dab747`.
- 전체 native run07: `implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run07.v1.json`, 1199486bytes, SHA `fe6e12c51e4cff5180b494be9cb9ada404b9b167d5da3ecefb32c5d845d8f0c5`.

문서 verifier는 현재246계약/16-controller와 원 runtime validator를 재사용해 현재 큐를 계산한다. 현재43계약 입력, 원 CPU 실패 및 당시 source, 전체 run07의 정확한1467 입력 집합·현재 source pin·전후 fresh·stream/handle/probe 정리·open accounting을 독립적으로 검증한다. 추가 증거 판정8계약을 실행하며 새 제품 body나 EXE 재해시는 없다. 두 원장의 동일 r76 prefix와 이전 r75 이하 byte를 대조한다. 별도 doc-sync terminal PASS가 문서 수용 증거이며 native proof를 제품/Gate 결과로 승격하지 않는다.

최초 doc-sync run010은 상태 블록이 prefix가 아닌 suffix로 붙은 편집 오류를 `P199_DOC_EXACT_PREVIOUS_BYTES`로 거부했다. FAILED_NOT_ACCEPTED/stop=null 기록을 보존했다. 두 문서를 보존본 r75와 정확히 같은 SHA/byte로 복구한 뒤 명시적인 첫 줄 anchor로 r76 prefix를 다시 적용했다. 별도 run011은 기존 admission 기준의 `DEFERRED_ALREADY_SATURATED_SYSTEM`으로 reader 생성 전에 거부됐다. 두 기록을 보존하며 제품/전체 native 검증을 재실행하지 않는다. doc checker는 시작 단계 실패에서도 원 완료 표본의 CPU/RAM/자기 프로세스 관측을 저장하도록 보완했다. 새 sampler/PID 조회/guard 완화는 없다. 문서 수용은 별도 terminal PASS로만 판정한다.

원 runtime closing8개 SHA를 유지한다. 경로는 `implementation/p09/evidence/runtime-r07/` 아래다.

| closing | SHA-256 |
| --- | --- |
| p196-case-004-attempt-001-close-01.v1.json | c2e361fee38147adca14a78f27fac6285d8093c64ed1163f0b16360d7de88ccd |
| p198-case-005-attempt-001-close-01.v1.json | f633b39324247808fcfd75047ecd3a009ad7c486932c043179f5b7fe89c2e569 |
| p198-case-006-attempt-001-close-02.v1.json | 08d60ca30bb76ed5c88772c5b61d1551d0a27ceeedb4c755c8d2006e1a98a9de |
| p198-case-007-attempt-001-close-03.v1.json | d786ce0b729dd273f776870531de791f0a1493daf9f22a7b1f3b8d9b062fa8fc |
| p198-case-008-attempt-001-close-04.v1.json | e04e457e974217bb9bec4b50b286aa20ea1edca6f5cb2b8bbafdf6f47c621a54 |
| p198-case-009-attempt-001-close-05.v1.json | 08dd6dbf07f2de549d2bb1f57a6260f86ce5c619e9273bb56564252824119d29 |
| p198-case-010-attempt-001-close-06.v1.json | cfa19969a89e822e38b9b8e9094b3cfdcc6f9cde0dbf3cf0ef5fc4d300e24218 |
| p198-case-011-attempt-001-close-07.v1.json | 23f0505522ea72495377986ed944bf9adc2c967d195ef56a291fb79829f4c5ae |
