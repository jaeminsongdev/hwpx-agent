# P09-346 — Native 획득 계측과 source facade 클래스 재사용 (2026-10-10)

## 현재 결론과 목표

목표 ACTIVE. 이전 턴의 metadata 중복 조회 제거·실제582 계약 검증은 진행으로 분류한다. 이번에는 원 Native 획득 경로를 최소 계측하고 실제672 계약 검토와 full1658 source 시도를 수행했다. CPU STOP 이후 같은 명령을 반복하지 않고 실제 읽기 경로의 반복 class 생성도 제거했다. 최신v16의700 계약은 CPU STOP 때문에 미검증이며 현재 full Native/source 자격은 아직 없다.

이 턴의 CPU 중단은 Native 획득 검사 자체의 비정상적인 장시간 실행으로 확인되지 않았다. 원 획득1966개 전부 완료했고 inspect 전체0.064723초, open 전체140.643137초였다. open 시간에는 기존14/s pacing과 pressure 대기가 포함되므로 kernel 호출 시간이라고 주장하지 않는다. 후반 final_fresh_hash에서 host CPU100%가 지속되어 원 guard가 중단했다. 자체 CPU/메모리, 전체 시스템 CPU, 이 작업이 간접적으로 야기할 수 있는 외부 부하를 구분하며 PC 프리즈의 단일 원인을 확정하지 않는다.

## 변경 — 고정 runtime/test 두 경로

1. v15 AcquisitionDiagnostics/AcquisitionNative/AcquisitionInputLocks를 연결했다. 원 Native instance, 메서드·인자·반환값·예외·pacer·guard·identity 검사를 유지하면서 take 종류/순번, open-with-pacing/inspect-metadata 두 operation의 집계 시간·성공·실패·unknown을 기록한다. 파일 경로·handle 값·예외 문자열, 입력별 전체 trace는 기록하지 않는다. 통계는 고정크기이며 시계 오류가 원 결과를 가리지 않는다. close/create/borrow 및 비획득 inspect는 원 bound method에 위임하고 cleanup에 새 계측·guard를 넣지 않는다. 별도 resource sampler/thread/native query를 만들지 않았다.
2. v16 HeldPathSource를 사전 정의한 slots class로 옮겼다. 매 source 요청의 동적 class 정의·메서드 closure 재생성·instance dictionary 생성만 제거한다. 매 요청 새 facade instance와 fresh Native metadata 조회를 수행한다. 세 원 predicate의 owner/frame/borrow binding/token guard도 각각 그대로 실행한다. 요청 간 metadata cache가 아니다. 실제 CPU/프리즈 개선이나 전체 제품 완료로 주장하지 않는다.
3. 원 source027(v14)/source029(v15) 실패를 exact pin 및 당시 code2 archive와 바인딩했다. source029의 완성된 before1658,1966 원 핸들과3135 복제 핸들 정리, after 부분 상태를 검사하며 전체 source PASS/GO로 승격하지 않는다.

원 frozen93/code95/controller191/full1658/directory308을 유지했다. runtime schema는 v16, test350×current/following2=700이다. 기존291개는 유지했고 v15에45개, v16에14개를 더했다.

## 실행 증거

### v15 review028 — 실제672 계약 PASS, Native/제품 PASS 아님

순수 신규45개 PASS 후 current336+following336=672개 모두 PASS. metadata202 bound/202fresh/404read/39,350,838bytes/finished TRUE, 원 path predicate1212개, watcher cleanup TRUE다. Native/제품 새 실행0이다.

73sample: host CPU max20.04%, own machine CPU max6.470588%, own private max98,770,944bytes, free RAM min32.510184%.

- receipt evidence/locked-r07/p340-closing-review-run028.v1.json
- bytes189415 / SHA256 ce69eff1ec284d4cc5daf0203b39f2b2617fde2534e9bf9845288b22b6b1c8f7
- exact qualified code2 archive evidence/p340-formal672-code/

### v15 source029 — full 획득·before 완료, after CPU STOP

review028 exact pin으로 독립 전체 source 시도1회. preparation203bound/203fresh/406read/39,729,668bytes/finished TRUE. Native take1966/1966, directory308+regular1658, open/inspect 모두1966성공, take실패0, unknown0, phase14→20 복구. 획득시 pressure warning0이었다.

완성된 before 경계는 실제1658pins/1658read/121,150,122bytes다. after는 부분 상태이며 완성된 두 번째 byte boundary는 없다. after path query1478/원 predicate4434이다. Native metadata checks5101은 원 handle 검사 회계이고, source guard의 extra fresh-held query는 별도 회계다.

원 핸들1966opened/1966closed, 복제3135opened/3135closed, handle/reader/stream/duplicate 잔여0, close실패0, frame CLOSED/unregistered, root복구 TRUE, watcher cleanup TRUE를 확인했다. 새 제품 실행0. 실제Native획득 집계가 완성됐다는 사실과 전체 source 자격은 다르다.

830sample: host CPU max100%, own machine CPU max1.724138%, own private max85,319,680bytes, free RAM min31.526207%. 마지막4sample host100/own0/logicalread delta0이며 원 CPU98%×4 보호 기준으로 final_fresh_hash에서 중단했다. 자체 CPU 풀로드나 RAM 풀로드를 확인한 결과가 아니다. 간접 영향까지 없다고 단정하지도 않는다.

- receipt evidence/locked-r07/p340-closing-source-run029.v1.json
- bytes1395264 / SHA256 1f5af31def4ea7476296b049af54490b852cfcda875f4a44c1e82e10f3975cc0
- FAILED_NOT_ACCEPTED / source·compound·제품 미수용
- 동일 full source 즉시 retry0

### v16 facade 재사용 — 순수84 PASS, 정식700 미검증

동적 class 생성 제거 후 획득·held guard·facade·원 CPU 실패검토 순수 subset84개가 PASS했다(실제 제품/full Native 자격 아님). 새 변경 중 indentation 오류를 AST 단계에서 발견·수정했고, 수정 후 두 코드 AST/compile PASS 및84개 PASS를 확인했다. 그 오류로 Native/제품을 실행하지 않았다. current header의 source029 실패검토 필수 조건도 연결하고 부정 계약을 추가했다. 이84개 PASS 뒤 source029 header 필수검사와 부정1개를 더한 최종 candidate 전체를 검증한 것은 아니다. 최종 code pair의 정식 자격은 review030에서 미검증으로 남았다.

정식 closing-review030은 anchor에서 CPU STOP.8sample/원metadata5bound/6read/1,708,135bytes/0fresh/unfinished, 계약 실행0, Native frame/제품 미시작, watcher cleanup TRUE다. 700개를 통과했다고 말하지 않는다.

host CPU max100%, own machine CPU max1.123596%, own private max46,546,944bytes, free RAM min30.994404%. 마지막4sample host100/own0/read delta0. 기존 observer의 GetSystemTimes delta 계산을 재확인했고 원 계산 코드는 바꾸지 않았다. 모든 자체 실행이 terminal인 뒤 별도 Windows performance counter 단일 read-only snapshot도 host100%, free RAM32.82%였다. 같은 기간의 평균 또는 특정 프로세스 원인 증거는 아니다.

- receipt evidence/locked-r07/p340-closing-review-run030.v1.json
- bytes33393 / SHA256 ede89b1ced23a869b9554c871f089363f7cdaa4cb70b3ab0029b7444e8799633
- 최신 candidate exact archive evidence/p340-v16-preformal700-code/
- 최신 code2는 preformal candidate이며 review028의 qualified672 code와 다르다.
- review030 실패 보존, 즉시 동일 검토 재시도0

## 보호, 잔여와 다음 작업

기존1LP/BelowNormal, Job CPU6.25%/active16/kill-close/no-breakaway, RAM cap8%/own stop7%, CPU98%×4, RAM admit10%/stop8%, commit95%, Native600/metadata720/scope600/parent1200, acq14/native20/meta32 no-burst,64KiB chunk, binary1/other2MiB/s를 유지했다. CPU35% 이하에서만 실행 같은 기준을 추가하지 않았다. 통과한 제품107/108을 재실행하지 않았고, 원 full1658 또는 두 byte boundary를 줄이지 않았다.

수용101/249, 잔여148(regular142+corpus6), next108, source closing pending1, whole 재조정98, compound102 NOT_ACCEPTED, P09/A12/A13 OPEN이다. 249는 해당 큐이며 P09 전체 진행률이 아니다. 현재 문서 전체 finalfresh도 NOT_RUN이다. 제품·Gate·프리즈 해소는 미완료다.

다음 안전한 관련 후보는 MetadataPathQueries.source에도 남아 있는 요청별 Source class 재정의다. 원 predicate 순서·fallback·reader/token 수명·JSON/finalfresh/CPU·RAM·deadline 검사를 유지하는 class 재사용 후보를 검토한다. 최신 formal700 qualification은 아직 필요하다. 원 CPU 포화 상태가 지속될 때 새 근거/변경 없이 큰 source 프레임을 반복하지 않는다. 안전한 관련 코드 개선이 남아 있으므로 지금 목표를 BLOCKED/PAUSED/COMPLETE로 바꾸지 않는다.

Git/Review, Cargo/build, 접근 허용/한글, Defender/WSL/OS 변경, 외부 프로세스 종료, 삭제·이동은 하지 않았다. 원 r138 문서3개는 evidence/runtime-progress-r138/에 exact byte/hash로 보존했다. 기존 source027/029/review030, qualified672와 v16 candidate를 구분하여 유지한다.

상세 exact pin·whitelist 관측·진단 원장: evidence/p09-346-native-acquisition-progress.v1.json.

## 작성 후 제한 점검

최신 candidate 코드2·실행 receipt028/029/030의 exact bytes/SHA256, v16 preformal code archive2, r138 문서3의 전체 suffix byte 보존, 진단 JSON 수용 산술·계약0·단일 before 경계·잔여handle0, 원 actual108 zero-byte 증거 보존을 확인했다. 이 점검은 최신700 계약/전체Native/source/제품/Gate/문서전체finalfresh 자격을 대신하지 않는다. 실행 세션68438(review028),20369(source029)는 terminal exit를 확인했으며 review030도 명령에서 terminal 반환했다. 새 대기나 자동 재실행을 시작하지 않았다.
