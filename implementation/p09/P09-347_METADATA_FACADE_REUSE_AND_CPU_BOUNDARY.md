# P09-347 — Metadata facade 재사용과 CPU 보호 경계 (2026-10-10)

## 결과

metadata source 요청마다 같은 Python class와 method closure를 재정의하던 중복을 제거했다. 고정 runtime/test2경로, frozen93/code95/controller191/full1658/directory308은 유지했다. 현재 v17/code365×current/following2=730 계약 검토가 실제 PASS했고 exact code2 archive를 보존했다. 전체 Native/source와 compound102는 아직 미수용이다.

source032는 anchor에서 CPU STOP, source034는 잠금1932개 완료 뒤1933번째 regular open-with-pacing에서 원 CPU guard로 STOP됐다. source034의 원1932핸들은 전부 닫혔고 현재 해당 큐 프로세스0·Git0인 종료 후에도 Windows counter의 단일 표본은 시스템 CPU100%였다. 이후에 보호를 풀거나 같은 full frame을 다시 시작하지 않았다.

목표 BLOCKED: 단일 보호중단의 자동 판정이 아니다. 사용자 재개 후 세 연속 목표 턴에서 같은 CPU 포화 조건이 재발했고, 그동안 실제 관련 중복을 구현·검증했다. 현재 확인한 metadata/held-source/Native 획득/원 JSON·full-byte 경로에는 제거할 수 있는 비싼 중복이 더 남지 않았고, 필수 guard나 원 검증 범위를 제거할 수 없다. 현 범위에서 다음 유효 source 검증은 안정적인 외부 상태가 필요하다. 짧은 CPU 회복만으로 full1658 완료를 보장하지 못했다. 다른 프로세스의 원인 추적 또는 OS 조정은 현재 자체 코드 최적화 범위를 넘어서는 사용자 선택이다. 완료나 임의 일시정지가 아니다.

## 구현과 불변 조건

MetadataPathSource는 모듈의 사전 정의된 slots class다. 요청마다 새 instance·새 token·초기화된 판정 상태를 만들고, 기존 is_file와 fresh lstat symlink/junction 판정 및 실패 시 원 fallback을 그대로 실행한다. 각 predicate/open의 원 owner/thread/reader/root/request-token 검사를 유지한다. 호출 순서, byte open, 모든 바이트 읽기, JSON/canonical 해석, finalfresh, resource/entry pacing/deadline/cleanup은 변경하지 않았다. 요청 간 metadata/raw/JSON/검증 결과를 재사용하지 않는다. Root adapter는 원 방식이며 STOP 후 복구를 유지한다.

source029 실패검토에 이어, review030의 exact 원 anchor CPU STOP와 preformal700 candidate archive2를 바인딩했다. 원 실패030에서는95코드 header를 검증하지 못했고700계약이 시작되지 않았으므로, candidate archive를 runtime95 qualification으로 표현하지 않는다.

기존350계약을 유지하고 metadata facade6개·review030 stop8개·current header 필수검사1개를 더했다. schema v17, count365, executed730이다. 새 facade/원 metadata/실패검토 순수39개 PASS, 두 코드 AST/compile PASS 후 정식 검토로 갔다. CPU 개선·Native 원자성·PC 프리즈 해결을 주장하지 않는다.

## 실제 실행

### review031 — current730 계약 PASS

current365+following365 모두 실제 PASS. metadata208bound/208finalfresh/416read/43,098,180bytes/finished TRUE.416 original is_file+416 fresh lstat, junction416 coalesced, 원 predicate1248, fallback0, root복구 TRUE, active binding FALSE다.

94sample: host CPU max27.08%, own machine CPU max6.31769%, own private max102,739,968bytes, free RAM min30.893452%. Native/제품 새 실행0, watcher cleanup TRUE. 계약 PASS를 Native/제품/Gate PASS로 표현하지 않는다.

- receipt evidence/locked-r07/p340-closing-review-run031.v1.json
- bytes193495 / SHA256 bd3de3f92235390c1ae17576181c2326ce694ceb9cbf48bc8a1b31b2c3868fa5
- current source132620bytes SHA256341e5a327adeb1e6111c600a19b9b39a71afa85a6e8956b823292c957e57839e
- current test93235bytes SHA2566b3e68e2e8f32977499b47131a6fd216ad17416224b181c108aa4fa0e8ae6783
- evidence/p340-formal730-code/ exact code2 archive

### source032 — anchor CPU STOP, Native 미시작

review031 exact pin으로 source-only 시도. anchor5bound/6read/1,773,671bytes/0fresh/unfinished에서 STOP.8sample: hostmax100%, ownmax1.325758%, private46,596,096bytes, RAMfree min30.921639%. 마지막4sample host100/own0/read delta0. Native/제품 시작0, watcher cleanup TRUE다.

- receipt evidence/locked-r07/p340-closing-source-run032.v1.json
- bytes33388 / SHA256 5a544fd010bd3ee446f070783db64ea7da432eb65bb8e0ce92051b915f331bd9
- FAILED_NOT_ACCEPTED, original receipt 보존

이 원 실패의 exact bytes/hash·원 stage/CPU/cleanup/미완료 metadata/Native·제품 미시작을 read-only로 검토했다. 원 읽기·JSON·freshness·backpressure 코드를 재확인했고 제거 가능한 추가 중복은 찾지 못했다. .gitignore에서 target/node_modules/build cache 제외와 공개 P09 evidence 유지 경계를 읽기만 했고 수정하지 않았다. 임시 증거를 무조건 ignore하여 누락시키지 않았다. 해당 큐 Python0·Git0인 이후 단일 Windows counter 표본은 CPU21%/free RAM33.045%로 회복되어 있었다. current code2와 review031 exact pin도 재확인했다.

### source034 — 관측된 회복 뒤 단1회 새로운 source-only 시도

코드를 바꾸지 않고 실제730 자격을 재사용했다. 원 resource admission/watch를 다시 통과해야 하며, source032를 덮어쓰거나 성공 제품107/108을 재실행하는 시도가 아니다. 관측 회복과 exact 실패 검토 없이 반복한 blind retry가 아니다. Source mode만 실행했고 새로운 제품 본체는0이다.

preparation209bound/209fresh/418read/43,485,170bytes/finished TRUE 뒤 source_frame_acquire에서 STOP. 실제 입력1658/121,166,202bytes 프레임은 CLOSED/unregistered, byte boundaries0이다.

Native take1933attempt/1932complete/1failed. directory308complete, regular1624complete/1failed. open1933attempt/1932complete/1failed, 총139.829651초(원 pacing·pressure 포함), max1.576423초다. 원 inspect1932complete, 총0.059494초, max0.0000909초. 실패 순번1933/kind regular/last operation open_with_pacing이며 경로명·handle·예외 값은 기록하지 않았다. 느린 metadata inspect 또는 자체 CPU 풀로드를 입증하는 수치가 아니다.

원 handle1932open/1932close, remaining0, metadata_checks1932, reader0, stream0, closefailure0, cleanup TRUE. borrower NULL이다. actual byte read 전 단계여서 전체 Source PASS나 after 완료가 아니다.

335sample: hostmax100%, ownmax1.893939%, private86,675,456bytes, RAMfree min32.708568%. 마지막4sample host98.3/100/100/100%, own0, read delta0, pass418 고정이다. 단순 명령 관측 timeout이 아니라 원 CPU guard의 terminal STOP 및 cleanup을 확인했다.

- receipt evidence/locked-r07/p340-closing-source-run034.v1.json
- bytes702168 / SHA256 1bb2287a87fea409601d575520600157414633bb9070894cbe7e698a1d4bc72b
- FAILED_NOT_ACCEPTED / watcher cleanup TRUE
- PTY57571 terminal exit1 확인, PID282032 후속 조회에서 없음
- 종료 후 단일 Windows counter: host100%, free RAM32.092%, queue Python0, Git0

## BLOCKED audit와 재개 경계

재개 후 같은 host 포화 조건의 연속 목표 턴은 다음과 같다. 진행이 있었어도 보호 조건이 계속 재발했다는 사실과 구분한다.

1. source027: metadata pathname 중복을 줄이고582 계약을 검증했지만 source guard가 CPU STOP.
2. source029/review030: Native 최소 계측·672 계약과 held-source class 중복 제거를 수행했지만 full after/다음 anchor에서 CPU STOP.
3. source032/source034: metadata class 중복 제거·730 계약을 검증하고, exact 실패를 검토한 뒤 실제 회복 표본에서 한 번 재시도했으나 다시 CPU STOP.

현재의 Native 검사 자체는 빠르고, 전체 open 시간 대부분은 원 pacing을 포함한다. 원 guard/identity/JSON/byte/최종fresh·whole scope를 빼는 것은 최적화가 아니다. 현재 확인한 후보는 구현했고 새 안전한 성능 후보 없이 같은 큰 검증을 계속 돌리는 것은 목표 진전으로 취급하지 않는다. 추가 외부 상태 안정 또는 사용자 범위 선택 없이는 지금 full source를 완료할 수 없는 경계로 판단했다.

재개 때 current730/code2 자격을 보존하고 source034 exact 실패를 먼저 검토한다. fresh resource admission을 유지한 source-only 경로부터 이어간다. source-only PASS 전에는 closing-accept를 실행하지 않는다. 성공한 제품 본체107/108을 다시 실행하지 않는다. 전체1658과두 실제 byte 경계, CPU98×4/RAM/commit/600/720/Job/pacing을 유지한다.

원1LP/BelowNormal, Job CPU6.25%/active16/kill-close/no-breakaway, RAM cap8%/own stop7%, admit RAM10%/stop8%, commit95%, Native600/metadata720/scope600/parent1200, acquisition14/native20/metadata32 no-burst,64KiB chunk, binary1/other2MiB/s는 그대로다. CPU35% admission이나 새 느슨한 기준은 추가하지 않았다. OS/Defender/WSL 변경, 다른 프로세스 종료, 접근 허용/한글, Git/Review 명령, Cargo/build, 삭제·이동은 없었다.

## 수용과 보존

수용101/249, 잔여148(regular142+corpus6), next108, source closing pending1, whole 재조정98. 현재95코드 contract730만 QUALIFIED이고 full Native/source NOT_QUALIFIED, compound102 NOT_ACCEPTED다. P09/A12/A13 OPEN, full1470/full249/signed16/product_complete/PC_freeze_resolved 미완료.249는 해당 큐이며 P09 전체 진행률 분모가 아니다. 현재 문서 전체 finalfresh NOT_RUN.

r139 CURRENT_STATE/P09-149/P09-346 원3파일은 evidence/runtime-progress-r139/에 exact byte/hash로 보존했다. 원 source032/034는 삭제/승격하지 않는다. 진단 whitelist·자격·blocked audit·pin은 evidence/p09-347-metadata-facade-progress.v1.json에 남겼다.

작성 후 current code2/receipt031·032·034 exact bytes/SHA256, formal730 code archive2, r139 문서3의 전체 suffix byte 보존, 진단 JSON 수용 산술/730계약/0byte boundary/잔여0/3턴 audit, 원 actual108 zero-byte/hash 보존을 확인했다. 이 제한 점검은 Native/제품/Gate/문서전체finalfresh 자격이 아니다. review031 PTY16292와 source034 PTY57571은 terminal 반환을 확인했고 source032도 명령에서 terminal 반환했다. 새 실행·대기를 시작하지 않았다.
