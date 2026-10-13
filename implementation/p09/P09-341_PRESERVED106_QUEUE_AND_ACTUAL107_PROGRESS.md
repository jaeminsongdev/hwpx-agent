# P09-341 — 통과107 보존, 현재 큐 검증기 보완 및 자원 보호 유지 (2026-10-10)

## 확정 상태와 범위

목표 ACTIVE, P09/A12/A13 OPEN. 실제107은 정확한 제품 자식1·전체 원본1658 전후 각1회·Job 및 정리 확인 후 수용101/249로 진행했다. 이 검증군의 잔여148 = regular142 + corpus6, 다음108, source closing pending0, whole reconciliation pending98이다. 249개는 전체 P09 작업 수 또는 전체 P09 진행률이 아니다. whole1470/full249/signed16/product_complete/PC_freeze_resolved는 FALSE 또는 미확정으로 유지한다.

## CPU STOP마다 검토할 범위

중단 원본의 phase, 마지막 연속 표본, 자체 CPU·private RAM, 읽기 증가, Native acquire/close 및 Job·자식 정리 결과를 확인한 뒤 관련 코드만 검토한다. 같은 실패 세대의 명령을 자동 재시도하지 않는다. 실제 제품 자식이 이미 성공했다면 원본 capture를 보존하고 필요한 source closing만 독립 검증한다. 호스트 CPU 포화만으로 자체 코드의 근본 원인이나 PC 프리즈 해결을 확정하지 않는다.

고정 새2경로를 사용하여 scope1658/code95/controller191/directory308을 유지한다. frozen93 실제 bytes/hash는 그대로 보존한다. 원래 own1LP/BelowNormal, CPU98x4(.5s), RAM 비율, JobCPU6.25%machine/active16/killclose/RAMcap8%·stop7%, 원 전체 byte 전후 검증, Native identity, Native600/metadata720/parent1200, acquire14/native20/meta32 no-burst 및 binary1/other2 MiB/s를 유지한다.

## 코드 검토와 변경

- 같은 Reader 안에서 이미 bind한 immutable code93 및 healthy body를 다시 읽지 않고 정확한 snapshot/pin을 사용한다. 별도 명령 간 cache로 최신성 검증을 대신하지 않는다.
- 같은 Reader에서 마지막 LIGHT JSON 1개만 유지해 중복 JSON read/parse를 제거한다. checkpoint와 모든 입력의 final-fresh hash, Native 전체 byte 전후 검증은 생략하지 않는다.
- 합성 계약의 현재 scope는 bootstrap100/101에 고정하지 않고 scan 결과의 실제 cursor를 사용한다. 다음 항목의 검증이 이전 항목의 scope를 재사용하는 오류를 예방한다.
- 실제107 schema v5의 원 code2를 별도 archive로 검증하고 원 body/light/fresh/Job/전체byte/정리를 확인해 base101에 연결한다. 이전 제품107을 다시 실행하지 않으며 현재 v7 code95가 이미 Native 통과했다고 해석하지 않는다.
- schema v6의 계약 실패를 조사해 body의 actual_product_child_executed=False를 거부하지 않는 순수 검증기 조건을 발견했다. v7에서 root 및 body 양쪽의 TRUE를 명시적으로 요구한다. 실제107 원본은 TRUE이고 원 pin과 일치한다. 실패 테스트를 삭제하거나 약화하지 않았다.
- 원 schema v6 light010 FAILED의 코드2/receipt/부분128검사/정리를 별도로 검토하고 보존한다. 256 PASS나 CPU STOP으로 재분류하지 않는다. schema v7 계약136x2=272 PASS 후 새 독립 fresh 검토를 요구한다.
- 계약 재사용은 실제 실행0/재사용272로 기록한다. 새 Native 자격이나 제품 통과로 바꾸지 않는다. post metadata aggregate720 예약은 원 foundation 모듈의 실제 limit를 확인한다.

변경 source: tools/p09/resume_preserved106_queue_runtime.py, tools/p09/tests/test_preserved106_queue_runtime.py. 새로운 runtime 보조 소스는 추가하지 않았다.

## 검증 기록

| 기록 | 실제 수행과 판정 |
| --- | --- |
| p340-case-107-run009.v1.json | v5 제품1/exit0·full1658/121012153bytes before+after 각1회·FrameCOMMITTED/unregistered·lock1966/1966·dup3316/3316·Job membership/owned_tree_empty/정리TRUE; 수용101, 현재v7 Native 자격 아님 |
| p340-light-run010.v1.json | v6 계약128/1runner에서 body actual-child 거부 테스트1 실패; Native/제품0·정리TRUE, 256 PASS 아님 |
| p340-light-run011.v1.json | v7 현재136+다음136=272 실제 계약 PASS; runner2 before/after 모두;170bound/170fresh/340reads/27781436bytes·정리TRUE·Native/제품0 |
| p340-light-review-run012.v1.json | v7 별도 명령 fresh PASS; 새계약0/재사용272·171bound/171fresh/342reads/27888504bytes·정리TRUE·Native/제품0 |
| p340-case-108-run013.v1.json | v7 source_frame_acquire CPU STOP, 163잠금 모두 close·byte boundary0·제품0·정리TRUE; FAILED 그대로, 수용 증가0 |
| p340-stop-review-run014.v1.json | 108 실패의 독립 검토 시 anchor CPU STOP·116bound/0fresh/116reads/5247335bytes·Native/제품0·정리TRUE; 독립STOP검토 미완료, GO 아님 |

실제107 root 677180bytes SHA7e88493af85906c48e69cc620daa432adad87a785109c35d458b77bd8f65b7fb 및 body 191699bytes SHAc74a592e305a882f5aadda54a10ced7f98a8369cd3b83ec412084bd6b0782e6d. 현재 v7 정식272 code2는 evidence/p340-formal272-code/에 bytes/hash 일치로 보존했다. source54919bytes SHA78fb64845c7f4b00afa81ed0f5c4dbb0a1a321a37d5f857da7b001d8f651f08f, test29158bytes SHAf51d1933e043c81bb1526992663d688a98bb74181f1fd41a232231680bc9571e.

## 이번 CPU STOP 조사 및 판단

108 run013에서 원 전체 metadata 최신성 검사는172bound/172fresh/344reads/27989852bytes로 완료됐다. Native acquire14/s의 163번째 잠금 이후, 원 early90 경고 대기4창/2.0초 동안 호스트 CPU가 계속 포화돼 hard98x4가 중단시켰다. Native 획득 경과14.397405초, 잠금163/163 close·남은 handle/reader/stream/probe/close-failure0·FrameCLOSED/unregistered, 제품 body 파일 미생성이다.

원76표본에서 ownCPUmax1.893939%machine/private63287296bytes, freeRAMmin30.624939%. 마지막4 모두 hostCPU100/ownCPU0/읽기증가0/private63287296bytes, commit39.517~39.603%, freeRAM32.361~32.753%. 직접 자체 CPU 또는 자체 RAM 풀로드의 증거가 아니다. 파일 접근이 외부 보안검사 등에 간접 부하를 유발했는지와 프리즈 인과는 확인하지 않았으므로 원인 해결을 주장하지 않는다.

run014는 Native 없이 anchor에서 중단됐다. 원18표본/ownCPUmax1.470588%/private45678592bytes/freeRAMmin25.488920%, 마지막3 host100/ownCPU0/읽기증가0. 검토 검증 자체도 보호에 의해 중단됐으며, 이를 완료한 검토로 사용하지 않는다.

이번에 source acquisition, 원 Native OpenPacer, 조상 디렉터리 순회, 기존 early/backpressure, 큐 JSON cache와 계약 재사용을 코드로 확인했다. 조상 경로는 이미 방문한 부모에서 멈추고, Native OpenPacer는64회 제한·원 checkpoint·짧은 대기/no-burst를 유지한다. 원 sampler를 재사용하며 새로운 polling thread·외부 PID 조회·Git 실행이 없다. 읽기와 Native 작업이 이미 멈춘 원 표본에서 시스템 포화가 계속되므로, 이 실패를 없애기 위해 보호 수치를 낮추거나 검증 범위를 제외하는 변경은 하지 않았다. 전체 저장소의 모든 성능 문제가 해소됐다고 주장하지 않는다.

## 보존, 문서, 다음 경계

원 실패 및 성공 기록, frozen93과 각 코드 세대 archive는 그대로다. r133 문서3개 전체 byte는 evidence/runtime-progress-r133/에 해시 일치로 보존한 뒤 최신 요약만 prepend한다. 이번 문서 final-fresh 마감은 NOT_RUN이며, r128/P325 기존 문서 자격과 이번 runtime 수용을 구분한다.

이번 실행 PTYS42660/76490/86542/87215는 모두 종료했다. 이전 저장되지 않은 별도 진단 세션30727은 현재 handle이 없어 결과 UNCONFIRMED; PASS 또는 정리 완료로 추정하지 않는다. 이번 Native/제품 검증 프로세스는 잔류시키지 않았다.

다음 목표 작업은 원108 STOP과 run014 검토 중단을 검토한 후, 현재 code95/queue101에 대한 독립 최신성 검토를 다시 갖추는 것이다. 현 GO는 유효하지 않으며 이번 실패 세대의 동일 제품 명령 자동 반복은 없다. 수용101을 보존하고 미수용108만 대상으로 진행한다. CPU 보호 중단마다 정확한 단계의 own code/표본/정리를 먼저 검토하고 정당화된 최적화만 적용하는 정책을 유지한다. 목표 ACTIVE, Gate OPEN; P10 전환 없음.

한글/접근허용/Git/빌드/설치/push/삭제·이동/Defender·WSL·OS 설정 변경/외부 프로세스 종료는 하지 않았다. 짧은 소스 AST·136개 test method 확인과 산출물 구조/원문 suffix 확인은 제품/Native/문서 final-fresh 자격을 대신하지 않는다.

조사 요약: implementation/p09/evidence/p09-341-own-cpu-stop-investigation.v1.json.

