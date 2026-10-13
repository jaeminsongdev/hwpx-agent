# P09-206: 전체 입력 잠금 코드 조사·구조 최적화

## 조사에서 확인한 문제

2026-10-08. 전체 입력 잠금은 원 runtime1421개를 제외하지 않고 명시 fixture/manifest와 helper를 더한1467개, ancestor directory306개를 대상으로 구현했다. 최초 전체 확인은 **STOP_SUSTAINED_SYSTEM_CPU / FAILED_NOT_ACCEPTED**다. 신규20계약은 통과했지만 whole 입력의 최종 fresh 단계는 완료하지 못했다. 원 실패를 PASS로 재분류하지 않는다.

중단 직전 metadata hash 단계에서 logical read1361회106379548bytes, bound1349/fresh0/finished=false였다. 마지막 CPU 표본은100/99.8/100/100%, 같은 구간 검증 parent CPU는0~0.378788%였다. 전체 ownCPU최대2.298851%, ownprivate최대31088640bytes, RAM여유최저34.232280315016624%다. 제품 child는 없었으며 외부 프로세스의 원인 귀속은 수행하지 않았다. 검증의 파일 I/O가 간접적으로 영향을 주었을 가능성은 배제하지 못한다. 프리즈 원인·해결은 미확정이다.

잠금/acquire와 최초 identity 확인에 사용한3546개 handle은 모두 닫혔고 남은 handle0/cleanup=true다. 실패 기록과 당시 코드4개는 각각 원 evidence와 `source-archive/p09-206-failed-full-lock-preimage/`에 보존했다. 이후의 작은 파일 native probe는24계약과 읽기 허용/쓰기·삭제 권한 open의 공유 충돌32/해제 후 권한 open 복구만 확인한 **과거 버전의 제한된 결과**다. 그 코드도 `source-archive/p09-206-probe02-preimage/`에 보존했으며 최신 전체 검사나 제품 PASS로 사용하지 않는다.

사용자의 전체 코드 조사·최적화 우선 요청 이후 전체 잠금 검사와 작은 native probe를 재실행하지 않았다. 다음의 전체 경로 변경과 순수 계약/비용 조사만 수행했다.

## 적용한 구조 변경

1. 별도 pathname 재열기 두 번을 제거했다. 잠금을 취득할 때 원 handle의 file ID/type/size/reparse/상속 여부를 확인한다. 이후 필수 byte hash를 위해 **이미 열린 stream의 OS handle**을 가져와 같은 file ID인지 검사한다. 마지막에는 보유한 file/directory handle의 identity를 대조한다. 다른 파일을 읽었거나 held identity가 바뀌면 실패한다.
2. 파일별 전후 전체 hash 읽기2회는 그대로 유지한다. 모든 입력의 같은 stream identity 확인이 정확히2회여야 통과한다. 필수 byte 읽기를 캐시 pin, 크기, timestamp 또는 표본으로 대체하지 않는다.
3. Native 잠금 open과 byte reader의 stream open이 **동일한32open/초 pacing**을 사용한다. idle 후에도 여러 open credit이 쌓이지 않는다. 작은 파일에서 byte credit refund만으로 open 요청이 몰리는 경로도 제한한다. 전체 CPU 35% 같은 새 시작 조건은 없다.
4. 새 qualification reader의 읽기 상한을 binary1MiB/s·other2MiB/s로 정렬했다. 기존 byte accounting/64KiB burst/CPU·RAM guard/600초 scope/owned cleanup을 유지한다. 기존 제품 runner의 정책이나 입력 집합을 바꾸지 않았다.
5. Reader adapter는 종료·예외 때 원 `_source`를 복구하고 stream은 원 reader의 context manager로 닫는다. handle 취득·metadata 검사·읽기 실패·deadline·guard 중단 경로의 cleanup은 계속 실패 여부를 명시한다. 원본의 쓰기·truncate·삭제·rename·속성 변경 API는 호출하지 않는다.
6. 추가 조사에서 부모 경로 집합을 매 파일마다 다시 순회하던 경로를 메모화했다. 이미 등록된 부모를 만나면 종료하되 ancestor handle은 전부 유지한다. 각 입력을 처리할 때 deadline/resource guard를 확인한다. 방문 횟수는 별도 기록하며 작은 모형의 두 파일은 공통 조상2개만 순회하고 file2+directory3의 handle5개를 유지했다.
7. CloseHandle wrapper가 예외를 내면 나머지 handle 정리까지 중단되던 경로를 수정했다. 모든 보유 handle의 close를 시도하고 실패한 것만 재시도 대상으로 보존한다. 실패 횟수와 잔여 handle을 기록하며 cleanup=false를 성공으로 바꾸지 않는다. 해제 시작 이후 identity 확인·reader 연결을 금지한다.
8. 같은 reader의 중첩 연결은 다른 InputLocks 객체를 쓰더라도 거부한다. reader 연결이 살아 있는 동안 잠금 해제를 거부하며 context 종료 후 원 source·소유 marker를 정리한다. identity mismatch가 발생해도 이미 열린 byte stream을 닫고 reader를 복구하는 계약을 추가했다.
9. NUL/control character 및 Windows에서 사용할 수 없는 wildcard/예약 문자를 native open 전에 거부한다. 원 입력을 제외하거나 pin을 약화하지 않는다.

FILE_SHARE_READ는 일반 Windows API의 쓰기·삭제 접근 공유를 허용하지 않는 방식이며, 보안 sandbox나 kernel/악성 우회 방지를 주장하지 않는다. [Microsoft CreateFileW](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew). Python stream의 기존 OS handle은 [msvcrt.get_osfhandle](https://docs.python.org/3/library/msvcrt.html#msvcrt.get_osfhandle)로 취득해 [GetFileInformationByHandle](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-getfileinformationbyhandle)로 대조하는 구현이다. 새 stream 통합의 실제 전체 native qualification은 아직 NOT_RUN이다.

## 전체 입력 기준 비용 계산과 회귀 검증

| 입력 검사 범위의 open 요청 | 이전 구조 | 최적화 구조 |
| --- | ---: | ---: |
| 잠금 유지 handle 취득 | 1773 | 1773 |
| 별도 pathname 재열기 | 3546 | 0 |
| 필수 byte hash2회의 stream open | 2934 | 2934 |
| 합계 | 8253 | 4707 |

1467입력+306디렉터리 기준으로 불필요한open3546개, **모델상42.96619411123228%**를 제거했다. bootstrap/import/baseline metadata/권한 probe 등의 open은 이 계산 밖이다. 이것은 전체 검사 경로의 operation 계산이지 CPU·RAM·벽시계 시간의 개선 실측이 아니다. 과거 증거81MB를 미사용이라고 판단하거나 검사에서 제외하지 않았다.

`python -B tools/p09/qualify_locked_runtime_inputs.py --run 4 --scope contracts-only`는 terminal exit0이다. 최신35계약 PASS/stop=null/cleanup=true/bound5=fresh5다. 실제 native input lock/제품/shared frame 생성은 없다. 기존29계약에 공통 ancestor 메모화·close 예외 전수 정리·reader 중첩 거부·활성 reader 중 close 거부·잘못된 native 경로 문자·stream identity 실패 시 닫힘/복구의6계약을 더했다. 과거29계약 run03과 당시4개 source는 `source-archive/p09-206-contract03-preimage/`에 보존했다.

과거 run03은 logical read11회1106065bytes, hostCPUmax16.51%·ownCPUmax0.191939%·ownprivate최대25645056bytes였다. 이는 당시 순수 계약 확인 구간이며 전체 성능 비교가 아니다. 최신 전체 잠금 검증은 NOT_RUN이며, 원 full run은 FAILED_NOT_ACCEPTED로 남는다. 전체 CPU 100%의 원인 및 프리즈 해결은 증명하지 않았다.

## 현재 제품 standing과 다음 단계

기존246계약 및 runtime 수용11/249·잔여238(일반232+corpus6)·미closing후보0·다음index12는 그대로다. whole 수용3/whole미확인성공8, compiled249=true/full249=false/signed16=false, whole/Gate 미수용, 목표active/product=false/P09·A12·A13 OPEN/P10 새 구현 없음이다. 신규35계약은 제품 테스트35건이 아니다.

다음은 최적화된 전체 입력 경로의 실제 native qualification을 독립적으로 확인하는 단계다. 통과하기 전 공유 source frame이나 새 제품 body에 적용하지 않는다. 전체 source pin/fresh hash/경로 identity/guard/cleanup 증거가 없으면 그 부분은 미검증으로 유지한다. 한글·접근허용/Git/Review/Cargo/build/SQL/OS·Defender·WSL 변경은 없다.

## 정확한 증거와 원장

- 원 full 실패: `implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run01.v1.json`, 344819bytes, SHA-256 `a71f78acdeb3a0d86a5c9798415be2c374fa4cf97142f9e011de749094e2a43a`.
- 최신 추가 코드 조사·계약: `implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run04.v1.json`, 10052bytes, SHA-256 `685ef608fe578efd84cb54e45c96ab85d90775b0cfde90b67598b37a03da5576`.
- 이전 구조 최적화29계약·전체 비용 조사: `implementation/p09/evidence/runtime-r07/p09-206-input-lock-qualification-run03.v1.json`, 10066bytes, SHA-256 `6dad3b7306703b81d2c1e847c5d169c757e843d0908e9f0c0e110457696959eb`.
- 제품246계약·현재 큐 재사용: `implementation/p09/evidence/runtime-r07/p198-runtime-resume-light-run09.v1.json`.

원 runtime closing8개의 SHA를 보존한다. 경로는 `implementation/p09/evidence/runtime-r07/` 아래다.

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

두 상태 문서에 같은 r75 prefix를 추가하고 이전 r74 이하 byte는 `source-archive/runtime-progress-r74/`와 대조한다. checker 전 원본은 `source-archive/p09-206-doc-checker-preimage/`에 보존했다. doc-sync는246계약16-controller/current 큐/원 runtime validator와 새35계약의 source pin, 실패 원본·당시 코드 preimage, 전체 open 비용 계산, latest full NOT_RUN 경계를 확인한다. 별도 terminal PASS가 문서 동기화의 증거이며 native/product/whole/Gate PASS가 아니다.
