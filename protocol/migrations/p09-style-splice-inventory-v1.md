# 서식 치환 후보의 실제 최종 splice 목록

`hwpx-agent.source-style-splice-inventory/v1`은 부분 run 글자 모양과 text-style 후보가 실제
PatchIntent로 전달한 최종 Subtree splice를 보관한다. 검색 일치 수나 원 변경 run 수만으로
operation 대상을 추정하지 않도록 compiler에 전달할 입력을 남긴다. 기존 요청/receipt JSON과
서식 치환 의미는 변경하지 않았으며, 이 목록은 실행 권한이나 완성된 CompiledOperationPlan이 아니다.

## 목록과 원본 좌표

SourceStyleSpliceInventory는 외부 생성자와 Deserialize가 없는 불변 결과다. JSON 필드는 다음과 같다.

| 필드 | 의미 |
|---|---|
| profile | hwpx-agent.source-style-splice-inventory/v1 |
| axis | run_character_property 또는 text_character_style |
| source_package_sha256 | 원 패키지 SHA의32-byte 배열 |
| output_package_sha256 | 검증한 출력 패키지 SHA의32-byte 배열 |
| legacy_receipt_sha256 | 변경 없는 기존 source receipt의 원 직렬화 SHA |
| splices | 실제 최종 patch 순서의 목록 |

각 SourceStyleSubtreeSplice의 필드는 source_anchor, source_start, source_end,
replacement_sha256, replacement_bytes, fragments다. source_anchor는 같은 원본의 실제 요소
handle/fingerprint이고 start/end는 해당 part의0-based·반열린 바이트 범위다. NFC scalar나 새 출력의
좌표가 아니다. replacement SHA/크기는 실제 최종 splice bytes 전체를 대상으로 하며 namespace·
entity·quote도 포함한다. fragments는 해당 최종 splice에 전달한 validated fragment 수다.

splices는 원 plan.edits의 part 순서와 원본 시작 위치 순서로 수집한다. 중첩 overlay가 상위 edit에
합쳐졌으면 최종 상위 splice만 남는다. 두 검색 일치가 한 원 run/t에 있거나 세 변경 run이 한 상위
splice로 병합될 수 있다. 물리적인 subtree 범위에 포함된 선택 밖 내용은 기존 readback·원본 보존
검사로 그대로 유지하며, 이 범위 자체를 새로운 semantic 편집 허가로 쓰지 않는다.

## 수집과 한도

원 compiler의 최종 edit에서 PatchIntent를 구성하는 같은 loop가 실제 element anchor·outer span과
치환 bytes의 해시/크기를 수집한다. 원본 outer end와 edit end, 비어 있지 않은 fragment, 최종
intents와 목록 개수를 확인한다. 최대4096개를 추가 전 확인하고 목록 직렬화는8MiB 아래로 제한한다.

기존 receipt의 결과 한도는 그대로 적용한다. receipt와 목록의 해시는 bounded streaming writer로
계산해 별도 JSON 버퍼를 만들지 않는다. 최종 fragment bytes는 해시한 뒤 보관하지 않고 새 원본
수입이나 검색·치환·출력 생성도 추가하지 않는다. canonical_sha256 getter는 목록의 원 Serialize
바이트 SHA를 반환하며 자기 해시 필드는 JSON에 포함하지 않는다.

기존 두 matcher/compiler·보호·no-op·렌더·중첩 overlay·patch/writer·출력 readback과 receipt 선언은
추가분을 제거하면 원 바이트로 복원된다. 기존 source/stored/product receipt의 JSON shape는 동일하다.

## 현재 권한을 확인하는 전달

core의 splice_inventory 조회는 metadata일 뿐이다. stored/product의 with_verified_splice_inventory는
원 with_verified_bytes를 재사용해 현재 write/scope/head/ACL/quarantine/AEAD와 writer integrity·
consumer 직전 최종 head를 검사한다. 제품에서는 원 request/receipt binding도 먼저 확인한다.
원 후보 소유권 이동과 같은 목록을 공유하며 접근을 다시 확인할 때 목록이나 검색을 재생성하지 않는다.

idempotency_key/plan_id는 기존 제품 요청의 identity로 별도 결속한다. key/plan만 달라져도 실제
편집과 기존 source receipt가 같으면 이 목록은 같을 수 있다. 따라서 목록 해시를 멱등 key claim이나
실행 identity로 사용하지 않는다. Debug는 private anchor·fragment·원문을 출력하지 않고 JSON에도
fragment XML이나 검색어 원문을 넣지 않는다. 원 RouteUnqualified와 실행 차단은 그대로다.

## 검증 결과

components209는 시험 helper의 비공개 XML 바이트 접근 E0624와 고정 repository 타입 E0308로
컴파일 실패/시험0이다. 공개 bounded ZIP reader와 generic repository로 helper만 고친 recovery210은
신규12+영향 기존 제품36+영향 공통 dispatcher2=50pass·737fresh/final737·진단/경고없음·cleanupTrue다.
원209 실패와 원 요구사항은 보존했다. 무관 공통24·공식249와 다른 기능 시험은 반복하지 않았다.

새 시험은 각 splice의 원 anchor와 바이트 범위를 원본에서 resolve하고, 출력의 실제 치환 byte SHA/
크기와 범위 밖 전체 bytes를 독립 대조한다. 기존 receipt와 목록 SHA·부분/불연속·중첩 최종 병합·
no-op 제외·review 정책/선택 창·128개 target·현재 write/외부5scope·ACL/격리/AEAD·최종head 경합·
비노출/미게시를 포함한다. 기존36개와 공통2개는 실제 영향을 받는 경로의 원 시험 본문 그대로다.

210 전체134.609초·명령40.359초/시험30.61초·Job CPU39.062초·private최고934.70MiB/2.9337%·
시스템CPU최고50.80%·가용RAM최저27.7148%다. Job active0/empty/handle closed와 한 코어 affinity4·
BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%·명령300초·guard600초를 유지했다.
OS/Defender/다른 앱 변경이나 PC 프리즈 해결을 주장하지 않는다. 근거는
implementation/p09/evidence/p09-361-style-splice-inventory-components209.v1.json 및
p09-361-style-splice-inventory-recovery210.v1.json이다.

## 다음 실제 실행 경계

다음은 실제 source anchor를 원 IR target에 결속하는 operation compiler다. 임의 첫 문단이나
가상 document node로 대체하지 않는다. CompiledOperationPlan·실제 route manifest·저장/ingest/
commit/CAS·영속 멱등 실행·실행 dispatcher/transport/게시·전체 검색/참조·target/Native/Gate는 남는다.
source API v12 incomplete/미해결4/report없음/exit3·공식158/249·잔여91·next165·P09/A12/A13 OPEN·
목표ACTIVE·P10 미시작·고정 CROSSREF8종 NOT_RUN·Native011 미승인/미실행을 유지한다.

## 검증한 원본 operation compiler 소비자

위 다음 단계였던 compiler 연결은 product-source-search-operation-compiler/v1로 구현했다.
CharacterStyle/TextStyle의 실제 최종 splice를 원 source graph의 실제 소유 node에 결속하며 정확한
편집 목록·원본/출력·요청 지문을 원 OperationPlanCompiler의 필수 argument에 보관한다. 소유 node는
문맥일 뿐 편집 범위 확대나 실행 권한이 아니다. 제품30+owner6 고유36개 구성요소 검증이며 실제
route/transaction/Native/Gate는 여전히 미완료다. [공통 compiler 계약](p09-source-search-operation-compiler-v1.md)을 따른다.
