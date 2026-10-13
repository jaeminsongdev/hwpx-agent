# P09-345 — Anchor metadata 경로 조회 중복 제거 (2026-10-10)

## 목표 상태와 범위

사용자는 CPU 보호중단 시 관련 코드를 검토·최적화하면서 목표를 계속 추진하도록 요청했다. 안전한 자체 코드 점검·개선이 남아 있는데 P344에서 BLOCKED로 종결한 판단은 성급했다. 이 턴에서 목표 ACTIVE를 확인했고, 원 실패를 보존한 채 실제 중복 후보를 구현·검증했다. 보호중단만으로 자동 BLOCKED 처리하지 않는다. 반복 중단 뒤에도 새 근거·변경 없이 동일 전체 검증을 재시도하지 않는다.

고정 runtime/test 2경로만 수정했다. 원 frozen93경로, full1658입력, directory308, code95, controller191 경계를 유지했다. Git/Review, Cargo/build, 제품 재실행, 접근 허용/한글, Defender/WSL/OS 설정, 다른 프로세스 종료, 삭제·이동은 하지 않았다.

## 변경과 불변 조건

- runtime의 MetadataPathQueries와 MetadataReader: 원 is_file 판정은 그대로 수행하고, 현재 요청의 fresh lstat로 symlink를 판정한 뒤 같은 결과의 Windows reparse flag/tag로 junction을 판정한다. 일반 경로의 3 pathname metadata 조회를 2회로 줄였다. 요청 간 재사용은 없다.
- lstat 오류나 지원되지 않는 필드 형태에서는 원 symlink/junction 판정으로 돌아간다. 원 오류 처리, 이름 resolve/ROOT 경계, rb open, 전체 바이트, JSON 해석·canonical 검증, final fresh hash, 읽기 pacing/deadline/resource guard를 유지했다.
- 판정 실패, parse 실패, 보호중단에서도 reader root를 원래대로 복구한다. root/owner/thread/request binding을 검증한다. Native 원자적 입장 판정으로 주장하지 않는다.
- 원 source025 실패와 당시 v13 코드2의 exact pin을 현 bootstrap 계약에 추가했다. 새 코드로 과거 실패를 덮어쓰지 않는다.
- 기존 tests252개에 metadata 경로25개, source025 실패검토7개, metadata 회계/oracle7개를 더해 runner당291개, current/following 합계582개다. 기존 검사·보호 기준은 축소하지 않았다.

junction 판정은 현재 설치 Python3.13의 원 함수와 Windows 구현을 확인한 뒤 reparse flag와 mount-point tag의 결합을 유지했다. [CPython 3.13 Windows 경로 판정](https://github.com/python/cpython/blob/3.13/Modules/posixmodule.c#L4853-L4866). 이 최적화는 metadata 단계의 중복 제거이며 Native frame 획득·보안 판정의 대체가 아니다.

## 실제 검증

### review026 — 계약 검토 PASS, 제품/Native PASS 아님

순수 metadata25개 PASS 후 정식 closing-review run026은291×2=582개 모두 PASS했다. 원 before/after test 체크도 각각582개, runner2회 모두 반환했다.

199 bound +199 finalfresh,398 read passes,37,906,026bytes를 원 경로로 읽었다. metadata 요청398회마다 원 is_file398회와 fresh lstat398회를 수행했고 junction398회를 동일 요청 안에서 묶었다. 논리 predicate1194개는 유지했다. fallback0, root restoration TRUE, active binding FALSE.

관측73sample: host CPU max21.28%, own machine CPU max6.51341%, own private max95,371,264bytes, free RAM min32.775975%. 새 Native/제품 실행0, watcher cleanup TRUE. 이 수치는 해당 실행 관측이며 PC 프리즈 해소의 증거가 아니다.

- receipt: evidence/locked-r07/p340-closing-review-run026.v1.json
- bytes188519 / SHA256 e6c245bc7701e84b6401c67328fa5bd774f5b47b690a3d29913185a51e5610e4
- qualified code2 exact archive: evidence/p340-formal582-code/

### source027 — Native acquire 중 CPU 보호중단, 미수용

run026 exact pin으로 전체 source 검증 run027을 한 번 실행했다. preparation은200 bound/200 finalfresh/400read/38,283,064bytes/finished TRUE까지 진행했고 path predicate1200개를 유지했다. source025의 anchor 중단과 달리 이번에는 source_frame_acquire에서 STOP_SUSTAINED_SYSTEM_CPU가 발생했다. 환경 차이를 배제할 수 없어 최적화가 단계 진전을 인과적으로 보장했다고 말하지 않는다.

전체1658입력/121,125,991bytes 프레임은 CLOSED, registered FALSE다. 열린365핸들 전부365closed, remaining0, metadata checks365, reader0, stream0, close failure0, input cleanup TRUE다. borrower는 생성 전 NULL, actual byte boundaries는 빈 배열이다. 전체 source byte 전후 검증이나 HeldPathGuard full1658 자격을 통과한 것은 아니다.

119sample: host CPU max100%, own machine CPU max1.481481%, own private max80,506,880bytes, free RAM min30.387739%. 마지막4sample의 host CPU100%와 own CPU0%, logical read delta0를 확인했다. 자체 CPU 풀로드 또는 PC 프리즈의 단일 원인은 확정하지 않았다. 원 receipt observer phase label metadata_hash와 실제 실패 stage source_frame_acquire를 혼동하지 않는다.

- receipt: evidence/locked-r07/p340-closing-source-run027.v1.json
- bytes512631 / SHA256 f1d51aa582d5242ac74acde41252f5bff2ce3f78dd601f556f02cc66bcf6865c
- state FAILED_NOT_ACCEPTED / watcher cleanup TRUE
- 동일 source blind retry0, 제품107/108 재실행0

## 보호 기준과 다음 작업

1LP/BelowNormal, Job CPU6.25%/active16/kill-on-close/no-breakaway, RAM cap8%/own stop7%, host CPU98%×4, admit free RAM10%/stop8%, commit95%, 원 단계·부모 deadline, acquisition14/native20/metadata32 pacing/no-burst,64KiB chunk, 원 바이트 rate를 유지했다. CPU35% admission 같은 새 기준을 추가하지 않았다.

원 Native open/inspect/InputLocks.take/acquire 경로를 검토했다. 읽기 접근/share-read, reparse 처리, filetype/identity/inherit/size 검사, directory ordering, acquire pacing, 실패 cleanup을 제거할 근거는 없었다. 다음 안전한 자체 작업은 Native 획득의 원 호출을 유지하면서 operation enum/input kind/ordinal/elapsed 같은 최소 계측을 추가해 중단 위치를 좁히는 것이다. 사적 경로·전체 로그 출력, 별도 sampler/thread, 보호 완화 없이 계약 검증부터 한다. 아직 그 계측을 구현·검증했다고 주장하지 않는다.

## 수용 상태와 문서 경계

수용101/249, 잔여148(regular142+corpus6), next108, 성공한108 body의 source closing pending1, whole 재조정98을 유지한다. 249는 해당 큐이며 P09 전체 진행률 분모가 아니다. 현재95코드의 full Native/source NOT_QUALIFIED, compound102 NOT_ACCEPTED, P09/A12/A13 OPEN이다. full1470/full249/signed16/product_complete/PC_freeze_resolved를 완료로 승격하지 않는다. 현재 문서 전체 finalfresh는 NOT_RUN이며 아래 byte/AST 점검은 그 자격을 대신하지 않는다.

기존 r137 CURRENT_STATE/P09-149/P09-344 전체3파일은 evidence/runtime-progress-r137/에 exact byte/hash로 보존했다. P344 과거 서술은 수정하지 않고 r138 현재 상태에서 ACTIVE로 정정한다. 원 v13 formal504, source025, actual108 root18/sidecar와 zero-byte case 증거를 유지한다.

상세 회계·pin·관측 whitelist: evidence/p09-345-anchor-metadata-path-progress.v1.json.

## 이 보고서 작성 후 제한 검토

현재 코드2 및 review026/source027 receipt2의 exact byte/SHA256 일치, qualified code archive2 일치, r137 전체3파일의 현재 문서 suffix byte 보존, 진단 JSON 수용 산술/빈 byte boundary/잔여handle0, 원 actual108 zero-byte case 보존을 확인했다. 현재 코드2 AST parse와 compile도 PASS했다. 이 검토는 새 제품 실행·Native frame 재획득·현재 문서 전체 finalfresh 검증이 아니다.
