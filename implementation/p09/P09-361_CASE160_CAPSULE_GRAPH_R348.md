# P09 case160 worker 캡슐과 공유 입력 그래프

160번의 실제24쌍 manifest를 closed worker capsule v3와 parent/frame/worker/full-oracle 공통 Binding 타입으로 연결했다. 실제160 engine 설정·worker dispatch·Native·제품 실행과 독립 승인은 아직 수행하지 않았다. 공식153/249·잔여96·next160·generation48, P09/A12/A13 OPEN 및 목표ACTIVE 상태를 유지한다.

## 캡슐과 원래 worker 코드

runtime_successor_worker_capsule_v2.py는 원래 encoder/decoder의 metadata만 정확한160/before153/authority153/root159로 연결한다. tuple과frozenset을 포함한 metadata 역변환으로 전체 원래 code equality를 확인한다. 원래 defaults/closure/kwdefaults, closed schema, hash, 정확한 Binding 타입, 16KiB 상한을 유지한다. worker dispatch bytecode는 원래 객체와 같다.

검사6개와 실제manifest24의encode/decode가 통과한r758 상태는 PASS_ACTUAL160_CAPSULE_CODE6_MANIFEST24_MEMORY_TRANSPORT_NOT_WORKER_DISPATCH_OR_PRODUCT이다. fresh143/final143/cleanup true를 확인했다. 실제 capsule001.v3는13081bytes/SHA256aec00cb8654f501d6dc6abf49271315412f92fad57a9d9979e6b79644ec73723이며 canonical byte에LF1개를 추가한 실제 file 핀을 구분했다. 원본·관측 row는 변경하지 않는다.

## CPU peak 관측과 코드 재점검

r758의 전체CPU 최대98.48%, 최소 가용RAM45.92039%를 보존한다. 이 receipt에는 peak 당시 parent CPU attribution이 출력되지 않았으므로 검증기 단독 부하나 원인 프로세스를 확정하지 않는다. 기존 hard guard의 연속 과부하 중단은 발동하지 않았으며, 단일 peak가 있었다는 사실을 성공 기록에서 숨기지 않는다.

이후의 bounded snapshot에서 System은machine CPU8.81%, CompatTelRunner는5.44%였지만 당시 peak의 원인 증거는 아니다. Defender 설정을 변경하거나 외부 프로세스를 종료하지 않았다.

decoder 코드가64KiB 출력 단위마다 checkpoint, 진행·크기·hash 검사를 유지하고 캡슐이16KiB 안이며, 무제한 loop/parallel task/retry를 추가하지 않았음을 확인했다. 같은reader에서 문맥admission을두번 호출하던 부분은 기존 source-admission declaration wrapper로한번 줄였다. JSON/hash/byte cache나최종fresh 생략은 없다.

## 공통 그래프와 자원 보호 검증

successor_runtime_graph_v2.py는 원래core source16개를 핀 검증 후private namespace로 연결한다. parent access/frame, worker/raw policy, full oracle 모두같은160 Binding module을 사용한다. 실제capsule file을decode하여24쌍과manifest 핀이원manifest admission 결과와같음을검사한다. 현재160 engine이실제로설정됐다고주장하지않는다.

r759는 기존sampler에75% metadata 경고를 적용하고원hard guard/deadline/cleanup을유지했다. PASS_ACTUAL160_SHARED_PARENT_WORKER_ORACLE_GRAPH_MANIFEST24_NOT_ENGINE_CONFIG_NATIVE_OR_GO, fresh154/final154/cleanup true를 확인했다. 문맥declaration 실제admission1/중복회피1, 경고checks16392/stops0/latchedfalse이다.

전체CPU 최대44.88%, 최소 가용RAM42.31558%, parent 최대machine CPU3.82863%/private59.73829MiB를관측했다. actual engine/frame/workerdispatch는모두0이다. 이전peak의원인이해결됐거나PC프리즈가해결됐다는증거가아니다.

## 다음 단계와 보존

다음은160 실제engine 설정, 이전159의독립전체oracle, controller/DATA와wholecurrent source/import/Rust scope-cost/preflight이다. 이를통과한뒤에만160 단일제품실행·독립승인을수행한다. 성공159는재실행하지않는다. 기존600초·60margin·14/20rates·twobyte·15capture·shareddecoder5 및CPU/RAM보호를유지한다.

full249-current/signed16/P09 Gate는미완료이고P10 새구현은없다. authority153/152와성공159/158, 이전manifest/capsule, 실패034 및P08/P17/sharedRust/private 원본을보존한다. 한글·접근허용·UAC·OS/Defender/WSL 변경·외부종료·원본삭제이동·원격push는없었다.

근거는implementation/p09/evidence 아래case160 capsule-code6-r758, worker-policy-capsule001.v3, shared-graph-r759 및capsule-resource-review-r760이다.
