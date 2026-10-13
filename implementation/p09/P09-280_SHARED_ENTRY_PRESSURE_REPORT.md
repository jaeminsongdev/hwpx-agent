# P278~P280: 획득 phase14 연결 사전검증·cached entry callback 보완

2026-10-09. 목표 ACTIVE. 제품 runtime 수용88/249, 잔여161(일반155+corpus6), 다음index95, whole 재조정대기85, 독립source 마감대기0. P09·A12·A13 OPEN. 이 비율은 개별 runtime 부분집합이며 P09 전체 완료율이 아니다. 접근허용·한글 UI·빌드·Git·설치·OS/Defender/WSL 설정 변경 없음.

## 현재 실행 결과와 수용 경계

| 실행 | 결과 | 확인한 범위 | 제품 본체 |
| --- | --- | --- | --- |
| P278 light run001 | PASS, 754 계약 | 원1563+24=1587 입력 연결·원 CPU/RAM/600/720·준비 입력 최종 fresh·획득14/s 선택 사전검증 | 미실행 |
| P278 actual95 run002 | CPU STOP, 미수용 | final_fresh_preparation에서 중단; Native Frame/원parent/Job 호출 전 | 미실행 |
| P279 support run01 | PASS, 54 계약 | entry와 byte의 같은 early90 객체 연결·원95 base 유지·실제 reader 29입력 fresh | 미실행 |
| P280 light run001 | CPU STOP, 미수용 | anchor 초기에 중단; 공통 callback 선택 확인; 870 계약과 전체1591 사전검증 미완료 | 미실행 |

P278 light의 754 계약은 원650+현재52+다음52이다. 준비 IO452 reads/211 bound 및 최종 fresh, STOP null, 정리 확인. 실제 전체1587 Native Frame/두 byte boundary/Job 검증을 대신하지 않는다. 원 P273 수용94 본체를 재실행하지 않았다.

P278 actual95는 754 계약 후 준비 최종fresh13/212, IO255 reads/38,495,800bytes 상태에서 중단. 마지막4 표본 시스템100%/검증 프로세스0%; cleanup 확인. Frame·본체 경로·원parent·Job이 생성/호출되지 않아 획득14/s의 실제 전체범위 성능은 미확정이다. 실패를 runtime 수용으로 승격하거나 재시도하지 않는다.

## 확인된 코드 문제와 수정

기존 `metadata_read_entry_pacing.Binding`은 생성 시 `reader.checkpoint`를 entry pacer에 보관했다. 이후 P270은 byte reader callback만 early90으로 바꾸므로 cached entry callback은 원95에 남아 있었다. P278 actual의 원95 경고1회/3 windows와 byte90 경고0회는 이 코드 경로와 일치한다. 다만 시스템 고부하의 단독 원인을 증명하지 않는다.

새 `qualify_metadata_entry_early_pressure.Binding`은 아직 사용하지 않은 reader와 원 entry pacer의 identity/rate32/clock/sleeper/0 counter를 확인한 뒤 **entry callback만 이미 존재하는 byte early90 객체로 연결**한다. 원95는 early의 base로 매번 먼저 호출된다. clock·credit·read counter 초기화, 추가 sampler/thread/CPU query, guard 생략, byte/identity 검사 삭제, cleanup 변경은 없다.

P279는 원32 계약과 새22 계약(공통 callback16, 실패 검토6)을 통과했다. 합성 CPU92→89→88 표본에서 cached entry의 경고 구간 진입과 두 냉각 표본 대기를 확인했고, 실제 reader는29 bound/fresh·58 reads·1,326,798bytes·정리 완료였다. 실제 지원 실행의 시스템CPUmax5.61%, 검증 CPUmax0.396825%, private29,790,208bytes. 합성/소규모 검증은 전체 runtime 또는 PC 프리즈 해결 증거가 아니다.

## P280의 중단 단계 검토

새 전체 실행기는 원1587 입력에 entry 보완 source/test와 새 실행기 source/test 4개를 추가하여1591을 선언한다. ancestor308, 원754+현재58+다음58=870 계약, 동일한 Native20/획득14/metadata32/byte binary1·other2MiB/s/두 byte pass/identity/Job/600/720 보호를 요구한다. 원95와 기존 수용 본체의 자동 재실행은 차단한다.

P280 light는 anchor에서 원 `STOP_SUSTAINED_SYSTEM_CPU`로 중단됐다. 총8 표본, 시스템CPUmax100%, 검증 CPUmax0.195312%, private31,264,768bytes, 가용RAM최저19.394708%. IO6 reads/4 bound/fresh0·3,121,842bytes, entry6 reservations/성공5/실패1·정리 후 binding inactive. 원95 경고1회/3 windows·1.5초 대기, byte90 경고0회. 88.45%에서 다음100% 표본으로 넘어가 원95 base가 먼저 대기/STOP했고, 이는 공통 early 객체 연결 누락과 다른 경로다. entry/byte 공통객체·원95 base·원clock/reader/rate32는 실제 실패 receipt에서 모두 참이다.

마지막4 표본은 시스템CPU100%, 검증 CPU 각각0.195312/0/0/0%, logical byte delta1,007,066/0/0/0이었다. 첫 표본 phase 이름은 metadata_read_parse지만 마지막3 표본은 읽기 증가 없이 기존 보호 대기 중이다. 이 phase label만으로 JSON 파서가 CPU100%를 썼다고 해석하지 않는다. Native Frame/원parent/Job/제품 본체는 호출 전, 수용0, watcher cleanup 확인. 870 계약은 미실행이며 전체1591 연결 미수용이다. CPU STOP 직후 같은 검증을 다시 실행하지 않았다.

추가 검토한 관련 코드는 entry pacer의 no-idle-burst/64회 한도·sleep, byte pacer의64KiB/유한 재시도·sleep, JSON16MiB parse 한도, 원 리소스 sampler의0.5초 debounce와 기존 watcher 재사용, STOP 뒤 unguarded cleanup이다. 확인 범위에서 신규 무한루프/스레드 증식/CPU sampler 중복은 발견하지 못했다. 검토 범위 밖 전체 저장소 최적화가 완료됐다는 뜻은 아니다. 원 소스/수용/실패를 변경하지 않고 확인된 cached callback 보완만 적용했다. 더 낮은 임의 CPU 시작 기준이나 guard 상향은 적용하지 않았다.

작업 후 제한된 read-only 프로세스/RAM 조회에서 가용RAM21.43%를 확인했지만, 단기 프로세스 CPU 차분은 전부0으로 나와 원인 귀속 근거로 사용하지 않았다. Defender·WSL·Codex 또는 별도 프로세스를 범인으로 단정하거나 종료/설정을 변경하지 않았다.

## 불변 증거

| 경로(아래 evidence/locked-r07 기준) | bytes | SHA256 |
| --- | ---: | --- |
| p273-case-094-run002.v1.json | 624020 | 4c8b5cb8db208be26487e966653747a2ad92c3bc37d1c5268047957b6b166eb5 |
| p278-light-run001.v1.json | 43566 | f36a1b47e16f179e3420043901e2664658026f7843e22d88857008d88da235ea |
| p278-case-095-run002.v1.json | 120336 | 677c1d0f02c456b6db4b1e577307a0d8055087d1b120b93e0d3bc13d303c6dc8 |
| p279-metadata-entry-early-pressure-run01.v1.json | 25942 | 5a0bcb6ea02cd41894f0cf306237b9f53c1eaf343832b724bd66d50c2f443ec8 |
| p280-light-run001.v1.json | 16577 | 97ca3589b715c599861b707dd1d584377041f4fc69afbc5aacde9b57c4baf4c3 |

P279 source11263bytes SHA335aea52c483a0d89c8ea07cd89e1b6a1e0f9c0ffd989186fd2c292fbd5429d2, test7250bytes SHA21039b0483318fd05394ca0c4c763ab8a43d547ba2755e776a258a76378a8dc9. P280 source33268bytes SHAe9d6d5525efc6545ab1d8e012749f308d2e687e5b0ebd4e78b856e651c6ba01b, test10012bytes SHAa6c68fbb22c49cee23c883647884c562234e1d7e6d1a86ebd0a88751c3ae2b64. 수용된 원P278/P279와 실행된 P280 파일·실패 receipt는 이후 수정하지 않는다.

## 다음 안전 경계

목표는 ACTIVE로 유지한다. 제품 수용은88/249 그대로이고 다음 본체는95다. 최신 CPU STOP은 보존·원guard/공통 callback/관측 코드 검토 완료이며, 관련 코드에서 근거 있는 추가 수정이 발견될 때만 새 불변 generation으로 수정한다. 동일 P280 실행을 즉시 반복하지 않는다. 다음 전체 실행기는 최신 STOP을 명시 검토하고 정확한 추가파일/ancestor/원600 예산을 다시 계산한 뒤 전체 사전검증부터 통과해야 한다. 실제95 본체는 그 이후 한 건만 실행한다. 수용된 본체 재실행, guard 완화, 접근허용 실행, 원P09 Gate 미완료 상태의 P10 진입은 하지 않는다.
