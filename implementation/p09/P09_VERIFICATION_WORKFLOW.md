# P09 검증 결과 재사용과 변경 영향 검사

## 실제 API의 캡션 상태 결속값과 저장 요청

실제 source 응답 v10은 `caption_source_state_import`, `caption_owner_links`, `caption_source_events`를 제공한다. 기존 한 assembly에서 생성한 exact joined-state receipt와 owner/frame/object/event 인덱스를 그대로 재사용하며 새 원본 import를 하지 않는다. 기존 응답의 의미를 조용히 바꾸지 않고 schema를 v9에서v10으로 명시적으로 올렸다.

호출자는 이 API의 joined-state 지문·owner·frame만으로 `prepare_caption_structure_candidate` 요청을 구성할 수 있다. 새 저장 연결 시험은 caller가 caption state를 다시 import하지 않고 생성·삭제 후보를 준비해 출력 API를 확인한다. foreign document·변조한 지문은 거부하고 기존 현재 접근/원본/proof/writer/final-head 경계는 바꾸지 않는다. receipt/지문은 접근 허가가 아니며 이벤트 XML 순서는 Native counter/문서 흐름으로 해석하지 않는다.

새 API5+연결1+기존 source41=47pass·278fresh/final278·cleanupTrue다. 기존 source41은 include와 schema 예상값8곳 밖을 정확히 보존했다. 실제 CLI v10/exit3, 두 part local-ID 분리, 전체 연결과 빈 owner, 전체 원본/문서 지문, 출력 byte 한도와 비공개 값 비노출을 확인했다. 기존 저장6개 시험과 생산 저장 코드는 새 연결 사례 밖을 그대로 두었고 core49/patch13/저장30은 반복하거나 새 feature graph로 승격하지 않았다.

`p09-361-source-caption-join-components001.v1.json`은 전체81.735초·소유40.235초·Job CPU13.938초·최고765.94MiB·시스템CPU최고51.37%·가용RAM최저25.1971%·Job active0/empty/handle closed다. 한 코어·BelowNormal·CPU cap6.25%·RAM/commit95%·64인자/8536byte·출력32KiB와 전체 입력 전후 확인을 유지했다.

다음은 CROSSREF의 원본 파라미터/대상 결속을 공식 정의와 캡처 원본으로 확인해 참조 관계 import를 구현하는 단계다. API v10의 네 미해결 단계·incomplete·report없음·exit3, 공식158/249·잔여91·next165·P09/A12/A13 OPEN·Native011 별도 승인 조건은 그대로다.

## 원본 캡션 생성과 삭제 후보의 저장 접근 검사

`prepare_caption_structure_candidate`는 새 whole-caption 요청을 기존의 현재 scope/head/ACL/quarantine/AEAD·전체 원본/Form proof·joined state·writer integrity·최종 callback head 검사에 연결한다. private Captions variant는 같은 공통 경계를 사용하고 별도의 바이트 전달 통로나 inner content를 공개하지 않는다. 생성 결과는 원본 owner 순서이므로 원본 owner별 인덱스로 local ID 지문/개체/paragraph 수를 대조하며 삭제 ID/지문·request digest·joined state도 결속한다.

새6+기존 content/sequence/number-topology/program 각6=30개를 확인했다. 최초001은29pass였고 혼합 사례의 예상 검사량4N만 실패했다. 조상·layout subtree·content subtree 세 맵의 두 번 순회에 맞춰 시험만6N으로 바로잡고 recovery002에서 해당 사례1개만 PASS했다. 다른29개와 제품/보호 코드는 그대로다. recovery002의 tuple/list 집계 비교 실패는 보존했고 metadata003은 전체 성공 목록·입력274fresh/final274·종료를 확인했으며 시험을 재실행하지 않았다.

정상 경로는 source/head를 쓰지 않고 read audit만 남긴다. saved receipt/proof로 ACL 철회·격리·AEAD 변조·foreign scope·원본/head 변경을 우회하지 못하며 최종 callback 이전에 거부한다. 혼합 생성·삭제·교체·유지 본문/layout/style·요청 순서 역전과 잘못된 요청/보호/한도를 확인했다. 공통 접근 코드와 기존 시험 본문은 선언/import/dispatch/include 밖을 정확히 역변환해 대조했다.

회복002는 전체90.703초·소유68.078초·Job CPU4.484초·최고723.91MiB·시스템CPU최고52.51%·가용RAM최저26.2935%·Job active0/empty/handle closed다. 한 코어·BelowNormal·CPU cap6.25%·RAM/commit95%·원 인자/출력 한도를 유지했다. 최초001과 회복002 원본 및 metadata003을 보존하며 기존 core49/patch13을 반복하거나 다른 feature graph로 승격하지 않는다.

다음은 실제 source API의 CompleteAuxiliaryState·ReferenceEdgeSemantics에서 캡션/번호 결속에 필요한 누락 원본 관측과 정책 구현이다. Native/완전한 state/flow/protection/CAS/실행/게시 자격과 공식158/249·잔여91·next165·P09/A12/A13 OPEN·Native011 별도 승인 조건은 그대로다.

## 원본 캡션 생성과 삭제 후보의 검증 범위

`lower_caption_structure_candidate`는 전체 원본/Form proof와 joined state에 결속된 명시적 생성·삭제 목록을 한 patch/writer/출력 재수입으로 처리한다. 생성은 원본 owner 지문·layout·모든 paragraph/run/text/autoNum/restart와 기존 character/paragraph/named style 선언을 요구한다. 이미 있는 캡션은 matching deletion 없이 덮어쓰지 않고 삭제된 캡션을 향한 다른 요청은 무변경도 거부한다.

원본 paragraph ID 최댓값 이후에만 part별로 할당하며 삭제 ID는 재사용하지 않는다. 변경 part의 ID 탐색과 보호 인덱스는 공유하고 유지되는 text/layout/style는 byte 위치로 재결속한다. 모든 출력 owner/caption/control을 다시 대조하고 선택한 편집 밖 바이트는 그대로 보존한다.

공식 Hancom 모델 commit `1453388472c703a4b299a0834f425cdac16644b9`의 ArcType/ConnectLineType → AbstractDrawingObjectType → AbstractShapeComponentType/AbstractShapeObjectType 상속에 따라 새 caption-owner/v8 프로필에 arc/connectLine의 id/instid를 별도로 선언했다. shape/v6·chart/v7은 그대로이며 새 모드만 v8을 선택한다. 중복 ID/instid, 미지 참조, HWPX 요소의 namespaced ID 속성은 거부한다. 외부 namespace는 HWPX ID로 인식하지 않고 보존한다. chart와 연결선 endpoint 참조는 지원하지 않는다. [공식 모델](https://github.com/hancom-io/hwpx-owpml-model/tree/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para)

core49 중 components003의48pass를 유지하고 foreign namespace 예상값만 고친 실패 사례를 recovery005에서1회 실행해 PASS했다. 생산 코드·다른 시험·보호 설정은 정확히 같고 실패 시험의 변경도 역변환 hash로 대조했다. 초기001/002 및003/004 실패는 보존한다. 새 생성/삭제6+영향 기존43과 영향 저장24/patch13의 총86개 component를 확인했으며 다른 feature graph로 결과를 승격하지 않는다.

`p09-361-caption-structure-regressions006.v1.json`은37pass·267fresh/final267·전체69.797초·소유30.609초·Job CPU28.734초·최고1514.32MiB·시스템CPU최고19.32%·가용RAM최저27.1792%·Job active0/empty/handle closed다. 원 자원/인자/출력 한도를 유지했고 새 경고는 없다. 회복005는266fresh/final266·cleanupTrue이며 core48을 재실행하지 않았다.

다음은 새 구조 요청을 현재 scope/head/ACL/quarantine/AEAD와 최종 전달 경계에 연결하는 저장 서비스 구현이다. 기존 서비스24개 회귀 PASS는 새 연결 자격이 아니다. Native counter/렌더링, 전체 state/flow/protection, CAS/실행/게시와 Native는 남고 공식158/249·잔여91·next165·P09/A12/A13 OPEN·Native011 별도 승인 조건은 그대로다.

## 저장된 캡션 계산 요청과 생성 라벨의 현재 접근 검사

`prepare_caption_program_candidate`는 기존 저장 후보의 현재 scope/head/ACL/quarantine/AEAD, 전체 원본/Form proof, joined state, writer integrity와 최종 head 검사를 공유한다. private 요청/output enum의 Program variant가 생성한 label+separator도 일반 텍스트 요청 원장에 포함한다. sequence별로 지문과 UTF-8 길이를 한 번 계산하며 caption/object/text/control·명시 순서와 출력 metadata를 인덱스로 대조한다. 무변경 라벨도 누락하지 않고 기존 `request_bindings_match`와 content 검증을 사용한다.

새 wrapper는 inner content와 bytes 경로를 private로 유지한다. 요청 digest는 전체 program과 낮춘 번호 snapshot receipt에 결속하지만 접근 권한은 아니다. 모든 verify/전달에서 현재 원본을 다시 확인하고 마지막 head 변경은 callback 전에 거부한다. 정상 경로에 ingest/commit을 추가하지 않으며 실행/게시 route는 계속 거부한다.

`p09-361-stored-caption-program-components001.v1.json`의 새6+영향 기존18=24개가 PASS했고 입력253개를 전후 확인했다. 기존71개 서비스 시험 본문과 공통 코드의 새 선언/dispatch/라벨 결속 밖은 정확히 보존했다. 원 core program30은 재실행하지 않았으며 다른 feature graph로 승격하지 않는다. 전체89.313초·소유52.000초·Job CPU49.172초·최고1868.71MiB·시스템CPU최고21.78%·가용RAM최저25.6073%, Job active0/empty/handle closed다. 한 코어·BelowNormal·CPU cap6.25%·RAM/commit95%·39인자/12154byte·출력32KiB를 유지했다.

기존 캡션 편집 결과이며 원본 캡션 추가/삭제·Native 재계산/렌더링·전체 state/flow/protection·CAS/실행/게시·Native 자격은 남는다. source API v9와 공식158/249·잔여91·next165·P09/A12/A13 OPEN·Native011 별도 승인 조건은 그대로다. 다음은 기존 plain-static 삽입/ID allocation 경로를 확인해 실제 원본에 대한 캡션 추가·삭제를 구현하는 작업이다.

## 명시적 캡션 순서 요청의 원본 결속과 출력

`SourceCaptionSequenceRequest`는 원본 joined-state와 기존 `CaptionSequenceDefinition`을 결속하고 모든 원본 캡션의 object/sequence, 선택한 전체 라벨 hp:t와 autoNum, caller document_order를 요구한다. 라벨+separator를 선택한 전체 텍스트에 쓰고 7서식·연속/구역별 번호를 계산해 기존 text/layout/style/전체 번호 snapshot compiler로 한 번 출력한다. caller 순서는 Native/render 순서로 승격하지 않으며 다른 제어와 문서/구역 시작값0·원 affix/userChar·미지 속성은 보존한다.

새 profile의 number_style_sha256는 선택한 run의 유일한 character style 선언 지문을 가리킨다. 변경할 character style이 명시되면 같은 원본 header에서 그 선언을 확인한다. 상속 서식이나 라벨/본문 span은 추정하지 않으며 캡션 누락/중복·잘못된 object/control/text/kind/style/order·overflow·보호·한도를 거부한다. Native 대응이 없는 sequence lock/opaque metadata도 부분 적용하지 않는다. 원 auxiliary/v1 상태를 완전한 원본 상태라고 만들어내지 않는다.

기존 full-state와 새 요청 계산은 같은 counter kernel을 쓴다. `p09-361-caption-program-components002.v1.json`의 새12+기존domain14=26pass·247fresh/final247을 유지하고, `p09-361-caption-program-oracles003.v1.json`에서 기존4개만 추가 확인했다. 1,555개 변형·보호512조합·기존 오류/overflow·8,192개 계산 기록 비교를 포함한 서로 다른30개 component다. 원26개를 반복하지 않았다. 최초001 컴파일 실패는 시험0인 원형으로 보존했고 lib의 테스트 전용 hex 참조를 기존 helper 호출 한 곳으로 고쳤다.

002의 시스템CPU최고27.65%·가용RAM최저26.2074%·Job private최고1479.08MiB,003은20.83%·27.3802%·1538.28MiB였다. 최초 실패는61.70%·24.1313%·1858.65MiB였고 모든 Job은 종료/empty/handle closed다. 자원 보호와 전체 입력 전후 확인을 유지했다. Native 계산/렌더링·program 저장 서비스 결속·전체 state/flow/protection·CAS/실행/게시를 검증한 결과가 아니며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·Native011 별도 승인 조건은 그대로다. 다음은 생성된 라벨 요청을 포함한 저장 서비스의 기존 fresh source/최종 head 검사 연결이다.

## 저장된 번호 제어 구조 편집의 현재 접근 검사

`prepare_caption_topology_candidate`는 기존 content/sequence와 같은 현재 서비스 scope/head/ACL/quarantine/AEAD·전체 원본/Form proof·joined-state 검사 경로를 사용한다. 배타적인 private 요청 enum은 sequence 값 변경과 topology 변경을 동시에 넘길 수 없게 하며, private output enum은 기존 fresh 검증과 writer callback 직전 head 검사를 공유한다. 요청 digest는 원본 joined state, 삭제 대상 ID/지문/순서와 wrapper 제거 선택, 삽입 anchor/지문/위치·local ID·제어 순서/값/서식을 결속하지만 접근/실행 허가는 아니다.

새 후보의 verify/바이트 전달은 매번 원본의 현재 접근을 다시 확인한다. inner content는 private이며 외부 bytes accessor나 caller가 구현하는 trusted output 경로를 추가하지 않았다. ACL 철회·격리·암호문 변조·foreign scope·최종 callback head 변경은 consumer 호출 전에 거부한다. 정상 경로도 source/head에 쓰지 않고 실행/게시 route는 거부한다.

`p09-361-stored-number-topology-components001.v1.json`은 새6+기존content6/sequence6=18pass·240fresh/final240·cleanupTrue다. 기존65개 시험 본문과 공통 코드의 선언/dispatch 밖은 정확한 역변환으로 유지했다. 전체45.375초·소유9.422초·Job CPU8.031초·최고698.41MiB·시스템CPU최고17.19%·가용RAM최저30.3688%, Job active0/empty/handle closed다. 한 코어·BelowNormal·CPU cap6.25%·RAM/commit95%·33인자/9136byte·출력32KiB를 유지했고 통과한 core topology62는 재실행하지 않았다.

실제 번호 계산·완전한 auxiliary state·전체 flow/protection·CAS/실행/게시·Native 자격을 수용하지 않는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·Native011 별도 승인 조건은 그대로다. 다음은 기존 typed caption-sequence 요청과 원본 번호/개체/캡션 상태의 source binding 및 실제 출력 연결이며, 미확정 시작값이나 label/separator를 추정하지 않는다.

## 번호 제어 삽입 삭제

`NativeNumberTopologyRequest`는 원본 joined-state SHA, 삭제 대상 control ID/지문, 삽입 anchor/지문·위치와 typed 번호/서식만 받는다. 기존 text/layout/style와 한 transaction/출력 재수입을 공유하며 원본의 전체 번호 목록에서 유지·삭제·삽입된 항목을 빠짐없이 대조한다. source byte 좌표와 정렬된 edit 길이를 이용해 출력 위치를 대응시키고, 추가 제어로 변한 element/segment ordinal을 기존 본문 ID 대신 사용하지 않는다. section/document 시작값은 명시값만 생성하며 0이나 누락을 기본값으로 계산하지 않는다.

보호 지도는 part당 기존 text/style 지도와 공유한다. wrapper 내부 삽입은 정렬된 위치 인덱스, 삭제 경계 교체는 경계 인덱스로 찾고 요청마다 전체 목록을 재탐색하지 않는다. 알 수 없는 속성·주석·다른 자식이 있는 ctrl는 보존하며, 모든 선택 자식의 wrapper 제거 요청이 일치할 때만 빈 wrapper를 삭제한다. 기존 overlap/ID/원문 보존/writer 검사는 유지한다.

`p09-361-number-topology-components001.v1.json`의42개 실행은 모두 PASS/exit0/owned cleanup 후 최종 입력 확인에서 CPU91.73%로 중단됐다. 이 실패를 원형 보존하며 완료한 시험을 반복하지 않는다. production·통과한 시험 본문을 보존한 `p09-361-number-topology-boundaries002.v1.json`은 추가 경계7+영향 patch13만20pass, 전체236개 입력을 전후 확인했다. 이로써 topology7/splice6/core30/stored sequence6/patch13의 서로 다른62개 component 결과를 결속했다.002의 시스템CPU최고26.70%·가용RAM최저26.2837%·Job private최고1468.02MiB이고 소유 Job 종료를 확인했다.

원본 번호 의미/재계산·전체 flow/protection·저장 topology service binding·CAS/실행/게시·Native를 수용한 결과는 아니다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·Native011 별도 승인 조건과 모든 자원 보호를 유지한다. 다음 구현은 저장 서비스의 기존 fresh access/source/Form proof와 최종 head 검사에 topology 후보를 연결하는 것이다.

## 현재 적용 범위

현재 제품 대기열의 수용 결과는 158/249이며 잔여 91개, 다음 사례는 case165다. 기존 수용 원장은 `p09-361-case164-current-epoch-accept001.v1.json`이다. 이 원장은 통과한 제품 사례를 재실행하지 않고 이전 실행 세대를 보존하며, 전체 통합 재조정은 별도 요구한다. 이 문서는 그 수용 결과를 재판정하거나 다른 환경의 결과로 승격하지 않는다.

2026-10-16 사용자가 분리 정책의 설계·검증 후 적용을 승인했다. 새 정책과 입력 합성 어댑터를 Native010 제품 실행기와 원 독립 판정기까지 연결하고 비제품 구성 자격003을 확인했다. 이후 별도 승인된 Native010 1회는 입력 잠금 중 전체 CPU90.62% 경고로 제품 프로세스 생성 전에 중단됐다. 실패/소비된 intent를 보존하고 재실행하지 않는다. 2026-10-17 사용자의 계속 진행 요청 후 목표는 ACTIVE로 확인했으며, 새 제품 시도와 별개로 읽기전용 구현을 진행한다.

반복을 먼저 제거한 대상은 고정162 전달·재구성 준비 검증이다. `tools/p09/verification_reuse.py`는 기존 `p09-361-case165-fixed162-worker-transport-g001-code002.v1.json`의 정확한 크기와 SHA-256, 결과·계약·종료 상태, 선언된 의존 파일 185개와 실제 전달 산출물을 확인한다. 모든 의존 파일이 같으면 기존 준비 결과를 유지하고 구성·복원 시험 16개를 다시 실행하지 않는다. 변경·누락·불완전 종료·자원 중단이 있으면 재사용하지 않는다.

재사용 확인에도 기존 읽기 속도 제한, 처음과 마지막의 실제 전체 바이트 읽기, 원 자원 검사와 cleanup을 유지한다. 과거 결과 파일에 들어 있는 다른 의존 목록을 재귀적으로 확장하지 않는다. 새 결과 JSON이나 캐시를 만들지 않으므로 확인을 반복했다는 이유만으로 다음 Native 입력 선언에 결과 파일이 추가되지 않는다.

## Native011 제품 대기열 준비

### 저장된 전체 번호 요청의 현재 접근 검사

`prepare_caption_sequence_candidate`는 현재 서비스 scope/head/ACL/quarantine/AEAD·전체 source/Form proof와 한 joined state를 네 요청 계열에 재사용한다. private `StoredCaptionOutput`의 closed Content/Sequence variant가 기존 fresh·writer integrity·callback 직전 head 검사를 공유한다. caller가 output 구현이나 trusted flag를 넣을 수 없고, 새 raw bytes accessor나 별도 권한 경로를 만들지 않는다. 기존 content 후보 API/receipt 형식과 모든 거부 조건을 유지한다.

bounded `NativeNumberSequenceReplacement::canonical_sha256`는 원본 joined-state와 document begin 존재/ID/지문/여섯 값, 순서 있는 모든 event ID/지문·kind·category/정수·구역 시작값·format Preserve/Replace 및22종/문자·affix·superscript를 결속한다. affix는 직렬화 전에 해싱한다. output-v2의 caller_request_sha256와 저장 후보의 요청 해시를 대조하고 기존 source node/value complete_request_sha256도 유지한다. 이 순수 요청 identity는 원본 재구성·접근 권한·Native 실행 자격을 대신하지 않는다. v1 원본 결과는 그대로 남는다.

`p09-361-stored-number-stream-components002.v1.json`은 새 저장 시험6+변경된 core 번호6+기존 stored content6=18pass·227fresh/final227이다. 두 target의 실제 전체 이름 집합과 summary를 검사했으며37인자/8290byte로 원 상한을 유지했다. 네 계열 조합/readback, no-op 포함 모든 요청 필드의 독립 해시 변화, 권한 회수·격리·암호문 변조·foreign scope·전달 직전 실제 공유 head 이동, 누락/중복/순서/kind/지문/join/보호/값/한도를 확인했다. 정상 서비스 효과는 read audit뿐이며 원본/head를 변경하지 않는다.

001은 새 import의 괄호 누락으로 시험 실행0에서 실패했다.002는 그 한 글자만 바뀐 정확한 역변환과 나머지 모든 원 입력을 대조해 같은18개를 처음 실행했다. 기존107개 core 시험과59개 서비스 시험 본문/fixture는 유지했고, 새 시험은 짧은 include로 분리했다. 실패를 보존하며 이미 통과한 하위/서비스 전체를 재실행하지 않았다. 새 경고는 없고 기존 CLI unused import 경고1건은 유지한다.

전체 sequence의 native counter 해석/재계산·제어/format 생성·삭제·전체 유효 서식/flow/protection·CAS/실행/게시·Native는 남는다. 다음은 기존 topology 제약을 제거할 번호 제어 삽입·삭제다. source API v9·일반 제품 route·Native dispatcher와 원 보호 한도는 변경하지 않았다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 원본 번호 제어 전체 요청과 원자 출력

`NativeNumberSequenceReplacement`는 exact joined-state 지문과 원본 document begin의 존재/identity, 모든 autoNum/newNum/startNum의 순서 있는 요청을 받는다. 문서·구역 시작값, 캡션 밖 제어와 캡션 내부 재시작도 빠뜨릴 수 없다. `lower_sequence_batch_candidate` 및 whole Form proof 진입점은 텍스트/layout/스타일과 같은 patch/writer/전체 출력 import를 사용하고 원본 namespace/선택자·kind·지문·요청/출력의 모든 값을 대조한다. 순서는 원본 XML 순서이며 rendered/native counter 순서로 표시하지 않는다.

숫자/boolean의 semantic no-op은00019/false 같은 원문 표기를 보존한다. 기존22종 NumberFormat과 format user/prefix/suffix/supscript 변경을 지원하며 Preserve는 기존 format을 그대로 둔다. 새 제어·format 생성/삭제나 native 재계산은 포함하지 않는다. 출력 receipt는 전체 요청과 원본 노드/요청 값의 지문을 결속하며 서식 평문은 Debug/직렬화 receipt에 넣지 않는다. 번호와 스타일의 ancestor/subtree 보호 map을 공유하므로 한 part에128번호+64스타일+64텍스트 요청도4N 순회다.

공통 속성 escaper는 탭/개행/CR을 문자 참조로 기록한다. literal whitespace와 character reference의 의미 차이는 [XML 1.0 속성 정규화](https://www.w3.org/TR/xml/#AVNormalize)에 따른다. 원 SafeXml 정규화·보안 parser는 변경하지 않았다. 양쪽 quote·특수 문자·whitespace를 독립 재수입한 format 지문과 비교한다.

`p09-361-number-stream-content-components001.v1.json`은 새6+영향37=43pass·221fresh/final221이다. 한 Cargo graph의 core30/source1/stored12이며64인자/14974byte로 원 상한을 유지했다. 기존101개 core 시험 본문은 include 제거 역변환으로 대조했다. `p09-361-number-stream-attribute-regressions001.v1.json`은 별도 core graph의 기존 patch13pass·222fresh/final222다. `p09-361-number-stream-warning-compile002.v1.json`은 새 unused import만 제거한 exact inverse와 시험 미실행 compile-only·223fresh/final223을 확인했다. 각 scope의 원본 결과를 유지하며 합쳐서 제품/Gate PASS로 표시하지 않는다.

원본 compiler 단계에서는 source API v9·저장 content wrapper와 일반 route를 변경하지 않았다. 전체 번호 요청의 fresh 저장 서비스 연결은 위 후속 단계에서 완료했으며 실제 counter 해석/재계산·구조 추가/삭제·전체 유효 서식/flow/protection·CAS/실행/게시·Native는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 저장 서비스의 캡션 content 후보

`StoredImportedDocumentForms::prepare_caption_content_candidate`는 세 요청 계열을 현재 서비스 원본·한 operation-local Form proof·한 joined state에 결속한다. 스타일 요청은 source caption/node ID, family, 원본 header의 선언 ID·지문과 변경/no-op 여부를 포함한다. 텍스트/layout 요청 대조는 기존 `request_bindings_match`를 공유하며 기존 후보 API/receipt 형식과 오류·거부 조건을 유지한다. 모델과 원본을 요청별로 다시 수입하지 않는다.

매 prepare/verify/바이트 전달은 현재 scope/head/ACL/quarantine/AEAD·전체 원본 재구성을 확인한다. writer가 바이트를 확인한 후 consumer를 호출하기 직전에 head를 한 번 더 읽는다. 시험 전용 repository가 이 마지막 읽기에서 실제 공유 in-memory head를 전진시킨 경우에도 consumer는 호출되지 않았다. 정상 동작의 서비스 효과는 metadata/download read audit뿐이며 source/head 변경·ingest/commit/게시가 없다. 이 fresh 확인은 atomic CAS나 보관된 평문 접근 권한이 아니며 실행/게시 route는 계속 거부한다.

`p09-361-stored-caption-content-components001.v1.json`은 새6+영향받는 기존 mixed6=12pass·212fresh/final212·cleanupTrue다. 권한 회수/격리/변조/head 이동/foreign scope·원본·state·proof·bytes와 중복/잘못된 family/미선언/보호/no-op/한도를 확인했다. 기존53개 시험 본문은 include를 제거한 정확한 역변환으로 대조했다.002는 새 unused import만 제거한 compile-only이며213fresh/final213·시험 실행0이다. 실제12개 시험과 기존 경고1건을 보존했다.

이전62개 범위 중 helper 변경의 영향을 받는 stored mixed6개는 재검증했고56개는 원 범위·입력 근거를 유지했다. 새6개를 더하면 범위별 서로 다른 component68개이지 제품 대기열68개가 아니다.001의 `retained_core_and_style_scope62_without_reexecution` 필드는 이 영향을 구분하지 못하므로 그대로 해석하지 않는다.003 최종 closure가 실제 사례 이름 집합과 현재 source 핀을 대조해 이 범위를 교정한다. 근거: `p09-361-stored-caption-content-closure003.v1.json`.

P09 roadmap의 원본 보존/재현 가능한 산출물/실제 수행 범위를 유지한다. source API v9와 일반 typed 제품 route는 바꾸지 않았으며 전체 sequence·번호 재계산·유효 서식·flow/protection·CAS/실행/게시·Native는 미완료다. 원본 번호 제어의 전체 관측 순서 요청/저장값 출력은 위 후속 단계에서 연결했으며 저장 서비스 연결은 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 캡션의 선언된 스타일 참조 출력

`ImportedCaptionSourceState::lower_content_batch_candidate`와 whole Form proof의 `lower_caption_state_content_batch_candidate`는 텍스트/layout/문자·문단·이름 스타일 참조를 한 원본·한 transaction·한 출력으로 처리한다. 정확한 원본 객체/한도/fresh bytes와 원본 header의 유일한 선언 지문을 요구하며 유효/상속 서식을 계산하지 않는다. frame 조립 중 한 번 만든 선언 인덱스를 보유하므로 요청마다 header/ZIP/XML을 다시 읽지 않는다. 기존 text/layout API와 receipt 형식은 유지하고 새 content receipt가 모든 스타일 요청 수와 변경 결속을 포함한다.

`InsertUnsignedAttributes`는 누락된 unqualified ASCII 이름의 u32 속성들을 정렬해 한 위치에 삽입한다. namespace 선언/주입 이름/기존 속성 덮어쓰기/빈 묶음/한도 초과/겹치는 intent를 거부한다. 같은 문단의 빠진 두 속성도 한 번 삽입하며 기존 overlap 규칙을 완화하지 않는다. 스타일 변경은 ancestor와 descendant 보호를 part별 두 번의 순회로 각각 확인한다. 96개 스타일 요청에서 보호 순회는 한 part의4N이며 원본 text/layout의 보호 조건은 변경하지 않았다.

`p09-361-caption-style-content-components001.v1.json`의43개 중41개가 통과했고 두 합성 fixture가 실패했다. unknown namespaced ID형 속성과 caption 내부 지원 밖 중첩 개체에 대한 기존 거부는 유지했다. 정상 namespace flag/지원되는 표 조상 fixture로 고친 두 사례만 `p09-361-caption-style-content-components003.v1.json`에서2pass했다.002는 reader 역변환 경계 오류로 steps0이며 원본을 보존한다.003은 production/기존37개/새4개 통과 본문이 그대로인 정확한 역변환과206fresh/final206을 확인했다. 첫43개는 두 package feature-union graph, 후속2개는 core-only graph의 범위이며 단일43개 동일 graph 결과로 표시하지 않는다.

후속 `p09-361-caption-style-content-regressions001.v1.json`에서 수정 없는 기존 patch13/frame6 사례19pass·209fresh/final209·cleanupTrue다. component 총62개는41개 유지+실패2개 수정 후 통과+영향19개이며 제품 대기열 수용은 아니다. 기존 single-Cargo helper의 허용 target은 넓히지 않았다. 공통 patch 영향 시험은 별도 명시한4개 core target/정확한19개 이름·완전한 그룹/summary를 기존 보호 실행기로 검증했다. 자원 수치는 CURRENT_STATE.md와 원장에 있다.

source API v9와 실행/게시 route는 그대로이며 저장 서비스의 content 후보는 위 후속 단계에서 fresh 접근 검사에 연결했다. 유효 서식/sequence/번호 재계산·전체 flow/protection·CAS/실행/게시·Native는 미완료다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 정확한 component 사례의 단일 Cargo 빌드 graph

`tools/p09/component_cargo_batch_v1.py`는 검증한 component target 세 개만 허용한다. `command(cargo, spec)`의 spec은 target별 정확한 사례 ID 목록이며 두 package와 세 integration target을 한 Cargo 호출로 선택하고 `--exact` 사례를 전달한다. source/범위는 기존 AcceptanceReader로 처음과 마지막에 확인하고, 실행은 기존 owned launcher·guard·한 코어·BelowNormal·RAM/commit95%·단일 시험 스레드·capture32768을 사용한다. helper 자체는 프로세스를 생성하지 않는다. 인자64개/UTF-16 24000byte 상한을 넘으면 분할 설계 없이 조용히 넓히지 않고 거부한다.

완전한 출력은 `validate_stdout(output, spec)`으로 대상별 사례 집합·개수·성공 summary까지 대조한다. 빠진/추가/중복/부분/실패/ignored 결과나 요약만 맞춘 결과는 PASS가 아니다. [Cargo의 다중 package feature union](https://doc.rust-lang.org/cargo/reference/resolver.html#features)은 별도 빌드 범위이므로 기존 개별 package 결과를 그대로 승격하지 않는다. 새 graph에 대한 자격을 얻은 뒤 같은 source/scope에서만 사용하며 Native 입력·실행·대기열 수용과는 별개다.

`p09-361-component-cargo-batch-qualification001.v1.json`은 순수 계약15+실제 동일37(core24/source1/stored12)pass·201fresh/final201·cleanupTrue다. 실제 시험은 한 Cargo 호출·58인자/12166byte로 수행했다. 뒤의 같은 graph `no_run=True` 준비 관측은 재컴파일 공지0·시험 실행0이었다. 원 Rust/시험 본문·기존 실행기/Native dispatcher·경고1건은 보존했다. 자원 상세는 CURRENT_STATE.md와 원장에 있다. 단일 package compile 공지1과 warm 준비1.734초는 전체 cold build 속도 배율이나 rustc unit 개수의 증거가 아니다.

이후 이 세 target의 허용된 선별 범위에는 위 helper를 기존 보호 실행기와 함께 사용한다. 새 입력은 다시 fresh 확인하고 실패/부분/다른 scope를 재사용하지 않는다. 다른 core71/CLI40/서비스/249제품·대형 binary·한글/COM/Native는 실행하지 않았다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 조립한 원본 상태의 출력 compiler 입력 재사용

`ImportedCaptionSourceState::lower_edit_batch_candidate`와 whole Form proof의 `lower_caption_state_edit_batch_candidate`는 같은 원본 객체·조립 입력 한도·fresh bytes를 결속한 후 기존 numbering/frame을 빌려 쓴다. 다른 객체나 더 작거나 큰 입력 한도는 재사용하지 않는다. fresh whole-source 또는 exact operation-local Form proof가 필수이며 전체 출력 import/readback·원 보호/오류·선택 밖 byte 검증은 유지한다. private 후보는 joined source receipt와 실제 출력 receipt를 함께 보유한다. 큰 lowering 본문은 proof callback 종류와 무관한 비제네릭 함수 하나로 분리했다.

`p09-361-caption-source-state-compiler-components002.v1.json`은 새6+영향 core18+stored mixed6/text6+실제 API1=37pass·198fresh/final198·cleanupTrue다. 기존 모델/compiler 본문/core89개 시험은 정확한 역변환으로 보존했다.001은 빌드 전 reader의 말미 빈 줄 검색 실패(steps0)로 보존했다. 새 시험을 support 파일과 짧은 include 선언으로 분리해 원본문 전체 대조의 경계를 고쳤으며 시험 조건/production 코드는 그대로다. 기존 unused import 경고1건도 보존했다. 다른 core71/CLI40/서비스/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다.

검증 시간은 큰 두 빌드 단계가 대부분이다. 최근 두 라이브러리 산출물은 같은 자체 profile/features에서도 의존성 지문이 달랐으며 이는 후속 빌드 재사용 설계의 관측일 뿐, 원인 전체나 속도 개선 자격은 아니다. 자원 상세는 CURRENT_STATE.md와 원장에 있다. 입력 모델 재사용을 접근 권한 캐시·전체 sequence/state·번호 재계산·flow/protection·CAS/실행/게시·Native 자격으로 승격하지 않는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 원본 캡션 상태 조립과 실제 평가 연결

`ImportedCaptionSourceState`는 한 원본 numbering/caption 모델을 소비해 문서/소유 맥락·frame·본체 지문을 조립한다. 모든 owner/caption/envelope/frame/body 인덱스와 번호 제어의 section/spine/XML 위치를 대조하며 누락/중복/불일치는 부분 결과 없이 거부한다. 추가 ZIP/XML/graph 재수입이나 개체마다 전체 컬렉션 재검색은 하지 않는다. 실제 평가 API/CLI는 이 조립 상태의 기존 모델을 사용하고 v9 응답·receipt·incomplete/미해결4/report=null/exit3를 유지한다.

`p09-361-caption-source-state-assembly-components001.v1.json`은 새6+영향 API/CLI41=47pass·194fresh/final194·cleanupTrue다. 기존 core83/CLI41 시험과 원 모델은 변경하지 않았고 root/API scoped 역변환으로 대조했다.10종 개체·캡션 없는 개체·missing/NONE·0/19·ZIP 역순과 실제 spine·중복 native ID·캡션 내부 재시작·복잡한 frame·fresh drift·128owner/64caption/192event 연결을 확인했다. 하위 compiler/저장 서비스/다른 core83/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다. 자원 상세는 CURRENT_STATE.md와 원장에 있다.

이 조립은 원본 관측의 정확한 관계를 제공하며 기존 typed v1의 단일 label/시작값/연속 또는 구역별 restart로 강제 변환하지 않는다. 공식 [num 입출력 모델](https://raw.githubusercontent.com/hancom-io/hwpx-owpml-model/1453388472c703a4b299a0834f425cdac16644b9/OWPML/Class/Para/AutoNumNewNumType.cpp)은 재계산 알고리즘 자격이 아니며, [구역 도움말](https://help.hancom.com/hoffice120/ko-KR/Hwp/format/section/section.htm)은 구역 시작과 구역 안의 임의 재시작을 구별한다. 전체 sequence/state 요청·출력 compiler·전체 보호·CAS/실행/게시·Native는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 저장 원본 캡션의 텍스트와 layout 조합 검증

`prepare_caption_edit_batch_candidate`는 현재 원본의 scope/head/ACL/quarantine/AEAD·전체 Form proof 한 번을 공통 compiler의 두 요청 계열에 재사용한다. 모든 변경/no-op 텍스트는 source caption/text ID·SHA·UTF-8 길이로, layout은 source caption ID·다섯 요청 값·변경 여부로 결속한다. 매 verify/바이트 전달은 현재 원본/접근을 재확인하고 writer callback 안에서 마지막 head를 검사한다. 정상 경로는 read audit만 발생시키며 원본/head·평문 비공개를 유지한다. 실행/게시 route는 계속 거부하며 서비스 CAS가 아니다.

`p09-361-stored-caption-edit-batch-output-components001.v1.json`은 새6개만6pass/기존47filtered·192fresh/final192·cleanupTrue다. 두 요청 계열의 변경/no-op·전체 출력 readback·반복 fresh 확인과 권한 회수/격리/변조/head 이동/foreign scope·원본·proof·bytes 및 잘못된 혼합 요청의 부분 출력 없는 거부를 확인했다. 기존 provider/47개 시험은 정확한 역변환으로 보존했고 하위 compiler19/core83/source CLI41/다른 서비스/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다. 기존 unused import 경고1건도 보존한다. 자원 수치는 CURRENT_STATE.md와 원장에 있다.

격리된 저장소·fixture scanner·합성 key의 component 결과이며 실제 issuer/scanner·전체 상태/번호 체계·전체 보호·CAS/실행/게시·Native는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 캡션 텍스트와 layout의 원자적 출력 조합

`lower_caption_edit_batch_candidate`는 여러 원본 캡션의 단순 텍스트와 다섯 layout 속성을 원본 검증·number/frame 모델·patch/writer·전체 출력 재수입 각 한 번으로 처리한다. 중간 패키지를 재수입하는 연쇄 편집이 아니다. 기존 text batch API/receipt는 공통 compiler에 위임하되 유지한다. 선택 밖 byte/part·번호 제어·원본은 보존하고 하나라도 invalid/duplicate/foreign/protected/limit이면 전체 후보를 거부한다. 메모리 후보 생성의 원자성이며 서비스 CAS·실행 권한이 아니다.

`p09-361-caption-edit-batch-output-components003.v1.json`은002의 새6+영향 text6+stored6+source API1=19pass를 재실행 없이 보존하고190fresh/final190·cleanupTrue로 마감한다.001 reader 줄바꿈 실패는 steps0,002는 세 명령 exit0·19pass 뒤 tuple/list 비교에서 실패했다.003은 원 기록·무손실 자원 표본·동일한 현재 소스/입력·세 Job 종료를 독립 확인한다. 경고1건은 원 stored 시험의 기존 unused import다. 나머지 core71/CLI40/다른 서비스/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다.

기존 단일 text/layout 출력과의 대조, layout 보호64조합·내부 보호 table/cell/size·여러 part·exact Form proof·lexical no-op·원본 번호19 보존이 통과했다.192요청(text128/layout64)은 part 하나의 네 번 요소 순회를 공유하고 역순 expanded 출력도 같다. 자원 수치는 원002에 있으며 속도 배율이나 프리즈 해결로 해석하지 않는다. 당시 남았던 저장 서비스 결속은 위의 저장 조합 component로 이어졌으며 전체 상태/번호 체계·전체 보호·CAS/실행/게시·Native가 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 실제 평가 API와 CLI의 캡션 frame 연결

실제 원본 평가 v9는 `caption_frame_import`와 `caption_frames`를 반환한다. 기존 numbering/caption 모델에서 frame을 조립하며 추가 ZIP/XML/graph import를 하지 않는다. 문서 시작·소유 개체·번호 제어·캡션 본체 지문과 같은 원본에 결속한 ID로 단순 텍스트 batch 후보를 만들고 출력을 다시 평가한다. 요청 내용·저장 번호19·본체 보존을 확인했으며 label/separator·계산 번호·유효 서식/sequence를 추측하지 않는다. CLI는 평문 없이 frame과 지문만 출력하고 incomplete·미해결4단계·validation_report=null·exit3를 유지한다.

`p09-361-source-caption-frames-cli-components001.v1.json`은 영향 기존38개+새3개=41pass·186fresh/final186·cleanupTrue다. 기존 v8 구현과38개 시험은 schema 기대7곳 외 정확한 역변환으로 보존했다. 서식의 누락/미선언/중복/잘못된 위치 구분, 잘못된 ID의 부분 출력 없는 거부, 실제 CLI/API 일치·원본/비밀 보호·최종 JSON 한도를 확인했다. 하위 frame/batch/저장 시험·249제품·대형 binary·한글/COM/Native는 재실행하지 않았다. 자원 상세는 CURRENT_STATE.md와 원장에 있다.

전체 caption state/sequence/compiler·전체 보호·서비스 CAS/실행/게시·Native는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 저장 원본의 캡션 텍스트 묶음 접근 검증

`prepare_caption_text_batch_candidate`는 현재 scope/head/ACL/quarantine/AEAD와 전체 Form 재구성을 묶음당 한 번 수행하고 동일 원본 proof로 pure batch를 생성한다. 모든 변경/no-op 요청의 source caption/text ID·SHA·UTF-8 길이·변경 여부를 결속한다. 후보 verify/바이트 전달은 매번 fresh 원본 검증을 수행하며 writer callback 안에서 마지막 head를 확인한다. 요청 평문은 receipt/Debug에 남기지 않으며 실행/게시 route는 fresh 확인 뒤에도 거부한다. 메모리 후보 생성 외 ingest/commit·원본 변경·서비스 atomic CAS는 없다.

`p09-361-stored-caption-text-batch-output-components001.v1.json`은 새6개만6pass/기존41filtered·185fresh/final185·cleanupTrue다. 정상 변경/no-op 결속·반복 fresh 노출·원본/head 보존·read audit만 발생함을 확인했다. 접근 회수·격리·변조·head 이동·foreign scope/proof/bytes와 잘못된 묶음은 부분 출력 없이 거부한다. 기존 module/시험 원문은 정확한 역변환으로 보존했고 통과한 pure batch6/단일9/저장6/sourceCLI38/원 core71/제품41/249제품은 재실행하지 않았다. 자원 상세는 CURRENT_STATE.md와 원장에 있다.

격리된 저장소·fixture scanner·합성 key의 component 결과다. 실제 issuer/scanner·서비스 CAS·전체 caption state/sequence/compiler·전체 보호·CLI/실행 연결·Native는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 여러 캡션 텍스트의 단일 출력 후보

`lower_caption_text_batch_candidate`는 원본 검증·number/frame 모델·patch/writer·전체 출력 재수입을 묶음당 한 번 수행한다. 원본 anchor index와 subtree 지문으로 선택하고 관측 보호 조건은 변경 part별 두 번의 요소 순회로 계산한다.128 leaf도 같은 XML guard를 한 번만 만들며, 의미가 같은 항목은 원 lexical byte를 보존한다. 중복/foreign/보호/값/한도 실패는 전체 후보를 거부한다. 원본은 덮어쓰지 않으며 이 원자성은 메모리 출력 후보 생성에 한정되고 서비스 atomic CAS가 아니다.

`p09-361-caption-text-batch-output-components006.v1.json`은001의5pass+006의수정1pass·183fresh/final183·cleanupTrue다. 128개 보호 조건은 기존 단일 경로와 대조했고 여러 section, source-bound Form proof, 요청 순서 독립 결과, 선택 영역 밖의 정확한 byte 보존을 확인했다. 원 제품 코드는 변경하지 않고 시험 자료와 추가 admission 기대만 수정했다. 원 실패001/002/004/diagnostic005 및 reader-only003(steps0)은 보존했다. 원 단일9/저장6/sourceCLI38/원71/제품41/249 대기열은 재실행하지 않았다. 자원 수치는 CURRENT_STATE.md와 원장에 있으며, 작업량 감소를 PC 프리즈 원인 해결이나 속도 배율로 해석하지 않는다.

이 pure batch 검증 당시의 서비스 결속은 위의 저장 묶음 component로 이어졌다. CLI 결속·전체 caption state/sequence/compiler·전체 보호·Native는 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 저장 원본 캡션 텍스트 후보의 접근 검증

`prepare_caption_text_candidate`와 후보의 verify/바이트 전달은 매번 현재 scope/head/ACL/quarantine/AEAD 및 전체 원본/form 재구성을 확인한다. 준비 단계는 그 original-bound proof를 재사용하며, 전달은 writer 무결성 확인과 callback 내부 마지막 head 검사 뒤에만 실행한다. 요청은 source caption/text ID·SHA/UTF-8 길이로 결속하고 평문을 receipt에 저장하지 않는다. 보관한 후보나 pure proof는 접근 권한·atomic CAS가 아니다. 서비스 변경은 정상 metadata/download read audit뿐이며 ingest/commit/게시·원본 덮어쓰기는 없다.

`p09-361-stored-caption-text-output-components001.v1.json`의 새6개만6pass/원35filtered·176fresh/final176·cleanupTrue다. 권한 회수·격리·변조·head 이동·foreign scope/proof/bytes에서 callback이 호출되지 않음과 원 selector/보호/값/no-op/한도 거부를 확인했다. 이전 출력9/sourceCLI38/기존35/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다. 자원 상세와 최신 요약은 CURRENT_STATE.md 및 이 원장에 있다.

격리된 메모리 저장소·fixture scanner·합성 key의 component 결과이며 실제 issuer/scanner·전체 caption state/sequence/compiler·전체 보호·Native 자격은 아니다. 실행 route는 fresh 확인 뒤에도 거부한다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 선택한 원본 캡션 텍스트의 출력 후보

`lower_caption_text_candidate`는 정확한 caption/text source ID 쌍으로 한 단순 hp:t만 바꾼다. caller offset/숫자 ID·추측한 label 구간을 받지 않으며 원 ReplaceLeafText·shape v6 ID 검사·보존 patch/writer를 재사용한다. 전체 출력 source/number/frame을 다시 가져와 요청한 의미 텍스트와 선택 leaf 밖의 정확한 expanded bytes를 대조한다. self-closing leaf는 원 QName/속성을 유지해 열고 닫으며 의미가 같은 no-op는 원 lexical byte를 보존하도록 거부한다. 원본 파일은 덮어쓰지 않는다.

CR이 LF로 바뀌지 않도록 leaf 경로에서만 문자 참조로 출력하며 일반 text/attribute escaping은 그대로다. 기존 leaf2+새 CR1/caption 출력6의9pass·174fresh/final174·cleanupTrue, 근거는 `p09-361-caption-text-output-components001.v1.json`이다. 전체61.531초·소유33.687/2.906초·시험0.10/0.50초·Job CPU18.578/2.469초·최고1398.11/547.86MiB·시스템CPU최고24.67%·가용RAM최저25.9173%였으며 원 자원 보호·무손실 표본·두 Job 종료 정리를 유지했다.

원 structure/output/leaf 코드의 정확한 역변환·원 core65 전체 prefix, Unicode/entity/namespace·빈 leaf·번호/서식/다른 내용/part 보존, drift/foreign/opaque/번호 selector·관측 잠금/표 보호·중복 ID·한도 거부를 확인했다. 정확한 Form reconstruction 재사용 경로는 추가 원본 ZIP/XML/graph import 없이 foreign proof/bytes를 거부한다. 원 사각형 메모리 후보에서 저장된19와 원본 파일도 보존했다.

전체 caption state/sequence/compiler·전체 보호·서비스 실행/게시·Native/저장/렌더는 남는다. CLI v8/원 core65/sourceCLI38/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격은 변하지 않는다.

### 캡션 본문 서식 번호 제어의 원본 입력

`ImportedCaptionNumbering::import_frames`는 한 원본 모델의 caption/subList/p/run 구조와 번호 제어를 결속한다. 직접 run의 단순 hp:t만 문자 참조·줄바꿈 처리 후 원래 순서와 공백을 보존하며, label/separator를 추정해 분리하지 않는다. XML 원문의 CRLF/CR을 LF로 정규화한 후 문자 참조를 확장하므로 `&#13;`의 CR은 보존한다. 이 처리는 [W3C XML 1.0의 줄바꿈 규칙](https://www.w3.org/TR/xml/#sec-line-ends)에 따른다. 복잡한 텍스트·주석·혼합 구조·복수 문단/번호·foreign 내용은 단순 번호줄로 승격하지 않는다.

문단/character/named 서식 참조는 실제 header 선언과 source anchor 지문으로 결속하고 누락/미선언/중복/잘못된 위치를 구별한다. 일치한 선언도 상속/유효 폰트·Native 의미 자격은 아니다. 평문은 명시적 원본 snapshot getter에 한정하고 Debug/직렬화 관측에는 지문만 반환한다. XML token은 part별 한 번 분류하고, 서식과 기존 numbering/caption 모델을 재사용해 캡션별 ZIP/XML/graph import·전체 token 검색·서식 재파싱을 하지 않는다.

`p09-361-caption-source-frames-components001.v1.json`의 새6개만6pass/원59filtered·171fresh/final171·cleanupTrue다. 전체89.844초·소유65.735초·시험0.19초·Job CPU21.203초·최고1396.21MiB·시스템CPU최고39.18%·가용RAM최저26.2586%였으며 원 자원/종료 보호를 유지했다. 기존 코드의 정확한 역변환·원59개 전체 prefix, 표/주석·실제 spine 순서·중복 native ID·본문 번호 제어와의 구분·원 사각형의 저장된19·한도/fresh drift를 확인했다.

실제 CLI v8·기존 source CLI38/context/projection/index/layout/저장/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다. 전체 typed state/sequence·번호 계산·출력 compiler·flow/protection·Native는 남으며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격은 변하지 않는다.

### 원본 번호 맥락과 본체 지문의 실제 제품 출력

실제 원본 평가 API/CLI v8은 문서 시작 번호·캡션 없는 개체를 포함한 소유 관계·실제 spine/XML 제어 순서·캡션을 제외한 본체 지문을 반환한다. 한 원본 numbering/caption 모델과 source graph를 재사용하고 추가 ZIP/XML/graph import는 하지 않는다. 기존 field/security coverage와 legacy target/caption/numbering/SDK receipt를 유지하며 알려지지 않은 번호 종류·0·저장된19를 추정한 값으로 바꾸지 않는다. 정상 응답은 incomplete·미해결4단계·validation_report=null·exit3다.

`p09-361-source-caption-context-cli-components001.v1.json`은 새3개+변경 영향 원35개의38pass·169fresh/final169·cleanupTrue다. 출력 schema가 바뀌므로 원본 평가의35개만 다시 확인했고 하위 core/context/projection·직접 제품35/index54/layout/저장/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다. 원 v7 코드와 시험 전체는 schema 기대6곳 외 정확한 역변환으로 대조했다. 잘못된/중복/숨은 문서 시작·지원 밖 번호 소유 개체의 무출력 거부, 정상 원본 파일 보존, 정확한 JSON 한도와 private 값 비노출도 확인했다.

전체91.625초·소유66.094초·시험3.22초·Job CPU25.750초·최고1399.24MiB·시스템CPU최고21.09%·가용RAM최저26.4718%였으며 원 한 코어/BelowNormal/CPU cap6.25%/RAM·commit95%·무손실 표본·종료 보호를 유지했다. 전체 typed 상태·번호 계산·flow/protection·일반 compiler·Native는 남으며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격은 변하지 않는다. 다음은 캡션 본문/서식과 번호 제어의 typed sequence/state 조립이다.

### 캡션과 분리한 개체 본체 지문

`ImportedNumberingContext::project_object_states`는 기존 캡션 subtree만 고정 marker로 대체하고 본체의 나머지 원문·해석된 namespace·캡션 위치/존재를 해싱한다. 원 전체 캡션 envelope는 별도로 유지하고 marker 내부 변경도 전체 원본 fresh 검증에서는 거부한다. 중첩 개체는 한 번 계산한 child digest를 재사용한다. 깊이4/6/8에서 요소당 지문1회·원문 해싱량≤해당 XML 크기를 확인했으며 새 graph/ZIP/XML import나 subtree 복사는 없다. 원 import의 별도 중첩 지문 계산을 바꾼 결과는 아니다.

새6개는 `p09-361-caption-object-state-projection-components002.v1.json`의4pass를 보존하고 `p09-361-caption-object-state-projection-components003.v1.json`에서 실패2개만 통과했다. 001의 비공개 함수 접근 컴파일 오류와002의 PI/과도한 깊이 합성 자료 실패는 보존했다. 입력 보안/깊이 한도·production 코드·먼저 통과한4개는 변경하지 않았다.003은168fresh/final168·cleanupTrue·전체25.953초·소유1.954초·시험0.05초·Job CPU1.828초·최고544.24MiB·시스템CPU최고72.66%·가용RAM최저29.0199%다. 한 코어·BelowNormal·CPU cap6.25%·RAM/commit95%·무손실 표본과 종료 보호는 유지한다.

이 projection은 기존 캡션 편집에 안정적인 본체 식별자이며 캡션 추가/삭제·전체 typed 상태/번호 계산·flow/protection·일반 compiler·Native 자격은 아니다. source CLI v7·공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격은 유지한다. 원 core53/sourceCLI35/index54/249제품·대형 binary·한글/COM/Native는 재실행하지 않았다.

### 문서 시작 번호와 개체 전체의 원본 맥락

`ImportedCaptionNumbering::import_context`는 문서 `beginNum`의 여섯 명시값과 캡션이 없는 개체를 포함한 10종 소유 개체를 원 graph에 결속한다. `numberingType` 누락과 명시적 `NONE`을 구분하고 실제 spine/XML 순서로 개체·번호 제어를 정렬한다. 0의 의미·native 렌더 순서·카운터 전이는 추정하지 않는다. 원 import와 anchor 지문을 재사용하며 지원 밖 번호 개체·잘못된 header 위치·한도·source drift는 거부한다.

새 6개만 통과했고 기존 47개는 filtered다. 164fresh/final164·cleanupTrue, 근거는 `p09-361-numbering-document-owner-context-components001.v1.json`이다. 전체107.500초·소유84.235초·시험0.12초·Job CPU44.562초·최고1855.35MiB·시스템CPU최고31.82%·가용RAM최저26.4467%였으며 원 자원 보호와 종료 정리를 유지했다. 이전 core47/sourceCLI35/index54/249제품·대형 시험 binary·한글/COM/Native는 재실행하지 않았다.

원 subtree 지문은 캡션 변경에 안정적인 typed object-state projection이 아니다. 전체 sequence/state/compiler·mutable projection·flow/protection·Native는 남고 CLI v7와 false 자격 flag는 유지한다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE·Native011 별도 승인/현재 입력 자격은 변하지 않는다.

### 캡션 전체 상태 검사의 일회성 색인

validate_caption_state는 source 전체 개체/sequence/구역을 한 번 borrowed index로 만들고 각 caption에서 tree lookup을 재사용한다. 객체의 section 존재 검사와 번호 계산도 같은 색인을 쓴다. 잠금 보존은 target sequence/caption의 find-first map, 기존 source/target-by-object의 last-entry map과 변경된 section 집합을 사용해 반복 전체 검색을 없앤다. counter key는 sequence ID를 참조하며 반복 clone을 하지 않는다. 색인은 operation-local이고 원 canonical state/flow/plan/projection 검사를 건너뛰거나 권한을 보관하지 않는다.

원 validation/counter/lock 구현을 cfg(test) oracle로 보존했다. 원 전체 파일의 scoped 역변환을 대조하고 1,555개 작은 source 변형과 역순,512개 잠금 mask×8개 target 변형을 비교했다. missing/ambiguous selector·stale cache·기존 overflow 오류·입력 JSON bytes·find-first와 last-entry map의 차이도 보존했다. 8,192개 private counter 입력에서 index record+caption visit16,388회를 확인했다. 이는 BTreeMap 조회와 sort의 log 비용을 제외한 방문 횟수이며 큰 입력의 full typed/native 수용이나 실행 시간 선형성 주장이 아니다. 큰 입력으로 느린 원 oracle를 다시 돌리지는 않았다.

evidence/p09-361-caption-index-optimization-components001.v1.json은 새4+원 sealed-plan1/domain14/직접 제품35의54pass·159fresh/final159·cleanupTrue다. 전체349.656초·소유84.422/24.453/215.204초·시험1.23/0.09/0.56초, Job CPU18.484/23.141/52.578초·최고1536.72/1855.00/1869.82MiB·시스템CPU최고80.66%·가용RAM최저25.6854%다. 원 한 코어/BelowNormal/CPU cap6.25%/RAM·commit95%/종료 보호와 lossless 전체 표본은 유지했다. 빌드 대기와 PC 프리즈 원인 해결로 승격하지 않는다. source CLI35·번호6·layout/service·직렬화3·cycle701·249제품·대형 form_stored_provider binary·한글/COM/Native는 재실행하지 않았다. 다음은 source 번호 제어의 typed state/compiler 연결이며 공식158/249·잔여91·P09 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 원본 번호 제어와 실제 CLI 응답

ImportedCaptionNumbering은 autoNum/newNum/startNum의 실제 원본 값과 section/caption 소속을 가져온다. 표현된 문단 또는 정확한 caption/subList/p/run/ctrl 관계에 결속하고 header/nonspine/opaque/잘못된 ancestry의 native 제어를 전체 XML 검사에서 거부한다. 필수 속성 누락·잘못된 enum/수/boolean·중복 format/start·종류/문자열/구역/출력 한도를 거부한다. 7개 native category와 공식22개 format을 읽고 기존 domain format7개 외에는 대응을 추측하지 않는다. raw affix/user 문자열은 hash만 반환하며 원 지문을 재사용하고 caption별 재파싱은 없다. startNum의0과 autoNum의 signed INT는 관측값이지 실제 번호 계산 결과가 아니다.

구역 시작과 구역 중간 재시작은 서로 다른 제어다. [한컴 구역 설정 설명](https://help.hancom.com/hoffice120/ko-KR/Hwp/format/section/section.htm)은 구역 안에서도 개체 번호를 다시 시작할 수 있음을 설명한다. native num/numType·format 속성·startNum 어휘는 고정된 official-source-cache의 AutoNumNewNumType.cpp/h, AutoNumFormatType.cpp, startNum.cpp, SectionDefinitionType.cpp, enumdef.h에 결속했다. 이 자료와 저장된19를 구역별/연속 sequence 또는 재계산된1의 증거로 승격하지 않는다.

reference-source v7는 numbering_import/numbering_controls/numbering_section_starts를 추가한다. 번호 importer가 기존 caption 모델도 보유해 CLI가 다시 caption import를 하지 않으며 기존 target/caption/SDK receipt와 field/security 검사를 유지한다. sequence_interpretation_qualified/native_recalculation_qualified/complete_auxiliary_state_qualified는 false다. 응답은 계속 incomplete·미해결4단계·validation_report=null이다.

core6와 영향받은 API/실제 CLI35의41개 범위를 확인했다. schema 기대5곳 외 원32개 시험과 v6 API 코드의 역변환을 대조했다. standalone 구역 한도 보강에는 해당 core1개만 확인하고 core5/CLI35는 보존했다. evidence/p09-361-source-caption-numbering-section-limit-components004.v1.json은158fresh/final158·cleanupTrue이며001 core/002 CLI와 steps0 사전 경로 판정 오류003을 보존한다. 41개 동시 재실행 결과로 쓰지 않는다. 이전 layout/service/auxiliary/249제품·대형 form_stored_provider binary·한글/COM/Native는 재실행하지 않았다.

core001/CLI002/한도004는 전체41.140/48.016/57.859초·소유19.110/26.047/35.234초·시험0.11/2.02/0.01초, Job CPU17.641/23.453/18.594초·최고1371.65/1383.20/1373.27MiB다. 시스템CPU 묶음최고62.30%·가용RAM최저29.8439%였고 원 한 코어/BelowNormal/6.25% cap/RAM·commit95%/cleanup을 유지했다. 새 component receipt만 lossless_columns_v1로 반복 key를 묶고 모든 자원 표본·값·순서의 roundtrip을 확인했다. 보호 표본이나 Native 정책을 줄이지 않았다. 다음은 번호 제어의 typed sequence/state/compiler 결속이며 공식158/249·잔여91·P09 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 저장 원본에 결속된 캡션 배치 출력 후보

StoredImportedDocumentForms.prepare_caption_layout_candidate는 원 서비스의 fresh source/head/ACL/quarantine/AEAD/전체 form 재구성을 통과한 뒤 배치 출력을 만든다. VerifiedFormReconstruction.lower_caption_layout_candidate는 원 original pointer와 supplied fresh bytes를 결속해 이미 검증된 재구성을 재사용한다. 두 번째 원본 ZIP/XML/graph import는 없고, 기존 순수 lowerer의 원 verify_source 및 배치/ID/보호/patch/writer/전체 출력 readback은 같은 private 경로에 그대로 남는다. caller 검증 flag나 graph, deserialize된 proof를 받지 않는다.

PreparedStoredCaptionLayoutCandidate.verify/with_verified_bytes는 매번 원 서비스에서 전체 원본을 새로 읽고 재구성한다. immutable 후보와 source/output receipt를 대조하며 writer integrity 확인 후 callback 내부에서 마지막 head를 검사한다. ACL 회수·격리·변조·동일 artifact의 새 head·다른 문서/원본/proof/fresh bytes·한도/보호/selector/no-op 실패는 바이트 전달을 차단한다. 정상 read audit 외 production ingest/commit/publication은 없고 실행 route는 fresh 검증 후에도 거부한다. 여러 head 검사나 pure reconstruction 보관은 atomic CAS/접근 권한을 보장하지 않는다.

evidence/p09-361-stored-caption-layout-output-components001.v1.json은 새6개만6pass·148fresh/final148·cleanupTrue를 기록한다. 원 core delegation의 정확한 역변환과 기존 service/test bytes를 대조했으며 source layout6/source38/auxiliary41/기존 저장 캡션6/249제품·대형 form_stored_provider binary는 재실행하지 않았다. 전체282.891초·소유260.063초·시험0.12초·Job CPU24.266초·최고1369.26MiB·시스템CPU최고30.98%·가용RAM최저36.3097%다. 원 한 코어·BelowNormal·6.25% CPU cap·RAM/commit95%·Job 보호와 종료 정리를 유지했다. 경과 시간과 CPU 시간 차이의 세부 원인은 미확정이며 시험 지연을 CPU 포화로 단정하지 않는다.

격리된 in-memory 저장소/fixture scanner/합성 key의 후보 서비스 결속 결과다. 전체 캡션 번호 sequence/typed auxiliary state/protection·일반 compiler·실제 issuer/scanner·실행/게시·Native/저장/렌더는 미완료다. 다음은 원본 번호 의미와 typed 상태/compiler 연결이다. 공식158/249·잔여91·P09 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격은 그대로다.

### 캡션 배치 속성의 원본 보존 출력

ImportedDocumentStructure.lower_caption_layout_candidate는 source anchor로 선택한 caption의 side/fullSz/width/gap/lastWidth만 수정한다. 의미가 같은 속성의 원 lexical 값은 그대로 두며 다른 값은 기존 ReplaceAttribute를 이용한다. 기존 shape v6 ID profile로 개체/서식/문단 참조를 검증하고 원 table/cell/개체 보호를 확인한다. 원 patch/writer/ID index/protection 구현은 바꾸지 않았다. 출력 package와 구조/caption을 다시 import하고 지정한 값 외 XML을 streaming 비교하며 다른 expanded part와 번호·본문·unknown 속성·namespace를 보존한다. 전체 예상 section 복사나 caption별 재파싱은 없고, 원본 파일 변경 없이 writer-verified 메모리 후보만 반환한다.

새6개는001의 보호1개,003의 원 완성형 사각형 패키지1개,004의2개와005의2개로 확인됐다. 005는 통과4개를 제외하고 마지막 합성2개만 실행했다. 원 실패는 삭제하지 않았으며, field용 v3 profile을 새 개체 편집에 사용한 오류와 합성 fixture의 누락된 style/border 선언·ZIP mimetype 순서·중복 문단/개체 ID를 수정했다. dangling reference와 duplicate object/paragraph ID 거부를 유지했다. 원 structure와 기존 시험의 전체 prefix는 exact이며 원 완성형 패키지는7886bytes/SHA fe58ad76019828a0df0051fc54b97f98f04de82a8c46e7fc1d8b68ad5f2fbc91로 고정했다.

근거: evidence/p09-361-source-caption-layout-output-components005.v1.json 및 원 components001/diagnostic002/components003/components004.v1.json. 147fresh/final147·cleanupTrue, 전체71.922초·소유48.516초·시험0.25초·Job CPU1.875초/최고540.06MiB·시스템CPU최고18.52%·가용RAM최저35.8384%다. 한 코어·BelowNormal·CPU cap6.25%·RAM/commit95%와 원 Job 보호는 유지했다. wall time과 CPU time 차이를 원인 미확정 상태로 남긴다. 저장 원본 서비스 결속은 별도 절의 결과로 구분하며, 전체 번호 sequence/typed auxiliary state/문서 보호·실행/게시·Native 자격은 여전히 미완료다. 공식158/249·잔여91·P09 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격은 유지한다.

### 저장 원본 서비스의 캡션 접근 확인

StoredImportedReferenceCaptions는 기존 sealed Result와 원본 importer에 연결된다. 매 verify/with_source_captions에서 원 서비스의 scope/head/ACL/quarantine/AEAD/전체 바이트·receipt 검증을 유지한다. operation-local VerifiedFormReconstruction을 원 ImportedDocumentForms와 pointer 결속하고 재구성된 caption receipt/target/envelope를 비교해 추가 package parse를 피한다. callback 직전 head도 확인하지만 atomic CAS로 취급하지 않는다. 모델을 보관해도 접근 권한은 보관되지 않으며 실행 route는 fresh 확인 후에도 거부한다. 새 production ingest/commit/publication은 없고 정상 read audit만 발생한다.

새 시험은 read-only/route/privacy, ACL 회수, quarantine/AEAD 변조, 같은 artifact의 head 변경, 다른 문서/다른 reconstruction, 한도/잘못된 envelope의6개다. components003의5pass를 보존하고 입력/출력 한도 관계를 잘못 설정한 시험1개만 수정해004에서pass했다. 6개 동시 재실행으로 쓰지 않는다. 정확한 원3파일 역변환, 141fresh/final141·cleanupTrue를 확인했다. 004 전체22.094초·소유2.125초·시험0.02초·Job CPU1.938초·최고642.19MiB·시스템CPU25.29%·가용RAM38.1353%이며 한 코어·BelowNormal·CPU cap6.25%와 기존 RAM/commit 보호를 유지했다.

근거는 evidence/p09-361-stored-reference-caption-service-components004.v1.json과 원 components001/compile002/components003.v1.json이다. 001은 시스템CPU92.77% 보호중단·cleanupTrue, Job CPU cap6.25%·최고1373.29MiB였으나 급등 원인 프로세스는 미확정이다. compile002의 비공개 모듈 import 컴파일 실패와003의 시험 설정 실패도 보존했다. 격리된 저장소/fixture scanner/합성 key의 component 결과로, 번호/전체 상태/issuer/실제 scanner/Native 자격이 아니다. 이전 source38·auxiliary41·249제품·대형 form_stored_provider binary·한글/COM은 재실행하지 않았고 공식158/249·잔여91·P09 OPEN·목표ACTIVE·Native011 별도 승인/현재 입력 자격을 유지한다.

### 원본 캡션 envelope와 소유 개체 결속

ImportedReferenceCaptions는 실제 source graph의 개체/표 node와 원 XML caption의 직접 부모 anchor를 결속한다. 그림/도형8종·수식·표를 지원하며 nested table/note와 확장 namespace를 보존한다. 원본의 모든 XML을 확인해 header/nonspine/opaque/지원하지 않는 owner 아래의 caption을 누락시키지 않고 거부한다. 필수 side/fullSz/width/gap/lastWidth를 기본값 없이 읽고 단일 native subList와 caption 전체의 원 fingerprint를 쓴다. 중복 caption/subList·잘못된 수치/방향/boolean·유한 한도·fresh 원본 drift를 거부한다. caption별 ZIP/XML 재파싱이나 subtree 직렬화는 없고 원 table grid·전체 field coverage·보안 검사는 보존한다.

reference-source v6는 기존 bookmark/note/table v3·object v1 receipt를 유지한 채 caption_import/caption_envelopes 및 별도 Caption target을 합친다. raw text/label은 반환하지 않고 번호 의미·전체 caption schema·typed 흐름/상태를 추측하지 않는다. sub_list_numbering_qualified와 complete_auxiliary_state_qualified는 false, semantic_binding은 UnverifiedSubListNumbering이다. incomplete·미해결4단계·validation_report=null과 원 Native 실패를 유지한다.

`evidence/p09-361-source-caption-envelopes-components001.v1.json`은 새core6개와 변경된 API/실제 CLI32개가38pass·136fresh/final136·cleanupTrue임을 기록한다. 원core29개는 filtered였고 source의 원29개는 schema 기대4곳만 바꿔 새3개와 함께 확인했다. 원 target/object/SDK/core 시험 전체 prefix와 source v5의 정확한 역변환을 대조했다. 이전 auxiliary41/cycle701/literal9/249제품·대형 form_stored_provider binary·Native는 실행하지 않았다.

전체85.844초·소유42.500/22.578초·실제 시험0.12/1.21초, Job CPU40.250/20.969초·최고1854.46/1367.26MiB·active0/empty/handle closed다. 시스템CPU최고19.92%·가용RAM최저33.7862%, 한 코어·BelowNormal·CPU cap6.25%와 원 RAM/commit/Job 보호를 유지했다. source envelope 가져오기를 P09 Gate나 Native/저장/렌더 수용으로 승격하지 않으며 공식158/249·잔여91·P09 OPEN·목표ACTIVE와 Native011 별도 승인/현재 입력 자격 경계는 그대로다.

### 참조 상태의 참조 직렬화와 bounded SHA

ReferenceAuxiliaryDocumentState의 Serialize는 원 Draft field31개의 정확한 순서를 빌려서 기록한다. serde의 into 변환이 직렬화 때 전체 state를 clone하던 경로만 제거하고 Deserialize/TryFrom·실제 전이의 clone은 보존한다. state/report/caption/date/plan/edge inventory 지문은 같은 serde JSON 바이트를 bounded hash sink로 전달한다. canonical_json은 bounded byte sink를 사용한다. 두 sink는 chunk를 쓰기 전에 한도/overflow를 확인하고 실패를 latch한다. 원 상태·graph·lock·cache·strict JSON·오류·한도 검사는 유지한다.

`evidence/p09-361-auxiliary-borrowed-stream-serialization-components001.v1.json`은 field 이름 수집 정규식이 sha256의 숫자를 놓쳐 Rust 명령 전에 steps0으로 중단된 원본이다. 수집 규칙을 수정한 `evidence/p09-361-auxiliary-borrowed-stream-serialization-components002.v1.json`은 private4+domain14+직접 제품23=41pass·133fresh/final133·cleanupTrue다. 새3개는 독립적인 Draft JSON/UTF-8 escaping/Deserialize/SHA oracle, 정확한 한도와1byte 부족, 원 serializer 오류 및 실패 후 재개 금지를 다룬다. 원 전체 domain source의 정확한 역변환은 이 직렬화/helper/지문 경로와 새3개 외 코드·기존 시험이 같음을 확인한다. cycle701/16384 전용 시험·source35·249제품·대형 form_stored_provider binary·Native는 실행하지 않았다.

002는 전체159.594초·소유15.265/71.828/51.516초·실제 시험0.02/0.10/1.08초, Job CPU14.219/27.094/45.281초·최고1528.67/1850.87/1867.08MiB·active0/empty/handle closed다. 시스템CPU최고33.52%·가용RAM최저31.8891%, 한 코어·BelowNormal·CPU cap6.25%와 원 RAM/commit/Job 보호를 유지했다. 복제/임시 buffer 제거는 코드/정확한 결과 증거이며 실행 시간/heap 절감 비율이나 과거 PC 프리즈/Defender 원인은 측정하지 않았다. 공식158/249·잔여91·P09 OPEN·목표ACTIVE와 Native011 승인/현재 입력 자격은 바뀌지 않는다.

### 저장 결과 descriptor의 전체 파일명 대조

StoredFormProvider의 prepare_file_literal_candidate는 기존 sealed head/source 읽기를 그대로 사용하고, 해당 결과 artifact의 descriptor 파일명과 literal 및 UTF-8 SHA를 대조한다. 원 head/node/tenant/scope/ACL/quarantine/AEAD/size/digest 검사 뒤 추가 descriptor의 kind/state/digest/size/name을 확인한다. 문서/리비전/패키지 결속과 원 strict Request/Plan/Build 및 보존 HWPX 후보를 재사용한다. caller artifact/name selector, 저장 결과 ingest·commit·publication은 추가하지 않으며 원 metadata/download read audit는 발생한다.

PreparedStoredFileLiteralCandidate의 verify와 with_verified_bytes는 현재 scope/head·전체 원본 bytes·descriptor name을 매번 다시 읽는다. byte callback 직전에도 head를 확인한다. 기존 snapshot을 ACL 권한으로 재사용하지 않고 철회/격리/AEAD 변조/head 이동 뒤에는 callback을 호출하지 않는다. require_current_product_route는 fresh 확인 후에도 RouteUnqualified다. provider_scoped_filename_metadata_verified=true는 저장 결과의 전체 leaf-name 대조만 뜻한다. 원 pure preparation/candidate의 자격 flag, 전체 source state/스타일/flow·issuer·atomic CAS·Native/실제 제품 route는 미확인이다. 확장자 제외는 Projection 오류이며 임의의 stem 규칙을 적용하지 않는다.

`evidence/p09-361-stored-file-literal-service-components001.v1.json`은 시험용 ArtifactId namespace 충돌로 compiler 단계에서 시험0개인 원본이다. 수정 후 `evidence/p09-361-stored-file-literal-service-components002.v1.json`의 새6개만6pass/17filtered·131fresh/final131·cleanupTrue였다. 이름 바꿔치기·중복 JSON·확장자 제외 거부, 정상 후보와 read audit만 추가됨, ACL 회수·격리·AEAD 변조·같은 artifact의 head 이동·문서 scope 재결속 거부를 다룬다. callback 미호출과 원 결과 bytes/head 보존, issuer/route 거부, Debug/receipt redaction도 확인했다. 시험 repository·scanner·crypto는 격리 fixture이며 실제 issuer/scanner/Native 자격이 아니다.

002는 전체22.704초·소유3.938초·실제 시험0.14초, Job CPU3.094초·최고662.82MiB·active0/empty/handle closed, 시스템CPU최고12.69%·가용RAM최저38.6142%였다. 원 한 코어·BelowNormal·CPU cap6.25%와 RAM/commit/Job 보호를 유지했다. 원 provider/기존 시험의 전체 prefix와 Artifact/Revision/ACL/암호화/source lowerer 구현은 보존했다. 이전 literal9/cycle32/source35/249제품·대형 form_stored_provider 시험 binary·Native는 실행하지 않았다. 공식158/249·잔여91·P09 OPEN·목표ACTIVE와 Native011 승인/현재 입력 자격은 그대로다.

### 파일명 리터럴의 보존 HWPX 출력 후보

원본 구조의 lower_file_literal_candidate는 실제 section/paragraph/run의 child 경계를 선택해 caller의 frozen leaf-name payload를 hp:t로 삽입한다. 비어 있거나 자가닫힘인 run, 기존 child 앞/사이/뒤를 처리하며 원 namespace 문맥을 standalone fragment에 결속한다. 원 patch/ID/preservation/writer를 그대로 사용하고, 완전한 package/구조 재읽기에서 선택 run 전체·밖의 prefix/suffix·원 run/문단 속성·다른 part의 보존을 확인한다. 원본 덮어쓰기와 동적 PATH 필드, 외부 소스 조회, 저장/publication 권한은 없다.

원 field-pair importer로 기존 동적 필드 안의 표시 cache 위치를 거부한다. 원 observed protection 검사와 미표현/외부/범위 밖 선택·fresh drift·leaf 경로 문법·문자/출력 한도 거부를 유지한다. PreparedReferenceAuxiliaryProductOperation의 연결은 원 strict Request/Plan/Build의 fresh 결과와 문서/패키지/리비전을 결속한다. 현재는 collapsed point를 지원하며 range·locked·opaque target 의미는 명시적으로 거부한다. 원 source file metadata·caller 스타일 지문·전체 state/target flow·issuer/service 권한은 여전히 미확인이다. 원 preparation의 hwpx_lowered와 자격 flag는 false로 남고 require_current_product_route도 거부한다. 이는 실제 byte 후보 생성이지 전체 ref.file_name_literal 제품 수용이 아니다.

`evidence/p09-361-file-literal-output-candidates-components001.v1.json`은 compiler 오류/시험0개,002는4pass/2fail,003은 실패2개만의 진단 원본이다. 두 실패는 기존 source admission이 거부하는 속성/주석이 positive fixture에 포함됐기 때문이었다. 그 입력은 negative로 보존하고,004는 다른4개 시험/helper/제품 코드가 그대로인 정확한 역변환을 확인한 뒤 수정2개와 새 연결3개만5pass로 실행했다.004는102fresh/final102·cleanupTrue이며 유지4+수정2+새3을 한 번의9개 PASS로 승격하지 않는다. 실제 캡처1개는 source read/candidate 시험이지 Native acceptance가 아니다. 이전 cycle32/source35/auxiliary14/249제품/Native는 실행하지 않았다.

현재 근거는 `evidence/p09-361-file-literal-output-candidates-components004.v1.json`이다. 전체78.297초·소유7.562/54.547초·실제 시험1.26/0.04초, Job CPU1.812/23.266초·최고537.49/1369.87MiB·active0/empty/handle closed다. 시스템CPU최고22.39%·가용RAM최저33.7829%, 원 한 코어·BelowNormal·CPU cap6.25%와 RAM/commit/Job 보호를 유지했다. 기존 source/API/시험의 전체 prefix와 patch/writer/보호/ID 구현은 보존했다. 공식158/249·잔여91·P09 OPEN·목표ACTIVE와 Native011 승인/현재 입력 자격 경계는 그대로다.

### 참조 순환 검사의 경로 재사용

find_cyclic_sources는 동일 호출 안에서 분류를 끝낸 경로를 재사용한다. 각 source의 successor는 하나이므로 이미 끝난 경로로 들어가는 새 prefix는 새로운 순환을 만들 수 없다. 현재 경로의 재방문 위치부터만 순환 집합에 넣고 prefix는 제외한다. 전체 source를 매번 다시 탐색하던 O(V² log V)를 O(V log V)로 줄이되, 과거 문서 결과 cache나 원 fresh 검증 생략은 추가하지 않는다. 공개 schema·보고서·지문·오류·잠금·한도 및 원 state/request/plan/build는 그대로다.

작은 functional graph701종의 원 알고리즘과 역순 입력을 대조했다. source16,384개의 긴 chain은 경로 방문16,384회, 전체 cycle과64개짜리 cycle로 들어가는 긴 tail은16,385회였고, tail 자체는 순환으로 표시하지 않았다. 비공개 step hook은 시험에서만 방문 횟수를 세는 용도이며 제품의 work limit나 수용 조건을 완화하지 않는다. 원 긴 경로 알고리즘은 실제 실행하지 않았다.

`evidence/p09-361-reference-cycle-memoization-components001.v1.json`은 Rust unit4개가 통과했으나 결과 수집기의 기존 시험 경로 tests/private_tests 불일치로 중단된 원본이다. 전체 성공 기록으로 승격하지 않는다.002는 그4개의 모든 원 실행 입력이 그대로인지 재대조하고 미실행 domain14개와 직접 제품 준비 API14개만 실행했다. 유지4+새28의 두 실행을 구분하며 이전4개·source35·249제품·Native는 반복 실행하지 않았다.002는91fresh/final91·cleanupTrue이고, 원 domain 전체에서 새 순환 함수/시험만 역변환하면 원 bytes/SHA와 일치한다.

001/002는 전체24.671/121.078초·소유16.828 및60.062/46.000초·실제 시험0.19 및0.08/0.21초였다. Job CPU15.094 및26.797/44.078초·최고1520.32 및1854.16/1866.63MiB·active0/empty/handle closed, 시스템CPU최고21.21/30.10%·가용RAM최저30.9850/30.3109%다. 한 코어·BelowNormal·CPU cap6.25%와 원 자원 보호를 유지했다. 이는 반복 연산 제거 증거이며 PC 프리즈/Defender의 원인 확정이나 벽시계 속도 개선 benchmark가 아니다. 파일명 출력 연결·전체 source 상태/흐름·Native/저장/렌더, 공식158/249·잔여91·P09 OPEN은 여전히 미완료 범위다.

### 원본 개체와 수식 참조 대상

reference-source v5는 원 책갈피/주석/표 target_import를 보존하면서 별도 object_target_import의 원본 개체·수식을 targets에 합친다. ImportedReferenceObjectTargets는 실제 구조 graph의 node와 source anchor를 사용한다. 기존 캡션 분류기와 같은 pic·rect·ellipse·line·arc·polygon·curve·connectLine·equation만 대상으로 하며 native id/instId나 이름을 전역 identity로 사용하지 않는다. 구조/원본을 다시 파싱하거나 개체 subtree를 직렬화하지 않고 원 source fingerprint를 재사용한다. 원 SDK와 v3 target receipt는 변경하지 않는다.

원본의 모든 XML에서 대상 namespace와 전체 coverage를 대조해 header/nonspine/opaque wrapper 안의 누락 대상을 오류로 처리한다. 동일 local name의 다른 namespace는 native 대상이 아니다. 각 개체/수식 계열의 수와 전체 inventory JSON에 한도를 적용하고, fresh 확인은 원 whole-source/graph 재구성에 위임한다. active=true는 정확한 원본 요소의 존재만 뜻한다. geometry·수식 의미/계산·Native navigation·전체 참조 상태는 미확인이며 v5도 incomplete·미해결4단계·validation_report=null이다.

`evidence/p09-361-source-object-equation-targets-components001.v1.json`은 새 core6개와 변경된 실제 source API/CLI29개가35pass·87fresh/final87·cleanupTrue임을 기록한다. core의 기존17개는 filtered였고, source의 기존25개는 바뀐 진입점/응답 schema의 영향 범위이므로 새4개와 함께 확인했다. 원 core 구현/시험의 전체 prefix, 원 source 코드와 기존25개 시험에서 schema 기대3곳만 바꾼 정확한 역변환을 대조했다. 이전 typed13·제품249·Native는 실행하지 않았다.

전체125.562초·소유88.468/22.610초·실제 시험0.05/1.00초, Job CPU19.500/21.047초·최고1345.64/1358.73MiB·active0/empty/handle closed였다. 시스템CPU최고30.08%·가용RAM최저31.9967%, 한 코어·BelowNormal·CPU cap6.25%와 원 RAM/commit/Job 보호를 유지했다. 이는 빌드/준비를 포함한 기록이며 속도 향상 benchmark는 아니다. 전체 auxiliary 원본 상태·참조 의미/흐름·compiler/하위화·licensed reopen/render와 공식158/249·잔여91·P09 OPEN 경계는 그대로다.

### 참조 보조 여섯 작업의 typed 준비 API

ReferenceAuxiliaryProductPreparation은 ref.caption_sequence·ref.date_time_format·ref.file_name_literal·ref.correction_mark·ref.data_link·ref.reference_validate를 원 strict JSON Request→sealed Plan→Build에 연결한다. 입력은 caller가 제공한 ReferenceAuxiliaryDocumentState와 문서/리비전/패키지/흐름 pin이며 독립적으로 인증된 원본이 아니다. 같은 준비에 한도를 고정하고 context·원 요청·원 계획을 bounded stream SHA로 결속한다. target/plan/request/receipt는 외부에서 수정하거나 역직렬화할 수 없으며 fresh verify는 원 과정을 재구성해 비교한다. receipt만 요청하면 append 전 한도를 확인하는 JSON을 반환한다.

기존 read-only execute_json과 원4개 시험은 새 코드 이전 전체 prefix bytes/SHA를 보존한다. 새 API의 읽기 전용 검증도 상태/흐름 변경을 선언하면 거부한다. 다른 작업의 target flow pin은 선언된 값만 결속할 뿐 실제 흐름으로 관측/검증하지 않는다. source_completeness_verified·target_document_flow_verified·hwpx_lowered·execution_authority_verified·external_data_access_verified는 모두 false다. require_current_product_route는 fresh verify 뒤에도 RouteUnqualified를 반환한다. HWPX 파일 수정·CLI/MCP/raw action·외부 데이터 접근·Native 실행 경로를 추가하지 않는다.

001은 기존4개와 새9개가13pass/0filtered,31fresh/final31·cleanupTrue로 통과했다. 여섯 작업의 원 target/receipt 일치·fresh 재구성·문서/리비전/패키지/상태/흐름/한도 drift·중복/unknown/raw JSON 거부·문서 잠금·캡션 cache·보고서 지문·날짜 cache stale/관련 없는 상태 보존·출력 경계/privacy·19종 교정부호·4개 inheritance×2개 availability를 다룬다. 이후 read-only 상태/흐름 거부와 원 요청/계획 SHA oracle을 보강해002에서 공통 여섯 작업 시험과 새 거부 시험2개만2pass/12filtered로 실행했다.002는32fresh/final32·cleanupTrue다. 두 run의 시험명 합집합14개와 중복1개를 구분하며, 보강 후14개를 한꺼번에 재실행한 것으로 승격하지 않는다. 원13개 기록과 정확한 전체 소스 역변환은 보존한다.

001/002는 전체13.297/13.500초·소유7.219/7.485초·실제 시험0.15/0.05초, Job CPU5.531/5.391초·최고661.78/661.66MiB·active0/empty/handle closed였다. 시스템CPU최고21.21/12.11%·가용RAM최저28.5156/28.5739%, 한 코어·BelowNormal·CPU cap6.25%·기존 RAM/commit/Job 보호를 유지했다. 근거는 `evidence/p09-361-typed-auxiliary-product-preparation-components001.v1.json`과 `evidence/p09-361-typed-auxiliary-product-preparation-guard002.v1.json`이다.

이는 caller typed-state 준비 자격이며 actual-source 전체 상태·graph/compiler/하위화·Native/저장/렌더·정식 issuer/service authority 자격이 아니다. 현재도 incomplete인 reference-source v7을 완전한 상태로 자동 변환하거나 Native entry465를 현재 준비/실행 자격으로 재사용하지 않는다. 당시 다른 시험·36원본·249제품·한글/COM은 실행하지 않았다. Native011 별도 승인/현재 입력 자격, 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 활성 콘텐츠 JSON 임시 버퍼 제거

active_content의 scan 종료 검사는 완성된 canonical JSON을 할당했다 버리는 대신 같은 Serialize 출력을 Count writer로 검사한다. state SHA도 기존 ActiveState와 정렬된 control-state projection을 그대로 사용하면서 직렬화 바이트를 Digest writer에 바로 전달한다. 순서 보존용 참조 projection Vec는 유지하지만 두 전체 JSON 임시 버퍼는 없다. canonical_json을 실제 요청할 때만 Bytes writer를 사용하며 각 append 전에 checked length/원 max_json_bytes를 검사하고 할당 실패도 닫힌 오류로 반환한다. graph/namespace/resource signature/activation 및 공개 JSON/schema v4·지문·오류 코드는 바꾸지 않았다. state projection이 전체 inventory보다 크지 않으므로 state 단계의 같은 출력 한도는 원 전체 JSON에서 거부될 입력을 일찍 거부할 뿐이다.

원 모듈의 세 직렬화 경로와 writer 추가만 역변환하면 전체 원본 bytes/SHA가 일치한다. 새3개를 제거한 핵심 test 파일도 원10개 전체 preimage와 같다. 핵심13개·source 요약2개·실제 CLI2개, 정확한17개 결과가 pass다. core는 filter0, source는2pass/5filtered, CLI는2pass/23filtered다. 독립적인 기존 방식의 serde JSON/state projection SHA,256개 control 입력의 정확한 출력 경계·1byte 초과·초소형 한도·불관련 XML ordinal shift 보존을 확인했다. 과거36개와 기존 전체 CLI25/보안32/249제품을 누적 재실행하거나 이번17개에 합산하지 않는다.

001은37fresh/final37·cleanupTrue, 전체105.985초·소유18.453/1.781/78.719초·실제 시험0.07/0.02/0.13초다. Job CPU16.891/1.469/23.984초·최고1345.87/534.49/1354.66MiB·active0/empty/handle closed, 시스템CPU최고30.35%·가용RAM최저24.6841%였다. 한 코어·BelowNormal·CPU cap6.25%·기존 RAM/commit/Job 보호는 그대로다. 전체 시간에는 컴파일·연결·입출력·준비 비용이 포함되며 기존 기록과 통제된 성능 비교가 아니므로 속도 향상이나 메모리 감소의 측정값으로 제시하지 않는다. 근거는 `evidence/p09-361-active-inventory-streamed-serialization-components001.v1.json`이다.

이번17개는 현재 직렬화 변경의 영향 검사다. 이전32개/44개나 Native entry465를 현재 전체 제품/Native 자격으로 재기반하지 않으며 status incomplete·null report·보안/외부 접근 미확인·Native011 별도 승인과 현재 실행 입력 자격을 유지한다. 한글/COM/249제품 실행은 없고 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE다.

### 실제 참조 원본의 수동 보안 요약

현재 reference-source 응답은 `hwpx-agent.product.reference-source-assessment/v4`이며 active_security에 SourceActiveSecurityAssessment를 포함한다. immutable source의 새 assess_active_content와 기존 catalog 보안 importer는 원 scanner 생성부를 공유한다. 원 PackageGraph 재구성/동일성·namespace·관계·resource signature·activation 거부와 기존 경로의 default limits/오류는 그대로다. 요약 경로는 catalog/meaning 그래프를 추가로 만들지 않으며 caller graph나 inventory를 받지 않는다. 원 inventory의 지문·분류 수만 노출하고 경로·명령·URI는 반환하지 않는다. 새 참조 경로의 items/JSON 한도는 원 스캐너 한도를 늘리지 않고 더 엄격하게만 적용한다.

activation_allowed는 false이며 native_security는 not_assessed_by_active_content_inventory다. native_form_security_qualified와 external_data_access_qualified도 false다. 원 inventory가 세지 않는 native form 종류를 없다고 추정하거나 분류 수0을 잠금 해제·안전 attestation으로 승격하지 않는다. 이전 section_flows의 페이지/잠금 null, 전체 흐름 false·status incomplete·validation_report null·네 unresolved 단계는 유지한다.

원 보안5개와 새2개, 실제 CLI25개를 합친32개가 skip/filter 없이 통과했다. 기존 보안 importer 전체는 새 요약/추출부를 역변환하면 원 bytes/SHA와 같고, 두 test 파일도 새5개·schema v3→v4 기대값2개와 대응 시험명1개의 명시적 변경만 되돌리면 전체 preimage가 일치한다. 원 보안 시험의 historical36개는 실제 파일을 읽는 검사이며 제품/한글 재실행이 아니다. 원 스캐너와 요약의 지문/분류 일치·최소 header의 catalog 비승격·위장 namespace·원 items/JSON 제한·실제 CLI 명령 비노출·부분 성공 거부를 확인했다. 이전44개 시험이나 fixed probe는 이 결과에 합산하거나 다시 실행하지 않았다.

002는79fresh/final79·cleanupTrue, 전체70.062초·소유35.532/22.437초·실제 시험17.02/1.03초다. Job CPU33.109/21.125초·최고1344.89/1361.54MiB·active0/empty/handle closed였다. 시스템CPU 최고80.04%는138표본 중 유일한75% 이상 표본이고90% 이상은0개이며 해당 부모CPU는0%다. 소유 CPU cap6.25%·한 코어·BelowNormal은 확인됐지만 이 기록은 원인 프로세스 식별 자료가 아니다. 가용RAM최저25.8953%·기존 RAM/commit/Job 보호를 유지했고 보호 중단은 없었다.

001은 사전 검토기의 CRLF 역변환 경계가 맞지 않아 원 전체 bytes/SHA 대조에서 거부됐고 시험0·cleanupTrue·최종 source closing 미완료로 보존한다.002는 검토기의 경계만 바로잡고 원 정확한 동일성 조건을 통과한 뒤 실행했다. 원 실패를 PASS로 재분류하지 않는다. 근거는 `evidence/p09-361-passive-source-security-components001.v1.json`과 `evidence/p09-361-passive-source-security-components002.v1.json`이다. 이는 전체 auxiliary state/flow·문서 보호/서명·외부 데이터 접근·Native 자격이 아니다. Native011의 별도 승인과 현재 실행 입력 자격, 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 실제 원본의 섹션 구조 지문

reference-source 응답 v3에서 section_flows와 ImportedSectionFlowObservation을 도입했고 현재 v4도 유지한다. 기존 원본 문단 인덱스를 재사용해 paragraph/run/inline 개수와 순서·경계·expanded-name 종류를 framed SHA-256으로 묶는다. 원 lowerer의 투명 책갈피 wrapper 기준을 유지하므로 책갈피 추가만으로 구조 지문을 바꾸지 않되, source_part_fingerprint_sha256은 원본 part를 별도로 결속한다. opaque 문단·표·각주도 실제 XML 순서로 관측하고 prefix 별칭은 같은 expanded name으로 처리한다. 새 ZIP/XML 파싱·부분 트리 직렬화·후보별 재구성은 없다. 원 structure/forms fresh 검사는 새 섹션 관측의 동일성도 확인한다.

v3는 기존 form/field 기록을 유지하고 섹션 수·전체 출력 크기에 원 reference 한도를 적용한다. 페이지 배치와 잠금은 확인되지 않았으므로 null이며 complete_document_flow_qualified는 false다. NativeFormPackage의 비폼 내용 지문을 참조 run/inline topology로 치환하거나 AuxiliarySectionState에 빈 지문·unlocked 기본값을 채우지 않는다. status incomplete·validation_report null·기존 네 unresolved 단계는 그대로다.

importer22개와 실제 CLI 제품 경로22개, 정확한44개 이름/결과가 모두 pass이며 skip/filter0이다. 새7개 시험 제거와 기존 schema 기대값1개의 v3→v2 역변환만으로 두 test 파일 전체 preimage bytes/SHA가 일치한다. 투명 책갈피·run 경계·inline 종류·namespace 별칭·opaque/native 문단 차이·spine reset·표/각주·fresh 관측·CLI v3·원본 historical 입력·미확인 페이지/잠금·섹션 한도·출력의 정확한 경계와1byte 초과 거부를 다룬다. 기존8개 준비 packet의 receipt/명령과 fixed probe의 원1836bytes/SHA·전체 JSON도 현재 빌드에서 동일하다.44개 시험을 probe 확인 때 다시 돌리지 않았다.

001은38fresh/final38·cleanupTrue, 전체47.422초·소유18.532/21.937초·실제 시험0.22/0.89초다. Job CPU17.078/20.750초·최고1344.72/1362.28MiB·active0/empty/handle closed, 시스템CPU최고20.45%·가용RAM최저27.0955%였다.002는44fresh/final44·cleanupTrue, 전체10.125초·빌드1.563초/baseline0.828초·Job CPU1.125/0.219초·최고633.94/19.62MiB·시스템CPU최고9.57%다. 한 코어·BelowNormal·CPU cap6.25%·기존 RAM/commit/Job 보호를 유지한다. 근거는 `evidence/p09-361-source-section-topology-components001.v1.json`과 `evidence/p09-361-source-section-topology-fixed-probe002.v1.json`이다.

이는 전체 auxiliary state/flow·대상/edge 의미·페이지·보호·Native 실행 자격이 아니다. 이전 v1/v2와 Native entry 자격465를 현재 v3 전체 제품/Native 자격으로 재사용하지 않는다.249제품·한글/COM은 실행하지 않았으며 Native011의 별도 승인과 현재 빌드/입력 세대 자격이 필요하다. 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE다.

### 원본 섹션과 문단 순서 연결

ImportedBookmarkSectionLocation은 실제 section ID와 해당 XML의 paragraph ordinal/count를 원 책갈피 관측과 source-bound SDK 후보에 연결한다. 기존 bookmark lowerer의 native XML 요소 순서와 같은 기준이며, 표를 attached node로 옮기거나 각주 body를 분리한 그래프 순서를 사용하지 않는다. section마다 한 번 수집하는 bounded 정렬 Vec와 binary search를 사용한다. 후보마다 재탐색·ZIP/XML/구조 재구성이나 문단별 tree-node 할당을 추가하지 않는다. opaque 영역의 native 문단도 source 순번에 포함하지만 typed coverage로 승격하지 않는다. 새 private 위치는 serde skip이며 기존 관측 JSON·target 지문·SDK receipt·명령을 바꾸지 않는다.

새6개 시험을 제거한 세 test 파일의 전체 bytes/SHA가 원 preimage와 일치한다. importer18개·SDK8개는 filter/skip 없이 통과했고, 제품 준비 경로는 새1개만 통과·기존4개 filtered였다. 합계27개의 정확한 이름·결과를 확인했다. 표·각주·각주 안 표·opaque 문단·spine part별 reset·동일 native 문단 ID·신선한 원본의 문단 삽입 drift·기존6-key JSON·Debug privacy와8개 제품 후보의 위치 연결을 다룬다. 원27개를 재실행하지 않고 현재 fixed probe를 빌드해 기존 준비 packet의8개 receipt/명령과 원 baseline 응답1836bytes/SHA·전체 JSON이 같음을 확인했다.

001은37fresh/final37·cleanupTrue, 전체72.422초·소유19.360/46.094초·실제 시험0.25/0.03/0.03초다. Job CPU17.812/21.781초·최고1342.78/1357.41MiB(4.2145/4.2604%)·active0/empty/handle closed, 시스템CPU최고25.78%·가용RAM최저26.0128%였다.002는43fresh/final43·cleanupTrue, 전체11.688초·빌드2.969초/실제 baseline1.047초·Job CPU1.547/0.219초·최고633.08/19.95MiB이며 시스템CPU최고17.42%·가용RAM최저30.3921%다. 한 코어·BelowNormal·CPU cap6.25%·기존 RAM/commit/Job 한도를 유지했다. 근거는 `evidence/p09-361-bookmark-source-section-location-components001.v1.json`과 `evidence/p09-361-bookmark-source-section-location-fixed-probe002.v1.json`이다.

이 좌표는 원본 XML 위치일 뿐 완전한 AuxiliarySectionState/LinkAnchor·page assignment·protection·reference edge 의미나 Native 목적지/실행 자격이 아니다. ValidationTarget.anchor를 새 좌표로 자동 채우지 않고 전체 reference status·네 unresolved 단계·null report와 별도 Native011 승인을 유지한다. 앞선 원본 CLI19개를 새 Rust source에서 재검증한 것으로 부르지 않으며 과거 Native entry 자격465도 현재 binary/입력 세대의 자격이 아니다.249제품·한글/COM은 실행하지 않았고 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE다.

### 실제 참조 원본의 필드 목록

reference-source CLI의 v2에서 form_import와 field_range_import 기록을 도입했고 현재 v3도 이를 유지한다. 같은 immutable package에서 원 form/field importer를 호출한다. 대상 목록은 forms.body_structure를 빌려 만들며 ZIP/XML/구조를 다시 import하지 않는다. 원 필드 범위 importer의 pairing·중첩·header·parameter·표/각주 검사를 유지하고, 전체 XML part의 실제 시작과 끝 개수를 별도로 대조해 header/nonspine/opaque 영역의 누락도 거부한다. 필드 수는 기존 reference items 한도 안이어야 한다. 전체 출력 버퍼를 먼저 만든 뒤 크기를 재는 대신 bounded writer가 쓰기 전 한도를 검사한다.

원13개 시험 본문은 전체 preimage bytes/SHA와 같은 prefix이며 새6개를 추가했다. 실제 CLI를 포함한19개가 오류/skip/filter 없이 통과했다. 원 form/range 기록의 정확한 동일성·source/body/form/range graph 연결·중첩과 문단별 같은 native ID·표/각주·본문 밖 시작/끝/쌍·깨진 pair의 CLI 오류·원 필드 한도·과거 실제 저장 원본의 CLI 관측과 원본 보존을 확인했다.19개는 변경된 source 제품 경로의 회귀/구성요소 시험이며 이전 참조16개나249제품을 재실행한 것이 아니다.

002는39fresh/final39·cleanupTrue, 전체11.453초·소유 빌드/시험4.500초·실제 시험0.78초다. Job CPU3.281초·최고660.42MiB(2.0728%)·active0/empty/handle closed, 시스템CPU최고11.17%·가용RAM최저30.0495%였다. 한 코어·BelowNormal·CPU cap6.25%·기존 RAM/commit/Job 보호를 유지했다. 최초001은 새 시험의 `Result<_, Box<dyn Error>>`와 typed 오류 직접 비교가 컴파일되지 않아 시험0개에서 종료했다. 시험을 원 typed API 호출로 바로잡았고 원 실패/cleanupTrue는 보존한다. 근거는 `evidence/p09-361-reference-source-field-inventory-components001.v1.json`과 `evidence/p09-361-reference-source-field-inventory-components002.v1.json`이다.

v2의 상태는 계속 incomplete·validation_report null이며 기존 네 unresolved 단계를 유지한다. 관측 필드 목록은 해석된 validation edge나 전체 auxiliary state/flow가 아니고 Native 목적지·캐시 평가·실행 권한을 주지 않는다. 이전 v1 결과와 이전 Native entry 자격465를 현재 v2 전체 제품/Native 자격으로 재사용하지 않는다. 실제 Native011의 별도 실행 승인과 현재 빌드/입력 세대 자격이 필요하다. 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE다.

### 같은 출력 스냅샷의 결합 교차참조 관측

고정 worker probe의 실제 소비 경로도 observe_output_for_discovery에 연결했다. summarize의 두 개별 import 호출만 단일 결합 호출과 원 두 보고서 getter로 바꿨고, 전체 파일 역변환 bytes/SHA로 나머지 응답·입력·경로·원 전후 파일 재확인이 동일함을 확인했다. 변경된 소비 경로의 원4개 시험은 모두 통과했고 새 실행 파일의 읽기 전용 baseline 응답은 이전011의1836bytes/SHA 및 전체 JSON과 같다. 앞서 통과한16개나249제품은 재실행하지 않았다. 기존 합산/개별 출력 한도와 Native false·원 자원 보호는 그대로다.

소비 경로005는40fresh/final40·cleanupTrue, 전체102.750초다. 소유 시험45.922초(실제 시험3.64초)·빌드44.062초·baseline4.110초, Job CPU1.781/1.234/0.141초·최고634.38/633.05/20.04MiB이며 각 tree active0/empty/handle closed다. 시스템CPU최고26.54%·가용RAM최저28.5645%였다. 과거 baseline0.988초보다 벽시계 시간이 길어 실행 속도 향상으로 보고하지 않는다. 한 출력의 중복 해석 제거와 응답 호환성 확인이며 Native/전체 참조 자격은 아니다. 근거는 `evidence/p09-361-combined-crossref-probe-integration005.v1.json`이다.

P09-10의 observe_output_for_discovery는 출력 package/form/field를 한 번 import하고 원 body_structure를 빌려 기존 책갈피 대상 관측도 수행한다. 기존 command/target 개별 API와 모든 coverage·SHA·이름 모호성·field pair·부분 해석 거부 조건은 유지한다. 새 결과는 서로 다른 caller 보고서가 아니라 한 원본에서 만든 두 관측을 보유하며 전체 JSON을 한 bounded writer/count로 제한한다. 개별 보고서가 각각 한도 안이어도 합계가 넘으면 거부한다. 같은 snapshot의 이름/문자열 일치는 Native 의미·해결·인과적 보존·전체 state/flow의 증거가 아니다.

001은 compile/test250.078초 뒤 첫9개 중8pass/합산 한도 시험1fail로 종료했다. default input1MiB와 작은 output cap의 불일치가 원 limit 생성 규칙에서 거부된 시험 설정 오류다. output cap을 높이거나 제품 검증을 낮추지 않고 그 시험의 input cap만 output과 맞췄다.002는 실패한1개만 재시험해1pass/8filtered, 이어 미실행 target7개를7pass/0filtered로 실행했다. 원8pass와 현재8pass의 합집합16개이며16개 동시 재실행이 아니다. 전체 test 파일의 단일 수정 역변환 bytes/hash와 나머지 원 source pin 동일성을 확인했다. 원001 FAILED와 final source hash 미완료는 그대로이고,002의34fresh/final34는 별도 source 사후 검토·새 실행 결과이지 원 guard/Native 검사 credit가 아니다.

새 경로와 원 두 API의 JSON 일치, 누락/중복 대상과 matching command의 비승격, 잘못된 SHA/깨진 field pair, 합산 출력 한도를 확인했다. 실제 과거 저장 HYPERLINK 원본도 새 경로에서 CROSSREF0/대상 미관찰·Native flagsFalse이며 원본 bytes는 변하지 않았다.001은 전체253.219초·Job CPU201.938초·최고1904.73MiB·시스템CPU최고55.27%·가용RAM최저27.4786%다.002는 전체8.922초·소유1.672/0.406초·libtest0.04/0.16초·Job CPU1.344/0.391초·최고633.64/53.71MiB·시스템CPU최고13.48%·가용RAM최저31.2934%다. 각 소유 tree active0/empty/handle closed·cleanupTrue, 한 코어·BelowNormal·CPU cap6.25%·Cargo1/test1·기존 RAM/commit/Job 보호를 유지했다.

원본 이름/명령/URI를 새 JSON·Debug에 노출하지 않고 public CLI/MCP/raw action 경로를 열지 않았다. Native011/기존249개/한글/COM/접근 허용은 실행하지 않았다. Rust 변경에 대한 현재 build/input 세대 확인과 별도 Native011 승인은 계속 필요하며 이전465를 새 Rust binary/corpus 자격으로 쓰지 않는다. Native/완전한 참조 검증은 미완료, 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE다. 근거는 `evidence/p09-361-combined-crossref-readback-components001.v1.json`과 `evidence/p09-361-combined-crossref-readback-components002.v1.json`이다.

별도 source/document 사후 검토004는39fresh/final39·cleanupTrue로 통과했다.003은 시험의 원 소스 순서와 libtest의 이름순 실행 순서를 그대로 비교한 검토기 오류로 중단했으며 원 실패/cleanupTrue·실행 단계0을 보존했다.004는 이름과 상태의 정확한 집합을 비교하되 중복·누락·원8개/새8개 분리·원 실패/미완료 source closing과 양쪽 의존 파일 역대조를 그대로 확인했다. 제품·구성요소 시험을 재실행하거나 원 실패를 재분류하지 않았다. `evidence/p09-361-combined-crossref-readback-source-sync003.v1.json`과 `evidence/p09-361-combined-crossref-readback-source-sync004.v1.json`을 보존한다.

### 독립적인 원본 책갈피 좌표 구성요소

Native011 승인 대기 중 P09-10 원본 참조의 좌표 경계를 진행했다. 기존 bookmark_projection의 실제 run/non-bookmark child 순번을 ImportedBookmarkSourcePoint에 보존하고 source-bound SDK 후보에 원 paragraph ID와 함께 연결한다. ControlRef/합성 BookmarkAnchor를 포함하는 control_inline_position으로 원 경계를 추정하지 않는다. 인접 책갈피·여러 run·표/각주 안의 원 paragraph를 구분하며 새 원본 전체 순회는 없다. getter는 원본 로컬 관측만 반환하고 LinkPoint/LinkAnchor/페이지/Native cursor를 만들지 않는다. serde skip으로 기존 관측 JSON과 대상 지문을 유지하고 Debug도 이름을 노출하지 않는다.

원본 import14개·SDK7개를 한 소유 Cargo 작업에서 직렬 실행해21개 모두 pass, 오류/skip/filter0이었다. 입력/최종 witness28개는 이번에 명시한 source/manifest/운영 helper 범위이며 전체 Rust/Cargo 또는 Native corpus의 완전한 byte closure가 아니다. 전체148.890초·compile/test142.765초·libtest0.17/0.03초, Job CPU64.516초·최고1891.54MiB/5.9369%·active0/empty/handle closed·cleanupTrue다. 한 코어·BelowNormal·CPU cap6.25%·Cargo1/test1·debug/incremental off·codegen16·기존 RAM/commit95%·Job 한도를 유지했다. 시스템CPU최고34.47%·가용RAM최저26.1559%이며 프리즈 해결을 증명하는 수치는 아니다.

첫001은 심볼릭 링크 Cargo가 allowlist에서 거부돼 compiler/test를 시작하지 않았으며 원 cleanupFalse는 보존한다.002는 같은1.96.0의 실제 Cargo 파일을 사용해 통과했다. 일반 target 개발 캐시를 사용했고 이전 Native 제품 target·249개 제품 시험·한글/COM·접근 허용을 실행하지 않았다. Rust source 변경 뒤에는 이전 entry qualification465를 새 Rust binary/전체 corpus 실행 자격으로 재기반하지 않는다. 실제 Native011에는 현재 Rust 빌드/입력 세대 확인과 별도 승인이 필요하다. 전체 참조 state/flow/native mapping·제품 검증은 미완료이며 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE다. 근거는 `evidence/p09-361-reference-bookmark-source-point-components001.v1.json`과 `evidence/p09-361-reference-bookmark-source-point-components002.v1.json`이다.

### 잡힌 중복 호출 오류의 최초 원인 보존

현재 `native011_product_entry.Driver.run`은 중복 거부도 원 try/except 안에서 처리한다. 구성 반환 직후와 원 dispatch 반환 직후에 entry_error를 확인하고, 첫 실행이 반환했더라도 잡힌 재호출/재진입 오류를 숨겨 성공으로 발행하지 않는다. 실제 호출 수와 모든 호출 시도 수를 분리해 기록한다. 생성 시점의 승인 의존성을 바꾸거나 원 Once/부모/Native/Frame/기한/독립 판정/수용 상태를 변경하지 않는다.

모델462는 원 코드에서 중복 거부 오류를 잡은 뒤 성공한 첫 반환을 발행하는 경우와, 생성 시 전달한 승인 callback이 재진입 오류를 잡고 True를 반환하는 경우를 재현해2개 모두 실패했다.463은 기존13개와 이 회귀2개를 합친15개가74fresh/final74·cleanupTrue로 통과한 현재 기록이다. 최초 ONE_ENTRY_NO_RETRY를 보존하고 결과 발행을 차단하며 반환 객체도 해제한다. 이 모델의 guard/Frame/IO/프로세스는 synthetic이다. 실패462와 이전461 자격·구성001은 원본으로 보존하고 현재 소스의 제품 통과로 재기반하지 않는다.

실제 연결 전용 entry-connect002/owned464은 current3075/whole3494/history419·원 구성429fresh/final429·연결24/24·독립 참조3/3·외부86/86·helper59/Native64·cleanupTrue다. 구성 entry 호출 시도/실제 호출/terminal은 각각1회, 제품 Once 호출·승인 함수·Frame/제품/GO/intent와 결과 part 발행은0이다. 실제002는118.609초·외부135.954초, Job CPU8.562초·최고88.31MiB·active0/empty/handle closed, CPU cap6.25%·한 코어·BelowNormal을 확인했다. 자식/외부 합산 시스템CPU최고72.46%·가용RAM최저29.9354%이며 이 전체 시스템 표본을 검증 자체의 CPU로 단정하지 않는다. READY15 포함 명목597.500421초/600초는 실행 성공 보장이 아니다.

현재 모델/구성 입력의 자격을 갱신한 뒤 별도 승인 범위에서 실제 제품/종료/발행을 통합 검증한다. 실제 통합 자격은 미완료이며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기를 유지한다. 근거는 `implementation/p09/evidence/p09-361-native011-current805-product-oracle-input-models462.v1.json`, `p09-361-native011-current805-product-oracle-input-models463.v1.json`, `p09-361-native011-current805-product-entry-connect002.v1.json`, `p09-361-native011-current805-product-oracle-input-construct-owned464.v1.json`이며 축약명도 같은 디렉터리다.

### 별도 실행 진입점과 종료 결과 발행

`native011_product_entry.entry`는 명시적인 새 승인 callback이 있을 때만 원 전체 dispatch를 호출할 수 있다. CLI는 `--connect-only`만 허용하며 제품 실행/GO/재시도 옵션은 없다. 새 파일과 시험2개를 명시적 current 입력에 추가했다. 기본 인스턴스의 None 승인이나 기존 실패/소비 intent를 재활성화하지 않는다.

종료 wrapper는 기존 구성 코드의 제품 False/0 표시를 그대로 내보내지 않고 원 부모의 실제 Frame/attempts를 관측한다. 원 _terminal/_checker·닫힌 제어기·COMMITTED Frame/source cleanup·한 번의 원 audit·whole closing/독립 판정을 확인한 후 별도로 발행한다. 원 무손실 pack과 새 post-owner guard, 원 배타 publisher를 사용해 carrier를180000byte 단위로 보존한다. 원16MiB 한도·부분당262144byte 한도·원 보호/기한은 유지한다. 기존 닫힌 guard를 다시 사용하거나 Native 시계를 초기화하지 않는다.

원 제품/독립 판정 성공과 결과 발행 성공은 별개다. 발행/cleanup 실패를 전체 PASS로 바꾸지 않고 최초 오류·부수 종료 오류·부분 출력 pin/시도 경로를 남기며 삭제나 자동 재시도하지 않는다. Frame 또는 attempts가 있으면 제품 본문 실행 여부는 미확인(None)으로 남기고, 검증된 원 전체 lifecycle의 실제 반환이 있어야 True로 표시한다. 큰 반환 객체는 종료 후 내부 참조를 해제한다. 수용 원장/Gate/P10은 변경하지 않는다.

현재 모델459의13개는74fresh/final74·cleanupTrue로 통과했다. 원 전체 invoke/claim_writer/pack을 사용하지만 IO/guard/Frame/프로세스는 synthetic이다. 모델458의 Frame 관측 후 False 표시 실패는 원본으로 보존했다.459에서 그 보수적 표시를 수정했고 원 오류/정리 오류 동시 발생, 미완료 oracle, canonical 경로 오류, 발행 CPU 보호, cleanup 실패, 큰 결과 분할/부분 실패/재시도 차단을 확인했다. 실제 Native/제품/물리 발행의 통합 자격은 미완료다.

실제 연결 전용 entry-connect001/owned460은 current3075/whole3494/history419·원 구성429fresh/final429·연결24/24·독립 참조3/3·외부86/86·helper59/Native64·cleanupTrue다. 구성 entry/terminal은 각각1회, 제품 Once 호출/승인 함수/Frame/제품/GO/intent는0이며 실제 결과 part 발행도0이다. 실제114.969초·외부130.860초·Job CPU8.312초·최고87.04MiB·active0/empty/handle closed, CPU cap6.25%·한 코어·BelowNormal을 확인했다. 자식/외부 합산 시스템CPU최고17.54%·가용RAM최저30.3779%, READY15 포함 명목597.498854초/600초이며 실제 성공 보장은 아니다.

다음은 현재 모델·실제 구성·실행 입력의 자격을 최종 연결한 뒤 별도 승인 범위에서 실제 통합 실행을 확인하는 일이다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기를 유지한다. 근거는 `implementation/p09/evidence/p09-361-native011-current805-product-oracle-input-models459.v1.json`, `p09-361-native011-current805-product-entry-connect001.v1.json`, `p09-361-native011-current805-product-oracle-input-construct-owned460.v1.json`이며 축약명도 같은 디렉터리다.

### 실제 입력 선언과 비실행 호출부 연결

새 dispatch와 시험2개를 명시적 control 입력으로 선언하고 private source로 연결했다. 원 publisher의 고정 source pin과 현재 입력 선언을 새 reader로 대조해 원 claim_writer를 구성한다. 같은 부모·열린 제어기·판정 Reader/API/process_policy·원 전체 invoke가 연결된 plan을 만들지만 구성 과정에서는 plan.run·승인 함수·intent·제품을 호출하지 않는다. None plan의 실행 요청은 원 entry/claim/Native 이전에 거부하며 기본 CLI는 인자 없는 비실행 구성만 허용한다. 새 인스턴스의 명시적 승인 함수/wrapper 구성 의존성은 이전 기본 인스턴스를 재활성화하지 않는다.

현재455는 dispatch17개와 영향받은 lifecycle 연결5개를 선택해22개 모두 통과했고72fresh/final72·cleanupTrue다. 선택5개는 기본 부모 연결·암묵 승인 거부·새 명시적 승인 연결·잘못된 구성 인자 차단·중복 없는 control 선언이다. 원 전체72개 lifecycle 모델과 기존 제품/no-GO005를 다시 실행하지 않았다. 새4개 dispatch 모델은 None plan 실행 거부, 실제 연결의 명시적3source 읽기, 현재 publisher 선언 불일치와 원 publisher byte 변조 차단을 검사한다.

실제 비실행 구성012/owned456은 current3073/whole3492/history419·원 구성427fresh/final427·연결24/24·독립 참조3/3·외부86/86·helper59/Native64·cleanupTrue다. 새2개 선언은 원 구성427과 연결24 양쪽에 직접 나타나며 원 publisher1개는 새 연결 reader에 추가됐다. plan.boundTrue·실행 시도0·승인 함수 없음·Native/제품/GO/intent0이다. 기본 helper를 숨기거나 원 Native64 한도를 늘리지 않았다.

실제012 구성114.438초·외부130.625초·Job CPU8.375초·최고91.74MiB·active0/empty/handle closed를 확인했다. CPU cap6.25%·한 코어·BelowNormal·기존 RAM/기한 보호를 유지했고 자식/외부 합산 시스템CPU최고18.75%·가용RAM최저31.8042%, READY15 포함 명목597.333834초/600초다. 실제 실행/종료 결과 발행 자격은 미완료이며 명목 예산은 실행 성공 보장이 아니다. 다음은 별도 승인된 실행 진입점과 종료·독립 판정 결과 발행 경로다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기는 유지한다.

근거는 `implementation/p09/evidence/p09-361-native011-current805-product-oracle-input-models455.v1.json`, `p09-361-native011-current805-product-lifecycle-construct012.v1.json`, `p09-361-native011-current805-product-oracle-input-construct-owned456.v1.json`이며 축약명도 같은 디렉터리다.

### 이전 단독 호출부 모델과 승인 의존성 고정

`native011_product_dispatch.bind`는 같은 실제 부모 문맥·열린 제어기·Reader/API/process_policy·원 배타 `claim_writer`의 전체 함수 code를 확인한다. 실행 때 원 `procedure.invoke`에 같은 의존성을 전달하며 opening/Native/정리/closing/독립 판정 절차를 다시 구현하지 않는다. 원 Once와 원 전체 절차가 각각 한 번 반환하고 정리 오류가 없다는 조건을 확인한 뒤 원 결과를 그대로 반환한다. 호출부는 GO/Frame commit/제품 결과/수용 기록을 만들지 않으며 결과 객체를 내부에 보유하지 않는다. 실제 제품 경로 연결과 실행 자격은 아직 미완료다.

Once 구성 함수는 새 인스턴스에만 명시적인 승인 함수를 전달할 수 있다. 기본값None과 구성 전용 CLI는 그대로이며 flag·다른 함수·기존 기본 인스턴스의 사후 재활성화는 거부한다. 생성 시점의 승인 의존성을 `_authority_origin`에 보존하고 원 owner 검사에서 동일성을 확인한다. 별도 실행 승인이 없는 구성에서 승인 함수를 제공하거나 호출하지 않는다.

현재 모델452는 dispatch13개·Once21개 모두 통과했으며73fresh/final73·cleanupTrue다. 원 전체 lifecycle/원 claim_writer code를 실행하지만 IO/Job/프로세스는 synthetic이다. 승인 거부·잘못된 callback/문맥·닫힌 제어기·소유자 변경·source guard 실패·원 Native와 정리의 동시 오류·독립 판정 실패·성공/실패 후 반복 차단을 검사했다. 실제 Native/제품 자격이나 현재 입력 범위 확장의 근거로 쓰지 않는다. 새 dispatch와 시험 파일은 실제 Native 입력 범위에 아직 편입하지 않았다.

모델449는 시험에서 callable 대신True를 전달한 오류,450은 보완 후32개 통과 기록이다.451은 기존 caught-failure 시험이 생성 뒤 승인 필드를 바꿔 origin 검사에서 먼저 거부된 기록이며452는 callback을 생성 시 전달하도록 고쳤다. 내부 실패를 잡아도 entry에 도달하지 않고 최초 원인을 보존한다는 원 조건은 유지한다. 모든 실패 원본과 기존70개 모델445/446의 당시 소스 기록은 보존하며 후자를 현재 변경 소스의 전체 재검증으로 승격하지 않는다.

현재 실제 기본 구성011/owned453은 current3071/whole3490/history419·원 구성425fresh/final425·연결21/21·독립 참조3/3·외부83/83·helper59/Native64·cleanupTrue다. 실제011 구성121.156초·외부136.859초·Job CPU8.406초·최고89.79MiB·active0/empty/handle closed를 확인했다. CPU cap6.25%·한 코어·BelowNormal·기존 RAM/기한 보호를 유지했고 자식/외부 합산 시스템CPU최고23.11%·가용RAM최저31.3661%, READY15 포함 명목597.172861초/600초다. 승인 함수 없음·Native/제품/GO/intent0이며 원제품/Native008/009/010/no-GO005를 재실행하지 않았다.

다음은 새 dispatch를 실제 명시적 입력 범위·새 인스턴스 구성 경로에 연결하고 결과 발행을 자격화하는 일이다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기를 유지한다. 근거는 `implementation/p09/evidence/p09-361-native011-current805-product-oracle-input-models452.v1.json`, `p09-361-native011-current805-product-lifecycle-construct011.v1.json`, `p09-361-native011-current805-product-oracle-input-construct-owned453.v1.json`이며 축약명도 같은 디렉터리다.

### 독립 판정 입력과 종료된 reader 분리

원 `oracle_inputs`의 다섯 입력 함수 본문과 독립 판정기·context 생성기·압축 해제 함수를 유지하면서 같은 실제 부모/Batch/Closing/Once에 연결했다. 예상 사례는 고정 STEP의 index165/before158·이전 수용 pin과 원 논리 참조3개의 독립 선언에서 얻는다. 원 context 생성기를 준비에서 한 번 호출해 정확한 단일 사례 인자를 확인하지만 후보 결과를 읽거나 판정기를 실행하지 않는다. 예전 목록의 `source_test_names`와 current805 물리 목록은 역할이 다르므로 서로 대체하지 않는다. 준비 참조 읽기를 미래 runtime 판정의 fresh credit로 재사용하지 않는다.

구성009/owned443은 최적화 reader의 로더가 이미 닫힌 원 구성 reader에 연결돼 새21개 입력 종료 검사가 실패한 원본이다. 기대21을19로 낮추지 않고 `oracle_reader_factory`에서 새 reader 전용 `PacedNamespaceLoader`를 만든다.010은 이전 reader의 읽기 횟수·바이트·snapshot·최종 hash 수가 바뀌지 않았음을 추가 확인한다. 원 process_policy의 `arm`은 같은 미사용 Once/부모/WAIT 경계를 확인하며 `attempts`는 원 audit의 허용 Popen 이벤트 횟수, `denied`는 모든 원 거부 이벤트의 같은 목록을 사용한다.

모델442의69개는 로더 보완 전 기록이고444는30초 제한 종료·cleanupTrue로 보존한다. 현재445/446은 같은70개 전체 선택을 정렬해 앞35개와 뒤35개로 나눠 실행했으며 각각35PASS·70fresh/final70·cleanupTrue다. 제한을 늘리거나 통과한 묶음을 누적 재실행하지 않았다. 두 결과의 실행 ID 합집합70·중복0과 같은 현재 source pin을 별도 감사한다.

실제 비실행 구성010/owned447은 current3071/whole3490/history419·원 구성425fresh/final425·새 연결21/21·독립 참조3/3·외부83/83·helper59/Native64·cleanupTrue다. 실제010은131.812초·외부148.625초, Job CPU8.594초·최고90MiB·active0/empty/handle closed, CPU cap6.25%·한 코어·BelowNormal을 유지했다. 자식/외부 합산 시스템CPU최고28.82%·가용RAM최저31.1558%, READY15 포함 명목597.170871초/600초이며 실제 Native 성공 보장은 아니다.

전체 실행 전환/Job commit/독립 제품 판정은 미완료다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기를 유지한다. 다음은 승인된 제품 진입점의 실행 조정과 실제 전환 검증이다. 이번 arm/이벤트/Frame/Native/제품/GO/intent는0이고 Native008/009/010·기존 제품/no-GO005 재실행과 접근 허용/한글/COM/OS 변경은 없다. 근거는 `p09-361-native011-current805-product-oracle-input-models445.v1.json`, `p09-361-native011-current805-product-oracle-input-models446.v1.json`, `p09-361-native011-current805-product-lifecycle-construct010.v1.json`, `p09-361-native011-current805-product-oracle-input-construct-owned447.v1.json`이며 모두 `implementation/p09/evidence/`에 있다.

### 원 제품 factory의 한 번 실행 제한

`product_audit_type`은 고정 원 AuditSelection의 등록과 원 공통 deny를 유지한다. 실제 원 부모의 private transfer.connect 의존성에서 factory만 선택하며 원 transfer.connect/Handoff 전체 함수·메서드 code를 고정 source와 대조한다. private loader의 import 별도 해석 형식도 모든 non-import AST를 원 순서로 컴파일한 전체 code와 대조한다. 기본 모듈·원 Job/Frame/READY15/제품10/자원 보호는 바꾸지 않는다.

허용 범위는 원 Once의 배타 intent/Native 승인 소비·원 실행 직전 체크, 실제 소유 Job, 첫 전체 Frame 경계, 원 Handoff.SPAWNING,202 source handle과 readonly descriptor/event의 정확한204개 순서다. 실제 원 spawn 호출 frame·11인자 command·실제 packet 길이/hash·cwd·pipes·flags·환경None을 확인한다. component 연결과 factory는 각각1회이며 다른 이벤트/실행 파일/환경/폴더/반복은 원 deny로 보낸다. strict-window가 전역 Popen을 임시 교체하므로 원 connect 인자로 받은 factory를 캡처해 그대로 사용한다. 자식을 만든 뒤 추가 guard 검사로 반환을 잃지 않고 원 source flags 복원·Job 배정/정리에 전달한다.

모델439의59개는 기존 lifecycle45개와 제품 factory/선언/private loader14개이며70fresh/final70·cleanupTrue다. 원 부모/launch/source handoff/READY/Window 코드를 사용하지만 IO/Job/프로세스는 synthetic이므로 실제 Native/제품 자격은 아니다. 원 대입 복원·다른 thread/임의 factory 호출 차단·guard 중단·생성 후 오류의 자식 유실 방지·전역 Popen 재귀 조회 금지를 확인했다.

이전 비실행 구성008/owned440은 current3071/whole3490/history419·원 구성425fresh/final425·연결16/16·외부78/78·helper59/Native64·cleanupTrue다. 원 deny wrapper 등록1회, 실제 component/factory/허용/거부 이벤트0, 미활성 scope와 private 의존성 복원을 확인했다. 외부 승인None·실제 Frame/제품/GO/intent0이며 실제 제품 생성 성공은 아니다. 당시 독립 판정 입력 연결과 실제 Native 전환/제품 실행이 남아 있었다. 현재010에서 입력 연결만 보완했고 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기는 유지한다.

모델434의 seconds 필드 예상 오류와 보완 후435의57개, 구성006/owned436의 공통 SELF 중복 선언, 보완 후437의58개, 구성007/owned438의 private 메서드 컴파일 형식 거부는 각각 원본으로 보존한다. 공통 SELF의 기존 입력 선언은 유지하고 중복 control 추가만 제거했다.439에서 실제 private 전달 클래스를 사용하는 시험도 포함했다. 원 성공 제품/no-GO005·Native008/009/010·실패006/007은 재실행하지 않는다.

실제008 구성111.062초·외부126.000초, Job CPU8.422초·최고88.64MiB·active0/empty/handle closed다. 기존6.25% cap·한 코어·BelowNormal·RAM/기한을 유지했고 외부 시스템CPU최고63.81%·가용RAM최저32.6756%·cleanupTrue다. READY15 포함 명목597.150703초/600초는 실제 완료 보장이 아니다. 근거: `implementation/p09/evidence/p09-361-native011-current805-product-process-audit-models439.v1.json`, `current805-product-lifecycle-construct008.v1.json`, `current805-product-process-audit-construct-owned440.v1.json`. 축약명에 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다. 아래431/구성005/433은 이전 경계 소스의 기록이다.

### 원 Once와 실행 전후 생명주기 연결

`bind_coordinator`는 원 Once의 전체 클래스 메서드와 생성자의 checkpoint bridge를 고정 전체 source에서 대조한다. `construct_entry`의 명시적인 outer 구성에만 checkpoint_route 의존성을 허용하며 기본 경로·외부 승인·Once 실행 순서·영구 intent·Native 승인 소비 본문은 유지한다. 콜백은 같은 bridge/_checked/원 부모 또는 원 execute의 실제 호출 frame과 같은 Once/부모/제어기를 확인한다. 임의 호출이나 바뀐 code·closure·문맥·종료 함수는 거부한다.

NEW/CLAIMING의 세 준비 체크는 원 route의 자원 검사를 호출한다. WAIT_ORIGINAL_NATIVE의 승인 직전에는 두 준비 owner가 실제 닫혔고 원 idle과 미사용 부모 상태가 유지되는지 확인한다. 이는 IO 허용이나 새 Native guard가 아니다. 최종 CHECKED_NOT_ACCEPTED 체크에는 전체 원 entry 반환·동일 결과·원 Native 종료·독립 판정1회·guard 정리가 필요하며 원 `_terminal`/`_checker`의 상태 검사만 사용한다. 닫힌 guard를 다시 호출하는 `_closed_oracle_case`를 사용하지 않고 실제 IO/Native 검사는 계속 원 route만 사용한다. 완료/실패 후 내부 entry/result 참조는 해제한다.

모델431의73개는 lifecycle45개·Once18개·승인 연결10개이며72fresh/final72·cleanupTrue다. 전체 원 entry/Once/부모를 통과하는 전환 모델의 IO/guard/Frame은 synthetic이며 실제 제품 자격이 아니다. 원 post-Native fixture의 종료/판정 후 `_terminal`/`_checker` 호출은 추가 source/guard 검사0으로 확인했다. 승인 없음/False·닫히지 않은 준비 owner·정리 미확인·잘못된 원 호출자·변경된 메서드와 실패 후 재시도를 차단한다.

실제 비실행 구성005/owned432는 current3071/whole3490/history419·원 구성425fresh/final425·연결13/13·외부78/78·helper59/Native64·cleanupTrue다. 경계 콜백은 연결됐지만 모든 실행 카운터0이며 실제 Native 전환·worker/제품/GO/intent 실행과 최종 제품 판정은 NOT_RUN이다. 실제 제품용 worker202 process audit와 독립 판정 입력 연결이 남아 있다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작 및 Native011 제품 GO 승인 대기는 유지한다.

실제005 구성110.750초·외부125.906초, Job CPU8.203초·최고86.76MiB·active0/empty/handle closed다. CPU cap6.25%·한 코어·BelowNormal·기존 RAM/기한을 유지했고 자식/외부 시스템CPU최고72.66%·가용RAM최저32.3980%·cleanupTrue다. READY15 포함 명목597.124034초/600초는 실제 완료 보장이 아니다. Native008/009/010·기존 성공 제품/no-GO005·구성004를 재실행하지 않는다.

근거: `implementation/p09/evidence/p09-361-native011-current805-product-coordinator-boundary-models431.v1.json`, `current805-product-lifecycle-construct005.v1.json`, `current805-product-coordinator-boundary-construct-owned432.v1.json`. 축약명에 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다. 아래427/구성004/430은 이전 제어기 소스의 기록이다.

### 입력 reader 생성 전 원 제어기 연결

`native011_product_lifecycle.controllers`는 원 준비 epochs, Native Handoff와 원 post-Job Handoff, preparation Checkpoint, post-Native Closing, source_checkpoint/connect_callback을 결합한다. reader 생성 전에 하나의 고정 checkpoint를 만들고 실제 구성 reader가 이를 캡처했는지 admission 시점에 확인한다. 같은 checkpoint로 생성한 실제 Batch·원 부모·원 독립 판정기를 연결하고 metadata 콜백의 원 reader admission을 선택한다. 종료 시 원 콜백 복원과 Closing/epochs 정리를 모두 수행하며 복원 실패도 guard 해제를 막지 않고 cleanup 실패로 남긴다. 같은 guard/시계를 이식하거나 실행 카운터를 초기화하지 않는다.

모델427의33개는 기존 lifecycle21개와 제어기/실제 private loader/지연 문맥 연결12개다.60fresh/final60·cleanupTrue이며 잘못된 reader·반복 바인딩·자원 중단·종료 복원 실패와 Native 없이 closing 진입을 차단했다. 소스 대조는 고정 전체 원본과 모든 대상 함수/메서드 code를 확인한다. 원 private loader의 import 별도 해석 때문에 bytecode가 다른 경우에도 모든 non-import AST를 원 순서로 유지한 동일 컴파일 입력과 전체 code를 대조한다. 원 본문·기본값 AST·보호 조건을 생략하지 않는다.

실제 비실행 구성004/owned428은 current3071/whole3490/history419·원 구성425fresh/final425·연결12/12·외부78/78·helper59/Native64·cleanupTrue다. 실제 같은 원 부모/Batch/checker와 콜백 바인딩 후 복원을 확인했다. Native metadata reader/Frame/제품/GO·원 Native 체크·closing guard·독립 판정 실행은0이며 원 relay는 PREPARATION, post-Native route는 정리 후 CLOSED_NOT_ACCEPTED다. 이 구성 확인을 실제 Native 전환·제품 또는 독립 판정 성공으로 승격하지 않는다.

구성003/owned423은 guard 생성 전 code 대조에서 실패했다. 하위 cleanupFalse와 외부 Job cleanupTrue를 보존한다. 모델420의 기본값 lambda 오인,421의 기존 post-Job override 예상 오류,424/425의 private compiler 차이 재현도 원본으로 남긴다.426은33개 보완 후 통과 기록이며427은 배타 출력004를 선택한 현재 소스다. source-sync429는 제어기 생성 전 실패003에 pipeline 필드가 있을 것으로 예상한 감사 오류이며 원본을 보존한다. 저장된 결과의 재검토만 수행하고 실제004·기존 제품·Native008/009/010·no-GO005·구성003은 재실행하지 않는다.

실제004 구성110.641초·외부125.328초, Job CPU8.266초·최고86.52MiB·active0/empty/handle closed다. 기존6.25% cap·한 코어·BelowNormal·RAM/기한을 유지했고 자식/외부 시스템CPU최고18.86%·가용RAM최저28.9661%·cleanupTrue다. READY15 포함 명목597.103357초/600초는 실제 완료 보장이 아니다. 다음은 실행 직전/최종 판정 직후 Once 체크의 원 제어기 전환, worker202 제품 process audit와 독립 판정 입력 연결이다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기는 유지한다.

근거: `implementation/p09/evidence/p09-361-native011-current805-product-controller-pipeline-models427.v1.json`, `current805-product-lifecycle-construct004.v1.json`, `current805-product-controller-pipeline-construct-owned428.v1.json`. 축약명에 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다. 아래 구성002/418/419는 이전 준비 문맥 소스의 기록이다.

### 실제 부모 문맥을 사용하는 원 준비 검사

`native011_product_lifecycle.preparation`은 고정 `batch_zlib_metadata`의 전체 source와 원 idle/ReadOnlyEpochs 여섯 메서드 code를 대조한다. private namespace의 문맥 선택기를 실제 원 제품 부모 문맥으로 연결하고, 원 idle의 batch/whole opening/Frame class·method/shared decoder/실행 카운터 검사를 그대로 실행한다. 예전 readiness closure를 만들거나 strict-window 함수를 바꾸지 않는다. 세 단계 순서·guard factory/검사·최초 실패 차단·정리 본문과 기본 모듈도 유지한다. seal은 단계 전환/문맥 바인딩에서만 확인하며 매 IO마다 추가 전체 source/AST 검사를 만들지 않는다.

모델417의21개는 lifecycle13개와 준비 연결8개이며55fresh/final55·cleanupTrue로 통과했다. 실제 원 준비 메서드의 construction/opening_and_metadata 정리 후 원 Handoff.arm이 WAIT_ORIGINAL_NATIVE로 전환함을 synthetic 의존성에서 확인했다. 잘못된 실제 문맥/실행 카운터, 주입된 readiness 함수, 보호 중단, 다른 owner, 단계 생략과 private dependency 변경은 차단된다. WAIT에서 metadata reader 없이 임의 체크를 호출해도 원 Native 차단이 유지된다. 이는 실제 전체 Native 전환의 자격은 아니다.

실제 비실행 구성002/owned418은 같은 새 제품 부모가 원 idle 전체 검사를 통과함을 확인했다. current3071/whole3490/history419·원 구성420fresh/final420·연결5/5·외부72/72·기본 helper59/Native64·cleanupTrue다. 기존 구성001의 입력 개수 예상 오류는 원 실패415와 별도 source 대조416으로 보존하며 재실행하지 않았다. 이번002는 준비 문맥 연결을 추가한 새 소스의 구성이다.

실제 구성123.063초·외부137.266초, 소유 Job CPU8초·최고85.84MiB·active0/empty/handle closed다. 기존6.25% hard cap·한 코어·BelowNormal·RAM/기한을 유지했고 외부 시스템CPU최고37.89%·가용RAM최저28.6213%·cleanupTrue를 확인했다. READY15 포함 명목597.083873초/600초는 실제 완료 보장이 아니다. 실제 전체 제어기/Native handoff, worker202 제품 process audit와 독립 판정 입력은 미완료다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작 및 Native011 제품 GO 승인 대기는 유지한다.

근거: `implementation/p09/evidence/p09-361-native011-current805-product-preparation-context-models417.v1.json`, `current805-product-lifecycle-construct002.v1.json`, `current805-product-preparation-context-construct-owned418.v1.json`. 축약명에도 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다. 아래414/구성001/416은 이전 소스의 기록이며 no-GO005의 이전3065개 범위나 제품 결과를 새 실행 증거로 승격하지 않는다.

### 원 전체 절차와 비실행 부모 연결 확인

`native011_product_lifecycle.py`는 원 `batch_product_runtime.execute_chain`과 `oracle_inputs`의 전체 code를 대조하고 Native011 결과 경로와 진행 label1개만 선택한다. 전체 code 역변환으로 opening→Native 실행→finally 종료 확인→whole closing→독립 판정 순서와 원 다섯 입력 판정 함수를 유지한다. 실행 오류와 종료 정리 오류가 겹치면 최초 실행 오류를 그대로 전파한다. 관련41모델414는 lifecycle13개·Once18개·승인 연결10개이며55fresh/final55·cleanupTrue로 통과했다. synthetic Job/Frame 시험이지 제품 자격은 아니다.

실제 비실행 구성001은 current3071/whole3490/history419·원 구성419fresh/final419·추가 연결4/4·기본 helper59/Native64·cleanupTrue다. 같은 원 제품 부모의 authorize closure, 동일 context/checkpoint와 미사용 Once 상태를 확인했다. 승인/intent/Native/GO/완전 entry 호출은0이다. 실제 준비/Native/종료 제어기 전환, worker202 제품 process audit, 독립 판정 데이터 연결은 미완료다. 구성 확인을 실제 전체 lifecycle 실행 또는 제품 성공으로 승격하지 않는다.

외부 owned415는 하위 구성 exit0/cleanupTrue 이후 입력 수를3072/3491로 예상해 실제3071/3490과 불일치했으므로 실패다. 원본을 보존한다. 원 절차 source는 이미 current 범위에 있어 control 역할 추가가 byte 범위를 중복 증가시키지 않고 신규 lifecycle 소스와 시험2개만 current 범위를 늘렸다. 구성 reader는 원 절차 source와 신규2개를 추가해416→419다. 저장된 결과와 현재 source의 재검토만 수행하며 실제 구성/Native/과거 성공 시험을 반복하지 않는다.

실제 구성114.907초·외부124.203초, 자식/외부 시스템CPU최고26.01%·가용RAM최저29.4766%·cleanupTrue다. CPU cap6.25%·한 코어·BelowNormal·기존 RAM/기한 보호를 유지했다. READY15 포함 명목597.073602초/600초는 실제 완료 보장이 아니다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작 및 Native011 제품 GO 승인 대기는 유지한다. 다음은 미연결 실제 제어기/제품 process audit/독립 판정 입력을 연결하는 일이다.

근거: `implementation/p09/evidence/p09-361-native011-current805-product-lifecycle-models414.v1.json`, `current805-product-lifecycle-construct001.v1.json`, `current805-product-lifecycle-construct-owned415.v1.json`. 축약명에도 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다. 아래 모델410/구성411은 이전 소스의 결과이며 no-GO005는 이전3065개 범위로 보존한다.

### 일회 실행 보호와 구성 전용 진입점

`native011_product_once.py`는 외부 함수가 정확히True를 반환한 뒤 고정 Native011 배타 intent를 요청하고, 원 제품 부모의 Native 승인 callback을 한 번만 허용한다. 기록은 실행 조정 출력이며 Native 바이트 credit나 외부 승인 자체가 아니다. 원 `successor_preparation_workspace_v1.publish`의 전체 source/code를 대조해 xb·완전 쓰기·flush/fsync·262144byte 상한을 그대로 사용한다. 실제 intent 쓰기는 아직 실행하지 않았다. 승인 없음/False/비boolean·중복 기록·publisher/원 entry 실패·재진입·다른 owner·잡아서 넘긴 차단 오류를 거부하고 최초 실패를 보존한다. coordinator는 GO·Job·Frame commit·제품 수용 결과를 만들지 않으며 원 entry 반환도 RETURNED_NOT_ACCEPTED로만 기록한다.

현재27모델410은 Once17개와 승인 연결10개를 실제 선택해 실행했고52fresh/final52·cleanupTrue다. 원 부모/Job/READY15/제품10에 연결한 모델도 포함되지만 Fake Job/Frame/프로세스이므로 Native/제품 자격은 아니다. 이후 실제 공통 once-entry 구성001/owned411이 current3069/whole3488/history419·worker202·원 구성416fresh/final416·handoff12/12·full18/18·승인 연결2/2·once2/2·외부68/68·cleanupTrue로 통과했다. 기본 helper59/Native helper64와 원 전체 실행 체인을 유지했다.

실제 원 execute의 authorize closure가 같은 Once.authorize_native를 가리키는지 확인했다. callback 설치는 실행 승인이 아니다. coordinator는 NEW·외부 승인 확인0·intent 쓰기0·Native 승인 소비0·완전 entry 호출0이며 실제 intent/runtime 파일도 없다. CLI는 구성만 허용하고 GO·Native/runtime·재시도 인자를 거부한다. 새 명시적 wrap은 원 구성 클래스의 subclass만 허용하며 구성 출력은 제한된 evidence 경로만 허용해 canonical runtime 출력으로의 우회를 막는다.

구성111.937초·외부126.484초, Job CPU7.5초·최고85.23MiB·active0/handle closed/cleanupTrue다. 원 한 코어·BelowNormal·CPU cap6.25%·RAM cap8%를 유지했고 외부 시스템CPU최고82.23%·가용RAM최저29.9214%, 하위74.4%/29.2330%였으며 보호 중단은 없었다. READY15 포함 명목596.906688초/600초는 실제 성공 자격이 아니다. 실제 전체 lifecycle 연결은False이며 다음은 승인 후 원 whole opening/실행/closing·empty Job 이후 Frame commit·독립 판정을 연결하는 일이다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작을 유지한다.

근거: `implementation/p09/evidence/p09-361-native011-current805-product-once-models408/409/410.v1.json`, `current805-product-once-entry-construct001.v1.json`, `current805-product-once-entry-construct-owned411.v1.json`。축약명에도 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다. 아래3067개 구성은 API 확장 전 소스, no-GO005는3065개 범위로 보존하며 현재3069개 Native 성공으로 승격하지 않는다. Native008/009/010·기존 제품·no-GO005를 재실행하지 않는다.

### 실제 제품 부모의 외부 승인 의존성 연결

`native011_product_authority_connection.py`와 해당9개 모델을 추가했다. 고정 원 `native011_product_parent_handoff.py`의 driver_type 전체 code를 대조하고 install 호출의 명시적 authorize 인자1곳·의존성 유무 보고 조건1곳만 연결하며 전체 AST 역변환으로 나머지를 복원한다. 원 install/execute·소유 Job/Frame·READY15/제품10·source/closing 코드는 그대로 호출한다. 기본 None 인스턴스는 영구 차단이며 새 인스턴스에 전달한 외부 함수만 원 execute가 호출할 수 있다. 모델의 True 반환 함수를 제품 실행 승인으로 사용하지 않고, 구성 중 승인 함수를 호출하지도 않는다. CLI는 인자 없는 구성만 허용하며 GO·runtime·재시도 옵션을 거부한다.

모델405의9개·50fresh/final50과 실제 구성002/owned406이 통과했다. 새 범위current3067/whole3486/history419·worker202·원 구성414fresh/final414·handoff12/12·기존 full 연결18/18·새 명시적 입력2/2·외부66/66·cleanupTrue다. 이번 실제 구성의 승인 함수는None이며 Native phase/Frame·worker·제품·GO·intent 소비·수용 증가는0이다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작과 Native011 제품 GO 승인 대기를 유지한다.

최초 구성001/owned404는 원 Native helper64 한도로 거부됐다. 새 진입점의 기본 import를 명시적인 고정 private source 의존성으로 옮겨 기본 helper59/Native helper64를 유지했다. 한도를 높이거나 sys.modules를 삭제/숨기지 않았고 실패 원본은 보존했다.002는 구성107.610초/외부121.719초, Job CPU7.531초·최고84.80MiB·active0/handle closed/cleanupTrue였다. 한 코어·BelowNormal·CPU cap6.25%·RAM cap8%를 유지했고 외부 시스템CPU최고23.11%·가용RAM최저29.5453%였다. READY15 포함 명목596.738797초/600초는 실제 실행 성공 자격이 아니다.

다음은 실제 실행용 진입점·배타 intent와 원 전체 opening/실행/closing·empty Job 이후 Frame commit·독립 제품 판정 연결이다. 현재 새3067개 범위의 Native/제품 실행은 NOT_RUN이다. 아래 no-GO005는 이전3065개 범위의 실제 READY/두 경계/EOF 증거로 보존하며 새 범위·승인 연결·제품 Job commit의 성공으로 승격하거나 재실행하지 않는다. Native008/009/010과 기존 성공 제품 시험도 재실행하지 않는다.

근거: `implementation/p09/evidence/p09-361-native011-current805-product-authority-models403/405.v1.json`, `current805-product-authority-construct001/002.v1.json`, `current805-product-authority-construct-owned404/406.v1.json`。축약명에도 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다.

### 전체 no GO 통합 진단 결과

실제 전체005/owned005는 `PASS_FULL_FRAME_WORKER202_READY_REAL_EOF_NOT_PRODUCT_OR_BATCH`와 `PASS_OWNED_FULL_FRAME_WORKER202_READY_REAL_EOF_NOT_PRODUCT_OR_BATCH`로 통과했다. current3065/whole3484/history419·worker202·412fresh/final412·cleanupTrue이며 현재 입력3065개198520878byte를 두 경계에서 각각 새로 읽어 합계397041756byte를 확인했다. source202 live coverage·202개 flags 복원·실제 child READY/EOF를 검증했다. 제품 GO/생성·Job commit·case_finished·수용 증가는0이므로 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작이다. no-GO 성공을 실제 제품 자격이나 Native011 GO 승인으로 승격하지 않는다.

원 읽기 전용 경계591.672초/600초·정리 포함 Native593.438초, 원 metadata325/Frame324 decode 합계4.102초/5초, READY5.610초/15초·자식 probe5.844초를 확인했다. 부모 원 checkpoint91회 누적벽시간0.038187초/최대0.028248초와 owned183회0.005355초는 관측 전용이다. 중첩 시간을 배타적 기여로 더하거나 이번5.610초를 이전003의 지연 원인 판정으로 쓰지 않는다. 제품10초가 이 Native 여유 안에 완료된다는 검증은 별도다.

whole opening3484개217002237byte, metadata342fresh/final342·691물리 read/query·157510626byte와 원1/2MiB·예약/반환 원장을 확인했다. 원 Frame JSON2151611byte/12part를 보존했다. 외부1100.328초는 구성118.765초·opening305초·Native593.438초·empty Job 후 terminal audit83.125초를 포함한다. 소유 Job CPU22.828초·최고148.96MiB·active0/handle closed/cleanupTrue, 한 코어·BelowNormal·CPU cap6.25%·RAM cap8%를 유지했다. 단계별 시스템CPU최고80.66%·가용RAM최저29.5307%였고 보호 중단은 없었으나 PC freeze 원인 해결을 주장하지 않는다.

실제 공통 구성004/owned400·준비005/owned401과 현재40모델399(72fresh/final72)가 먼저 통과했다. 실제005는 준비에서 한 번 만든 helper를 사용해 원 클래스/함수/global 불변을 확인하고 phase를 한 번 생성했다. 다음은 실제 제품 경로의 원 소유 Job·worker202·원 GO/10초·두 경계·empty Job 후 Frame commit/제품 판정 연결 자격이다. 현재 제품 경로는 외부 승인 의존성이 미제공된 차단 상태를 유지하며 no-GO 성공은 제품 실행 허가가 아니다. Native008/009/010과 실패001~004는 재실행/재분류하지 않는다.

근거: `implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-owned-precompiled-phase-models399.v1.json`, `current805-full-frame-worker-connection-construct004.v1.json`, `current805-full-frame-worker-connection-construct-owned400.v1.json`, `current805-full-frame-worker-owned-prepare005.v1.json`, `current805-full-frame-worker-owned-prepare-owned401.v1.json`, `current805-full-frame-worker-connection-probe005.v1.json`, `current805-full-frame-worker-owned005.v1.json`。축약명에도 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다.

#### 이전 실패와 최적화 기록

이전 실패 구간에서도 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작을 유지했다. `native011_full_frame_worker_owned.py`로 원3개 live epoch·Job 정리·실패 원본 보존·empty Job 이후 감사를 유지한 실제 전체 no-GO 진단을 실행했다. 제품 GO/생성·intent 소비·수용 증가는0이었다. 아래 구성 기록의 NOT_RUN과 실패001/002/003/004는 당시 상태로 보존하며 이후005 통과는 앞 절을 따른다. Native008/009/010 재실행과 Native011 제품 GO는 포함하지 않는다.

이전004는 관측을 포함한 준비004/owned395 이후 실행했지만 Native 입력 잠금 획득 중 `STOP_NATIVE_OPEN_AFTER_HOST_SATURATION`으로 종료됐다. 외부573.156초·구성116.375초·opening305.359초·Native151.422초·cleanupTrue이며 완성 바이트 경계0·자식 생성0·START/READY/GO0이다. 단계별 시스템CPU최고88.91%·가용RAM최저30.6940%와 원 내부 획득 checkpoint의90% 경고 정지는 서로 다른 sampler/시점의 관측이다. 외부 Job CPU13.562초·최고109.98MiB·active0/handle closed이며 한 코어·BelowNormal·CPU cap6.25%·RAM cap8%를 유지했다. 이 실행은 READY에 도달하지 못했으므로 준비 비용 관측도 실제 미실행이다. 당시 기여 프로세스나 PC freeze 원인을 확정하지 않는다.

보호 중단 뒤 `native011_full_frame_worker_ready.prepare_phase`로 준비 단계와 Native 생성 시점에 중복되던 실행/읽기 helper 검증·컴파일을 한 번으로 합쳤다. 원 source/code와 전체 AST 역변환은 준비에서 수행하고, Native 생성 전 원 클래스 구성·함수 code/defaults/closure·global binding 불변을 확인한다. 같은 factory의 생성 시도는1회이며 실패해도 재사용할 수 없다. 준비 중 Native phase/Frame·metadata reader·예산을 만들지 않고 실제 두 입력 경계·hash/JSON·최종 확인·원 guard·Native600/READY15/decoder5/제품10을 유지한다. 원 CPU 급등 해결이나 전체 실행 성능 향상 판정은 아니다.

결합40모델397·72fresh/final72·cleanupTrue가 helper 구성1회/Native 생성 시 재컴파일0·원 두 실제 모델 경계·함수/global 변경 거부·실패 factory 재시도 금지를 확인했다.396의 테스트 __code__ 원복 오류와 연쇄 거부는 원본 보존 후 테스트 원복 경로를 수정했다. 다음은 최적화된 공통 부모의 새 구성 자격과 새 준비 증거를 만든 뒤 별도 전체 진단에서 READY 관측을 수행하는 일이다. 기존004와 준비004는 마지막 helper 최적화 이전 소스이며 현재 실행 자격으로 재기반하지 않는다. 같은 실패의 즉시 반복·자동 retry·시간 제한 증가는 하지 않는다.

근거: `implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-owned-gate-observation-models394.v1.json`, `current805-full-frame-worker-owned-prepare004.v1.json`, `current805-full-frame-worker-owned-prepare-owned395.v1.json`, `current805-full-frame-worker-owned004.v1.json`, `current805-full-frame-worker-connection-probe004.v1.json`, `current805-full-frame-worker-owned-precompiled-phase-models396/397.v1.json`。축약명에도 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다.

전체001은 Windows Popen audit의 executable=None과 정확한 executable 정책의 불일치로 `CURRENT805_SHARED_NO_PROCESS`가 발생했다. 동일 Python executable을 명시하는 호출로 수정했으며 실제 Windows audit 경계에서 OS 생성 전에 중지하는 모델385가 통과했다. 전체003에서는 실제 child Popen 허용1·다른 Popen 거부0·자식 생성/START 전송이 확인됐다. 허용 조건이나 다른 프로세스 차단을 완화하지 않았다.

전체002는 구성14.375초에 시스템CPU95.71%로 보호 중단했다. 소유 Job CPU0.875초·최고46.54MiB·잔류0/cleanupTrue였고 CPU상한6.25%·한 코어·BelowNormal·RAM8% cap을 확인했다. 가용RAM최저30.8212%/commit49.5172%로 RAM 중단은 아니다. 당시 CPU 기여 프로세스는 특정하지 못했으므로 Defender나 검증의 간접 유발 원인을 확정하지 않는다.

중복 최적화는 같은 사전 reader에서 이미 새로 읽은19개 source pin을 준비 증거와 대조하고 나머지17개를 새로 읽는 방식이다. reader의 두 번째 사용은 거부하고 최종 fresh hash/실제 Native 두 경계를 유지한다. 원 함수4개 code 확인도 같은 compile profile에서 수행한다. 확인 전 원 함수가 호출되던 순서 오류는 실패 모델387을 보존하고 수정했다. 모델388의25개·55fresh/final55, 별도 판정기 모델389의13개·44/44, 실제 준비003/owned390의41/41이 통과했다. 이전 성공 이력 전체를 매번 제품 시험으로 재실행한 결과가 아니다.

전체003은 외부937.016초에 `WORKER_READINESS_PREPARATION_TIMEOUT`으로 실패했다. 구성116.657초·opening304.796초·읽기 전용515.563초이며 원 Native600을 늘리지 않았다. 실제 opening3484개216994897byte, metadata342fresh/final342·691물리 read/query·157510752byte와 원1/2MiB 원장을 남겼다. 원 전체 Frame1633584byte/10part를 보존했다. READY15 대기15.140초/95회·준비 신호 미확인·GO0이며 자식 내부 Job CPU1.016초/최고32.28MiB·active0, 외부 Job CPU18.438초/최고127.74MiB·active0/handle closed/cleanupTrue다. 단계별 시스템CPU최고70.27%·가용RAM최저29.6878%로 이번 종료는 CPU/RAM 보호가 아니다. 두 번째 경계·READY/실제 EOF 통합 성공이나 제품 자격은 인정하지 않는다.

003 이후 원 Gate checkpoint/owned 함수를 그대로 호출하며 호출 수·실패 수·벽시간·CPU 시간을 구분하는 관측을 새 준비 증거에 연결했다. 관측은 입장 판정·예산에 사용하지 않고 READY15/Native600/decoder5/제품10·기존 검사·GO 차단·실패 고착·정리를 보존하며 추가 대기/재시도를 하지 않는다. 당시 단독13모델391과 결합38모델392(72fresh/final72)가 통과했다. 실제003에 관측을 소급 적용하지 않으며 관측 변경 후 준비003은 현재 소스의 실행 자격이 아니다. 이후004와 현재 helper 최적화·다음 실행 경계는 이 절의 최신 기록을 따른다.

근거: `implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-owned001/002/003.v1.json`, `current805-full-frame-worker-connection-probe001/003.v1.json`, `current805-full-frame-worker-owned-models385/387/388.v1.json`, `current805-full-frame-worker-owned-validation-models389.v1.json`, `current805-full-frame-worker-owned-prepare003.v1.json`, `current805-full-frame-worker-owned-prepare-owned390.v1.json`, `current805-full-frame-worker-ready-gate-observation-models391.v1.json`, `current805-full-frame-worker-owned-gate-observation-models392.v1.json`。축약명에도 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다.

### 전체 Frame과 no GO worker 종료 판정

`native011_full_frame_worker_validation.py`는 고정 원 판정기3개 함수의 code를 대조하고 전체 AST 역변환으로 source201→202 숫자4곳·오류 label2곳·진단 worker1/GO0 분리1곳·실제 metadata factory 선택1곳·미사용 allocator 속성 경로2곳만 선택한다. 원 두 전체 byte 경계/물리 byte·raw policy 복원·모든 handle/stream 정리·Native600·decoder5/325·324 횟수·원 의도적 BROKEN 판정은 보존한다. 후보의 자기 보고 대신 고정 원201과 검증된 child202의 선언을 읽고,202개 실제 source pin이 원 전체 Frame 첫 경계와 정확히 일치해야 한다. 이전 byte/READY 결과를 새 실행 credit로 쓰지 않는다.

추가 판정은 원 READY15·실제 EOF·child source 첫/최종202·소스 digest·product 생성0·동일 Job·부모 cap 아래 준비 전용 상대 quota·empty Job·flags/descriptor 정리·부모 byte credit 불변을 검사한다. 제품 Job commit과 수용 증가를 허용하지 않는다. 원 Frame 복원 함수는 한 판정에서 한 번 호출하고 복원한 같은 객체에 추가 검사를 수행한다. 다음 판정에서는 실제 part를 다시 복원하며 parsed evidence 캐시를 만들지 않는다. 실제 metadata 재지정1회·원 두 문장 prefix·첫/최종 semantic hash·물리 read/query·예약/반환/pacing 원장·실제1/2MiB를 교차 확인한다.

기존 metadata 보고의 고정2.5/4MiB 표시는 `native011_full_frame_worker_connection.py`에서 실제 adoption 상태와 paced byte를 확인하는 보고로 보완했다. 원 metadata_evidence의 전체 ledger 검사는 그대로 호출하고 기존 속도 표시는False, 실제1/2MiB·adoption/바이트 기록을 별도 필드로 반환한다. private view에서도 같은 owner의 메서드를 사용하며 재지정 누락·원장 불일치는 거부한다. 모델378의14개·42fresh/final42와 판정기 모델381의13개·45fresh/final45가 통과했다.381에는 고정 선언 receipt2개의 첫·최종 확인이 포함된다.379의12개는 고정 선언 getter 추가 전 소스로 보존한다.

실제 connection-construct003/owned380은 current3065/whole3484/history419·명시적control70·구성412fresh/final412·제품 handoff12/12·새 진단 source18/18·외부61/61·default helper59·cleanupTrue로 통과했다. 구성 단계114.562초/외부127.156초, JobCPU7.891초·최고85.58MiB·active0/empty/handle closed였다. machine cap6.25%·한 코어·BelowNormal·원 RAM/기한을 유지했고 시스템CPU최고34.37%·가용RAM최저29.2552%다. 판정기 모델381의 시스템CPU최고74.9%·가용RAM최저30.9372%도 보존하며 PC freeze 해결은 주장하지 않는다. 원 실행기와 독립 판정기의 READY15 포함 명목596.569311초/600초·여유3.430689초는 실제 실행 성공 자격이 아니다.

위 구성003 당시 metadata 본문/Native Frame·자식·GO·제품·intent 소비는0이었고, 실제 외부 monitor 연결과 전체 no-GO 실행은 NOT_RUN이었다. 이후 실제 진단과 실패는 앞 절을 따른다. 원 Job commit·제품 실행 자격/권한·독립 제품 판정과 Native011 GO 승인은 별도다. 근거: `implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-connection-models378.v1.json`, `current805-full-frame-worker-validation-models381.v1.json`, `current805-full-frame-worker-connection-construct003.v1.json`, `current805-full-frame-worker-connection-construct-owned380.v1.json`。축약명에 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다.

### 공통 읽기 전용 driver와 고정 자식 생성 경로

`native011_full_frame_worker_connection.py`는 원 읽기 전용 Driver.run/finish 전체 본문에 상태 전달용 private view와 worker202 phase를 연결한다. 기본 owner는 construct_only와 제품 실행 차단을 유지한다. 원 metadata callback은 이미 검증된 OwnedPacer 연결을 통해 원 두 문장 할당/재지정을 먼저 실행하도록 선택한다. allocation1곳의 전체 AST 역변환으로 callback·helper 읽기·hash/JSON·closing 본문을 보존한다. 기본2.5/4MiB 준비 할당을 제품1/2MiB 할당의 대체 자격으로 쓰지 않는다.

process audit은 원 shared constructor의 deny 함수 전체 code와 closure 역할을 대조한다. 실제 SOURCE_FLAGS/첫 전체 Frame 경계에서 같은 thread·정확한 worker202 명령·cwd·pipes·BelowNormal/NO_WINDOW·204개 명시적 handle을 만족하는1회만 허용한다. 창·shell·다른 executable/경로/인자·다른 thread·재시도는 원 deny가 계속 차단한다. 생성된 process는 후속 검사로 잃지 않고 기존 handoff/Job 정리에 반환한다. 기본 구성 모드에서는 예외 audit hook을 등록하지 않는다. `--whole-no-go`는 원 NoGoReadySink와 실제 EOF를 쓰는 진단 모드이며 제품 GO나 canonical Native011 실행/intent를 허용하지 않는다.

이전 connection-construct002/owned376은 metadata 보고 보완 전 current3065/whole3484/history419·명시적control70·구성412fresh/final412·제품 handoff12/12·별도 진단 source17/17·외부61/61·default helper59·cleanupTrue로 통과했다. 모든17개 pin은 직접 current 입력과 대조하고 별도 reader를 한 번만 종료했다. 원 구성 reader를 재사용/초기화하지 않고 metadata reader/예산·whole opening·Native Frame·자식·제품·GO·intent 소비는0이다. 원5클래스 Frame/base와 실행기/독립 판정기의 같은 complete model을 확인했다. 모델375의13개·41fresh/final41에는 직접 읽는 audit/engine fixture의 첫·최종 확인도 포함했다.372의 load 인자 fixture 오류와 보완 전373은 원본으로 보존한다.

최초 연결001/owned374는 할당 보완 전 current3063/whole3482·410/410·진단12/12·외부57/57의 구성 기록이다. 이후 읽기 전용 metadata 할당과 현재 제품의 OwnedPacer 재지정 차이를 코드에서 확인해002에서 기존 연결을 적용했다. 당시 구성 단계106.797초/외부120.015초, JobCPU7.625초·최고85.57MiB·active0/empty/handle closed였다. machine cap6.25%·한 코어·BelowNormal·기존 RAM/기한을 유지했고 시스템CPU최고75.51%·가용RAM최저29.6082%다. 순간75% 초과 표본은 있었지만 준비 정책 보호 중단은 없었으며 실제 Native 보호는 완화하지 않았다. 당시 READY15 포함 명목596.566371초/600초·여유3.433629초는 실제 실행 성공을 보장하지 않는다. 최신003은 위에 구분한다.

이 단락의 구성 당시 실제 전체 no-GO 실행은 NOT_RUN이었다. 기존 owned 종료 판정기는 source201·worker0·이전 metadata 속도용이므로 새 결과를 그대로 통과시키지 않는다. 이후202 source·진단 worker1·원1/2MiB metadata·실제 READY/EOF/정리를 검사하는 판정기를 연결한 실행과 실패는 앞 절을 따른다. 원 Job commit·제품 실행 자격/권한·독립 제품 판정과 Native011 GO 승인은 별도다. 근거: `implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-connection-models375.v1.json`, `current805-full-frame-worker-connection-construct001/002.v1.json`, `current805-full-frame-worker-connection-construct-owned374/376.v1.json`。축약명에 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다.

### 전체 Native 읽기 사이의 worker 준비 진단 구성요소

`native011_full_frame_worker_ready.py`는 원 첫 전체 Native 읽기와 source flags 복원 뒤에 worker202의 READY·실제 EOF 확인을 넣고, 그 뒤 원 두 번째 전체 읽기를 유지한다. 고정 source와 원 NativePhase의 모든 메서드 code를 대조하며 기본 클래스는 변경하지 않는다. private run의 기대값201→202/오류 label은 전체 code 역변환으로, 진단 결과의 worker 개수0→1은 전체 class AST와 원 메서드 code 역변환으로 확인한다. 저장한 원 parent wrapper를 선택할 때도 실제 설치된 제품 진입점의 차단은 유지하고 원 no-product delegate만 호출한다.

자식 전달은 기존 Handoff·Gate15·NoGoReadySink와 원 child 판정기/cleanup을 사용한다. 자식의 실제 EOF/202개 첫·최종 source digest/정리와 product 생성 시도0을 확인해야만 다음 읽기로 진행한다. 원 Native guard/600초 안에서 실행하며 자식 검증기가 부모 Frame/guard를 닫거나 시계를 새로 시작하지 않는다. 부모 전체 stream 카운터/identity를 보존하고 자식의 읽기를 Native byte credit로 더하지 않는다. Gate에서 실제 자원 오류가 나면 EOF 대기 전에 원 오류를 보존하며, 정리 실패를 통과시키지 않는다. nested Job은 검증된6.25% 부모 아래의 준비 전용 상대 quota이며 제품 Job 정책·commit의 자격이 아니다.

모델370의13개·52fresh/final52·cleanupTrue가 통과했다. 첫 읽기/flags 복원/콜백/둘째 읽기 순서, 원600초 만료·잘못된 Job·flags/child/정리 실패, 원 오류 보존과 재시도 거부를 검사했다. 최신 시험의 시스템CPU최고12.89%·가용RAM최저34.0609%다. source 대조 fixture 오류367과 gate 이전 pipe fixture 오류369는 원본으로 보존하고,368의12개는 보완 전 소스로 구분한다.

당시 공통 읽기 전용 driver 미설치 상태는 위 connection-construct002/owned376으로 갱신했다. 실제 전체 Native 실행·자식 생성은 여전히 NOT_RUN이다. 아래 이전 구성365의 current3059/whole3478이나 원596.064595초 모델을 새 구성요소의 실제 실행 자격으로 재사용하지 않는다. 제품 GO·원 Job commit·Native011 실행 승인은 별도다. 근거: `implementation/p09/evidence/p09-361-native011-current805-full-frame-worker-ready-models367/368/369/370.v1.json`.

### 실제 공통 부모의 worker 소스 전달 연결

`native011_product_parent_handoff.py`는 이미 구성된 공통 부모의 private Window10 연결 의존성만 선택한다. 원 strict 실행 함수의 전체 code와 closure, 원 metadata reader와5클래스 Frame 연결을 보존한다. 원 Context가 실제 Job을 관찰하며, Frame과 handle을 미리 만들지 않고 원 Popen 시점에 첫 전체 byte 경계와 같은 Job·실제 Frame type을 확인해202개 소스를 전달한다. 원 Gate15와 Input10/완전 capture 코드를 그대로 사용하며 새 Job·sampler·worker 재구성은 추가하지 않는다. 외부 실행 승인 의존성이 없으면 원 소유 범위·IO·Job 진입 전에 거부한다.

실제 handoff-construct002/owned365가 current3059/whole3478/history419·명시적control64·구성406fresh/final406·별도 연결 입력12/12·외부49/49·cleanupTrue로 통과했다. default helper59와 worker202 직접 현재 입력/누락·충돌0, 원 실행기/독립 판정기 동일 모델을 유지했다. Job·Frame·worker·GO·제품·intent 소비와 metadata reader/예산 생성은0이다. 이는 실제 연결의 구성 자격이며 전체 Native 경계에서 소스 전달·원 Job commit·제품 실행을 통과한 결과는 아니다.

최초 구성001/owned363은 원 구성 원장에 finish를 두 번 호출해 `audit_final_hash_inventory`로 실패했다. 원 실패와 cleanup을 보존한다.002는 원 원장을 한 번만 종료하고 같은 guard 아래 새 연결의 명시적12개 입력을 별도 reader로 읽는다. 각 pin을 현재 Native 선언과 대조하고 첫·최종12/12를 확인한다. 카운터 초기화·과거 이력의 중복 전체 검사·hash/AST/JSON 캐시·Native byte credit 재사용은 없다. 원 Job과 capture cleanup을 유지하고 최종 소스 handle 정리 미확인은 성공 반환을 차단한다. 모델364의14개·45fresh/final45가 통과했으며359/360의 모델 이름 참조 오류와 수정 전361/362 결과는 당시 소스로 보존한다.

최신 구성 단계103.032초/외부114.500초, JobCPU7.078초·최고84.92MiB·active0/empty/handle closed였다. machine hard cap6.25%·한 코어·BelowNormal·기존 RAM/기한을 유지했고 시스템CPU최고25.76%·가용RAM최저32.1872%다. READY15 포함 명목596.064595초/600초·여유3.935405초는 실제 실행 성공을 보장하지 않는다. 다음은 실제 전체 Native 경계에서의 소스 전달과 원 Job 정리/commit·완전 실행 자격/권한·독립 제품 판정이다. Native011 GO는 미승인이며 통과한 제품 사례나 전체 준비001/읽기 전용008을 반복하지 않는다.

근거: `implementation/p09/evidence/p09-361-native011-current805-product-parent-handoff-models364.v1.json`, `current805-product-parent-handoff-construct001/002.v1.json`, `current805-product-parent-handoff-construct-owned363/365.v1.json`。축약명에는 같은 디렉터리와 `p09-361-native011-` 접두사를 적용한다.

### 검증된 worker202의 공통 Native 부모 선언

`native011_product_worker_scope.py`는 고정 no-GO202 결과의 실제 두 source 경계/READY15/EOF/정리와 전체 source digest를 대조하고, 원201 및 새 child entry pin이 현재 구성의 선언과 정확히 일치해야만 새202를 admit한다. 원 공통 inspector는 보존한다. 새 private inspector는201→202 기대 개수와 결과 숫자·오류 label만 변경하고 전체 AST 역변환으로 raw 직접 현재 입력/보존419/논리·물리 재합성/원5클래스 Frame/base 판정을 유지한다. 원 admission에서 방금 fresh 확인한201은 같은 구성의 값으로 대조하고 qualifier 추가11개만 fresh 확인한다. 원 closing과 미래 Native 전체 읽기를 생략하지 않는다.

`native011_product_parent_construction.py`의 실제 parent-construct001/owned357은 current3057/whole3476/history419·control59·401fresh/final401·외부37/37·cleanupTrue로 통과했다. worker202가 모두 직접 current에 포함되고 누락·충돌이 없으며 원 OwnedPacer metadata 선택과 실행기/독립 판정기의 같은 complete model을 확인했다. 원 worker201 진단 key는 호환용 이름으로 남기되 실제 값202와 명시적인 worker202 필드를 함께 기록한다. 모델355의7개·34fresh/final34, 부모 모델356의4개·33fresh/final33도 통과했다.

구성은 자식100.344초/외부109.844초, JobCPU7.547초·최고83.79MiB·active0/empty/handle closed였다. machine cap6.25%·한 코어·BelowNormal·기존 RAM/기한을 유지했고 자식/외부 시스템CPU최고25.14%·가용RAM최저30.6975%다. READY15 포함 명목595.888196초/600초·여유4.111804초는 실행 성공 자격이 아니다. reader/예산/whole opening/본문/Native Frame/worker/GO/제품/intent 소비는0이다.

이전 parent-construct001/owned357에서는 제품 launch handoff를 설치하지 않았으며, 최신 설치 구성은 위 handoff-construct002/owned365로 구분한다. 기존 no-GO202/전체 준비001/읽기 전용008을 단순 반복하거나 이전 byte 경계를 새 current로 재기반하지 않는다. 근거: `p09-361-native011-current805-product-worker-scope202-models355.v1.json`, `current805-product-parent202-models356.v1.json`, `current805-product-worker202-parent-construct001.v1.json`, `current805-product-parent202-construct-owned357.v1.json`。축약명에 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

### 새 child202의 실제 소스 전달과 READY

`native011_product_worker_ready_probe.py`의 실제 ready002/owned353이 통과했다. 부모213fresh/final213·외부20/20, 실제 child202fresh/final202·pin digest 일치·전 source 최소2회 실제 읽기, 부모202개 전후 byte 경계와 원 coverage를 확인했다. 원 Gate는7.5초/15초에 READY를 관측한 뒤 고정 NoGoReadySink에서 GO를 거부했고 실제 EOF를 전달했다. child는 원 WORKER_NOT_AUTHORIZED/exit1·GO 관측False·제품 생성 시도0으로 종료했다. child202 handle과 부모208 handle은 전부 닫혔고 원 owned Job active0·cleanupTrue다. Frame은 COMMITTED가 아닌 CLOSED이며 전체 제품 Native corpus의 경계나 Job commit 자격이 아니다.

소유 inner Job은 CPU2.438초·최고53.8MiB였고 검증된 parent machine상한6.25% 아래에서만 inner relative100%를 사용했다. 한 코어·BelowNormal·원 RAM/commit/기한을 유지했고 Native 정책은 바꾸지 않았다. 자식/외부 합산 시스템CPU최고31.89%·가용RAM최저29.0094%다. 부모213/외부20 source closing과 실제 Job 정리는 전체 PC freeze 해결을 입증하지 않는다.

최초 ready001/owned351은 원 READY15.016초 timeout으로 실패했고 failure/cleanupTrue를 보존했다. child의202개 IO·EOF·정리는 완료됐지만37.234초로 늦었다. 첫 실행의 구간 계측 부재로 scheduling/IO/외부 반응 등 원인은 특정하지 않는다. 기한/속도를 바꾸거나 READY 이전에 child를 초기화하지 않고 단계 wall/CPU 및 기존 카운터만 추가했다.002는 constructor 반환6.234초·closing7.359초·원 readline7.375초,601 streams/6228587byte/ReadFile1206회·reader 대기2.287초였다. 이 계측 추가 후 통과를 성능 개선이나 원인 해소로 주장하지 않는다.

부모 정리는 이미 복원 완료된 flags를 닫힌 Frame 뒤에 다시 조회하지 않도록 보완했다. 모델350의20개(부모16+probe4)·43fresh/final43, child 계측 모델352의13개·33fresh/final33이 통과했다. 다음은 새202 자격을 공통 Native 부모의 명시적 source/실행 연결에 반영하고 원 Job commit·전체 비용·권한/독립 제품 판정을 결합하는 일이다. 원 EOF201과 그 full Native 경계는 새202/새 current에 재기반하지 않는다. Native011 GO는 미승인이며 제품/intent 소비·accepted delta는0이다. 근거: `p09-361-native011-current805-product-worker-ready001.v1.json`, `current805-product-worker-ready002.v1.json`, `current805-product-worker-ready-owned351.v1.json`, `current805-product-worker-ready-owned353.v1.json`, `current805-product-worker-ready-models350.v1.json`, `current805-product-worker-entry-trace-models352.v1.json`。축약명에 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

### 상속 소스를 사용하는 제품 child 진입점

`native011_product_worker_entry.py`는 부모의 명시적 mapping 인자와 실제 START를 읽은 뒤 원 SourceReader/HeldSources/SourceImports로 선언된 소스를 사용한다. 원 worker.prepare와 전체 선언의 첫·최종 확인을 마친 뒤 원 ReadyReader/worker.main을 호출한다. EOF나 잘못된 stdin을 GO로 바꾸지 않는다. 제품 생성은 실제 GO를 관측한 뒤 원 worker arguments·EXE·cwd에 정확히 일치하는 최초1회만 허용하고 다른 process/exec 경로는 거부한다. 원 worker의 Job/GO/once-only policy와 제품10초는 그대로다.

새 source_declaration은 원 권위 있는 EOF201 선언 검증을 그대로 호출하고 새 child 파일1개를 더한202개를 명시적으로 fresh 대조한다. 이는 새 qualification을 위한 선언 API이며 실제202개 소스/READY/Native의 완료 결과가 아니다. 기존201을 교체하거나 제품 자격으로 재판정하지 않는다. 종료 출력은 전체 source pin 집합의 digest·개수·closing과 원 worker 반환 코드/정리 요약만 포함하며 전체 source 목록/로그나 제품 수용 결과를 만들지 않는다. import finder 순서가 달라도 다른 hook을 제거하지 않고 상속 source 닫기를 반드시 시도한다.

모델348의12개·33fresh/final33·cleanupTrue는 계측 추가 전 소스로 보존한다. 인자/GO·EOF 보존, 완전 closing/제품10초/원 arguments 의존성, 제품 생성 전 GO와 정확한 명령, source202의 명시적 추가, 오류 시 원본 보존과 정리의 당시 결과다. 최신 child 계측 모델352/실제 no-GO002는 위에 구분했다. 원 Job commit·완전 비용·권한/독립 제품 판정은 별도다. 근거: `implementation/p09/evidence/p09-361-native011-current805-product-worker-entry-models348.v1.json`.

### 제품 worker의 부모측 소스 전달

`native011_product_source_handoff.py`는 원 SourceInheritance와 DescriptorMapping으로 실제 Frame에 선언된 worker 소스 handle을 전달하도록 구현했다. 기존 launch와 readiness connector의 함수 본문은 바꾸지 않고 scoped factory/Job 확인/Gate checkpoint 의존성만 연결한다. 명시적 entry pin은 실제 Frame과 같은 root/선언 안에 있어야 하며 원 stdin/stdout/stderr·BelowNormal/NO_WINDOW·명시적 상속 목록을 보존한다. 임의 shell/다른 root/과도한 handle 정수/변형된 Gate 메서드는 거부한다.

부모의 source 상속 flags와 descriptor는 spawn 직후 복원·닫는다. 생성 전 오류는 원 오류로 종료하고, 생성 후 복원/설정 오류는 실제 process를 기존 소유자에게 반환해 원 Job 배정·cleanup을 잃지 않으며 START/GO 전에 실패한다. 준비 START는 실제 Gate15의 시계와 Job 확인이 시작된 뒤 raw pipe에 한 번만 전달한다. 기존 Input10에는 실제 GO만 도달하므로 준비가 제품 시계를 미리 시작하지 않는다. 전체 coverage는 원 source loan과 첫 START 경계에서 확인하고, 매 이벤트 대기에는 원 live Frame/자원/Job 검사를 유지한다. 새 매-wait 전체 스캔, source/hash/JSON/AST 캐시, 검증 credit 재사용은 없다.

모델344의15개·41fresh/final41·cleanupTrue는 cleanup 보완 전 소스로 보존한다. 실제 원 launch·Gate·Input10 코드를 함께 사용한 모델은 START 전 product clock 미시작, 실제 GO에서만 시작, 동일15/10 한도와 완전 capture를 확인했다. 테스트의 파일/Frame/프로세스/OS API는 모델이며 그 자체로 실제 Native·제품·OS handle 전달 자격은 아니다. 최신 모델350/실제 no-GO002는 위에 구분했다.342/343도 수정 전 모델로 보존한다.

당시 부모 구성요소의 미설치 상태는 위 실제 공통 부모 handoff-construct002에서 갱신했다. 부모·자식의 실제 전체 Native source 전달·원 Job commit·완전 실행 자격/권한·독립 제품 판정은 남아 있다. 기존 EOF-only child/source201 수용을 새 제품 child의 source/GO 자격으로 승격하지 않는다. 새 코드의 Native current 명시 선언을 유지하며 통과한 EOF208/전체 준비001/읽기 전용008을 단순 반복하지 않는다. 근거: `implementation/p09/evidence/p09-361-native011-current805-product-source-handoff-models344.v1.json`.

### 공통 진입점의 실제 OwnedPacer 연결

`native011_engine_owned_metadata_validation.py`는 원 공통 validate 전체 source pin/함수 코드를 대조하고 metadata factory 선택1곳만 OwnedPacer 재지정용 연결로 바꾼다. 전체 AST 역변환으로 기존 source201·비용·decoder5·자원·기한 판정을 보존한다. main은 원 code/default/closure를 그대로 사용하고 private validate 의존성만 교체한다. 새 연결은 원 fresh private_source로 구현을 읽으며 기본 모듈과 원 실행기/독립 판정기 본문은 바꾸지 않는다. 모델339의7개·46fresh/final46 및 진입점 모델337의4개·33fresh/final33이 통과했다.

`native011_engine_owned_metadata_entry.py`의 실제 구성001/owned340은 current3045/whole3464/history419·control47·389fresh/final389·외부33/33·cleanupTrue로 통과했다. 새 원1/2MiB 재지정 selector와 원 실행기/독립 판정기의 동일 complete model을 확인했다. READY15 포함 명목594.886776초/600초는 모델이며 실제 제품 완료 자격이 아니다. metadata reader/예산/whole opening/본문/Native Frame/worker/GO/제품/intent 소비는0이다. 전체 준비001의 current3049/whole3468과 다른 선언 범위이며 이전 whole byte 경계를 이 구성에 재사용하지 않았다.

최초 owned338은 시스템CPU90.91%에서 보호 중단돼 원 실패로 보존했다. Job은 hard cap6.25%·한 코어·BelowNormal·CPU5.594초·최고83.75MiB·empty/handle closed였다. 원인 프로세스나 Defender 충돌은 특정하지 않는다. 코드 검토 후 두 compile 형식을 항상 계산하던 부분을 OR 단락 평가로 바꿨다. 첫 일치 때 compile1회, 불일치 때 fallback2회를 모델339에서 확인했고 fresh source/hash/코드·역변환 검증과 원 fallback은 그대로다. source/AST/JSON/hash 캐시, 보호/기한 완화는 없다. 별도 owned340은108.453초·JobCPU7.156초·최고83.15MiB·시스템CPU최고19.73%·가용RAM최저30.7656%로 완료했다. 재시도 통과를 중단 원인 해소나 PC freeze 해결로 주장하지 않는다.

다음은 실제 제품 worker handoff·원 Job commit·완전한 실행 자격과 권한/독립 제품 판정의 결합이다. 승인 없는 Native011 GO나 이미 완료한 전체 준비001/읽기 전용008은 실행하지 않는다. 근거는 `p09-361-native011-current805-engine-owned-metadata-validation-models339.v1.json`, `current805-engine-owned-metadata-entry-models337.v1.json`, `current805-engine-owned-metadata-entry-construct001.v1.json`, `current805-engine-owned-metadata-entry-construct-owned338.v1.json`, `current805-engine-owned-metadata-entry-construct-owned340.v1.json`이다. 축약명에는 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

### 종료 처리와 제품 메타데이터 연결

읽기 전용 감시기는 원3개 live epoch와 마지막 산출물 marker를 구분한다. 마지막 marker는 새 live guard를 만들지 않고 원 guard를 프로세스 종료/capture/cleanup까지 유지한다. 실제 exit0·소유 Job empty/handle closed가 확인된 뒤에만 별도 terminal_audit guard를 acquire한다. 자식 Native600/공유5초를 연장하지 않고 누락된 live 단계를 추론하지 않는다. 실패한 자식의 원 오류를 보존하며, 하위 프로세스 잔존·종료 미확인·순서 오류·기존 자원 실패는 통과하지 못한다.

모델318의26개·40fresh/final40과 실제 marker fixture001의9.578초·26fresh/final26·cleanupTrue가 통과했다. 실제 OS exit0 뒤 마지막 marker를 수신해도 guard/시작시각이 바뀌지 않고, empty Job 뒤 terminal_audit가 시작됨을 확인했다. 수정 전 감시기18674byte는 source314에 정확히 보존했고 Frame/metadata 판정 함수의 AST는 그대로다. owned008 실패를 새 protocol PASS로 바꾸거나 본문을 재실행하지 않는다.315의 가상 clock이0초 interval을 만든 모델 오류는 양의 fixture interval을 명시해 수정했으며 실제 guard 시계는 바꾸지 않았다.

실제 준비된 실행기 검사322는 기존 execute→execute→run_owned 함수 링크와29개 code object에서 input_pins의 OwnedPacer 재지정1개를 확인했다. 선택 속도는binary1MiB/other2MiB다. 메타데이터 본문/reader/worker/제품은 실행하지 않았고 구성379fresh/final379·외부21/21·cleanupTrue다.320은 wrapper 밖에서 input_pins를 찾으려 해 실패했다. 기존 함수/closure 링크를 제한적으로 관찰하는 모델321의7개로 보완했으며, 함수를 찾지 못한 경우를 “재지정 없음”으로 자격 인정하지 않는다.

`native011_engine_owned_metadata_adoption.py`는 원 engine의 새 pacer 재지정을 정확히 한 번 요구하고 실제 읽기1/2MiB와 tail/EOF 예약·모든 원 source/read wrapper를 보존하는 미설치 구성요소다. 재지정 전 IO, 중복 지정, 사용한/실패한 상태의 초기화는 거부한다. 실제 원 OwnedPacer는 상속된 초기값4MiB를 갖지만 원 select(name)가 매 IO 전에1/2MiB를 선택하므로, 초기값을 IO 속도나 credit로 인정하지 않는다.323의 잘못된 초기값 기대를 바로잡은 모델324의6개·37fresh/final37·cleanupTrue가 통과했다. Frame/decoder/Native/제품 한도는 바꾸지 않았다.

새 `native011_engine_owned_metadata_connection.py`는 private factory의 reader 선택만 연결하고 기본 candidate/class는 바꾸지 않는다. 원 engine 전체 pin을 검증한 뒤 allocation/OwnedPacer 재지정 두 문장만 그대로 실행한다. 모델327의16개·47fresh/final47·cleanupTrue가 통과했다. 실제 구성요소328도 current3043/whole3462/history419·구성387fresh/final387·외부33/33·cleanupTrue로 통과했다. 별도 reader와 구성요소16fresh/final16을 사용해 원본2개의 첫·최종2/2, 물리4read/114590byte, decode4, 원 query4, 재지정1회·최종 other2MiB를 확인했다. 실제 paced byte는 other114590/binary0이고 예약114594byte 중 EOF4byte를 반환했다. metadata 공유5초는 등록됐지만 Frame은 등록하지 않았다.

328은 두 원본의 실제 구성요소 시험이며 이후 전체 준비001과 범위를 구분한다. 읽기 전용 기본2.5/4MiB와 제품1/2MiB의 차이를 보존하며 전자의 시간/closing 구성을 제품 성공으로 승격하지 않는다. source201 실제 worker handoff·원 Job commit·완전한 비용/권한·Native011 GO는 미완료다.

`native011_engine_owned_metadata_callback.py`는 원 metadata_audit 전체 source pin과 실제 함수 코드를 대조한 뒤 판독기 할당 한 곳만 원 engine 두 문장으로 연결한다. 전체 AST 역변환으로 callback/투영/helper 읽기/hash/JSON/finish 본문을 보존한다. 준비 callback은 한 번만 호출할 수 있고 원 자원 검사·callback·closing 실패는 원 오류를 보존하며 재시도를 거부한다. 최신 모델332의6개·35fresh/final35·cleanupTrue가 통과했다. 이 연결은 제품 전체 input_pins 본문이나 Native600/READY15/제품10의 자격이 아니다.

`native011_engine_owned_metadata_preparation.py`는 원 PreparationAudit와 Epochs를 합성해 실제 whole opening→원 metadata callback→whole closing을4개 준비600초 단계로 실행한다. 명시적 control51개, 별도 구성요소 source reader의 첫·최종 확인, 기존 decoder5·query20/초·1/2MiB 정책과 종료 증거 보존을 유지한다. 모델331의5개·36fresh/final36·cleanupTrue가 통과했다. 모델330의 시험용 guard 표본 필드 누락 실패는 원본을 보존하고 fixture만 보완했다.

실제 전체 준비001과 외부 owned001은 current3049/whole3468/history419·구성393fresh/final393·준비source32/32·외부404/404·cleanupTrue로 통과했다. 전체 양쪽 경계에서 각각3468개/216762048byte와 동일한 pin digest를 확인했다. 원 두 문장 할당 뒤 전체 metadata callback은335fresh/final335·675물리read/query675·156877676byte·325decode를 완료했다. callback_attempts2는 원 사전 거부1회와 실제 본문1회이며 두 번의 본문 실행이 아니다. 원1/2MiB 정책을 유지했고 shared5초 중 metadata1.700초·Frame미등록이다. 준비001에는 읽기 전용008의 추가 Native API 관찰이나 두 Native 경계가 없으므로 metadata335를 이전342의 대체 범위나 제품 전체 input_pins의 수용 증거로 쓰지 않는다.

자식 단계는 구성105.110초/opening336.468초/metadata94.047초/closing351.235초로 각각 원 준비600초 안에 완료했다. 자식 총886.860초·외부960.829초다. 새 외부 연결은 원 Monitor/Job/자원/실패 보존/cleanup을 유지하고 전체 main AST 역변환 모델334의7개·34fresh/final34를 통과했다. 실제 OS exit0·active0/Job empty/handle closed·CPU13.375초·최고109.12MiB를 확인했다. machine cap6.25%·한 코어·BelowNormal을 유지했고 자식/외부 합산 시스템CPU최고78.68%·가용RAM최저28.3541%로 자원 중단은 없었다. 이 결과는 전체 PC freeze 해결이나 Native600/READY15/제품10의 실제 성공을 뜻하지 않는다.

다음은 새 준비 연결을 제품 진입점과 독립 판정기에 결합하고 실제 제품 전체 input_pins·source201 worker handoff·원 Job commit·완전한 비용/권한을 연결하는 일이다. 입력/검증 조건 변경 없이 전체 준비001을 반복하거나 승인 없는 Native011 GO를 실행하지 않는다.

현재 근거: `p09-361-native011-current805-engine-owned-metadata-preparation001.v1.json`, `current805-engine-owned-metadata-preparation-owned001.v1.json`, `current805-engine-owned-metadata-preparation-owned-models334.v1.json`。구성요소328·모델331/332·아래 읽기 전용008은 당시 실행 범위의 보존 기록이다. 축약명에도 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

### 실제 읽기 전용 Frame의 현재 결과

읽기 전용008의 자식 본문은 실제 전체 metadata와 두 Native byte 경계를 완료했다. current3037/whole3456/history419·worker201, 각198202678byte/합계396405356byte, metadata325/Frame324 decode·공유4.234초/원5초, 엄격한 본문544.531초/원600초다. source201 coverage·201flag 복원·실제 잠금/stream 종료와 raw 함수 복원을 원 판정기로 확인했다. worker·GO·제품 실행은0이고 원 batch는 의도적인 읽기 전용 중단으로 BROKEN이다.

바깥 owned008은 마지막 marker가 프로세스 종료 후 처리되는 경쟁조건으로 `NATIVE011_OWNED_METADATA_AUDIT_NO_MONITOR_ROTATION_FROM_TERMINAL_PROCESS` 실패다. 실패 원본을 보존한다. 새 `native011_readonly_terminal_audit.py`는 실제3개 monitor epoch·원 Job 제한·cleanup을 대조하고 원 Frame/상세 timing/metadata 판정기를 그대로 호출한다. 네 번째 live phase나 직접 기록되지 않은 OS 종료 코드를 추론하지 않는다. 독립 감사312는 원 자식381개 source와 외부 monitor source/산출물의 첫·최종 byte hash를 대조해406fresh/final406·cleanupTrue로 통과했다. 이는 본문과 owned cleanup 감사이며 원4phase monitor PASS나 제품 수용은 아니다. 본문008을 재실행하지 않았다.

metadata는342fresh/final342·691물리read/query691회·157472082byte를 읽었다. 공유 decoder의 metadata1.567초+Frame2.667초와 별도 관측 시계1.684113/2.733181초를 각각 보존했다. Native guard 단계545.687초에는 본문 뒤 정리가 포함되고 전체 외부는975.281초다. Job CPU18.797초·최고109.71MiB·active0/cleanupTrue, machine cap6.25%·한 코어·BelowNormal을 유지했다. 실제 Native의 시스템CPU최고87.5%·가용RAM최저22.5888%로 자원 중단은 아니며 전체 PC freeze 해결을 뜻하지 않는다.

독립 감사310은 저장되지 않은 stage 필드를 요구해 실패했고, 실제 epochs 기록을 대조하도록 수정한 모델311의5개 및 실제312가 통과했다. 해당 실패 원본도 보존했다. 남는55.469초는 실제 worker READY15/제품10/추가 inventory·정리의 성공 자격이 아니다. 최신 종료 처리/제품 연결 상태는 위에 구분하며 Native008/009/010 재실행이나 승인 없는 Native011 GO를 하지 않는다.

현재 근거: `p09-361-native011-current805-readonly-frame-probe008.v1.json`, `current805-readonly-frame-owned008.v1.json`, `current805-readonly-terminal-audit-models311.v1.json`, `current805-readonly008-terminal-audit312.child.v1.json`, `current805-readonly008-terminal-audit-owned312.v1.json`。축약명에도 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

#### 읽기 전용 008 실행 전 구성

실제 allocator 검사302에서 원 metadata reader의 SnapshotReader/ChunkLeaf/BuildReader wrapper와 WeightedPacer의 binary2.5MiB/other4MiB·QueryPacer20회/초를 확인했다. 이전297의 owned1/2MiB 비교를 실제 metadata 구성의 속도 증거로 사용하지 않는다. 현재 연결은 실제 기존2.5/4MiB와20회/초를 그대로 보존한다.

`native011_metadata_tail_connection.py`는 metadata15742byte/BuildReader24527byte 전체 source pin 및 실제 factory/Router/BuildReader 메서드 코드를 대조하고 private factory의 old_reader closure 한 개만 선택 subclass로 바꾼다. metadata용 새 pacer의 rate tuple 역변환은 원 reserve 코드 전체와 같아야 하며, Native의 원1/2MiB pacer는 수정하지 않는다. 원 open/경로/weighted/semantic wrapper의 MRO, source snapshot,64KiB workspace, 물리/의미 hash·JSON·EOF·closing·공유 decoder를 보존한다. 정밀 시계는 새 미사용 query/byte pacer에만 선택하며 활성 deadline이나 counter를 재시작하지 않는다.

실제 private factory 소규모 시험305는 원자료2개의 첫·최종 읽기4회/114590byte·의미 decode4회·query4회·별도 source11fresh/final11·외부28/28·cleanupTrue였다. 원 shared budget의 metadata reader 하나만 사용했고 Frame/worker/GO는0이다. 전체 metadata callback이나 Native 성능 자격은 아니다. 현재 영향 모델306의68개·52fresh/final52·cleanupTrue가 통과했다.

구성 전용 readonly008/owned307은current3037/whole3456/history419·worker201·control39·381fresh/final381·외부23/23·helper59/원Native union64·cleanupTrue, reader/예산/Frame/worker 생성0으로 통과했다. 원 complete579.276509초+READY15=594.276509초·명목 여유5.723491초는 구성 시점 모델값이다. readonly008 판정은 전체 원 callback 결과의 fresh/closing/read/byte를 실제 tail ledger와 대조하고, 원 query 수·전체 물리 선언·실제 두 Native 경계·metadata325/Frame324 공유 decoder5초를 계속 요구한다. 작은 시험이나 구성 결과로 대신 통과하지 못한다. 실제 실행 결과는 위에 구분한다.

현재 근거는 `p09-361-native011-current805-metadata-reader-inspection-owned302.v1.json`, `current805-metadata-tail-private-probe-owned305.v1.json`, `current805-metadata-tail-readonly8-models306.v1.json`, `current805-metadata-tail-construct-owned307.v1.json`, `current805-readonly-frame-construct008.v1.json`이다. 축약명에도 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

#### 이전 읽기 전용 007 결과

읽기 전용007은current3033/whole3452/history419·worker201에서 실행했으나 잠금 획득 중 시스템CPU91.73% 표본으로 `STOP_NATIVE_OPEN_AFTER_HOST_SATURATION` 중단됐다. metadata342fresh/final342·691물리read·157472074byte·325decode를 완료했지만 전체 Native byte 경계는0개다. 공유decoder metadata1.959초/Frame0회로5초 초과나600초 timeout이 아니다. 준비123.390초·whole opening319.594초·Native176.641초·외부629.234초, 잠금832개 전부닫힘·raw 함수 복원·Job active0/cleanupTrue다. Job hard cap6.25%·한 코어·BelowNormal·최고108.6MiB를 유지했고 원인 프로세스나 Defender 간접 반응은 특정하지 않는다. 요약의 마지막 CPU50.69%와 실패 직전 자식 표본91.73%는 서로 다른 시점이다. worker·Native011 GO·제품 실행은0이다.

진단293은 같은 실패 Frame/상세 timing325행/Frame0행을 다시 읽어9fresh/final9·외부17/17·cleanupTrue를 확인했다. 전체007·제품을 재실행하지 않았고 수용 증가는0이다. 구성 전용007/owned290의377fresh/final377·외부19/19·helper59/원Native union64는 당시 구성 증거다. 원 engine/checker complete578.951672초+READY15=593.951672초는 명목값이며 실제 완료 보장이 아니다.

다음 후보 `native011_metadata_tail_candidate.py`는 C3 상속으로 원 metadata open/경로/weighted/semantic wrapper의 MRO 순서와 메서드 참조를 유지하면서 바이트 leaf만 실제 잔여 크기/1byte EOF 예약으로 바꾼다. 기존 workspace leaf는 원문 전체에서 재컴파일한 코드와 대조한다. hash/JSON/실제 EOF/closing·64KiB 버퍼·byte1/2MiB·open20회/초·원 sleeper/checkpoint를 유지하고 정밀 시계는 읽기/예약0인 새 pacer에만 선택한다. default 클래스/모듈·metadata factory·Native·제품에는 미연결이다.

작은 실제 비교295는14파일의 두 read에서 원3.134405초/후보3.247182초로 개선되지 않아 채택하지 않았다. 정밀 시계를 추가한 별도297은 같은14파일·각28read/1864490byte·14fresh/final14·open28회를 유지해 원2.256236초/후보1.767766초를 관측했다. 원 BuildReader/direct_path AST와 명시적 owned byte 정책의 비교이며 실제 private engine metadata 구성이 아니다. 캐시/외부 부하 미통제로 약22% 차이를 전체 성능 보장으로 해석하지 않는다. workspace 호환 검사까지 포함한 현재 모델298의12개·38fresh/final38·cleanupTrue가 통과했다. 이전294의38개/296의10개와297 측정은 당시 소스의 원본 기록이다. 다음은 실제 private metadata factory의 MRO/pacer/physical 선언과 후보 전제의 대조이며 전체008을 자동 실행하지 않는다.

실제 준비 부모를 유지한 원 디코더 프로파일001/owned284에서162개 원 자료의 checkpoint5562회는0.045425초, GC gen0 1회는0.0000348초였으며 bytearray.extend가0.230755초로 관측됐다. 이 구간을 근거로 GC를 끄거나 freeze/threshold를 변경하지 않았다. 원 측정의 별도 벽시계1.121884초와 후보002/owned287의0.918258초를 비교하면 약18% 차이가 있고 후보의 bytes.join은0.032275초였다. 각 실행은 실제71855107byte를 읽고251193341byte를 복원해162decode를 끝냈다. 원 예산값은 각각0.721/0.598초로 보존했다. 프로파일러가 포함되고 실행 시점·외부 부하/캐시는 통제하지 않았으므로 그 차이를 전체 Native 성능 보장이나 실제 metadata+Frame 공유5초로 판정하지 않는다. 원본001의 준비 source375/375와 별도 component162/162, 후보002의 준비377/377와 별도 component165/165의 closing을 각각 확인했으며 constructor reader를 재사용하거나 counter를 reset하지 않았다.

새 connector는 원 metadata15742byte/Projection6401byte/codec2891byte를 fresh 확인하고 실제 reader/router closure의 코드·owner 참조와162개 매핑을 검사한다. 원 Projection 클래스와 메서드/property 코드는 그대로이며 그 private decode 함수의 codec 의존성만 선택 후보로 바꾼다. 원 codec/default 모듈·클래스·전체 scope·물리/의미 hash·JSON/EOF/64KiB·예산/시계·보호 조건을 변경하지 않는다.007의 control은35개이며 기본27/exact29/timing31은 그대로다. 모델291의119개·55fresh/final55·cleanupTrue가 통과했다. 상세 timing은 별도 exclusive/fsync artifact에 전부 남기고 판정기가 original pin/hash 및 요약의 일치를 검사한다.119개에는 상세 행 누락/요약 drift 거부와 terminal writer의 원본 보존 검사도 포함된다. 기존 inline 기록의 판독도 유지한다.

최신 근거: `p09-361-native011-current805-readonly-frame-owned007.v1.json`, `current805-readonly-frame-probe007.v1.json`, `current805-readonly-observed-decoder-pressure-inspection-owned293.v1.json`, `current805-metadata-tail-candidate-models294.v1.json`, `current805-metadata-tail-component-owned295.v1.json`, `current805-metadata-tail-precise-models296.v1.json`, `current805-metadata-tail-precise-component-owned297.v1.json`, `current805-metadata-tail-workspace-models298.v1.json`。축약명에도 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다. 구성290·모델291·프로파일284/287 및 이하006 이전 결과는 당시 source 범위의 기록이다.

최신 readonly006은 공유 decoder5에서 실패했다. whole3448/current3029/history419의 첫198133150byte 전체 경계·source201 coverage·201flags 복원은 완료했지만 두 번째 경계는 미완료다. metadata325회1.880초+Frame226회 완료/227회 시도3.132초=5.012초이며 Native570.297초로600초 timeout이나 CPU/RAM 중단은 아니다. 외부989.672초·잠금3416개 전부닫힘·원 raw open 함수 복원·Job CPU18.75초/최고111.29MiB/active0·cleanupTrue다. 진단276은 같은 실패 원본과 terminal Frame을 손실 없이 복원했으며 전체 Native를 재실행하지 않았다. 원5초·600초·CPU/RAM 보호와 공식158/249를 유지한다.

006의 별도 벽시계 관측은 metadata2.623744초/Frame3.089323초로 합계5.713067초였다. 원 예산값보다 작지 않아 시계 과대계상을 원인으로 판정하지 않는다. 관측된 CPU 증가는 각각1.859375초/1.578125초지만 짧은 호출별 CPU 계측 해상도와 동시 원인 추적의 한계가 있어 그 차이를 선점/GC/Defender로 확정하지 않는다. 기본 control27/선택 exact29는 유지하고 관측 모드만31개로 선언했다. 실제 attach 후 원 budget/check/run 본문과 시계를 유지했으며 모델273의76개·50fresh/final50은 실행 전 소스 기준의 결과다. 제품·worker·GO mode는 없다.

별도 코어 관측274/275는 기존 bounded PDH array/cleanup 메서드를 그대로 사용해 Processor counter 한 개의4표본만 읽었다.16개 논리CPU와 mask1/CPU0을 확인했지만 CPU0 사후 표본은0~2.560724%로 해당 표본이 코어 혼잡을 지지하지는 않는다. 직접 상위 Job 조회는 flags0이었다. NULL handle 조회가 직접 Job을 반환하고 중첩 CPU 비율이 상위 비율에 상대적이라는 API 의미는 [Microsoft QueryInformationJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject)와 [CPU rate control](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information)에 근거한다. 이 별도 관측을006의 동시 전체 Job 계층 증거로 쓰지 않는다. 모델4개·37fresh/final37·실제 PDH query닫힘·외부20fresh/final20·cleanupTrue이며 affinity/CPU한도/시스템 설정 변경은0이다.

종료 reader 통계 추가277은 변경된 driver의13개 모델·41fresh/final41·cleanupTrue를 확인했다. 이미 닫힌 Frame의 실제 read_passes/byte/pacer/semantic counter와 원래 기록된 경계 개수만 보고한다. 모든 byte가 읽혀도 원 semantic 검사가 실패해 경계가 기록되지 않았다면 미완료다. 새 Native 전체 경계 자격은 아니며 과거006의 누락된 부분 counter를 만들어 채우지 않는다. 다음은 checkpoint 대기/객체 정리 비용을 좁힌 비제품 검사다. 근거 없이 전체007을 재실행하지 않는다.

코어 단위시험의 기존 외피274는 쓰지 않는 driver 소스까지 선언해 종료통계 변경 뒤 대조278/279에서 drift를 거부했다. 새 외피280은 실제 host/child에 로드된 보조 소스와 직접 시험 입력을 처음/종료에 fresh 확인한다.4개 모델이 통과했고23fresh/final23·cleanupTrue로 이전37개의 불필요한 의존성을 줄였다. 모델 입력 추적에만 적용하며 Native source scope를 관측 module 목록으로 합성하거나 축소하지 않는다. 시간 절감의 통제된 측정은 아니다. 관련 없는 수용 제품이나 전체76개 시험을 다시 실행하지 않았다.

최신 근거는 `p09-361-native011-current805-readonly-frame-owned006.v1.json`, `current805-readonly-frame-probe006.v1.json`, `current805-readonly-observed-decoder-failure-inspection-owned276.v1.json`, `current805-logical-cpu-models274.v1.json`, `current805-logical-cpu-observation001.v1.json`, `current805-logical-cpu-observation-owned275.v1.json`, `current805-terminal-reader-counters-models277.v1.json`이며 축약명에도 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

구성 전용006/owned269는 원 private 로더와 원문 전체 컴파일의 _work 호출 바이트코드 차이를 거부해 Frame 전에 실패했다. 모델270에서 재현했고 짧은271/272에서 LOAD_GLOBAL/LOAD_ATTR 호출 형태 차이를 확인했다. 같은 고정 원문에서 두 정확한 컴파일 문맥을 준비해 클래스 전체 일치를 검사하도록 수정했으며 바이트코드를 정규화하거나 생략하지 않았다. 새 관측은 원 budget7214byte·공유7823byte 전체 source pin과 모든 원 메서드/require/한도 검사를 유지한다. 실패 원본을 보존하고 제품/원 Frame006을 실행한 것으로 세지 않는다. 근거는 `p09-361-native011-current805-shared-timing-construct-owned269.v1.json`, `current805-shared-decoder-timing-models268/270/273.v1.json`, `current805-shared-private-code-inspection-owned271.v1.json`, `current805-shared-private-instruction-inspection-owned272.v1.json`이며 축약명에도 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

최신 readonly005는 선택적 exact-read factory를 연결한 새 current3027/whole3446 범위에서 실패했다. 첫198112319byte 전체 경계와 source201 coverage·201flags 복원은 완료했지만 두 번째 경계의 공유 decoder5에서 중단됐다. metadata325회2.065초+Frame240회2.939초=5.004초이며 Native 단계578.281초로600초 timeout은 아니다. 외부991.844초·Frame CLOSED·cleanupTrue다. 실패 원본005와 손실 없는 terminal Frame9part를 보존했으며 진단257은 같은 원본을 읽었을 뿐 제품이나 전체 경계를 재실행하지 않았다. 아래004는 이전 current3025 범위에서만 유효하다.

2026-10-18 현재 원 Native Frame의 두 전체 현재 byte 경계는 readonly004/owned004에서 실제 통과했다. 새 opening3444개 뒤 current3025개를 각198077362byte씩 읽어 합계396154724byte·worker201 live coverage·201flags 복원을 확인했다. 원 metadata325/Frame324decode의 공유 합계4.497초/5초·Native600·14/s·byte1/2MiB·CPU/RAM 보호를 유지한다. 주요 경계596.797초, 정리 포함 Native597.922초이므로 worker 준비/제품 시간을 보장하는 여유는 아니다. 원 클래스·메서드·guard·cleanup을 보존하며 원 부모 wrapper의 실제 attempt1 뒤 제품 엔진 대신 no-product 진단만 호출했다. 제품/worker/GO·가짜 Job commit·case_finished가 없고 batch는 BROKEN이다. 제품 수용과 P09 Gate는 별도다.

원3412handle 전부닫힘·raw open 함수 복원·Frame JSON2126766byte/12part 손실 없는 복원·구성369fresh/final369·외부387fresh/final387·cleanupTrue다. 외부 전체1075.797초·Job CPU18.781초/최고112.90MiB·active0이며 Native CPU표본최고73.2%·가용RAM최저38.6272%였다. acquire254.078초/계측 open252.025초다. 기본 잠금 프로파일234와 실제 held-view/scratch/failfast 연결235를 구분했다. 후자의 짧은14파일 두 경계는0.112초이며 물리 open예약은 잠금17회에만 발생했다. 이 관측은 PC프리즈 원인 해결이나 전체 제품 실행 자격이 아니다.

실제001은 직접 Frame 생성이 원 부모 소유 기록을 거치지 않아 EXACT_OWNED_PARENT_FRAME_REFERENCE에서 실패했고 원본을 보존한 뒤 연결을 수정했다. 실제002는 전체CPU93.6% 표본에 보호 중단됐으며 가용RAM27.7294%·commit49.9080%·Job 누적CPU10.422초/최고108.66MiB·정리 후 잔류0이다. 당시 프로세스별 기여가 없어 Defender나 검증의 간접 유발을 확정하지 않는다.

실제003은 CPU 중단이 아닌 원600초 timeout이다. 현재3025개 첫 경계198073353byte와 worker201 live coverage·201개 상속 flags 복원은 확인했으나 두 번째 읽기는 미완료다. 잠금3412개 전부 닫힘·active stream/reader0·raw open 함수 복원·소유 Job active0/cleanupTrue를 확인했다. metadata와 Frame decoder의 중단 시점 합계4.746초(325/232decode)는 두 경계 완료나 합계5초 PASS가 아니다. Frame JSON1614945byte를9개 bounded part에서 정확한 hash로 복원해 진단했고 제품을 재실행하지 않았다. 진단 외피229의 집계 키 오류도 원본을 보존하고230에서 바로잡았다.

준비 첫 전체 읽기의 사용 전 byte pacer와 원 Native/OpenPacer의 정밀 시계 선택을 연결했다. 원 생성자가 선택 뒤 phase clock을 저장하고14/s→20/s 복원·600초·decoder5·READY15·제품10·identity·CPU/RAM 보호를 유지한다. 모델236의29개와 전체004가 통과했다. 이전 짧은232의 기본1.572초/정밀1.732초는 속도 향상을 입증하지 않았고,004와003의 외부 부하/캐시 차이도 통제하지 않았다. 원003/002 실패를 재판정하거나600초/5초를 늘리지 않는다.

### 실제 읽기 크기별 예약 후보

`native011_exact_read_budget.py`는 제품에는 설치하지 않았으며, 읽기 전용 attempt005에서만 원 private factory에 선택적으로 연결했다. 기본27개 control은 유지하고 해당 모드만 후보2개를 추가해29개로 닫는다. 원 leaf의 AST 전체 역변환과 실제 reader 메서드 사슬을 확인하고 모든 원 checkpoint·hash·parse 한도·집계·새 실제 stream/EOF·fresh closing 문장을 유지한다. OS readinto 크기와 그 이전 예약량을 함께 남은 선언 크기 이하/최대64KiB로 제한하고 끝에서1byte 실제 EOF probe를 실행한다. 실제 추가 byte는 실패, 짧은 read는 실제 EOF까지 반복하며 선언 크기로 원 byte/hash를 합성하지 않는다. 속도1/2MiB·token 상한64KiB·원 sleeper·idle 다중 credit 금지·원 시계 한도는 유지한다. 후보 helper의 준비를 Native 전에 분리했지만 읽기/해시/JSON/AST 검증 credit를 재사용하지 않는다. readinto 프록시는 reader마다 한 번 구성하고 매 읽기 종료에 stream 참조를 해제한다. 모델252의58개와 구성 전용005/owned250은 통과했으나 실제005는 공유5초에 실패했으므로 전체 자격은 미완료다.

### 디코더 후보 비교와 시간 관측

`native011_decoder_chunk_join.py`는 원 decoder 전체 AST를 역변환해 원 JSON/중복키/base64/zlib/출력64KiB/hash/checkpoint/5초를 보존하는 저장 방식 후보이며 제품이나 readonly driver에 적용하지 않는다. 원16개를 포함한 모델253의21개는 통과했지만 실제162개 fresh 비교256/corpus001에서 기존 누적0.971초·후보1.112초로 개선 근거가 없었다. 각각 물리71855107byte와 복원251193341byte를 검증했다. 두 방식은 각각 별도 구성요소5초 예산이며 실제 metadata+Frame 공유5초 통과를 뜻하지 않는다. 외부 부하/캐시는 통제하지 않았다. 오류254의 잘못된 이전158 binding 연결,255의 출력 제한 실패를 보존했고256은 정확165 private projection을 사용해 상세 결과를 exclusive/fsync 파일에 저장했다. 출력 제한 자체를 높이지 않았다.

`native011_decoder_timing_observer.py`는 원 budget/check/run 본문과 시계·한도·실패를 보존하고 정밀 벽시계/프로세스CPU 관측만 병기한다. 모델261의7개는 원5초 보호·원 오류 우선·관측 오류·사용한 budget 재설치 및 실패 후 재시도 거부를 통과했다. 실제 가장 큰16개 자료의 두 held 경계263은32decode·원 누적0.535초·별도 벽시계0.611498초·21handle 전부닫힘·67fresh/final67·외부20fresh/final20·cleanupTrue다. 기존 GetTickCount64 시계 해상도15.625ms와 별도 QueryPerformanceCounter 100ns를 확인했지만 이 표본은 과대계상 원인을 뒷받침하지 않는다. 원 시계나5초 정책은 바꾸지 않았고 관측값은 판정에 쓰지 않는다. 큰 자료1개의 프로파일260·연결 실패258/259·보고 실패262도 보존했다. 전체 공유 경계와 제품은 이 작은 구성요소 시험으로 수용하지 않는다.

전체162개 압축 자료를 사용한 관측002/owned266은 실제 held 전후 경계324decode·원 누적2.089초·별도 벽시계2.058104초·167handle 전부닫힘·213fresh/final213·외부20fresh/final20·cleanupTrue로 끝났다. current3027의 나머지 입력 및 원 metadata callback은 실행하지 않았으므로 둘의 공유5초나 전체 Native 실행 자격이 아니다. 앞선 metadata2.065초와 단순 합산해 실제 통과라고 판정하지 않는다. 하위 시스템CPU표본최고90.48%·가용RAM최저23.1052%·소유 Job 최고메모리 약0.19%를 기록했으며 원인별 프로세스 기여는 수집하지 않았다. 원 예산 시계 및 정책 변경 없이 기존 디코더를 유지한다.

최신 증거: `p09-361-native011-current805-exact-read-connection-models252.v1.json`, `current805-exact-read-construct-owned250.v1.json`, `current805-readonly-frame-owned005.v1.json`, `current805-readonly-decoder-failure-inspection-owned257.v1.json`, `current805-decoder-chunk-join-models253.v1.json`, `current805-decoder-chunk-join-corpus001.v1.json`, `current805-decoder-chunk-join-owned256.v1.json`, `current805-decoder-held-profile-owned260.v1.json`, `current805-decoder-timing-observer-models261.v1.json`, `current805-decoder-held-observation001/002.v1.json`, `current805-decoder-held-observation-owned263/266.v1.json`。축약명에도 `implementation/p09/evidence/`와 `p09-361-native011-` 접두사를 적용한다.

모델244의21개는 원 semantic envelope decoder/경계 guard 조합, EOF/짧은 read/성장/축소/parse 오류/원 자원 중단/실패 고착/기존 workspace와 두 factory 호출을 확인했다. 실제245는 기본/후보 각14파일 두 경계·180480byte·56readinto·17handle 전부닫힘·28fresh/final28·외부19fresh/final19·cleanupTrue다. 관측벽시간0.102175초→0.025354초/요청수면0.079662초→0.014474초이며 실제 byte/hash/읽기 호출 수는 동일하다. 캐시/외부 부하를 통제한 전체 성능 비교가 아니다. 다음은 후보의 새 전체 범위 선언·원 engine/checker 구성 연결과 worker/제품 여유 자격 검증이다. 현재004 whole3444 경계를 후보의 새 범위로 승격하지 않는다.

모델246은 실제 로드된30개 보조 소스/fixture의 첫·최종 byte hash를 확인하고21개를 통과했다.30fresh/final30·외부42fresh/final42·cleanupTrue이며 Native 범위를 관측 목록으로 합성하지 않는다. 최신 근거는 `implementation/p09/evidence/p09-361-native011-current805-readonly-frame-owned004.v1.json`, `current805-readonly-frame-probe004.v1.json`, `current805-readonly-complete-inspection-owned238.v1.json`, `current805-exact-read-models244.v1.json`, `current805-exact-read-owned245.v1.json`, `current805-exact-read-closure-models246.v1.json`(뒤 항목에도 같은 디렉터리와 `p09-361-native011-` 접두사)다. 진단237 출력 상한 실패는 원본 보존 후238에서 집계 출력으로 수정했으며 제품/전체 Native 재실행이 아니다.

증거: `p09-361-native011-current805-readonly-frame-construct-owned224.v1.json`, `current805-readonly-frame-owned001/002/003.v1.json`, `current805-readonly-parent-opening-models228.v1.json`, `current805-readonly-timeout-inspection-owned229/230.v1.json`, `current805-readonly-native-open-models231.v1.json`, `current805-readonly-native-open-owned232.v1.json`(뒤 항목에도 `p09-361-native011-` 접두사, 모두 `implementation/p09/evidence/`). 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE와 Native011 제품 실행 권한 답변대기를 유지한다.

### Native 경계 읽기의 정밀 시계와 읽기 전용 중단 경로

`native011_precise_boundary_pacer.py`는 읽기/예약/수면/최종 해시 이력이 전혀 없는 원 pacer만 새 정밀 시계로 연결한다. 원 reader 클래스·모든 메서드·pressure checkpoint·최대 파싱 크기·집계·1/2MiB 속도·64KiB 이하 burst는 보존하고, 원 pacer를 변형하거나 사용 후 시간/credit를 초기화하지 않는다. 기존 Native600/공유decoder5/준비15/제품10의 deadline 시계는 바꾸지 않는다. 실제 원 Native BoundaryReader와 원 pressure API로14개 명시적 source를 기본/정밀 두 방식에서 각각 전후 읽어 각28회/185268byte/14final과 같은 pin·byte 집계를 확인했다. 요청 수면0.399468초→0.087695초, 실제벽시간0.653833초→0.514156초였고 기본 시계15.625ms/정밀100ns였다. 이는 파일 캐시·외부 부하를 통제한 성능 비교나 전체 현재 입력의 runtime 자격이 아니다. Frame/worker는 생성하지 않았다.

`native011_precise_boundary_connection.py`는 private engine의 원 BoundaryReader 생성 의존성 한 자리만 연결한다. 구성 중 reader를 만들지 않고, 실제 원 두 경계에서만 원 클래스의 새 reader를 반환한다. 실패한 연결·세 번째 생성·default 모듈 변경·기존 worker 시도 이후 연결은 거부한다. 원 reader 메서드와 엔진 함수는 그대로이며 기본 helper 집계를 숨기거나 상한을 올리지 않는다. 모델216의8개·실제 reader001/owned217·새 연결과 범위 모델219의16개가 통과했다.

`native011_readonly_frame_probe.py`는 새 전체 opening의 실제 reader 집계/byte pin을 요구한 뒤 metadata와 원 Native Frame의 두 전체 현재 읽기를 한600초 안에서 수행하는 core다. 원 parent lifecycle·shared metadata budget 선행·직접 현재 입력 전체·같은 registry·201개 source flags 복원·원 held-path guard를 유지한다. 제품을 실행하지 않았으므로 가짜 Job commit·case_finished·성공 batch close를 제공하지 않는다. 원 Frame.close 후 batch BROKEN을 정상 제품 통과로 바꾸지 않고, 원 실패는 cleanup 오류로 덮지 않으며 재시도를 거부한다. 모델218의8개만 통과했으며 실제 전체 driver/Frame 실행 자격은 아직 없다.

실제 parent003/owned220은 새 code/test6개를 더한 current3021+history419=whole3440로 원 부모·독립 checker를 구성했다. worker201 direct/누락0/충돌0·원 Frame5 base·같은 complete 모델·helper59/Native union64·365fresh/final365·외부8fresh/final8·factory 호출0이다. complete577.985701초+준비15초=592.985701초/600초·명목 여유7.014299초로 실제 완료 보장은 아니다. Job CPU6.719초/최고83.54MiB/active0·cleanupTrue·외부105.188초·시스템CPU표본최고36.70%/33.64%·가용RAM최저25.1600%/25.2318%였다. 이전 전체 감사/수용158개는 재실행하지 않았다.

다음은 새3440 opening·동일600초 metadata/Native Frame3021 두 경계·source201 상속 flags와 원본 증거 출력을 묶는 readonly driver다. 실제 Native 전체 잠금·합계decoder5·제품 GO·독립 제품 판정은 미완료다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다. 근거: `p09-361-native011-current805-precise-boundary-models216.v1.json`, `current805-precise-boundary001.v1.json`, `current805-precise-boundary-owned217.v1.json`, `current805-readonly-frame-models218.v1.json`, `current805-precise-native-connection-models219.v1.json`, `current805-live-source-parent003.v1.json`, `current805-precise-native-parent-owned220.v1.json`(뒤 항목도 동일 `p09-361-native011-` 접두사).

### 현재 Native 부모의 작업자 소스 범위 연결

`native011_ready_native_construction.py`와 `native011_ready_scope_connection.py`는 원 current805 공유 부모 생성기의 전체 AST 역변환을 보존하며 세 위치만 연결한다. 선언 시 worker201개의 현재 pin을 새로 대조하고 명시적14코드/1provenance 입력을 더하며, 닫기 전에 전체 범위·실제 Frame 클래스 계층·원 독립 비용 모델을 확인하고 새 배타 결과에 기록한다. 사전 metadata 거부·공유 owner·checker 구성·원 보호/정리 코드는 그대로다. readiness002의 PASS를 현재 byte나 살아 있는 handle로 대체하지 않는다.

실제 live-source-parent002/owned214는 current3015+history419=whole3434를 구성했다. worker201개가 모두 current에 같은 raw pin으로 직접 포함됐고 누락/충돌은 없었다. 보존 이력을 current로 옮기거나 carrier만 잠긴 것을 raw source 잠금으로 간주하지 않는다. Native 공유 Frame5 계층의 base가 기존 Native Frame와 같은 참조여서 원 SourceCoverage 클래스 조건을 수정하지 않았다. 검증 함수 본문은 원 source에서 그대로 선택했지만 살아 있는 Frame에서는 아직 호출하지 않았다. engine와 독립 checker가 같은 complete 모델을 사용하고 실제 inventory170·directories387·획득 예약3402/14s·두 byte 경계229.480485초를 포함한다. complete577.530485초+준비15초=592.530485초/600초·명목 여유7.469515초이며, 원60초 여유 항목·합계decoder5·제품10초·상한14/20과 추가 allowance를 줄이지 않았다. 이 계산은 실제 완료 보장이 아니다.

첫001/owned212는 Native helper64 상한에서 실패했다. 새 시작부가 보호 모듈4개를 default import한 원인이므로 원 pinned loader의 private namespace로 보호 모듈을 불러오도록 보완했다. default sys.modules 항목을 숨기거나 집계에서 제외하지 않는다. 성공002는 작업자 구성 중 기본 helper59개/독립 판정기의 원 Native union64개로 상한을 충족했다. 모델210의 잘못된 테스트 기대값1건·수정 후211의11개·private bootstrap 추가 후213의12개 정확ID와 실패 원본을 보존한다.

구성자식359fresh/final359·외부8fresh/final8·Job최고84.04MiB/누적CPU6.453초/active0·cleanupTrue·외부99.219초다. 시스템CPU표본최고53.71%/66.41%·가용RAM최저27.0497%/26.6032%이며 보호 중단은 없었다. Frame 인스턴스·metadata 본문·공유 decoder5 실작업·worker/GO/제품 및 새3434 전체 byte 감사는 실행하지 않았다. 원3421 감사003과 수용158개도 재실행하지 않았다. 새 범위가 선언됐다는 이유로 이전 감사의 byte 경계를 재사용하지 않는다.

다음은 actual Native3015 잠금/전후 byte 경계·동일 owner의 metadata/Frame 합계5초·새 worker201 상속을 연결하는 실행 자격 검증이다. 제품 권한·GO·독립 제품 판정은 별도이며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE다. 근거는 `p09-361-native011-current805-live-source-parent001/002.v1.json`, `current805-live-source-models210/211/213.v1.json`, `current805-live-source-parent-owned212/214.v1.json`이다(뒤 항목도 동일 `p09-361-native011-` 접두사).

### 원 작업자의 실제 준비 신호와 EOF 거부

`native011_inherited_worker_ready_inspection.py`의 실제002/owned208은 원 Gate의15초 시계가 시작된 첫 checkpoint 안에서만 준비start를 보내고, 같은 실제 Job 구성원 검사를 유지해 원 ReadyReader event를5.516초/89회 bounded wait 안에 확인했다. 대기 이전에 worker 초기화를 미리 실행하지 않는다. 실제 GO를 쓸 능력이 없는 `NoGoReadySink`는 원 Gate가 event를 확인한 뒤 정확한 GO 경계에서 거부한다. Gate의 readiness_confirmed=True/actual_original_GO_written=False/stopped=True를 그대로 보존하고, 실제 stdin을 닫아 EOF1회만 원 worker에 전달한다. 원 worker의 WORKER_NOT_AUTHORIZED·actual_worker_attempts/calls1·raw_policy_restored=True·162descriptor·제품10초·기본 helper62/상한64를 확인했다. 제품 프로세스/GO 전송0이며 이 검증을 Native 실제 GO/write 수용으로 승격하지 않는다.

상속 reader는 원 AuditEvidenceReader._read 본문과 _bind/pin/json/text/fresh_pin/finish를 보존하고 byte stream을 실제 보유 handle로 공급한다. OS ID 전후 확인·전체 byte/hash·실제 EOF·parse 상한·같은 PID/thread·부분 읽기 실패·마지막 전체 새 읽기를 유지한다. 기존 open20/s는 새 OS open이 없는 이 source stream에는 예약하지 않지만 원 byte reserve/refund는 유지한다. q byte pacer는 원 OwnedPacer의2MiB/s·64KiB 이하 burst 알고리즘이며 대기 시계만 perf_counter다. 별도 bootstrap/import 검증도2MiB/s로 제한하며, 전체 IO가 단일 공유 pacer라고 주장하지 않는다. Python 모듈은 명시적 source handle에서 새로 읽어 정상 모듈 namespace로 실행하고 기존 sys.modules를 숨기지 않는다. 기존 초기화의 프로젝트 pathname open93회는 제거하지 않았으며 새 handle byte/hash 확인 뒤 원 readonly open을 유지했다. Source stream open0과 전체 Python open0을 혼동하지 않는다.

첫001/owned206은 child 전체 구성·closing·EOF 거부까지36.781초였지만 Gate는15.015초에 원 timeout으로 실패했다. 이후 Windows의 중첩 Job CPU 비율이 바로 위 부모 할당량에 상대적이라는 계약을 확인했다. 바깥6.25%와 안쪽6.25%가 곱해지는 구조를 `native011_nested_preparation_job.py`로 정규화했다. 현재 부모를 `QueryInformationJobObject(NULL)`로 원 verify_job_limits에 통과시킨 뒤 private Windows copy의 안쪽 비율만 부모 기준100%로 지정한다. 부모 원6.25% 상한·1코어·BelowNormal·RAM8%·active16·breakaway금지·kill-on-close는 유지한다. 상위 제한은 하위에서 완화할 수 없으므로 PC 전체 상한은6.25% 이하이며, 현재 부모가 미확인/변경이면 거부한다. 원 Windows/Native 정책·바깥 Job을 변경하거나 breakaway를 사용하지 않는다. 실제 raw100%를 PC 전체100%라고 기록하지 않고 부모 상대비율과 시스템 상한을 분리한다. 이 보완은 현재 준비 진단에만 적용됐으며 Native 제품 경로 설치는 별도다. 계약 근거: Microsoft [중첩 CPU 비율](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information), [중첩 Job의 상속과 제한](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs), [현재 immediate Job 조회](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject).

모델203의12개,204/205의35개, 중첩 제한 추가 후207의42개 정확ID가 통과했다. 실제002는 원198+bridge3=201입력·201fresh/final201·6207611byte/ReadFile1204회로 원 초기화를 마쳤다. byte 수와 read 횟수는 실패001과 같고 worker 시작→closing36.766초에서5.812초, constructor33.250초에서4.062초로 줄었다. 실제 handle stream599회/6200899byte/ReadFile1202회와 작은 capability bootstrap6712byte/2회를 구분한다. 자식201/부모207handle 모두 닫힘·부모 원 두 경계 stream identity402회·209fresh/final209·외부8fresh/final8·Frame CLOSED·내부Job CPU2.375초/최고54.61MiB/active0·cleanupTrue다. 진단부모74.953초/외부78.719초·시스템CPU표본최고35.16%/29.55%·가용RAM최저30.0023%/30.1042%이며 PC프리즈 해결 판정은 아니다.

다음은 새 소스 범위·상속 reader·중첩 제한 정규화를 실제 Native 전체 Frame와 원 shared metadata/Frame 합계5초·독립 판정에 연결·자격화하는 일이다. 실제 Native GO/write·제품10초 경로·제품 권한은 미완료다. 수용158개와3421개 전체 감사003은 재실행하지 않았다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다. 근거: `p09-361-native011-current805-inherited-worker-ready001/002.v1.json`, `current805-inherited-worker-ready-models207.v1.json`, `current805-inherited-worker-ready-owned206/208.v1.json`(뒤 항목도 동일 `p09-361-native011-` 접두사).

### 전체 소스 상속과 읽기 전용 명세 전달

`native011_mapped_source_transfer_inspection.py`의 실제002/owned201은 원 worker001 receipt의198개 소스 pin을 현재 원본과 새로 대조한 뒤 전달 코드2개를 명시적으로 더해200개를 잠갔다. 부모 원 첫 경계 뒤 제한된 STARTUPINFO 목록으로200개 실제 소스handle과 metadata reader1개를 상속한다. 부모 상속 비트 복원·같은 소유 Job·원 OS identity 확인 뒤27byte 진단start만 stdin으로 전송한다. 42634byte descriptor는262144byte 이하 익명 mapping이며 source byte/hash cache가 아니다. writable view/원 writer를 닫고 명시적 FILE_MAP_READ로 복제한 reader만 넘기며 부모·자식에서 write view 접근 거부5를 확인했다. mapping 생성1회/metadata DuplicateHandle1회는 원 pacer 예약2회에 포함하며 소스 읽기 단계의 pathname reopen/DuplicateHandle0과 구분한다.

첫001/owned199는 원 진단10초에서 첫 읽기 도중 중단됐다. 완료pass0/실제1750433byte·자식200/부모206handle 닫힘을 보존했다. 내부Job의 conhost1개 잔류로 내부 cleanupFalse/외부 소유 Job cleanupTrue였다. 현재 Python3.12.14의 time.monotonic이 GetTickCount64/15.625ms여서 짧은 바이트 예약마다 시계 간격 대기가 누적되는 문제를 확인했다. 바이트 대기 계산만 단조 고해상도 perf_counter로 수정하고 실제 EOF읽기·두 번 해시·2MiB/s·idle credit금지·10초 진단 제한을 유지했다. Job 정리는 프로세스 본체 종료 이후 정확한 소유 Job 잔류 자식도 종료하고 active0을 확인한다. 원 Native600/READY15/제품10 시계나 보호 정책을 변경하지 않았다.

모델198의18개와 수정 후 모델200의19개 정확ID가 통과했다. 수정 후 실제002는200개2227362byte를 두 번4454724byte·ReadFile804회 읽어200pin×2를 확인했다. 자식 시작 후 admission0.094초/첫 읽기1.266초/두 번째2.438초·부모 진단token→자식 종료2.359초다. 부모205fresh/final205·자식200/부모206handle 닫힘·원 두 경계 stream identity400회·원 클래스/저장 identity 유지·Frame CLOSED·내부Job active0/최고12.57MiB/CPU0.125초·cleanupTrue다. 전체 진단부모72.297초/외부76.984초·외부6fresh/final6·시스템CPU표본최고43.36%/41.41%·RAM가용최저28.5896%/28.5910%였다. 이 수치는 전체 준비/부모 확인 시간을 생략하지 않은 관측이며 원 worker READY15 통과나 PC프리즈 해결 판정이 아니다.

다음은 실제 원 worker 초기화와 readiness event/Job 검사를 연결한 EOF-only 자격 검증이다. 원 worker/GO/제품은 실행하지 않았고 기존3421개 감사003·수용158개를 재실행하지 않았다. Native 전체 소스 범위 연결·실제 Native Frame·합계shared5·제품 권한은 별도로 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다. 근거는 `p09-361-native011-current805-mapped-source-transfer001/002.v1.json`, `current805-mapped-source-descriptor-models198/200.v1.json`, `current805-mapped-source-transfer-owned199/201.v1.json`이다(마지막 두 종류도 동일 `p09-361-native011-` 접두사). 권한과 수명 계약은 Microsoft의 [CreateFileMappingW](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-createfilemappingw), [MapViewOfFile](https://learn.microsoft.com/en-us/windows/win32/api/memoryapi/nf-memoryapi-mapviewoffile), [DuplicateHandle](https://learn.microsoft.com/en-us/windows/win32/api/handleapi/nf-handleapi-duplicatehandle) 명세에 따른다.

### 실제 자식 소스 핸들 전달과 두 번 읽기

`native011_source_transfer_inspection.py`는 원 부모 Frame 첫 경계 뒤 소스handle3개만 제한된 STARTUPINFO 목록으로 넘긴다. 부모 flags 복원과 같은 소유 Job·원 OS identity 확인 뒤에만 별도 진단 start/descriptor를 보낸다. descriptor는262144byte 이하이며 직렬화한 pin/handle 숫자 자체를 잠금이나 읽기 증거로 인정하지 않는다. `native011_inherited_source_probe_child.py`는 실제 상속 disk handle의 OS ID/크기와 부모 PID를 확인하고 자식 상속 비트만 끈 뒤 두 번 새로 읽어 해시를 대조한다. 소스 읽기 단계는64KiB workspace/2MiB/s 상한이며 새 pathname open/DuplicateHandle/hash·byte cache가 없다. Python 시작 자체의 모든 OS 읽기가0이라는 주장은 하지 않는다.

모델195의8개 정확ID와 실제 source-transfer001/owned196이 통과했다.3파일24073byte를 자식에서 두 번48146byte·ReadFile12회 읽었고 소스handle3개를 닫았다. 자식 읽기를 부모의 byte 횟수에 더하지 않았으며, 부모 공유잠금·write/delete 거부32·원 전후 두 경계/stream identity6회·원 클래스/저장identity·6handle 전체 닫힘/Frame CLOSED를 확인했다.10fresh/final10·진단child4.047초/외부부모7.328초·token→종료0.265초·내부Job active0/최고11.77MiB/CPU0.031초·외부Job active0/최고40.98MiB/CPU0.25초·cleanupTrue다.

이 검증은 전체198개 입력이나 원 worker 초기화/READY15/Native/제품을 실행·자격화하지 않았다. 다음 확장에서는 큰 descriptor의 전달이 블로킹 대기나15초 밖 prewarm으로 바뀌지 않도록 해야 한다. 전체 입력의 새 byte/hash 읽기와 원 readiness event/Job/GO 검사를 함께 연결한 뒤 실제 시간을 판정한다. 기존 전체 감사003/수용158개는 재실행하지 않았고 신규 코드의 Native 전체 범위 선언·합계shared5·제품 권한은 별도 경계로 유지한다.

### 준비 단계 소스 핸들 상속의 부모 경로

기존198개 소스의396회 재열기는20/s에서19.75초의 최소 간격을 요구해 READY15에 맞지 않는다. `native011_worker_source_inheritance.py`는 부모가 이미 잠근 정확한 파일 handle을 선택해 상속 비트만 설정하고 복원하는 기초 경로다. 원 SourceCoverage.verify(before)와 살아 있는 Frame/원소유자/첫 byte 경계를 요구한다. 원 클래스·저장 OS identity·byte count는 바꾸지 않고 worker의 새 byte/hash 읽기를 면제하지 않는다. armed 동안 원 OS identity 검사를 대체하지 않으며 복원 후 원 검사를 다시 적용한다. 상속 설정 자체는 CreateFile/DuplicateHandle/ReadFile/CloseHandle을 호출하지 않는다. 향후 자식의 실제 handle 생성·정리 비용은 별도로 관측해야 한다.

모델192의7개 정확ID가 통과했고 실제 source-inheritance001/owned193에서2파일12861byte의 원 전후 읽기·stream identity4개·실제 Win32 상속 비트2개 설정/복원·write/delete 공유 위반32를 확인했다. 원 Frame/Locks 클래스와 저장 identity/read count는 유지했고5handle 전부 닫힘·Frame CLOSED/미commit·7fresh/final7·부모6.094초·Job최고28.38MiB/CPU0.203초·active0/cleanupTrue다. 원 취득14/읽기20 속도와 실제 open 예약11회는 유지했다.

다음은 실제 제한된 STARTUPINFO handle_list, 같은 소유 Job, 부모 flags 복원 후 시작, 자식의 실제 두 byte/hash 읽기와 정리를 연결하는 것이다. 이2파일 부모 검증은 실제 자식 상속·전체198 worker·READY15·Native 전체 scope/Frame·제품 자격이 아니다. 기존 전체 감사003/수용158개는 재실행하지 않았으며 새 코드의 전체 실행 입력 범위 선언은 별도로 필요하다.

### 새 세대의 전체 입력 감사와 검사 본문 통과

실제 shared-parent005/현재805 owned-metadata-audit003이 전체 준비 감사를 통과했다. 전체3421=현재3002+보존419를 양쪽 경계에서 각각216312207byte 읽었고, 양쪽 pin digest는 e7e5754797d4c7e108c6a33b220836e749c0f924edb8d0ab483bb65c5ad55641로 같다. 원 Batch의 종료 상태는 EMPTY_BATCH_AUDITED_NOT_ACCEPTED이며 실제 Frame 사례/수용증가는0이다. metadata 본문은335fresh/final335·675actual physical reads/156879468byte·현재3002선택/Rust805·325회 fresh 읽기/복원을 확인했다. semantic 복원506953168byte를 물리 읽기 수치에 더하지 않았고 byte/hash/JSON cache도 사용하지 않았다.

원 shared5의 metadata decoder 작업은1.198초이며 Frame 등록/실작업은0이다. 실제 engine.run_owned/Frame/worker/제품 실행도0이다. 준비4단계의 개별600초와 실제 Native600/READY15/제품10을 구분하며, 이번 결과가 Native 시계 초기화나 실제 Native/준비15초/합계shared5/제품 통과를 뜻하지 않는다.

readonly002는 마지막 읽기 도중 시스템CPU92.8%로 중단돼 원 실패로 보존한다. 그 순간 부모CPU0%·RAM가용28.2737%·Job누적CPU12.734초/최고109.62MiB·active0/cleanupTrue다. 자식 최종 receipt는 없어 세부 metadata 자격은 인정하지 않는다. 특정 외부 프로세스의 과거 급등 책임은 확인하지 못했고, Defender나 검증 코드의 원인으로 단정하지 않는다. 검토 후 원 publisher를 이용한 opening/metadata/closing의 배타적 fsync checkpoint를 추가했다. checkpoint는 완료한 준비 단계의 증거 보존용이며 입력 cache·후속 fresh 읽기 생략·제품 권한으로 사용하지 않는다. 모델189의14개와 감시기 모델190의6개 통과 후003에서 단계별 증거3개가 실제 생성됐다.

003은 construction101.453초/opening332초/metadata85.547초/closing331.515초·child850.515초/부모912.953초였다. 구성344fresh/final344·부모348fresh/final348·Job최고108.69MiB/CPU13.672초·active0/cleanupTrue이며, 시스템CPU표본최고79.89%(자식)/68.38%(부모)·가용RAM최저27.5188%(자식)/27.2342%(부모)였다. CPU/RAM·1코어·6.25% Job 상한과 기존 읽기 속도·원 검사를 유지했다. 다음은 살아 있는 Native 입력 잠금과 실제 metadata/Frame 합계shared5, READY15 경로다. 제품 수용158/249·잔여91 및 제품 실행 권한 답변대기는 그대로다.

### 첫 전체 읽기와 검사 본문 인수 수정

`native011_current_epoch_audit.py`는 원4단계 준비 전용600초 epochs와 원 metadata 함수 전체를 호출한다. 실제 shared-parent003/현재805 owned-metadata-audit001에서 첫 전체3421개·216303851byte를337.140초에 읽어 모든 pin이 일치했다. construction89.891초 뒤 opening을 완료했고 metadata1.016초에 KeyError가 발생해 closing은 실행하지 않았다. 모든 단계 cleanupTrue·Job최고85.12MiB/CPU7.703초·active0·opening시스템CPU표본최고37.11%/가용RAM최저27.9957%다. 첫 전체 읽기 완료를 metadata·양 경계·Native600·READY15·Frame/worker/제품 PASS로 승격하지 않는다.

검사 함수가 직접 인덱싱하는 `case165-step-config001.v1.json`의 정확685byte pin은 현재 대기열에 있었지만 callback의 명시 인수 목록에 없었다. `callback_sources`는 이미 current에 있는 정확 pin만 검사 인수에 추가하며 원 보고서109입력·대기열 분류·역사419개는 변경하지 않는다. 원 scope4개/감사facade5개의 새 정확ID 모델185가 통과했다. 수정 후 실제 metadata 검증은 별도 readonly002/shared-parent004에서 수행해야 한다.

부모 감시기의001 실패는 늦게 관측된 metadata 신호로 실패 종료 자식의 phase를 회전하려다 원 Monitor의 terminal 거부가 자식 원인을 가린 것이다. 원 실패/자식 receipt를 보존한다. `native011_current_epoch_owned_audit.py`는 원 Monitor 클래스와 guard/Job/cleanup을 유지한 채 실패 terminal 자식의 원 오류·종료코드·미인정 단계 신호를 보존한다. 두 관측 지점의 종료 race에서도 원 Monitor.failed와 단계 수를 유지하며 새 guard/단계 credit/재실행/PASS를 부여하지 않는다. 모델187의6개가 통과했고 실제 종료 경로는 다음 회차에서 확인해야 한다. 자동 재시도나 새 제품 실행 권한은 없다.

### 새 세대의 실제 검사 실행기와 독립 비용 연결

`native011_current_epoch_shared.py`는 원 계획 prefix와 기존 prepare/입력 분류/shared 부모/metadata callback 코드를 직접 사용한다. 새805 scope 의존성만 원 Batch.install_scope에 연결하고 원3정책 슬롯과805의4변경에 대한 전체 AST 역복원을 모두 확인한다. 실제 callback1회는 NEW 상태에서 metadata IO 전에 원 오류로 거부된다. 별도 shared-parent001/owned178은274fresh/final274·전체3417/현재2998/보존419·원5단계 Frame class/동일 shared owner·등록/실작업0·정상 복원을 확인했다. 이후 shared-parent002/owned181에서 독립 판정 연결까지 진행했다.

`native011_current_epoch_runtime_cost.py`는 원 budget/cost/retained_evidence/project_checker 전체 코드와 현재 product10 mechanics를 유지하고, 새 Rust805 경로 inventory에서 측정한170회를 실제 엔진과 독립 판정에 같은 비용 의존성으로 전달한다. 원 엔진 함수 identity와 전체 독립 validator 본문·원 관측 기록·기본 모듈은 유지한다. 원 complete_cost의167 단일 데이터 슬롯만170으로 바꾸고 전체 코드 역복원을 확인한다. 새6개 정확ID 모델179와 shared scope3개 모델180 및 실제002가 통과했다. 기본helper59·Native64의 원 상한을 높이거나 모듈을 숨기지 않았다.

실제002는 전체3419=현재3000+보존419·원162descriptor/physical 매핑 유지·342fresh/final342·child88.344초/부모91.641초·Job최고83.88MiB/CPU6.031초·시스템CPU표본최고33.14%(부모)/32.25%(자식)·가용RAM최저30.6573%(부모)/30.7382%(자식)·active0/cleanupTrue다. 엔진/독립 판정/원 선언 비용 모델이 정확히 같으며 shared5를 포함한576.260595초+준비15=591.260595초/600미만이다. 여유60·최종 표본0.5·제품10을 유지한다. 이 값은 예상 비용이고 실제 Native600·공유5·READY15의 실행 자격은 아니다. metadata/Frame decoder 등록·실작업과 metadata 본문/Frame instance/worker/제품은 모두0이다.

다음은 새 구성을 준비 전용 construction/opening/metadata/closing의 실제 전체 감사에 전달하는 일이다.342개 구성 입력 확인을 전체3419/현재3000개 양 경계 바이트 확인으로 승격하지 않는다. 원 입력 읽기 속도·OS identity·live locks·CPU/RAM 보호와 기존158개 수용 및 Native011 제품 권한 답변대기를 유지한다.

### 새 소스 세대의 검사 명세와 대기열 연결

`native011_current_epoch_report.py`는 원 producer64와 기존 제어25 경로에 명시된 코드12/계보data3의15개 역할만 더한다. 원 main/정리/전체 canonical validator 코드를 전용 namespace에서 유지하며 새 build002/listing001/preimages001의 정확 pin과 generation003을 확인한다. 관측 파일을 자동 합집합으로 추가하거나 과거 listing을 새 runtime PASS로 바꾸지 않는다. 모델169의5개 정확ID와 실제 metadata-plan003/producer generation003/owned170이 통과했다. 명세 입력109개를 처음·끝에 fresh 확인했다. 전체805 Rust 바이트 감사나 살아 있는 Frame 자격은 아니다.

`native011_current_epoch_report_admission.py`는 원 shared-parent의 admit_report 전체 코드와 분류 검사를 유지하고 reports 의존성만 새 API로 바꾼다. admission001/owned172는 고정 projector 제어2개 자리에4개를 넣어 거부된 원본으로 보존한다. admission 전용2개는 cohort.required로 옮겨 명시했다. 모델173의 빈 required fixture 실패도 보존했으며 실제 비어 있지 않은 계약에 맞춘 모델174의4개가 통과했다. 실제 별도 admission002/owned175는 원 Batch/계획을 변경하지 않고 새 Batch.NEW에 명세를 연결했다. 전체3411=현재2992+보존419이며 기존 현재 입력·보존419개 pin·원162manifest를 유지했다. 134fresh/final134·부모55초·Job최고54.22MiB/CPU2.641초·시스템CPU표본최고20.08%·가용RAM최저28.1769%·active0/cleanupTrue다.

다음 경계는 이 명세와 새805 입력을 실제 shared decoder/Frame·원 독립 판정에 전달하는 것이다. 순회170을 계산용 복사본뿐 아니라 실제 엔진/독립 판정의 동일 비용 계보에 적용하고 원 양 경계 감사를 확인해야 한다. 이번 연결은 전체3411개 byte 감사·engine/Frame/worker READY15·제품 실행이 아니다. CPU/RAM·1코어·원600초/공유5초/준비15초/제품10초와 기존158개 수용 및 제품 권한 답변대기를 유지한다.

### 새 소스의 매핑과 검사 본문 연결

`native011_current_epoch_graph.py`는 같은 원162 Binding instance의 semantic_union 앞에서만 이전/현재 Rust5개를 정확 pin으로 구분한다. 원 semantic union을 호출하고 class의 project/budget/evidence 함수와 descriptor/manifest를 유지한다. `native011_current_epoch_metadata.py`는 실제 원 Batch.install_scope의3슬롯 결과에서 scope 의존성·실제 새 listing필드·Rust805 guard/label4곳만 바꿨다. 전체 승인 AST로의 역복원과 원 NEW 상태의 metadata 사전거부를 유지한다. 정확ID graph3/metadata4 모델164가7run/0error/0failure/0skip으로 통과했다.

actual parent-inspection003/owned165는 graph와 사전거부 뒤 비용 계산의 옛167 순회 조건에서 실패했다. 원 실패와 미완료 종료를 유지한다. 실제805개 inventory의 순회는170회다. `native011_current_epoch_inventory_budget.py`는 원 예산 함수의 전체 code/defaults/closure·정확 횟수 검사·model/views를 유지하고 전용 복사본의 inventory identity 데이터만170으로 결합한다. 기본 module과 원167은 유지한다. 정확ID 새3개 모델166이 통과했다. 단위모델의173은 합성 값이며 실제 측정값170과 구분한다.

별도 actual004/owned167은 전체3400=현재2981+보존419·동일162매핑·실제 graph physical current2981의 정확한 일치를 확인했다. 원 Batch.NEW에서 새 검사 함수는 metadata IO 전에 원 READY_METADATA_OWNER_ONLY로 거부됐다. 실제 metadata 본문/listing소비/worker/parent호출/Frame/제품은0이다.252fresh/final252·child61.203초·부모64.547초·helper59/64·Job87.19MiB/CPU4.5초·정리True다. 이는 구성 입력252개의 경계이지 전체2981/3400개 감사나 현재Rust805개 전체 hash 재검사가 아니다.

실제 inventory170을 넣은 원 전체 모델572.541132초(shared5 포함)에 준비15를 더해587.541132초/원600 미만을 확인했다. 원 margin60·제품10·마지막표본 등의 항목은 유지한다. 예상 비용이며 실제 준비15/decoder5/Native600 완료가 아니다. 이 단계는 계산용 budget 복사본만 결합했고 실제 engine/독립 판정의 비용 경로 적용은 남는다. 실제 engine의 metadata callback도 여전히 명시 거부한다. 다음은 새 metadata 보고서와 공통decoder/Frame 연결·동일170 모델 전달·원 전체 감사다.

근거는 `p09-361-native011-current805-graph-metadata-models164.v1.json`, `p09-361-native011-current805-parent-inspection003.v1.json`, `p09-361-native011-current805-inventory-models166.v1.json`, `p09-361-native011-current805-parent-inspection004.v1.json`, `p09-361-native011-current805-graph-metadata-owned167.v1.json`이다. 공식158/249·잔여91·next165·목표ACTIVE·새 제품 권한 대기를 유지한다.

### 시험 모듈 선택 오류 정정

범용 명령의 문자열 치환이 시험 파일 경로의 첫 일치만 바꾸고 실제 import 모듈을 그대로 두는 오류를 확인했다. 원 결과는 보존하되 아래 기록을 요청한 새 시험의 통과 근거로 사용하지 않는다. 아래 표의 모듈명은 공통 `test_native011_` 접두사를 생략했다.

| 기록 | 요청 모듈 | 실제 선택 또는 종료 |
| --- | --- | --- |
| 136 | build_start | current_cohort_build |
| 139 | build_generation2 | current_cohort_plan |
| 141 | build_generation2 | current_cohort_build |
| 151 | current_epoch_metadata_roles | current_epoch_binding |
| 155 | current_epoch_batch_plan | current_epoch_plan |
| 156 | current_epoch_plan_prefix | 잘못된 시험 경로로 자식 생성 전 실패 |

별도 `native011_scoped_test_runner.py`는 모듈명·실제 파일·실행test ID·개수를 함께 검증한다. 누락14개(시작4/회차3/metadata역할2/Batch3/prefix2)와 선택기 자체3개, 합계17개를 한 번씩 실제 실행했다. `p09-361-native011-scoped-test-selection-correction001.v1.json`/owned157은17run/0error/0failure/0skip·37fresh/final37·부모9.297초·cleanupTrue다. 제품/Native/과거 제품 통과 사례는 실행하지 않았다. 아래 이전136·139·141·151·155의 모델 수 인용은 이 정정으로 대체하며 합산하지 않는다. 실제 build002/listing001/metadata binding002는 별도 관측으로 보존한다.

### 새 소스의 실제 미개봉 계획과 엔진 연결

`native011_current_epoch_plan.py`는 원162개 wire alias 규칙을 호출하고 이전Rust5개와 새Rust5개만 정확 pin으로 구분한다. 제3의 hash·보관본 변조·현재와 보존의 중첩을 거부한다. 실제 원 Batch.NEW를 사용한 unopened-plan001/owned158에서 전체3392=현재2973+보존419와162개 manifest의 정확한 보존을 확인했다.64fresh/final64·child33.125초·부모35.922초·cleanupTrue다. 이는 구성을 위해 실제 읽은64개의 전후 경계이지 전체3392개 byte 감사가 아니다.

parent-inspection001/owned160은 원 엔진과 부모를 구성했으나 원 worker의 실행 대상이 여전히 이전 binary여서 거부됐다. 원 실패를 유지한다. 새 `native011_current_epoch_worker_scope.py`는 기본 모듈이 아닌 전용 namespace2개의 scope.EXE_PIN만 새805 빌드로 연결한다. 함수 code/defaults/closure·원 인수 함수와 결과는 유지하고 실행 뒤 변경/반복 변경을 거부한다. 정확-ID 모델161의4개와 actual parent-inspection002/owned162가 통과했다. 원 constructor 전체는 epoch 설치5문장만 추가한 AST 역복원을 확인했다.

실제002는 전체3394=현재2975+보존419·기본helper59/64 이내·worker/parent호출0·Frame0·metadata명시거부·제품0·246fresh/final246·child109.265초/부모112.719초·정리True다. Job최고86.79MiB/CPU4.188초·child시스템CPU표본최고39.03%/가용RAM최저29.4959%였다. 살아 있는 Frame·전체 source freshness·metadata 본문·준비15초·독립 제품 판정의 자격은 아니다. 다음은 Graph/metadata의 새805 소스와 listing 스키마/버전 투영, 원600초/decoder5초/준비15초/제품10초 모델 연결이다.

근거는 `p09-361-native011-current805-unopened-plan001.v1.json`, `p09-361-native011-current805-parent-inspection001.v1.json`, `p09-361-native011-current805-parent-inspection002.v1.json`, `p09-361-native011-current805-parent-owned162.v1.json`이다. 공식158/249·잔여91·next165·목표ACTIVE·새 제품 권한 대기를 유지한다.

### 최신 소스와 기존 시험 binary의 세대 분리

이전 Rust5개는 `native011_prior_source_preimages.py`에서 모듈 선언4곳과 CLI 확장만 역제거한 뒤 기존 크기/SHA256과 정확히 대조했다. 모델145의4개와 actual preimages001/owned146이 통과했고, 별도 `implementation/p09/evidence/p09-native011-prior-compiled-rust787-code/` 아래5개 .rs/82353byte를 생성했다. 원본 Rust 변경은 없다. actual scope-declaration001/owned148은 보관본5개의 전후 바이트를 확인하고 새 current855개/전체1715개 선언을 무손실 구성했다. 원 history1658개의3+4경로와 이전 compiled826개의5경로만 동일 바이트의 보관본으로 바꿨고 나머지는 보존했다.14fresh/final14는 선언 구성에 실제 읽은 입력이며 전체1715개 감사가 아니다.

`native011_current_epoch_binding.py`는 원 binding 전체의 `len(rust)==787` guard 하나만805로 투영하고 AST 역복원을 확인한다. 원 FRESH131/105 cursor/body 검사를 유지하고 실제 새 listing 스키마를 전용 API로 입증한다. 옛 listing PASS를 만들거나 전역 모듈을 수정하지 않는다. 모델149의4개와 actual001/owned150 이후 metadata 코드10/내재data3의 고정13역할을 선언했다. 새2개 역할 모델151 및 actual002/owned152가 통과했다. 원 함수 listing_inputs→compose1회, Rust805, 필요1725/현재866개 선언, 실제 읽기21개 전부가 필요 범위에 포함됨과21fresh/final21·정리를 확인했다. 실제21개 관측을 임의로 합쳐 선언을 늘리지 않았다.

actual152는 부모12.140초/child9.281초·Job35.07MiB/CPU0.391초였다. 전체1725개 현재 바이트·Native Frame·worker·준비15초·제품10초·독립 제품 판정은 미완료다. 다음은 실제 Batch.NEW 계획에서 보존419개와 전달 매핑162개를 유지하며 이 선언을 연결하는 일이다. 원600초 및 CPU/RAM 보호와 새 제품 실행 권한 경계를 유지한다. 기존158개/실패 원본은 보존하고 제품/249시험 본문/한글/접근허용은 실행하지 않았다.

근거는 `p09-361-native011-prior-source-preimages001.v1.json`, `p09-361-native011-current805-scope-declaration001.v1.json`, `p09-361-native011-current805-original-binding002.v1.json`, `p09-361-native011-current805-binding-owned152.v1.json`이다.

2026-10-18 별도 build002와 listing001이 통과했다. build002는805개 실제 Rust inventory와 전체843개 빌드 입력/산출물의 첫·최종 fresh 바이트 검사를 마쳤다. 원 profile81·opt1/line-tables/assertion/overflow와 단일 job/codegen16을 유지하고 Cargo JSON139개를 모두 검증했다.378.047초·Job최고1930.28MiB·시스템CPU표본최고46.77%·가용RAM최저36.2407%·cleanupTrue이며 제품 시험 본문은 실행하지 않았다. 실패001/그 intent와 예전 binary는 그대로다.

새 binary는 `target/p09-361-native011-current-source-g002/debug/deps/form_stored_provider-p361-native011-g002.exe`,14174720byte/SHA256 `1e782c2551ff96c191b1ab2aa6c86650f1c43676cb8c0db2b0c27613095925d8`다. listing001은 이 정확한 binary의 `--list --format=terse`만 실행했다. 원 고정 pure parser와 실제59모듈의 compiled source pin을 대조해 전체249이름·기존249목록의 일치를 확인했다.70fresh/final70·43.516초·cleanupTrue·제품/시험본문0이다. 이 단계에서805개 전체 소스를 재검사했다고 주장하지 않으며 current runtime/Native Frame/Gate 자격은 아직 아니다.

경로/회차 분리의139·141 모델과 actual plan002/owned140, build→list143 모델을 보존했다. 다음은 이 새805 빌드/목록 계보를 실제 runtime의 현재 입력 선언과 원 worker/Frame/독립 판정으로 연결하는 것이다. 기존158개는 과거 수용 세대로 보존하며 통과 사례를 다시 실행하지 않았다. 공식158/249·잔여91·next165·목표ACTIVE이며 새 제품 권한 답변은 대기다. 아래 최초 빌드001 및 계획001은 이전 상태의 이력이다.

근거는 `p09-361-native011-current-cohort-build002.v1.json`과 `p09-361-native011-current-cohort-listing001.v1.json`이다.

`native011_current_cohort_plan.py`는 원787개와 기록된 변경5/추가18개로 새805개 예상 입력을 분리한다. 실제 plan001/owned133은 변경23개를 포함한32fresh/final32·원 profile81/recipe 역복원을 통과했다. 새4개 계획 모델132와 parser/stream/env 모델134의6개·dependency 검사 추가 후135의7개는 제품 시험이 아니다. unchanged782개와 새 binary는 계획만으로 자격화하지 않는다.

`native011_current_cohort_build.py`의 실제 build001은842개 첫 읽기를 마친 뒤 capture가 stdin을 먼저 닫고 후속 token 쓰기가 실패해 종료됐다. 원 intent가 소비됐고 새 target은 생성되지 않았다. Cargo/제품 본문0·JobCPU0.141초/최고29.98MiB·cleanupTrue다. 양 바이트 경계/빌드/listing PASS가 아니며 원 CLOSED_READONLY_FAILURE와 실패 receipt를 보존한다. 회차001을 재실행하지 않는다.

수정은 고정 build-only token을 EOF capture 전에 쓰는 순서와 Windows CRLF/LF를 처리하는 경계에 한정했다. 새4개 모델136과 실제 owned137의 제한된 child에서 token→EOF→exit0/정리가 통과했다. 실제 child는 현재 Job 상한을 재확인했고 Cargo·제품 프로세스 생성은 항상 거부했다.10fresh/final10·3.5초이며 전체 빌드 자격은 아니다. 다음 빌드는 새 회차·새 출력 경로·별도 계획이 필요하고, 기존805개 전후 fresh 검사·실제 inventory·원 compiler stream 검증과 자원 보호를 유지한다. 제품 Native 권한/준비15초/제품10초는 변경하지 않는다.

근거는 evidence의 `p09-361-native011-current-cohort-build-plan001.v1.json`, `p09-361-native011-current-cohort-build001.v1.json`, `p09-361-native011-build-start-models136.v1.json`, `p09-361-native011-build-start-owned137.v1.json`이다.

2026-10-17 실제 metadata audit002는 whole opening에서 `document_import.rs`의 기존26919byte와 관측26946byte가 달라 거부됐다. `pub mod reference_targets;`27byte를 메모리에서만 제거하면 원 SHA와 정확히 같았다. 기존 binary를 현재 소스의 자격으로 승격하거나 추가된 구현을 제거해 감사를 통과시키지 않는다.

이후 전체 소스 조사129는 종료 재확인 중 시스템CPU90.91%로 중단됐다. 첫 읽기809pin을 보존한 원 실패 receipt에서만 별도 복구131을 수행했다. 기존 Rust787개가 모두 관측됐고 변경5개/추가18개로 관측805개였다. 새 추가 기능은 참조 API/SDK/읽기/시험/발견 예제다. 기록된 첫 읽기 비교이며 현재805개의 완전한 양 바이트 감사·inventory 재확인·최신 binary 자격은 아니다. 기존158개 수용은 과거 세대의 결과로 보존하고, 최신 빌드/정확한 시험 목록/변경 영향과 재사용 조건을 별도로 확인한다. 새 제품 실행 권한을 뜻하지 않는다.

조사 도구의 기록 크기 초과127은 입력 pin/검사를 유지하고 자원 표본만 count/extrema/마지막8개로 요약해 개선했다. 새 receipt 모델128의3개와 변경 후130의5개가 통과했다. CPU 중단129는 실패 원본으로 유지했다. 복구131은6fresh/final6·6.328초·cleanupTrue이며 과거 제품/전체 Rust/원본 문서를 다시 실행하거나 재검사하지 않았다. 근거는 `p09-361-native011-recorded-source-drift-recovery001.v1.json`, `p09-361-native011-source-recovery-owned131.v1.json`이다.

준비 전용 four-epoch 모델120의8개와 owned controller121의6개·cold sample123의4개는 통과했지만 실제 whole 감사002의 거부를 대신하지 않는다. 원 construction/opening/metadata/closing의600초 guard·최초 실패·owner/순서·정리를 유지하며 실제 Native600초·준비15초·제품10초는 변경하거나 재설정하지 않는다. 실제 metadata 본문/Frame/worker/제품은 아직 실행되지 않았다.

새 metadata 계획과 shared 연결은 `native011_metadata_report.py`/`native011_shared_parent.py`가 담당한다. 원 producer64에 고정 명명 code/data 역할만 더하고, 원 실패010과 source92개를 첫/최종 fresh 확인한 뒤 self-free 계획001을 독점 생성한다. 실제 producer generation001/owned115는92/96개 양 경계를 완료했다. 새8모델114는 임의 source 확장·보존 receipt 재분류·고정 실패/패키지 변조·False/0 혼동을 거부하며, 실제 파일 감사나 Frame 검증을 대신하지 않는다.

`--inspect-shared --metadata-generation 1`의 실제 shared-parent004/owned-preparation004는 원 shared Frame의5단계 체인·원 constructor/동일 owner·실제 engine lossless reader router·전체 scope AST inverse·metadata callback 연결을 확인했다. callback1회는 NEW 상태에서 원 사전감사 거부로 IO 전에 중단됐고 reader/Frame/worker는 모두0이다. 원 메타데이터와 Frame decoder의 shared owner는 연결됐지만 두 등록은False·실제 decoder 작업0이며 종료 시 복원했다. 실제 metadata 본문/whole 바이트 감사·shared5 디코딩·Native 잠금·준비15초·제품10초 통과가 아니다.

새 범위는 전체3364·현재2945·보존419다. 이전3358/2939에서 공유/계획/분류 코드4개와 원 실패010/계획001 데이터2개만 명시적으로 추가했고 보존419pin은 유지했다. helper59/Native합계64, 원 shared5/준비15 포함 선언 비용558.504513초로600 미만이다. 자식303fresh/final303·68.219초, 부모306fresh/final306·124.703초·cleanupTrue다. Job1코어/BelowNormal·CPU6.25%/RAM8% 상한·최고private87.20MiB·CPU4.969초·종료active0/핸들정리True이며 시스템CPU최고51.17%/55.27%·가용RAM최저31.47%/31.48%다. 이303/306개 source-byte 증거를 전체3364개 현행 감사나 살아 있는 잠금으로 사용하지 않는다. 다음은 실제 whole 초기/최종 감사 후 metadata 본문과 원 decoder를 검증하는 것이다.

`native011_parent_oracle.py`와 parent_plan의 `--inspect-oracle`은 실제 미개봉 부모에 원 독립 판정기와 metadata/Frame 추가 accounting을 구성하는 비제품 경로다. 원 코드·독립 선언·제품10초, shared5와 준비15를 포함한600초/여유60 모델, 실제 helper64 합계를 요구한다. 후보 검증·metadata 본문·Frame 취득·worker/GO 실행 모드는 없다. parent-oracle-attempt003과 owned-preparation-attempt003은 실제 연결·명시적 source/helper 대조·완전 비용 모델을 통과했다. 기본59개/Native합계64개이며 원 상한을 올리거나 정상 모듈을 숨기지 않았다. 실제 실행시간·준비15초·metadata/공유 Frame/제품 자격은 별도다.

준비 guard4개와 고정 원 bootstrap loader를 private namespace에 구성하고110의 보호 모듈2개·112의 명시적 부모 제어입력/bootstrap4개를 확인했다. 부모 진입/판정 연결 파일2개를 현재/전체/논리 계획에 명시적으로 추가해 전체3358·현재2939·보존419를 구성했다. 보존 pin과 기존 계획은 그대로 유지한다.002의 helper65/누락 진입파일 거부와104/108/109의 RAM 중단,106의 생성 전 거부/cleanup 집계 결함은 보존한다.

`native011_owned_preparation.py`는 이 readonly 부모 구성만1회 호출하는 내구성 실행기다. 최초 원인 보존·실제 Job cleanup·생성 전/부분 생성 구분의 새6개 모델111을 통과했다. 중단된 guard의 finally 재취득으로 RAM 오류가 CPU_STOP_LATCHED로 바뀌는 경로를 없앴다. 기존 Owned Job·bounded capture·원 guard/입력 비교를 유지하고 자동 재시도/제품 명령 인자는 없다. 현재95%까지의 fresh 여유와 이전 실측 peak83.47MiB를 시작 전에 대조하지만 이후95% 감시를 대체하지 않는다. 한 검증 프로세스가 실행 중일 때는 그 handle만 관측하며 별도 shell 조회 프로세스를 병행하지 않는다.

실제003의 shared5 포함 원 완전 비용은540.805985초, 준비15를 더하면555.805985초로600 미만이다. 자식290fresh/final290·57.297초, 부모293fresh/final293·106.218초·cleanupTrue이며 Job최고private84.38MiB·CPU4.625초·종료active0다.1코어/BelowNormal·CPU6.25%/RAM8% 상한은 유지했고 시스템CPU최고 자식20.50%/부모18.36%, 가용RAM최저44.56%/44.66%였다. 원 독립 checker/accounting 함수와 현재 선언은 연결했으나 후보 판정·metadata 본문·Native Frame·worker/제품은 실행하지 않았다. 전체3358개를 현행 fresh 검증한 결과가 아니며 다음은 새 metadata report/callback·shared Frame와 부모/worker의 살아 있는 입력 경계 연결이다.

`native011_worker_transport.py`는 고정 원 `batch_worker_entry.py` 바이트를 받아 회차·경로 상수만 private namespace에 투영한다. 중첩 코드 전체의 역복원과 원 defaults/closure 보존을 요구한다. 원16KB 제한, 내부/외부 해시, 원009 참조 입력과 전체162개 대조를 유지한다. 원010 파일/intent/함수를 변경하지 않는다. 실제 launcher·GO·파일 게시 기능은 없다.

`native011_zlib_binding.py`는 고정 원 `batch_zlib_binding.py`의 전체 생성자·디코더·선언표·과거 실패8역할을 유지한다.011 manifest/hint/zlib 경로를 별도로 구성하며 원009 참조를010 성공 이력으로 바꾸지 않는다. `native011_package.py`는 새 manifest/wire/bootstrap 바이트를 메모리에 구성하고 원 entry와 identity 바이트 검사를 연결한다. admission용 참조는 독립 재구성 후 새 Binding으로 연결하고 실제 inner decoder 결과와162개 전체/manifest를 대조한다. 메모리 입력 재검사는 이후 새 파일에 대한 물리적 첫/마지막 읽기를 대신하지 않는다.

새 검사071의7개,073의4개,076의통합2개가 통과했다. 총13개는 모델 계약이며 실제162 데이터 자격·제품 수용이 아니다. 각 회차fresh/final은8/8·12/12·14/14, 전체3.062·3.015·3.390초, cleanupTrue다. 성공 회차의 CPU표본최고26.32%·가용RAM최저31.89%였고 기존 자원 보호를 바꾸지 않았다.070의집계 실패,072의투영 슬롯 실패,074/075의새 Binding 연결 실패를 보존했다. 원16/648 준비 suite와 수용 제품 사례는 반복하지 않았다.

`native011_preparation.py`의 실제 고정 참조 구성과 새 파일 디스크 admission은 actual-package-attempt002/owned079에서 통과했다. 새 zlib manifest99480byte·capsule15058byte·bootstrap4898byte를 배타적으로 게시했다. 실제 원 entry가4개 입력을 fresh 읽고 독립 원009 참조→새 Binding→원 decoder로 전체162개/manifest를 대조했다. 원009 참조 생성/decoder3회는 새 패키지의 구성·메모리 admission·독립 디스크 admission이며 과거 자격 suite/제품 재실행이 아니다. 명시적 소스 선언75파일803825byte, 자식59fresh/final59·16.047초, 부모65fresh/final65·26.766초·cleanupTrue다. 실제162 envelope 파일 전체의 freshness나 Native source Frame은 이 결과의 범위가 아니다.

첫 attempt001/owned078은 부모와 자식의 원 배타 mutex 중복 확보로 입력0/출력0에서 거부됐다. 원본을 보존하고 읽기 전용 실행 동안만 자식이 잠금을 소유하도록 분리했다. 부모는 사전 읽기 후 잠금을 해제하고 자원 표본 감시를 유지하며, 자식은 원 acquire를 통과해야 구성하고 종료·정리 후 부모가 다시 확보한다. 별도 mutex 이름·검사 생략·잠금 파일 강제 제거는 없다. Job readback은1코어/BelowNormal·PC전체CPU6.25%·RAM8% 상한이며 최고 private46.63MiB·종료 후 active0이다. 자식 시스템CPU표본최고43.36%·가용RAM최저26.43%, 부모 최고42.80%·최저25.87%였다.

`native011_worker_preparation.py`와 `native011_eof_inspection.py`의 실제 engine/EOF 연결은 eof-inspection-attempt007/owned087에서 통과했다. 게시된011 패키지3개를 재생성하지 않고 원 entry·전체162개 decoder와 원 engine/worker를 구성했다. 원 builder의 회차/정체5상수를 투영하고 중첩 코드 전체의 역복원을 확인했으며 product10 상수는 원 engine build에 그대로 남는다. 실제 stdin EOF에서 원 run_case112_current_stored.py worker가1회 호출되고 WORKER_NOT_AUTHORIZED로 거부했다. 제품 호출0·프로세스 생성 시도0·정책 복원True이며 준비 신호 이벤트/Native Frame을 대신하지 않는다.

초기화의 실제 파일 열기는 고정 원 소스에 선언된 pin으로 확인한다. 원 flat 초기화 모듈36개509413byte의 닫힌 literal code pin174개를 사전 추출하며 코드를 실행해 pin을 만들거나 임의 파일을 허용하지 않는다. 중복은 같은 pin만 허용하고 누적은 선형 대조로 처리한다. 기존 Native009 profile의252개 코드와 추가 보관 코드6개는 허용 목록 선언으로만 사용하며 과거 전체 freshness를 재사용하지 않는다. 실제 초기화에서124개 선언 입력/140개 열기를 확인했고 bytecode 열기45개를 거부했다. 테스트 소스의 원 바이트 검사는 테스트 재실행이 아니다.

001~006의 누락 선언/빈 scope/STEP/helper 상한 실패는 보존한다. 검사나64개 상한을 제거하지 않고 새 준비 모듈4개와 원 publisher를 기존 전체 namespace loader에 연결해 기본 helper65→64를 확인했다. 원 모듈은 삭제·은폐·교체하지 않았다. 전체 Native helper union/Frame/제품 자격은 여전히 미확인이다. 자식198fresh/final198·32.938초, 부모199fresh/final199·61.937초·cleanupTrue다. 자식 closing은 EOF 전 준비 경계, 이후 STEP은 별도 fresh 확인, 부모의 전체 소스 대조는 자식 종료 후다. Job CPU6.25%/1코어/BelowNormal·RAM8%·최고 private63.77MiB·종료 active0이다. 자식 시스템CPU표본최고26.65%·가용RAM최저25.16%, 부모24.24%·25.14%다.

`native011_ready_worker.py`와 `native011_readiness_inspection.py`는 실제 상속 이벤트/원 launcher/ReadyReader/EOF를 physical-readiness-attempt002/worker001에서 확인했다. 원 launcher를 ENTRY/TASK만 다른 private namespace로 구성하고 상속 handle_list1개/같은 살아 있는 Job 소속을 이벤트 전후 대조했다. 별도 시작 토큰은 Job 할당·소속 확인 뒤에만 보내며 worker의 무거운 준비를 그전에는 차단한다. raw1byte 소비가 원 stdin 입력을 미리 가져가지 않으며 토큰은 제품 P149_GO가 아니다. 원 Gate.write에는 쓰지 않았다. 제품 허용 모드와 자식 프로세스 생성은 worker 자체에서 거부한다.

실제 이벤트 관측 뒤 EOF에서 원 worker1회/제품0·프로세스 생성 시도0·정책 복원을 확인했다. 자식198fresh/final198·기본helper60, 부모14fresh/final14·31.172초·cleanupTrue다. 원 제품 capture는 GO 전이라 호출하지 않았고 EOF pipe만 원형 capture로 수집했다. Job1코어/BelowNormal·CPU6.25%/RAM8% 상한, 최고private51.95MiB·누적CPU2.109초·종료active0/Job핸들정리True다. 시스템CPU표본최고20.90%·가용RAM최저26.88%였다. 실제001은 Windows audit가 argv를 명령문자열로 보내는 표현 차이로 자식 생성 전에 거부됐으며 같은 argv의 정확한 Windows 인코딩만 허용해 수정했다. 이 실패도 보존한다.

준비 신호까지28.157초로 시작15초 smoke는 미통과다. 원 Gate.write15초는 호출하지 않았고 제품10초 clock도 시작하지 않아 두 실행 시간 자격은 아직 없다.120초는 별도 읽기 전용 이벤트 관측 한도이며 원15초를 늘린 것이 아니다. 실제198개 입력을 첫/최종 각각 읽고 open을20/s로 제한하는 현재 독립 경로는 최소396개 열기 사이395개 간격, 즉19.75초가 필요하다. 추가 열기·바이트 속도·계산·프로세스 시작 시간은 이 하한에 포함하지 않는다. 따라서 같은 경로를 재실행하는 것으로15초 문제를 해결하지 않는다.

`native011_source_coverage.py`는 살아 있는 원 Frame 객체만 받아 Registry/소유자·정확한 경계 상태·불변 입력표·worker 전체 pin 포함·실제 경계 byte pin/통계·stream identity 횟수·현재 OS handle 정체를 대조한다. 직렬화된 summary나 닫힌 Frame, 같은 경로의 다른hash, 누락 입력은 거부한다. worker의 입력 읽기를 바꾸거나 면제하는 API는 없다. 원 Native 실행기는 Job 할당 직후 GO 대기를 시작하므로 앞에서 기다려15초를 우회하는 방식은 적용하지 않는다.

`native011_source_frame_inspection.py`의 source-frame-attempt001/owned090은 원 기초 Frame/Locks에 실제 worker198개 전체 입력을 넣어 새10계약을 통과했다. 원 두 read_boundary에서 각198파일2203510byte를 읽었고396개 stream identity가 모두 확인됐다. 잠금 중 WRITE/DELETE 권한 요청은 win32 32로 거부됐으며 내용·속성 변경은 없다. 원 클래스/메서드 유지·204handle 전부 닫힘·활성 reader/stream/probe0이다. 원 commit은 호출하지 않았고 Frame은 CLOSED다. 실제 Native 투영 Frame이나 제품 수용으로 승격하지 않는다.

자식42.812초·bootstrap5fresh/final5, 부모11fresh/final11·46.546초·cleanupTrue다. 두 원 Frame reader의 각198회 실제 읽기는 bootstrap 통계와 별도다. readonly Job1코어/BelowNormal·CPU6.25%/RAM8% 상한·최고private28.50MiB·누적CPU0.438초·종료active0이다. 자식 시스템CPU표본최고15.43%·가용RAM최저27.10%, 부모44.73%·26.72%다. 기초 진단은 원32/s ceiling 내에서 instance의 취득14/s·읽기20/s만 선택했으며 실제 Native saturation/guard를 변경하거나 자격화하지 않았다. 과거13계약·상속 이벤트·제품 시험은 재실행하지 않았다.

`native011_scope_map.py`는 마지막 실패 Native010 Frame의 명시적 입력 선언에 실제 worker198개를 대조한다. physical pin이 정확히 같을 때만 direct 선언으로 분류하며 semantic/물리 alias만 같은 것은 raw 경로의 잠금으로 인정하지 않는다. prior-scope-map-attempt001/owned092는 동일190·누락8·충돌/alias-only0이며 기준 선언은2929파일180317348byte다. 이 결과는 실패 회차의 선언 매핑이고 현재 살아 있는 Native011 Frame 커버리지가 아니다. 누락8개는 새 준비 코드5개와011 패키지3개다.

`native011_scope_delta.py`는 이 닫힌8역할을 case165의 NEW 원 Batch에만 더한다. 이미 연결·감사·사례 실행을 시작한 Batch, 다른 역할, pin 충돌, 이전 논리 역할 재분류, 재적용은 거부한다. 현재/전체/논리 계획에 같은8pin을 더하고 보존 partition은 유지한 새 원 Batch를 반환하며 원 계획은 수정하지 않는다. 새8계약093은 실제 원 Batch 생성자를 쓴 메모리 모델 검사다. Native 부모/Frame 생성이나 실제 worker 위임 자격으로 승격하지 않는다.

실제 데이터 기반 최소안은 minimal-scope-proposal-attempt001/owned094에 기록했다. 새8개161095byte를 fresh 확인했고 기준2929→최소2937 선언에서 계획상198개 pin을 모두 포함한다. 이8역할은 관측한 readonly worker용이며 별도 제품 entry 자격을 뜻하지 않는다. 기존2929파일 전체를 해시하지 않았고 사례 receipt에 없는 whole/history 목록을 만들지 않았다. Native011의 완전한 코드/자격/출력 및600초 비용/helper union은 별도로 확정해야 한다. 자식13fresh/final13·7.672초, 부모19fresh/final19·17.125초·cleanupTrue다. Job1코어/BelowNormal·CPU6.25%/RAM8%·최고private39.24MiB·누적CPU0.375초·종료active0이며 CPU표본최고34.88%/32.22%, 가용RAM최저26.22%/24.20%다. 앞선13/10계약과 제품 시험은 재실행하지 않았다.

`native011_parent_plan.py`는 원 `read_plan`으로 실제 전체/현재/보존 계획을 재구성한다. 원 Native `run_owned/input_pins`의 case112 실패001/003 직접 JSON 읽기가 초기 파일명 기반 보존421개 분류에서 빠진 것을 확인했다. 정확한 원 소스 SHA와 닫힌 두 pin/실제 읽기 표현을 확인하고, 새 미개봉 계획에서 두 입력만 현재 필수로 정정한다. 전체 pin과 원 계획은 바꾸지 않으며 나머지 보존419개를 정확히 유지한다. 실제 선언의 전체 논리→물리 일치, 임의 pin/열린 계획/다른 이력 재분류 거부를 요구한다.

parent-plan-attempt003/owned102는 전체3356·현재2937·보존419 계획과 원 Native011 engine/부모 객체, 원 Frame class/lifecycle hook 연결을 확인했다. 부모/worker 시도0·Frame instance0이며 실제 제품 경로는 실행하지 않았다. 새 metadata와 전체 경계 미연결 동안 callback은 항상 거부한다. 구성에 읽힌 자식221입력/부모222입력은 각각 fresh/최종 해시를 실제 확인했으며 전체3356파일의 현행 freshness를 뜻하지 않는다. 모델098은 실제6개 선언 검사다. 이전 상태명 EIGHT는8개 통과가 아니며 별도 필수분류4개101과 구분한다. 096/097 시험 실행·fixture 실패와099/100의 보존 중복 감지 실패는 보존하고 제품/Gate 실패나 통과로 승격하지 않는다.

102는82.015초·cleanupTrue, 시스템CPU표본최고15.43%·가용RAM최저5.18%다.1코어/BelowNormal·CPU6.25%/Job RAM8%·시스템RAM/commit95% 보호를 유지했다. 원 기본 비용은 선언 추정치이며 완전600초/실제 Native helper union은 별도다. 다음은 실제 부모의 독립 판정·metadata/공유 Frame·비용/helper 연결과 부모/child 실제 입력 경계 소유권 검증이다. 기존 두 실제 전체 바이트 경계·600초·준비15초·제품10초를 유지한다. 계획상의198/198 포함만으로 살아 있는 잠금이나 child 경계 생략을 허용하지 않는다. 실제 envelope 전체의 첫/최종 물리 확인·독립 판정·dispatch는 남는다. 검사 생략·속도 상향·15초/10초 완화는 적용하지 않았다. Native011 이후 제품 실행 범위 질문은 답변 대기이며 기존 Native010 승인을 재사용하지 않는다. 공식249 시험은158수용/91잔여, 다음case165 그대로다. 한글 고정8과 root062 실패는 이 Rust 제품 대기열과 별도로 관리한다.

## Canonical 실행 경로와 원 trace 보존 대조

`crossref-canonical-runtime.ps1`은 별도 case/고정8 함수 경로다. 원16단계와 고정8 core를 재사용하고 세션 생성2단계는 반드시 검증된 신뢰 프로그램 SessionFactory를 받는다. 원 `New-P58Owner`나 COM 생성 fallback을 호출하지 않는다. 나머지 IO/probe/정리 단계와 원 P58 CIM 정체는 그대로 유지하고 admission만 정밀 어댑터를 사용한다. 원 target-trace.json은 바꾸지 않고 고정 owner-identities.json에 원 trace의 바이트수/SHA/경로와 두 admission을 연결한다. 기존 CreateNew/fsync helper와 완료/쓰기1회 잠금을 사용하며 원 정리 오류와 보조 기록 오류를 분리한다. 실제 writer의 Native 성공은 아직 미실행이며 공개 실행 진입점이나 기본 legacy 경로를 활성화/교체하지 않았다.

`crossref_canonical_evidence.py`는 원 trace의 실제 UTF-8 바이트/해시/사례를 대조하고 save/reopen 각각의 원 CIM 정체가 별도 관측과 완전히 같은지 확인한다. 원 자료는 보존한 채 임시 메모리 사본의 명시적7정체 필드만 canonical로 투영한다. 원 producer 대조기의 산출물 pin/probe/정리·전체8 순서·고유 producer lifetime 조건을 그대로 적용한다. 전체8에서는 원 case 대조가8번뿐이며16번 중복되지 않는다. 원 파일은 재작성하지 않고, 현재 사례의 원/보조 기록만 기존 paced reader로 읽어 첫/최종 freshness를 호출자에게 유지한다. parse 상한은 파일별로 줄이고 예외 후 원 값을 복원한다. 일관성은 물리적 producer/Native 수용이 아니다.

068은 x86 실행 경로4계약과 메모리 대조8계약을 직렬 통과했다. 고정 음성 응답으로 실제 통합기 전체8 계획을 첫 prepare_slot에서 거부했고 SessionFactory0·창 타입 미로딩·한글/COM/제품 폴더/가짜 trace0이다.43fresh/final43·전체25.406초·시험6.813/0.390초·Job최고74.28/34.90MiB·CPU표본최고17.12%·가용RAM최저33.43%·cleanupTrue다. 이전 suite는 반복하지 않았다. positive Native factory/쓰기/실제 producer/전체8 제품 검증과 원 보호·현행 admission의 완전한 통합은 남는다. root062 실패나 기존 Native intent를 재시도하지 않는다.

별개인 공식249 제품 대기열은158수용/91잔여다. Native010 terminal-review001의1회 승인과 consumed intent를 재확인했다. Native011 이후 새 회차의 설계/자격 검증과 실행 범위를 사용자에게 확인 중이며, 답변 전 제품 실행이나 새 승인 기록을 만들지 않는다. 한글 접근 허용 검증은 그 질문 범위에서도 제외한다.

## CIM 호환 정보와 정밀 소유 정체의 분리

`crossref-dual-owner-identity.ps1`은 같은 query-limited/synchronize 핸들로 kernel 전후를 관측하며 그 사이에 원 `Test-P58Owner`의 fresh CIM/세션/창 검사를 그대로 호출한다. 원 함수 source/AST 확인도 유지한다. 정밀 PID·birth·세션·이미지·창 소속이 같아야 하고 query 핸들은 finally에서만 닫는다. 원 Owner.identity/CIM/trace/RCW 소유권은 변경하지 않는다. `Invoke-P09XrefCanonicalHostAdmission`은 정밀 정체/빌린 창의 proxy만 기존 HostMessage에 전달하고 원 CIM을 별도 관측에 보존한다. ACK는 승인/Native 자격이 아니다.

`crossref_dual_owner_identity.py`는 두 표현의 닫힌 schema와 정확한 kernel UTC/filetime 일치를 검사한다. CIM 시각을 kernel 시각으로 올림/절삭/허용오차 변환하지 않으며, record 후보는 여전히 원 Native backend의 독립 물리 핸들 검증이 필요하다. 자기 프로세스 관측은 한글 후보로 거부한다. [CIM_DATETIME](https://learn.microsoft.com/en-us/windows/win32/wmisdk/cim-datetime)의 microsecond 필드와 [GetProcessTimes](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getprocesstimes)의100ns FILETIME은 서로 다른 표현이며 이 구현은 관측값을 각각 보존한다.

066의 Python7계약에는 PowerShell 순수 모델2개가 포함된다. 서로 동급의9개 시험으로 합산하지 않는다. 원 Native 검사기의 모델에서는 canonical 정체는 통과하고 원 CIM/1tick 틀린 canonical 정체는 거부된다. 실제 x86 검사 자식은 같은 핸들로 kernel 전후와 자신의 CIM을 읽고, 고정 ACK를 기다리는 동안 부모가 독립 핸들로 정밀 birth/PID/세션/이미지를 확인했다. 정밀값 정확 일치·자기 관측의 Native 후보 거부·exit0·IO thread/핸들 정리True다.20fresh/final20·전체6.266초·시험2.625초·Job최고84.9MiB·CPU표본최고11.52%·가용RAM최저35.16%다. 원 source와 이전 suite는 변경/재실행하지 않았다.

새 admission 어댑터는 함수형 연결이며 기본 고정8 dispatcher는 아직 legacy admission을 쓴다. 원 child/producer v1의 CIM 정체와 새 부모 canonical 정체를 섞어 비교하거나 원 trace를 덮어쓰지 않는다. 이 증거 연결/실행 흐름 자격·한글의 실제 관측/시작 보호·독립 producer는 남았다. root062 실패/누락 경계는 보존하고 재시도하지 않는다. 전체8NOT_RUN·Native/한글/COM0·P09 OPEN을 유지한다.

## 분리 경계 실패와 생성 시각 정밀도

`crossref_root_job_anchor.py`는 고정 Python 읽기 본문만 허용한다. 외부 부모가 명시적으로 허용할 때만 정지된 자식을 만들며 기존 소유 검증 Job에 breakaway를 켜지 않는다. root-anchor062의 새5시험 자체PASS 보고 뒤 실제 자식은 분리 요청 후에도 Job에 속해 있어 `MEASURED_ALL_ANCESTOR_JOBS_REMOVED`로 전체 실패했다. root Job 가입/Native 생성으로 진행하지 않았다. 정확한 이미지/생성 정체·1코어/BelowNormal·사용자 CPU0을 확인한 고정 읽기 본문만 정상 종료시켜exit65를 받았고 핸들/빈 Job을 정리했다. 강제 종료·다른 실행기/부모로 우회·분리 재시도는 없다.

062는 최종fresh/runtime닫힘 해시 전에 중단됐다. 그 미완료 값을 성공으로 채우거나5시험 보고를 전체 자격으로 재사용하지 않는다. 063의13fresh/final13은 실패 원본/현행 소스의 새 대조이며 누락된 원 실행 경계의 소급 충족이 아니다. root/Native 자격은False다. 062 전체2.141초·CPU표본최고12.74%이고 외부 자식 peak 메모리는 별도 계측하지 않았다. 빈 root Job의0MiB를 자식 메모리0으로 보고하지 않는다.

`inspect-crossref-process-birth-precision.ps1`은 x86 검사 프로세스 자신의 PID만 CIM으로 한 번 조회한다. 063에서는 .NET Process의 생성 시각은 전후 동일했지만 CIM은6×100ns 작았다. 원 `New-P58Owner`의 CIM 시각을 정확한 kernel100ns 시각과 단순 동등 비교하면 오거부가 생길 수 있다. 이는 한글 재현이 아니며 허용오차/기존 소유 검사는 변경하지 않았다. 호환용 원 CIM 시각과 실제 열린 핸들의 정밀 생성 정체를 구분해 보존하는 연결이 다음 작업이다. 관측 전체3.781초·시험1.219초·해당 검사 Job최고62.95MiB·CPU표본최고19.13%·cleanupTrue다. 한글/COM/새 Native0·전체8NOT_RUN·P09 OPEN을 유지한다.

문서 대조064는 원 P58의 `[datetime]` 형변환을 빠뜨린 검색 문자열로 실패했다. 원 파일의6321byte/SHA는 기존값과 같았으며 파일이나 소유 검사는 변경하지 않았다. 검색 표현만 원 코드와 맞춘 별도 대조로 확인하고064 원본은 보존한다. root 분리나 생성 시각 관측을 다시 실행하는 수정이 아니다.

## 고정 한글 시작 backend와 상위 Job 경계

`crossref_native_startup.py`는 고정 한글 경로와 `-Automation`만 받고 실제32bit ProgID/CLSID/LocalServer32를 읽기 전용 대조한다. 레지스트리 문자열을 실행하지 않고 고정 argv를 재구성한다. 원 native7% Job의 제한을 생성 속성에 넣고 suspended 프로세스의 실제 PID·경로·생성100ns·현재 세션·Job 소속·1코어/BelowNormal과 사용자 CPU0을 확인한다. 첫 실행 전에 고정 EXE 바이트를 재확인하며 resume·소유자 연결은 각각 한 번이다. 연결 시에는 같은 열린 핸들·birth·세션과 실제 창 PID를 원 검사로 대조한다. 기존 P58 함수와 자원/host 코드, 읽기 검사 entry는 변경하지 않았다. CLI/COM 생성/문서/증거 쓰기/재시도/강제 종료는 없다. 아직 공개 Native 실행기나 기존 객체 전용 연결 공급자를 설치하지 않았다.

초기058의10계약은 실제 설치 등록/EXE읽기/프로세스목록과 빈 native Job의 상위 종료 정책 거부, 나머지 생성·재개·소유자 연결 모델을 포함한다. 10fresh/final10·EXE별도 실제 읽기1/1·전체8.125초·시험5.813초·Job최고35.95MiB·CPU표본최고10.84%·cleanupTrue다. 생성/재개/연결 성공은 모델이며 실제 Hwp/COM 생성은0이다.

`QueryInformationJobObject(NULL)`의 immediate Job 결과는 조상 Job 전체를 증명하지 않는다. 따라서059에 수정 전2소스를 보존하고, backend 부모 판정만 조상 Job 없는 호출자로 제한했다. 정확한 역복원 및 기존9시험 본문 동일성을 확인해 영향 없는8개는 재사용하고 부모 모델1+실제 조기 거부1만060에서 통과했다. 12fresh/final12·전체11.078초·시험8.453초·CPU표본최고21.03%·cleanupTrue다. 이는8+2 구성요소 증거이며 현행10개 동시 실행/실제 한글 시작 성공이 아니다.

059에서 원 조정 프로세스도 Job flags0x2800에 소속됨을 읽었다. 이 값에는 kill-on-close와 breakaway 허용이 있지만 조상 전체나 안전한 분리를 보장하지 않으므로 현재 Native 시작은 거부된다. 061시점에는 실제 분리 검사도 미실행이었고 이후062의 고정 읽기 분리 검사는 실패로 남았다. 상위 Job/보안 정책은 변경하지 않았다. 이 관측은 CPU 폭주의 원인 증거가 아니다. [Windows 중첩 Job 규칙](https://learn.microsoft.com/en-us/windows/win32/procthread/nested-jobs)에 따라 조상 없는 실행 경계를 확인하고 보호한 뒤 Native 연결을 자격화해야 한다. 한컴의 [등록 경로 안내](https://forum.developer.hancom.com/t/regserver-com/1689/2)는 `-Automation` 등록 형식의 근거일 뿐, 설치2020의 실제 시작/ROT 연결 성공을 대신하지 않는다.

## 첫 실행 전 Job 제한

`crossref_preassigned_readonly.py`는 `PROC_THREAD_ATTRIBUTE_JOB_LIST`로 이미 제한된 Job을 생성 속성에 넣고 `CREATE_SUSPENDED`로 고정 읽기 전용 Python 자식을 만든다. 첫 resume 전에 실제 핸들의 Job 소속·EXE·CPU affinity·priority·Job 제한과 사용자 CPU0을 확인한다. 자식도 자신의 immediate Job과 유효 제한을 재확인한다. 생성 후 `AssignProcessToJobObject`로 보완하거나 임의 명령/Native 모드로 전환하는 fallback은 없다. 살아 있는 프로세스나 tree의 핸들을 강제로 닫거나 종료하지 않는다. 원 보호 코드와 기존 실행 경로는 바꾸지 않았다.

job-at-creation056은 새5계약만 통과했다. 실제 고정 자식1개가 제한 확인 후 정상 종료했고 Job/핸들 정리True다. 7fresh/final7과 외부 고정 runtime EXE107312byte의 별도 실제 읽기1/1·전체2.391초·시험0.531초·전체 Job최고37.83MiB/자식7.54MiB·CPU표본최고8.44%·가용RAM최저24.57%다. 기존 suite를 반복하지 않았다. 이 검사는 실제 Hwp/COM 생성·ROT 연결·producer 자격이나 Native admission을 실행/승격하지 않는다. 원 `New-P58Owner`의 COM 생성 후 admission만으로 초기 생성 구간이 보호된다고 가정하지 않는다.

Windows는 Job list의 가입을 initial thread 실행 전에 수행한다([생성 속성 API](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-updateprocthreadattribute), [Microsoft 생성 시 가입 설명](https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812/)). 이는 명시적인 CreateProcess 자식에 관한 근거이며 외부 COM 서버가 호출자 Job을 상속한다는 증거가 아니다. 한컴 포럼의 [ROT 설명](https://forum.developer.hancom.com/t/rot/1701)은 실행 중인 오토메이션 객체와 창 개수를 구분하지만 2024년 120 버전 예시이므로 설치된 2020의 객체 이름·CLI 시작·연결 동작으로 추정 적용하지 않는다. 실제 한글 시작부터 제한된 소유 세션을 만드는 경로는 별도 자격이 필요하다.

## 실제 읽기 전용 runtime 연결

`inspect-crossref-runtime-connection.ps1`과 `crossref_runtime_inspection.py`는 실제 1% host, 고정8 통합기, 원 통신 및 부모 관측 wrapper를 연결한다. 새 host role은 닫힌 읽기 검사만 받으며 Native 공급자가 없다. 첫 단계는 반드시 거부한다. worker의 첫 응답 reader가 canonical 음성 ACK만 허용하므로 검사측이 잘못된 양성 ACK를 주어도 폴더·세션 생성 전에 중단한다. 실패 후 종료 ACK는 전달하지만 native 정리 자격을 뜻하지 않는다.

변경 전 host/시험053과 정확한 역복원으로 원 CPU·메모리·종료 처리 및 기존 시험 동일성을 확인했다. closed-runtime054는 새5계약만 실행했다. 두 실제 x86 STA 연결은 정상 거부와 양성 응답 차단을 확인하며, 각각 부모 기록1/failed·owner admission0·artifact0·실제8경로NOT_RUN이다. 30fresh/final30·전체23.547초·시험18.781초·전체 Job최고104.3MiB·CPU표본최고19.51%·가용RAM최저22.38%·cleanupTrue다. 이전 host/batch/기록 suite는 재실행하지 않았다. 실제 Native runtime 공급자·현행 admission·물리적 producer 자격 및 COM 생성 시작부터의 제한은 아직 미자격이다.

## 고정8 통합 실행과 producer 기록 일관성

`crossref-fixed-batch.ps1`은 전체8 packet을 확인한 뒤 기존 host-bound case를 고정 순서로 호출하는 함수형 통합기다. 한 사례가 반환되지 않거나 정리가 불확실하면 후속 사례를 실행하지 않고 부분 결과를 보존한다. subset·순서 변경·자동 재시도·기존 기록 덮어쓰기는 받지 않는다. 콜백 반환은 native/정리/제품 수용으로 승격하지 않으며 case 요약은 닫힌 필드만 복사한다. 실제 native 진입점은 활성화하지 않았다.

`crossref_producer_records.py`의 부모 관측 wrapper는 자원 scope와 파일 reader를 감싸 단계별 관측을 기록한다. 대조기는 자식 trace·부모 관측·파일 pin의 사례/소유자/생성시각/단계SHA와 probe/SDK/IO/정리 기록을 비교한다. 전체 판정은8개 순서와 producer lifetime 중복을 검사한다. 기록 일치는 물리적 producer·인과적 삽입·native 안전성 증명이 아니므로 `native_provenance_qualified=false`를 유지한다. 직렬화 전 snapshot의 `trace_write_returned=false`만으로 재저장을 시도하거나 실행 성공을 주장하지 않는다.

fixed-batch-producer051은 batch6계약과 기록9계약을 별도 소유 Job에서 직렬 실행했다. batch 모델은8순서·모든 실패 위치·오류 분리·승격/원장 덮어쓰기 거부를 확인하고, 실제 통합기는 외부 입력이 아닌 고정 StringReader 거부로 첫 사례에서 멈췄다. 기록의 양성 사례는 메모리 모델이며 제품 디렉터리나 가짜 native trace는 쓰지 않았다. 실제 전체8 경로는NOT_RUN이다. 29fresh/final29·전체18.547초·batch11.532초/기록2.015초·Job최고74.81/28.63MiB·CPU표본최고25.24%·cleanupTrue다. 이전 host/자원 보호 시험은 반복하지 않았다.

읽기 전용 runtime 연결은054에서 확인했다. 실제 Native runtime 공급자, 독립 물리적 producer 자격, COM 생성/상속 보호와 현행 native admission은 남아 있다. 통합기의 존재나 모델 결과를 전체8 native 시험 완료로 보고하지 않는다.

## 한글 생성 전 읽기 준비 검사

`inspect-crossref-pre-com-prefix.ps1`은 `-InspectOnly`만 허용한다. 고정 설치 EXE/DLL/TLB/보안 모듈4개를1MiB/s로 읽고 해시·버전을 확인하며 읽는 동안 write/delete 공유를 거부한다. Registry32의 COM 서버와 보안 모듈 등록은 읽기만 한다. 해시가 고정된 원 harness에서 창 식별 클래스 선언만 추출해 컴파일/로딩하고 메서드 signature/DLL import를 확인한다. 원 main, 실제 창 함수, COM 생성, 문서·저장·출력 디렉터리는 실행하지 않는다. 이 프로세스의 타입 로딩을 미래 제품 워커에서 재사용했다고 주장하지 않는다.

host에는 `wrapper_denial`과 `pre_com_prefix` 두 닫힌 읽기 role만 있으며 native/임의 경로·명령 role은 거부한다. snapshot048의 변경 전2소스와 정확한 역복원으로 기존 CPU/메모리/종료 처리·기본 거부 경로·원 시험이 동일함을 확인했다. 기존 host/통신 검사를 반복하지 않고 prefix049의 새3계약만 실행했다. 실제x86 STA·설치4파일/등록 일치·타입 로딩·한글 전후0/0·8출력 미생성·cleanupTrue다. 23fresh/final23·시험7.437초·전체11.5초·host Job최고71.22MiB·전체 검사 Job최고99.08MiB·CPU표본최고24.8%다.

이는 제한된 host 안의 생성 전 준비 작업 자격이며 실제 한글 생성이나 외부 COM 프로세스의 상속/제한·native 실행 승인·제품 수용은 아니다. producer 기록 대조와 전체8 통합기의 구현 범위는 앞 절을 따르며, 독립 물리적 producer/실제 native 보호·현행 묶음 admission 통합은 남아 있다.

## host 작업자 예산과 중첩 CPU 상한

`crossref_owned_host_process.py`는 원 대기 bootstrap과 두 고정 읽기 검사만 실행하는 host 작업자 Job이다. 최초 제한/소속/affinity/BelowNormal 확인 후에만 읽기 검사 시작 신호를 보낸다. 재시작·신호 재시도·강제 종료·kill-on-close·한글 대기 타이머가 없고 프로세스나 트리가 살아 있으면 핸들을 보존하고 닫기를 거부한다. 가입 전 메모리도 보수적으로 합산한다. 작업자1%는318.5625MiB이며 조정 프로세스는 포함하지 않는다. 조정 프로세스에는 원 별도 RAM/commit/CPU 보호가 필요하며 native7%+worker1%를 PC 전체8% 제한으로 보고하지 않는다.

중첩 Job의 CPU quota는 부모 예산에 대한 비율이다. 따라서 같은 값을 중첩 적용해 이중 축소하지 않도록 실제 immediate parent의 rate/flags/affinity/priority/breakaway를 읽는다. 부모 hard cap이 원1코어 상한 이하이고 동일1코어/BelowNormal·breakaway 금지인 경우에만 child quota를 부모의100%로 정한다. 기록은 설정값100%와 PC 상한≤6.25%를 구분한다. 부모 설정이 바뀌면 중단하고 미확인/약한 부모는 기존 child quota를 유지한다. 외부 COM 프로세스에는 이 상속 증명을 전용하지 않는다. 근거: [CPU rate control](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information), [현재 immediate Job 조회](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-queryinformationjobobject).

partition043의8계약은 실제 빈 Job, 신호 전 EOF(exit125/본체 미실행), 제한된 고정 wrapper 검사를 포함한다(20fresh/final20·시험35.047초·Job최고102.06MiB·cleanupTrue). CPU 보완 전2소스를044에 보존하고 정확한 변경 역복원과 원8본문 동일성을 확인했다. 영향 없는5개는 반복하지 않고 실제3역할과 새CPU2계약만 nested-host-cpu045에서 통과했다(22fresh/final22·시험14.937초·전체18.703초·Job최고101.88MiB·CPU표본최고29.69%·cleanupTrue). 이는5+5 구성요소 검증이며 현행10개 동시 실행이나 동일 범위 속도 벤치가 아니다. 기존10+1 통신 검사는 반복하지 않았다.

host1% 적용은 고정 읽기 검사에서만 자격화했다. 실제 한글/접근허용/native 실행, COM 생성 전후/상속 Job·외부 소유자 제한·현행 묶음 admission/원 native 보호 통합은 미자격이다. 공개 native 거부와158/249/P09 OPEN은 유지한다.

## 사례 실행부와 보호 host 통신

`crossref_native_host_channel.py`와 `crossref-host-channel.ps1`은 고정8사례×(원16 checkpoint+소유자 연결2+종료1)의 통신 순서를 제한한다. 입력은 4KiB 이내의 닫힌 JSON 필드만 받으며 중복 키·잘못된 순서·강제 형 변환·임의 명령을 거부한다. 실패는 고정하여 후속 작업을 막되 해당 사례의 종료 요청1회는 정리를 수행할 수 있다. ACK와 callback 반환은 승인·native 작업·소유 정리 완료 증거가 아니다. `NativeResourceScope`는 원 resource backend를 호출하고 준비 전용 CPU guard를 거부한다. 실제 case wrapper는 finally에서 종료를 통신한다.

`native-host-channel036.v1.json`의 새10계약은 전체152메시지 모델, 실제x86 parser와 읽기 pipe child2개를 포함한다. 실제 pipe에서는 첫 checkpoint 거부 뒤 core/ports가 폴더/세션 전에 중단하고 종료1회가 전달된다. 검사 전용 callback은 양성 응답에도 무조건 중단하므로 native 실행 경로가 아니다. 16fresh/final16·시험8.031초·전체11.203초·Job최고86.77MiB·cleanupTrue다.

실제 `Invoke-P09XrefHostBoundCase`는 고정 거부 StringReader로 별도 검사한다. 원038은 제품 중단/정리 확인 이후 검사기의 메시지 계수에서 실패했다.039는 수정 전3소스와 진단,040은 실제x86의 원 분리3/교정2 재현이다. 제품 코드는 변경하지 않고 분리 한 줄만 수정했다. 기존10본문·기본 child helper의 역복원 일치 및 제품 모듈 동일성을 확인하여10개를 반복하지 않았다. corrected041의 wrapper1계약은20fresh/final20·시험7.25초·전체10.828초·Job최고91.45MiB·CPU표본최고59.68%·cleanupTrue다. 이는10+1 구성요소 검증이며 현행11개 동시 실행이나 실제 native guard 통합 증거가 아니다.

host1%의 실제 native 연결, COM 생성/상속 Job 안전성, 원 native 보호와 현행 묶음 admission의 실제 통합, 독립 producer 판정 및 전체8 dispatcher는 아직 남아 있다. 공개 native 거부·158/249·P09 OPEN을 유지한다. 읽기 검사기의 제한 시간/정리 정책을 한글 접근허용 대기에 적용하지 않는다.

## 한글 소유 프로세스 자원 제한

`tools/p09/crossref_native_host_limits.py`는 실제 소유 한글 프로세스를 검증한 뒤 제한하는 내부 backend다. PID만으로 연결하지 않고 열린 프로세스 핸들의 EXE 경로·100ns 생성 시각·세션과 실제 창 PID, 새 고정 EXE 파일 pin을 확인한다. Job 연결 후 membership·CPU·affinity·priority를 재확인한다. 원 host checkpoint를 호출하며 별도 sampler나 준비 전용 CPU 정책으로 교체하지 않는다. native7%와 worker1%는 작업자 Job 예산이며 조정 프로세스는 별도 보호 대상이다. worker1%의 읽기 검사 적용과 native 통합 미자격 범위는 앞 절을 따른다.

가입 전 할당 메모리를 Windows Job이 소급 검사하지 않으므로 가입 직전 private bytes를 확인하고 이후 원 반올림 전 Job peak와 보수적으로 합산한다. 할당이 일부 중복 계산될 수 있으나 이전 메모리를 할인하지 않는다. 합산값에는 배분 상한의7/8 보호 중단 기준을 적용한다. native Job은 접근허용 대기 중 종료하지 않도록 kill-on-close·시간 제한·강제 종료가 없으며, 살아 있는 프로세스가 있으면 닫기를 거부하고 핸들을 보존한다. 원 P58 소유 정리 후에 닫아야 한다. 읽기 검증용 원 Job은 변경하지 않는다.

`native-host-limits031.v1.json`의 새10계약은 실제 빈 Job2개의 제한 readback/정리와 비한글 Python 프로세스 연결 거부를 포함한다. 시험0.578초·Job최고28.88MiB·전체2.437초다. snapshot032에 수정 전 소스를 보존한 후 preexisting-memory033에서 정확한 역복원을 확인하고 영향 없는9개를 재사용했다. 메모리 관련 기존1개와 새2개만 실행해 통과했다(시험0.688초·전체3.094초·Job최고28.66MiB·cleanupTrue). 이는9+3 구성요소 검증이며 현행12개 동시 실행이나 한글 실제 연결 검증이 아니다.

실제 한글의 제한 적용, COM 생성 전후 부하와 상속 Job, host1% 예산·원 native 보호·현행 전체 admission과의 연결은 미자격이다. 진입점의 native 거부와 수용 원장158/249는 유지한다. Windows 동작 근거: [AssignProcessToJobObject](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject), [Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

## 실제 사례 함수 연결과 정리 단일 실행

`crossref-native-case-ports.ps1`은 고정 16단계를 기존 소유 세션·SDK·저장 및 재열기·단계 probe 함수에 연결한다. 생성자는 고정 입력과 출력 경로, 살아 있는 읽기 lease 및 내부 host callbacks를 보관하지만 폴더나 한글 세션을 만들지 않는다. 원 harness 전체 SHA를 확인한 뒤 `Assert-P58File`과 `Write-P58Trace`만 추출하고 원 main은 실행하지 않는다. 원 소유 세션 및 IO 함수도 바꾸지 않는다.

단계 직전 host 검사에서 실패해도 사례가 failed 상태로 고정된다. 정리 함수는 소유 문서 해제 실패 시에도 원 소유자 정리를 한 번 시도하고, 소유자 변수가 비어 있어도 trace의 미정리 세션을 검사한다. 정리와 trace 저장 실패는 따로 남기며 정리 함수 전체의 두 번째 호출을 거부해 불명확한 저장과 이전 실패 기록 초기화를 막는다. 저장 직후의 producer 관측은 독립 판정 전까지 `producer_binding_qualified=false`다.

`native-ports-contracts027.v1.json`은 실제 x86 STA 자식의 소스 연결·생성자 무효과·host 거부·순서·실패 정리 경로 8계약이다. `native-ports-snapshot028.v1.json`의 수정 전 소스와 정확한 역복원 대조 후, 기존 8개를 재실행하지 않고 `native-completion029.v1.json`에서 정리 잠금 2계약만 추가했다. 027은 12fresh/final12·Job 최고79.14MiB·시스템 CPU 표본 최고39.26%, 029는 14fresh/final14·Job 최고70.46MiB·CPU 표본 최고30.88%이며 둘 다 cleanupTrue다. 8+2 구성요소 검증을 현행 10개 동시 실행으로 보고하지 않는다.

공개 준비 entry의 native 거부는 변경하지 않았다. 원 native 자원 보호·현행 묶음 admission을 수행할 host 연결, 독립 producer 및 정리 증거 판정, 전체 8사례 dispatcher는 아직 미자격이다. 실제 COM·한글·접근허용·새 native 사례 실행은 없으며 수용 원장 158/249는 그대로다.

## 단계별 관측 실행과 사례 콜백 흐름

`crossref-case-flow.ps1`은 고정16단계 callback 순서와 실패/정리를 다룬다.8사례 모델과16개 실패 위치를 대조하되 callback_entered/returned를 native 작업 증거로 취급하지 않는다. 정리 callback은 finally에서 한 번 호출하고 주 실패와 정리 실패를 따로 보존한다. 정리 callback 반환도 실제 session 정리 확인은 아니며, native 수용·완료·인과적 보존 flags는 False다. 실제 함수 연결은 앞 절의 내부 ports가 담당하며 승인된 native entry로 활성화하지 않았다.

`crossref-stage-probe.ps1`은 고정 binary5,112,832bytes를 한 번 해시하고 읽기 핸들로 write/delete 공유를 막는다. 묶음 동안 핸들이 살아 있으면 단계별 재해시를 피한다. template bytes의 고정SHA를 확인하고, 원 준비 child runner에서 bounded async capture·deadline·소유child 정리 suffix를 정확히 재사용한다. caller가 넘긴 임의 실행 코드 문자열은 사용하지 않는다. 고정case/stage/SHA만 받으며60초는 읽기 child에만 적용한다.

022는5통과 후 lease 생성의 CryptoException으로 실패했다.023은 해시 재사용 예외 위치와3개 수정 전 source를 보존했다. 별도 해시 객체로 고쳤고024의 검색 형식 오류는 child0의 검증 전 실패로 남겼다.025는 원5시험본문·case core·나머지소스의 일치를 확인해5개를 재사용하고 나머지4개만 실행했다. 실제case1 누락사본 프로브는exit2와 child 정리를 확인했으며 사본은 여전히 없었다. binary 쓰기용 open 차단·닫힌lease의 child 전 거부·변조template 거부도 검증했다.

`p09-361-crossref-case-flow-probe-corrected025.v1.json`은30fresh/final30·27.824756초·시험8.550939초·Job최고71.59MiB·시스템CPU표본최고52.34%·cleanupTrue다.5+4 component는 현행9개 동시실행이나 실제COM 사례 실행이 아니다. 다음은16단계의 실제 native 실행부/producer/session cleanup 결합과 원 native 자원 보호/현행 묶음 admission이다. 기존 준비entry의 native 거부와 P58/Native010 경계를 유지한다.

## 저장과 새 세션 재열기 어댑터

`crossref-save-reopen.ps1`은 opened 사전사본 저장, 삽입 후 saved 저장, 새 소유세션에서 saved 열기, reopened 저장을 구현한 함수 모듈이다. 원 P58 Open/Save 파일 지문과 실제 함수 AST를 대조한다. saved/reopened는 원 함수와 whitelist를 유지하고 opened만 별도 고정 HWPX SaveAs를 사용한다.8사례×3경로만 허용하며 출력 전 존재·조상 reparse 지점을 검사하고, 전후 active-document와 단계SHA를 확인한다. 존재검사 뒤 SaveAs는 OS create-new 원자성 증거가 아니다.

새 세션은 생성 UTC·로그인 session·EXE 지문·window/process 결합을 확인한다. PID가 같아도 생성시각이 엄격히 뒤이면 다른 생성 identity로 구분하며, PID만 다르고 생성시각이 같거나 뒤가 아니면 거부한다. fresh-open이 document를 상위에 넘기기 전에 실패하면 그 document만 해제한다. session 전체의 검증된 정리는 아직 상위 case 제어기에서 연결해야 한다.

최초6계약은17fresh/final17·14.288704초·Job최고69.48MiB·cleanupTrue로 통과했다. 후속 기록 검토에서는 원 helper 자체가 native 메서드 전에 거부될 수 있음을 반영했다. helper 진입 때 open/save_invoked는null, 효과는unknown이며, 정상 반환을 확인한 경우에만True로 바뀐다. 수정 전 source019와6통과018을 보존하고 정확한6시험본문·나머지구현 역복원을 확인한 뒤 새2계약만 실행했다.020은6filtered·2통과·19fresh/final19·9.724859초·Job최고65.68MiB·cleanupTrue다.

근거는 `p09-361-crossref-save-reopen-contracts018.v1.json`, `p09-361-crossref-save-reopen-source-snapshot019.v1.json`, `p09-361-crossref-save-reopen-records020.v1.json`이다.6+2는 component 증거이며 현행8개 동시실행이나 실제 Native open/save가 아니다. 다음은 단계별 제품probe 호출, case/batch 제어기와 producer·정리·원 native 보호/현행자격을 묶는 작업이다. 실제 실행권한과 준비entry의 거부 상태는 바뀌지 않았다.

## SDK 삽입 어댑터와 저장 단계별 문서 결합

`crossref-sdk-insertion.ps1`은 고정 private packet에서만 명령을 읽는 내부 함수다. 설치2020 선언에서 개별 Action 객체의1인자 호출과 HAction 허브의2인자 호출을 구분했다. HAction.GetDefault/Execute는 BSTR·Dispatch를 받아 BOOL을 반환하고 HParameterSet.HActionCrossRef/HSet은 Dispatch, Command는 BSTR이다. 두 읽기전용 조사 결과는 `p09-361-crossref-action-call-declarations014.v1.json`과 `p09-361-crossref-action-hub-declarations015.v1.json`에 보존했다. 선언은 실제 동작 자격이 아니다.

어댑터는 opened probe·소유문서 확인 후 기본값 가져오기, 고정 Command 설정/재읽기, 실행 직전 소유문서 재확인, Execute와 사후 결합을 수행하도록 구현했다. caller-owned record에 Execute 호출 전 intent와 호출 결과/실패 phase를 남긴다. 실제 호출이 시작된 뒤의 효과는 unknown으로 유지하며 재시도·rollback·인과적 삽입/보존을 선언하지 않는다. 임의 명령이나 승인boolean을 받지 않으며 아직 실제 native dispatcher에 연결하지 않았다.

`crossref-owned-artifact.ps1`은 고정8사례×4지점만 허용한다. opened_clean/saved_clean/reopened_clean은 실제 LONG0을 요구하고 opened_after_insert는 관찰된 LONG만 유지한다. 삽입 직후 값0/비0을 성공 판정으로 쓰지 않는다. 파일SHA를 확인한 읽기 핸들과 IUnknown identity를 전후 표본 동안 유지하되 결과는 실행권한이 아니다. 기존 원본 전용 bridge는 변경하지 않았다.

새 source/model/거부8계약은14fresh/final14·10.499380초·시험2.219670초·Job최고71.71MiB·시스템CPU표본최고22.49%·cleanupTrue로 통과했다. `p09-361-crossref-sdk-artifact-contracts016.v1.json`은32개 selector 조합·단계별 타입/변경상태·잘못된 probe·비COM 실행차단 및 호출구조를 검증한다.32개 native 시험이나 실제 SDK/저장/재열기 검증은 아니다. 기존13계약·제품시험은 반복하지 않았다.

다음은 실제 save/fresh-reopen·새 어댑터·단계probe의 case/batch 연결, producer 결합 및 원 native 자원 보호/현행전체 자격이다. 준비 entry의 native 거부는 유지하며, 이 소스 구현만으로 새 실행권한이나 Native010 재실행 권한이 생기지 않는다.

## 고정 제품 관측 실행 파일과 준비 연결

`crates/product-cli/examples/p09_crossref_discovery_probe.rs`는 두 제품 관측 API의 worker용 읽기 진입점이다. `baseline` 또는 고정 사례1~8·단계 opened/saved/reopened·예상 SHA만 받으며 임의 경로/명령은 받지 않는다. 고정 private packet의8개 후보와 receipt를 현재 준비 API 결과에 대조한다. 최종 출력은 최대16KiB이며 대상·CROSSREF 관측과 지문만 반환한다. native 실행, producer 귀속, 실제 대상 해석·보존을 증명하지 않는다. 사례별 경로는 미래 별도 발견 campaign용으로 고정돼 있으며 실제 native 폴더는 생성하지 않았다.

새 Rust4계약은29fresh/final29·8.377116초로 통과했다. 별도 actual binary baseline은 책갈피8후보/CROSSREF0을0.987596초·Job최고20.30MiB로 확인했다. build와 감사 전체는17.990212초·31fresh/final31이며 기존4계약·제품7시험은 반복하지 않았다. source 읽기2MiB/s·open당50ms·Windows reparse 지점 거부·읽기 중 write/delete 공유 거부를 적용하되 경로 교체 경쟁 sandbox를 주장하지 않는다.

`inspect-crossref-worker-composition.ps1`은 같은 소유 Job에서 원 전체8 사전검사1회와 제품 baseline probe1회를 연결하고 소유 binding 함수의 import 및 원 소유 검사 함수 identity를 확인한다. 새 PS4계약, 실제 native 요청의 조기 거부(exit2/준비child0), 실제 준비 경로의 child2/정리를 확인했다.45fresh/final45·전체51.698768초·준비본체23.891316초·Job최고141.73MiB·시스템CPU표본최고75.52%·cleanupTrue다. 원 CPU/RAM 보호는 유지했다. 비동기 stdout32KiB/stderr4KiB 상한과60초 deadline은 고정 비native 두 child에 한정하며 미래 한글 접근허용 대기에 적용하지 않는다.

근거는 `p09-361-crossref-worker-probe-tests010.v1.json`, `p09-361-crossref-worker-probe-baseline011.v1.json`, `p09-361-crossref-worker-composition012.v1.json`이다. 다음은 실제 SDK 삽입/저장/새세션 재열기 dispatcher·단계별 active-document/producer 결합·원 native 자원 보호의 연결과 자격화다. 준비 연결은 완료했지만 native dispatcher는 미구현·미승인이고 native_ready는 False다. 원본 경로에 대한 관측 결과를 저장 후 단계의 실행권한으로 재사용하지 않으며, 저장 단계별 경로/SHA와 실제 소유 문서를 다시 결합해야 한다. 기존 P58·249 대기열과 분리한다.

## 소유 활성 문서와 저장 사본의 대상 관찰

`crossref-owned-active-source.ps1`은 원 소유세션 검사 함수의 source identity를 대조하고 실제COM IUnknown·Application·활성문서·문서수1·경로·고정 원본 SHA·변경 상태를 전후 관찰한다. COM 생성이나 작업 실행은 없고 결과도 실행권한이 아니다. 소유자가 빌려준 RCW를 FinalRelease하지 않으며 직접 얻은 AddRef만 해제한다. 목록 보관 실패 시에도 해당 AddRef를 반납하는 분기를 추가했다. 실제COM·OOM 경로는 아직 실행하지 않았다.

설치2020의 `Modified`는 BOOL이 아닌 VT_I4/LONG이다. 최초 선언 기대 실패002와 함수 AST 범위 비교 실패004는 보존했다. 수정 전 source를 diagnostic005에 정확히 보관했으며7선통과 후 수정된 나머지5개만 실행했다. 이후 식별자 보관 분기를 보강할 때는 영향받지 않은10개 시험 본문과 나머지 구현의 일치를 확인하고 식별자 관련3개만 실행했다. `owned-identity-hardening008`의10재사용+3통과는13개 component 증거이며 현행13개 동시 실행이나 실제 한글 자격이 아니다.

제품의 `observe_bookmark_targets_in_output`은 준비 원본에서 기대 책갈피 이름을 도출하고 output package/structure/name index를8개 후보 전체에 한 번 만든다. 고유 이름 관찰·미관찰·모호성을 구분하고 다른 snapshot의 source-local ID를 같은 ID로 취급하지 않는다. 모든 XML part의 기존 target coverage 및 work/text/output 한도를 유지하며 출력은 원문 대신 지문만 포함한다. 시험7개는26fresh/final26·56.012538초·Job최고1,353.55MiB·cleanupTrue로 통과했다. 실제 준비사본과 과거 한글 저장 원본을 읽었지만 새 한글 실행이나 인과적 보존 증거가 아니다.

`crossref-product-target-readback-tests007.v1.json`은 기존 준비 본문에서 새 getter와 module export만 역제거해 원래 소스 일치를 확인한다. 이전 준비·249대기열 시험은 재실행하지 않았다. 다음은 bridge/관찰기의 실제 worker 연결, 변경된 구성의 현재 사전검사와 별도 native 권한, 실제 저장·재열기·보존 관찰이다. P58 동결 큐와 Native010의 소비된 권한은 유지한다.

## 참조 발견용 입력과 여덟 후보 준비

2026-10-17 고정된 과거 한글 저장 HWPX에서 private 발견용 입력을 생성했다. 원본은 보존하며 section 끝에 책갈피 문단 하나만 추가하고 다른 expanded parts를 그대로 유지한다. 이는 fixture 준비이며 일반 제품 책갈피 생성이나 실제 한글 열기 자격이 아니다. `crates/product-cli/examples/p09_crossref_discovery_prepare.rs`는 인자를 받지 않고 고정 입력·manifest만 읽으며 실제 원본 target에서 표시4종×링크2종의8개 후보를 만든다. 출력은 exclusive private `prepared-sdk-batch.v1.json`이며 같은 경로를 덮어쓰거나 재실행하지 않는다.

`p09-361-crossref-discovery-prepared-batch002.v1.json`은 실제42,762bytes packet 생성·원본 결합·입력 CROSSREF0/not_observed·8개 명령 지문을 확인한다. 전체16.243408초, packet 실행0.356991초, Job 최고632.55MiB, 시스템 CPU 표본 최고32.10%, cleanup True다. Rust 준비기3계약을 통과했으며 이전 source/제품 시험은 반복하지 않았다. Python fixture suite는 선언5개와 프로세스 종료0을 보존하되 stderr의 개별 시험 summary 미해석으로 실행 개수를 감사한 결과로 쓰지 않는다.

이어 `implementation/p09/tools/inspect-crossref-discovery-preflight.ps1`의 실제32bit/STA 검사에서 전체8개를 한 번에 검사했다. packet/입력/manifest·원 소유session 소스·설치2020 EXE/DLL/TLB·보안모듈·등록을 확인하고 같은process에서10fresh/final10 지문을 대조했다.8개별 설치 검사나 기존249대기열 시험은 반복하지 않았다. 새 순수/소스 계약8개도 통과했으며 한글process는 전후0이다. 전체19.867716초·Job최고88.93MiB·시스템CPU표본최고17.39%·cleanupTrue이며 `p09-361-crossref-discovery-preflight003.v1.json`에 보존했다. 이 검사는 실행 스위치나 COM activation을 제공하지 않으며 원 소유session 코드를 hash만 확인했다.

packet 상태는 `prepared_eight_source_bound_candidates_not_native_ready`다. 읽기전용 사전검사는 통과했지만 소유 worker의 runtime과 실제 active-document/target 결합, 미래 실행 시점의 전체 묶음 preflight, 별도 native 실행 권한, 실제 저장·재열기·보존 readback이 남는다. 이8개를 기존 동결 P58 full34에 추가하거나 과거 수용 대기열의 통과로 세지 않는다. Native010의 소비된 권한과 재실행 금지를 유지한다.

## 현재 남은 작업과 재사용 경계

2026-10-17 잔여 항목 대조에서는 P09-17의 옛 실패만 보고 후속 P09-18~20까지 미완료로 묶지 않는다. P09-18의 기존 캡션 대상 typed 번호 삽입과 P09-19 사각형·표·수식, P09-20 대체 원본 그림의 제한된 실제 저장·재열기 증거가 있다. 네 사례는 각각19→1→1이며 모두 non-green이다. 새 캡션 생성이나 객체 분류 변경은 fixture 준비와 제품 API를 구분해야 한다.

| 구분 | 남은 작업 | 재사용 또는 실행 경계 |
|---|---|---|
| 제품 시험 대기열 | 일반 case165–249의85개와 corpus47–52의6개, 합계91개 | 기존158개와 Native010 중단 원본은 보존. 후속 case165 제품 시도는 새 식별자와 별도 승인 필요 |
| 서명 원본과 전체 통합 | signed16·전체249 결과의 실행 세대/입력/결과 통합 확인 | 91개 완료만으로 전체 P09 종료를 주장하지 않음 |
| 실제 참조 검증 경로 | 실제 HWPX에서 읽은 참조 정보와 제품 CLI 연결·검증 | 원본 책갈피·각주·미주·표 target/실제 source-assessment CLI·source-bound SDK 후보·CROSSREF 문자열 관찰 구현. 다른 target/native mapping·완전한 의미/state/flow·최종 검증 결과는 남음. incomplete/exit3·source_observation_only를 검증 PASS로 승격하지 않음 |
| 캡션과 번호의 일반 제품 동작 | 일반 번호/갱신, 새 캡션 생성, 객체 분류 변경의 제품 자격 | 기존 캡션 삽입과 네 제한 사례를 처음부터 다시 만들거나 일반 API PASS로 승격하지 않음 |
| 원 그림 입력 실패 | 기존 그림 seed의 Open 실패 원인·지원 경계 확인 | 원 실패2건과 unnumbered control 실패 보존. 대체 원본 성공으로 원 실패를 지우지 않음 |
| 실제 화면 품질 | 사각형 미표시·수식 캡션 좁은 배치의 baseline/numbered 비교 및 보정 | 저장/재열기 PDF 일치와 화면 품질은 별개. 단순 일치 비교를 render Gate로 승격하지 않음 |
| 경로 통합 | 실제 automation fallback과 direct/automation differential | 구현/대상 증거에 맞춰 별도 자격 확인 |
| 최종 종료 | migration·negative·원본 보존·증거 통합·A12/A13/P09 판정·원장/인계 동기화 | P09 종료 전 P10 새 구현 금지 |

원 근거는 `P09-20_CANONICAL_PICTURE_CAPTION_TARGET_REPORT.md`와 네 성공/두 실패 public receipt다. `audit_caption_target_evidence_reuse.py`는 새 COM/제품/fixture/PDF 생성 없이 원 판정기로 여섯 기록과 원 source identity를 재현했다. 검사 종료코드0과 PASS 상태는 관측됐지만 stdout이 잘려 이번 감사의 전체 입력 수·완전한 source pin 표·전체 자원 통계는 보존하지 못했다. 이를 복구하려고 같은 감사를 반복하지 않았다. 이 한계를 포함한 기록은 `evidence/p09-361-caption-historical-reuse-audit001.v1.json`이다. 이 재사용 확인은 기존 제한된 증거의 역할을 바로잡는 것이며 공식158/249·green0·P09 OPEN을 바꾸지 않는다.

## 실제 참조 제어의 읽기전용 사전 목록

`reference_source_inventory.py`는 실제 ZIP 바이트에서 관측되는 paragraph namespace의 fieldBegin/fieldEnd·bookmark·autoNum·caption·note·일부 객체 제어를 집계한다. 알 수 없는 필드 type은 개수만 보고하고 입력 값·참조 이름·외부 URL은 출력하지 않는다. 모든 .xml/.hpf 파트를 관측하되 spine/part 역할이나 target/edge 의미를 완전하게 해석했다고 주장하지 않는다. 기존 typed product API·Rust 소스·Native 실행기와 큐 수용 결과는 변경하지 않았다.

ZIP 중앙 목록의 사전256항목/256KiB 한도는 ZipFile의 항목 할당 전에 적용한다. archive32MiB·확장 전체16MiB·파트2MiB·전체 XML요소100,000·깊이128을 제한하고64KiB 단위마다 기존 자원 검사를 호출한다. ZIP 항목은 불투명 binary도 포함해 한 번 확장하며 CRC를 확인한다. XML은 스트리밍 한 번만 순회하고 처리한 노드를 부모에서 제거한다. 원본 이름이 ZIP 파서에서 정규화/절단되면 거부하며, 경로 이탈·중복/대소문자 별칭·심볼릭링크·암호화·미지원 압축·DTD/비UTF8도 거부한다. 외부 entity나 외부 데이터 원본을 읽거나 파일을 추출하지 않는다.

핵심18계약은 오류/실패/skip0·2fresh/final2·cleanupTrue다. 첫 시험에서 Windows ZIP writer가 역슬래시를 먼저 정규화해 한 합성 경로 사례가 실제 악성 경로를 만들지 못했다. 같은 길이의 raw local/central 이름을 주입하도록 fixture를 보정하고, 실제 파서의 orig_filename 불일치 거부까지 보강했다. 첫 실패 결과와 source pins는 보존한다.

`python -B tools/p09/reference_source_inventory.py --inspect-caption-controls`는 기존 두 사각형/수식 대조 문서와 두 번호 입력만 검사했다. 종료코드0·PASS_FOUR_PINNED_SOURCE_INVENTORIES_NOT_PRODUCT_REFERENCE_VALIDATION·7fresh/final7·2.006560초·cleanupTrue를 관측했다. 도구 반환 한도로 stdout 중간이 잘렸으므로 전체 파트별 집계는 미보존이다. 완전하게 남은 후반부에는 source pins7개와 자원4표본·종료 통계가 있다. 자체 CPU최고0%·private최고15.753906MiB·시스템최고28.91%는 이 네 표본의 관측이며 프리즈 해결/CPU 무부하 보장이 아니다. 불완전 통계 회수를 위해 네 문서 검사를 반복하지 않았다.

이후 출력에 모든 part와 자원 표본을 나열하지 않고 archive identity·관측 합계·자원 요약을 반환하도록 바꿨다. 새 출력3계약만 실행해 PASS·2fresh/final2·cleanupTrue를 확인했다. 새 순수 summary 함수 추가와 출력 인자 한 곳을 제외하면 이전 검사 모듈의 전체 AST가 정확히 같음을 확인해18계약을 재사용했다. 변경 뒤 실제 네 문서 CLI를 다시 실행하지 않았으며 이전 실제 관측은 출력 변경 전 source pins에 묶여 있다. stdout 요약 자체도 무손실 상세 기록으로 취급하지 않는다.

기록은 `evidence/p09-361-reference-source-inventory-qualification001.v1.json`이다. 이 사전 도구는 완전한 참조 상태 reader나 product reference validation·수정/갱신·render/Gate가 아니다. 다음은 지원 가능한 원본 target/edge 의미와 coverage·미지원 표현 거부를 구현하고 typed 제품 API로 연결하는 것이다. 공식158/249·잔여91·P09 OPEN·P10미시작·목표ACTIVE를 유지한다.

## 원본 책갈피와 참조 검증 대상의 결합

`crates/hwpx-package/src/document_import/reference_targets.rs`는 실제 immutable 구조 import를 빌려 domain `ValidationTarget`을 만든다. 원 책갈피 ID와 전체 관측 digest를 유지하고 원본/package provenance·구조 graph·대상 inventory를 receipt에 묶는다. 이름 index는 정확히 디코딩된 원문만 비교하며 미존재와 중복을 구분한다. source anchor를 임의의 flow 좌표로 바꾸지 않고 optional anchor를 None으로 둔다. active는 그 marker의 존재만 뜻한다. 모든 imported XML part의 paragraph bookmark와 대조해 구조 밖 marker는 Coverage로 거부한다. native field 개수와 complete_reference_state_qualified=false를 남긴다.

처음 컴파일은 기존 소유 Job private7% 보호에서 최고2,254.63MiB로 중단됐고 트리가 모두 정리됐다. 한도를 올리지 않고 컴파일에 한해 incremental/debug 정보 생성을 끄고 codegen16으로 분리했다. CPU1코어·BelowNormal·Cargo1·test thread1·assertion/overflow·RAM/commit95%·기존 Job 한도는 그대로다. metadata 검사는 전체121.114962초·Job최고1,508.5MiB로 통과했다. 실제 시험 빌드·실행은113.414311초·Job최고1,855.68MiB로 종료했고8통과·1합성 fixture 실패였다. 이는 서로 다른 실행 관측이며 PC프리즈 해결이나 일반적인 성능 개선율로 환산하지 않는다.

실패 fixture는 ZIP 기본 압축으로 mimetype을 압축해 기존 원 패키지 검사에서 먼저 거부됐다. 생성문 한 곳만 Stored로 보정한 뒤 실패한 한 시험만 통과했고8개는 filtered out이었다. test004의 첫 보조 감사는 줄바꿈 escape 비교 오류로 실패 상태를 유지했다. 별도 review005에서 정확한 이전 테스트 preimage와 생성문 한 곳/줄바꿈 외 변경 없음·원 선언 의존 pin 동일성을 확인해8기존통과+1보정통과를 합성했다.14fresh/final14·cleanupTrue이며 판정을 위해 시험을 다시 실행하지 않았다. 원 실패 기록은 모두 보존한다.

상세 결과는 `P09-10_REFERENCE_VALIDATION_PRODUCT_API_PROGRESS.md`와 evidence의 `p09-361-reference-target-compile-pressure001.v1.json`부터 `p09-361-reference-target-composite-review005.v1.json`까지에 있다. Rust source가 바뀌었으므로 기존 세대 binary를 현행 source runtime 자격으로 재사용하지 않는다. 완전한 source auxiliary state/flow·다른 target·reference edge·CLI·target/통합 판정은 남는다. 공식158/249·잔여91·P09/A12/A13 OPEN·P10미시작·목표ACTIVE다.

## 실제 원본을 읽는 제품 CLI 진입점

`hwpx-agent-cli reference-source DOCUMENT_ID SHA256 ABSOLUTE_LOCAL_FILE`을 추가했다. 실제 바이트·문서 ID·예상 해시로 source/structure/책갈피 target을 결합하지만 완전한 reference edge/state/flow가 없으므로 status=incomplete·validation_report=null·exit3을 반환한다. 정상 참조0개나 실제 ref.reference_validate 성공으로 대신하지 않는다. 입력 실패는 원문 경로/이름/파라미터를 출력하지 않는 닫힌 오류와 exit2다. 기존 typed API의 caller-supplied-state 자격과 기존 생성 명령은 별개로 유지한다.

32MiB·직접 로컬 절대 경로·일반 파일을 요구하며 조상 경로를 루트부터 확인한다. Windows junction/reparse와 symlink·비로컬/장치/상위 경로를 거부한다. 이는 현재 경로의 사전검사이며 공격자의 경로 교체 경쟁까지 막는 sandbox/서비스 권한 증거가 아니다. 기존 자원 보호·단일CPU/Cargo/test·assertion/overflow를 유지했다.

기본9계약은 실제 CLI 하위 프로세스를 포함해 전부 통과했다. metadata101.590181초·Job최고1,518.61MiB, 실제 시험 build/run82.430596초·libtest0.55초·Job최고1,866.35MiB·15fresh/final15·cleanupTrue다. 조상 검사 보완 뒤 영향받은 CLI4통과/fixture생성1실패를 기록했다. 단독 진단으로 제품 검사가 아니라 fixture 생성 실패임을 확인하고 PowerShell Junction 생성으로 그1개만 보정·통과시켰다. 새 source는 private 입력경로 검사 외 역복원되고 기존9시험과 나머지4통과 함수/공유 도구는 정확히 보존됐음을 확인해6재사용+4CLI+1junction=분리11계약으로 묶었다. review008은21fresh/final21·cleanupTrue·시험재실행0이다. 실패 기록을 PASS로 덮어쓰지 않았다.

최종 실행기는 과거 한글 저장 원본15,097bytes/SHA256feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480을 읽었다.11parts/8XML/736elements/native field1/bookmark0이며 exit3·검증report null을 유지했다. 실제 소유 command 단계 약0.273초·전체 binary/source 전후감사13.640359초·Job최고17.34MiB·17fresh/final17·cleanupTrue다. 한글을 새로 실행하거나 field 의미/저장/재열기/render를 검증한 것은 아니다. 상세 기록은 P09-10 보충 문서와 evidence의 p09-361-reference-source-product-check001부터 component-review008까지다.

완전한 참조 edge 의미·source state/flow·native parameter 자격·최종 검증 결과와 P09 Gate는 남는다. 공식158/249·잔여91·P09/A12/A13 OPEN·P10미시작·목표ACTIVE다.

## 원본 각주 미주의 참조 대상 연결

참조 대상 profile을 `bookmarks-notes-v2`로 확장했다. 원 구조 import가 확인한 source-local note ID와 marker/body anchor를 사용하며 같은 instId나 번호를 가진 서로 다른 note를 합치지 않는다. note는 책갈피 이름 index에 넣지 않는다. 모든 imported XML part의 bookmark/footNote/endNote와 대조해 구조가 놓친 대상은 전체 가져오기를 거부한다. receipt의 `note_targets`는 인식한 원본 대상 수이며 번호 재계산·native navigability·완전한 참조 상태가 아니다.

대상13계약과 제품/CLI12계약을 순서대로 실행해 모두 통과했다. 과거 생성/저장/재열기 note9패키지와 원 실패 판정을 보존하며 실제 CLI의 혼합 bookmark/note 결과·원문 비노출·원본 무변경·incomplete/exit3을 확인했다. 32fresh/final32·전체56.769728초·Job최고1,344.39MiB·cleanupTrue다. Debug scope 문구의 후속 보정은 원 source/test의 정확한 역복원과 나머지 입력 동일성을 확인한 뒤 해당1계약만 통과시켰고12개는 반복하지 않았다. 이전 제품 binary의 실행은 최초 전체 시험의 pin에 속하며 후속 binary 실행으로 바꾸지 않는다.

범위가 고정된 별도 원본 조사는 P09 fixture/private 폴더의 HWPX248개, 고유 바이트125개를 해석했고 CROSSREF 후보0·거부0·제외0·250fresh/final250이었다. 이 집합에서 실제 native parameter 의미를 확보하지 못했으므로 임의 매핑을 추가하지 않는다. 전체 저장소/사용자 문서의 부재 증거는 아니다. 근거는 `evidence/p09-361-native-crossref-corpus-census001.v1.json`, `evidence/p09-361-reference-note-target-product-tests001.v1.json`, `evidence/p09-361-reference-note-target-debug-correction002.v1.json`이다. 원 자원 보호와 Native 재실행 금지를 유지한다.

## 실제 표를 참조 대상으로 연결

현재 profile은 `bookmarks-notes-tables-v3`다. 원 구조 import의 표 격자·병합·node ID·source anchor를 사용한다. section과 note의 borrowed flow에서 중첩 cell body를 한 번씩 순회하며, table state는 원본 subtree fingerprint와 실제 ID/행/열을 결합한다. 표 본문을 중첩 깊이마다 다시 직렬화하지 않는다. 모든 XML part의 native tbl과 대조하고 미지원 구조 안의 표·중복 anchor·종류별 한도 초과를 닫힌 오류로 거부한다. 수식/그림을 단순 local-name만으로 실행 가능한 typed 대상에 승격하지 않는다.

대상17/제품13계약이 통과했다. 합성 중첩·note 내 표·같은 native ID·본문 변화·정확한 per-kind 한도·foreign namespace·구조 밖 표와 실제CLI를 확인했고, 기존 생성/저장 표16개·note9개도 읽었다. 원장 검사의 첫 실패는 추가 속성이 있는 원장 전체 행과 3필드 파일 지문을 비교한 보조 preflight 오류였다. 제품 시험 전 종료된 실패001을 남기고 path/bytes/SHA 비교만 정확히 보정한002에서50fresh/final50·47.188584초·Job최고1,346.10MiB·cleanupTrue로 통과했다.

현행 실행기는 원래 한글 저장 표14,384bytes를 실제 읽었다.11parts/825elements/native field1/table1이며 원본은 그대로고 결과는 incomplete·null validation report·exit3이다. 실제명령0.572579초·전체14.513174초·Job최고17.00MiB·20fresh/final20·cleanupTrue다. 새 한글/COM/Native 제품시험이나 native 수식/field update 검증이 아니다. 근거는 `evidence/p09-361-reference-table-target-product-tests001.v1.json`, `reference-table-target-product-tests002`, `reference-table-captured-cli003`이며 뒤의 두 이름에도 `p09-361-` prefix와 `.v1.json` suffix가 붙는다. P09/A12/A13 OPEN·공식158/249·잔여91·목표ACTIVE를 유지한다.

## 교차참조 SDK 명령과 원본 좌표 경계

공식 고정 매뉴얼의 ActionTable16/23·ParameterSetTable1/175/176쪽에서 SDK의 전용 Action/Command 문법을 확인했다. 텍스트 검색으로2문서231페이지를 확인한 뒤 관련5페이지만 화면으로 검토했다. 설치2020의 HActionCrossRef.Command BSTR getter/setter도 실제 읽었으나 실제 Action은 호출하지 않았다. source SHA가 고정된 원 조사기를3개 닫힌 변환과 출력 필터로 재사용했고 원 binary/hash·읽기전용 registry·Hwp process-set 전후 조건은 유지했다.

내부 cross_reference_sdk 후보 생성기는7종 현재문서 대상의52허용조합을 포함하는6계약을 통과했다.18fresh/final18·68.048637초·Job최고1,343.52MiB·cleanupTrue이며 기존249개/참조 대상17개/제품13개를 반복하지 않았다. codegen/debug/incremental과 기존 CPU1코어·BelowNormal·RAM/commit/Job 보호를 유지했다. 실제 source target resolver·현재문서 권위·노트 index 원점·SDK 동작·HWPX field serialization은 별도 자격이 필요하다. 외부 문서 경로와 raw action 제품API는 열지 않는다.

원본 구조의 control_inline_position에는 합성 BookmarkAnchor가 포함되지만 기존 bookmark lowerer의 LinkPoint는 non-bookmark run child 경계를 센다. nested table/note 문단도 기존 top-level 평면 좌표에 그대로 넣을 수 없다. 이 차이를 임의 ordinal/flow SHA로 덮지 않으며 기존 source-assessment는 incomplete를 유지한다. P09-06 정책과 reference validation 진행 문서에 정확한 source/설치 선언/미확인 경계를 분리했다. 원 수용158/249·잔여91·P09/A12/A13 OPEN·목표ACTIVE와 Native 재실행 금지를 보존한다.

## 실제 원본과 SDK 후보의 묶음 결합

`SourceCrossReferenceContext`는 실제 immutable 원본에서 대상/정확한 이름 색인을 한 번 만들고 logical target ID를 SDK 후보와 결합한다. 원본에 존재하며 이름이 유일한 책갈피만 이 단계에서 결합한다. 누락·다른 문서·변경된 source ID와 중복 원본 이름은 거부하고, table id나 note instId를 다른 native 식별자/순서로 추정하지 않는다. nested table/note 안의 책갈피도 원본 ID를 쓰며 평면 좌표를 만들지 않는다. native 이름 해석/정규화와 active document는 별도 미확인이다.

제품 `prepare_source_crossref_discovery`는 하나의 원본/구조/대상 import로8개 표시·링크 조합을 준비했다. 한 후보가 실패하면 부분 결과를 반환하지 않고 빈/중복 선택도 거부한다. 각 후보의 receipt와 비공개 command 길이를 합친 작업/출력 예산을 누적 확인한다. 원본 freshness는 묶음 전체에 대해 원래 full source/graph verifier를 한 번 호출한다. JSON은 native_execution_not_run과 결합 지문만 반환하며 이름·명령은 노출하지 않는다. 새 public CLI/MCP나 SDK 실행·문서 수정은 없다.

원본6/제품준비4계약은22fresh/final22·전체108.913698초·Job최고1,349.89MiB·cleanupTrue로 통과했다. 단계별41.684282/62.384451초이며 실제 libtest는 각각0.03초다. 기존 SDK6/대상17/제품CLI13/전체249·Native를 다시 실행하지 않았다. 근거는 `evidence/p09-361-source-bound-crossref-tests001.v1.json`이다. Native 동작/명령 readback·다른 source target bindings·외부 문서·완전한 참조 state/flow와 Gate는 계속 OPEN이다.

## CROSSREF 저장 원본의 문자열 관찰

준비 객체의 `observe_crossref_output`은 실제 output package/form/field graph를 한 번 가져와 전체 후보에 사용한다. direct plain hp:stringParam을 한 번 디코딩하며 key 이름은 해석하지 않는다. 여러 leaf/field 중 첫 일치를 고르지 않고, 다른 후보가 한 field를 공유하는 경우도 모호성으로 남긴다. 주석/복합/비문자 payload는 opaque이며 미관찰은 그 밖의 값의 부재 증거가 아니다. 모든 XML part의 CROSSREF 누락과 잘못된 pair/SHA·중복 후보·일/출력 한도를 거부한다.

관찰8/제품3계약은28fresh/final28·100.164491초·Job최고1,354.52MiB·cleanupTrue로 통과했다. 결과는 source_observation_only로 key 의미/native attestation/삽입·보존/완전한 참조 검증을 모두 미확인으로 둔다. 기존에 있는 matching field도 새 삽입이나 보존의 증거가 아니다. SourceIndex/ByteSHA가 native current-window/history를 인증하지 않는다.

후속 실제 파일 부정1시험은 과거 고정 한글 저장 HYPERLINK15,097bytes를 읽고 CROSSREF0/not_observed를 반환했다. 원래3시험 prefix와 나머지 입력이 같음을 확인해8+3을 반복하지 않았으며1pass/3filtered·30fresh/final30·전체30.013898초·build/test23.267780초·libtest0.50초·Job최고633.11MiB다. 현재8+3+1 component 조합이며 새 세대의12개 동시 실행이 아니다. 근거는 `evidence/p09-361-crossref-source-observation-tests001.v1.json`과 `evidence/p09-361-crossref-source-observation-captured002.v1.json`이다. 기존Native34/249 대기열·SDK/한글/접근허용은 실행하지 않았다.

## 작업별 실행 방식

저장소 루트 `D:\개발\hwpx-agent`에서 아래처럼 구분한다.

| 작업 | 실행 | 판정 범위 |
| --- | --- | --- |
| 재사용 도구만 수정 | `python -B tools/p09/verification_reuse.py --self-test-only` | 변경한 도구의 회귀 시험만 실행. 과거 185개 입력을 읽지 않음 |
| 기존 고정162 준비 결과 적용 가능성 확인 | `python -B tools/p09/verification_reuse.py` | 기존 증거와 의존 파일을 전후 확인. 이전 구성·복원 시험은 실행하지 않음 |
| 도구 시험과 실제 의존 확인을 처음 함께 수행 | `python -B tools/p09/verification_reuse.py --self-test` | 위 두 범위를 한 번에 확인 |
| 기존 의존 파일 변경 또는 확인 실패 | 자동 실행 없음 | 영향받는 준비 검증을 먼저 수정·재검증. 제품 실행으로 넘어가지 않음 |
| 분리 정책 코드 변경 | `python -B tools/p09/verification_reuse.py --batch-policy-tests` | 정책·원 입력 합성·Frame·독립 판정·새 identity·입력 입구의 87개 계약 검사. 과거 코퍼스 재해시 없음 |
| 실제 선언 분리안 검산 | `python -B tools/p09/verification_reuse.py --batch-policy-plan` | 고정 기록에서 기존 3,305개를 복원하고 정책·시험·실행 소스 5개를 명시적으로 추가. 구성기·decoder 재실행 없음 |
| 작은 실제 읽기 경로 확인 | `python -B tools/p09/verification_reuse.py --batch-policy-io-check` | 실제 파일 4개의 묶음 시작·종료와 현재 입력 선택. 전체 런타임 범위 검증은 아님 |
| 실제 준비 그래프 연결 확인 | `python -B tools/p09/verification_reuse.py --batch-policy-connect` | 실제162 graph·private 입력 합성·이전 원장 선언 연결. 기존 단위 시험/부정 검사 재실행 없음, engine/GO/Native 없음 |
| 실제 engine과 과거 판정기 구성 | `python -B tools/p09/verification_reuse.py --batch-engine-connect` | 원 engine/worker 함수와 과거 전체 validator를 구성. worker/parent 실행·Frame·자식 프로세스·GO 없음 |
| 실제 NO-GO 준비 자료 발행 | `python -B tools/p09/verification_reuse.py --batch-package --package-generation 2` | 같은 데이터는 정확 pin 확인 후 재사용. 새 manifest·wire·bootstrap의 실제 파일 입구 복원과 별도 불변 보고서 발행. 제품·프로세스 실행 없음 |
| 큰 검증 전 선언과 비용 확인 | `python -B tools/p09/batch_scope_admission.py` | 고정 선언과 명시된 새 입력만 복원. 전체 코퍼스·원16/87시험·구성기·decoder·프로세스 실행 없이 보수적 원 비용을 먼저 계산 |
| 실제 묶음 경계와 부모 입력 함수 검사 | `python -B tools/p09/batch_scope_admission.py --metadata` | 전체 시작/종료 실제 읽기·원 부모 입력 함수와 현재2,898개 선택. 실제 engine/Native/Frame/worker/GO 없음 |

같은 작업의 설명·상태 조회마다 이 확인 명령을 반복하지 않는다. 의존 파일을 변경했거나 기존 준비 결과를 실제로 적용할 경계에서 사용한다. 재사용 판정은 확인 시점의 관측이며 이후 파일이 영구히 변하지 않는다는 보장은 아니다.

새 명령은 준비 엔진을 import하거나 실행하지 않으며 자식 프로세스 생성을 차단한다. 기본 명령은 자체 회귀 시험도 반복하지 않는다. 새로운 제품 시험, 접근 허용 창, Cargo, 한글, OS 설정 변경, 원장 갱신은 수행하지 않는다.

## 실제 확인 결과

2026-10-16 첫 실제 의존 확인은 기존 185개 모두 일치, 도구·시험·결과 파일을 포함한 188개 전후 해시 일치로 종료했다. 구성·복원 시험 재실행 0개, 새 증거 파일 0개, 자식 프로세스 생성 0회, cleanup=True였다. 약 27.432초, 자체 CPU 최고 0.3877%, 전용 메모리 최고 16.44MiB, 시스템 CPU 최고 45.35%, 가용 RAM 최저 19.59%를 관측했다. 이 실행에는 초기 도구 회귀 시험 14개가 포함됐다.

그 후 종료 경로 검사를 보강한 도구만 검사했다. 변경 후 회귀 시험 17개가 약 1.510초에 통과했으며 실제 과거 의존 집합은 재검사하지 않았다. 종료 해시 실패, 마지막 자원 검사 실패, 마지막 해시 개수 미완료 시 재사용 판정을 반환하지 않는 사례를 포함한다. 자체 CPU 최고 0.3901%, 전용 메모리 최고 15.86MiB, cleanup=True, 자식 프로세스 생성 0회였다. 이 도구 수정은 과거 185개 의존 파일을 수정하지 않았다. 두 실행의 결과는 세션 출력에 있으며 별도 자격 영수증으로 발행하지 않았다.

## 아직 바꾸지 않은 제품 검증 경계

기존 준비 결과를 유지한다는 판정은 현재 실행 환경, 현재 전체 비용, helper 한도, metadata/Frame 공유 decoder 시간, 실제 worker, Native 잠금, 제품 본문 또는 Gate의 새 자격이 아니다. 이전 소요 시간·CPU 표본을 현재 관측처럼 재사용하지 않는다. 특히 직전 3,305개 범위의 719.843905/720초 필요조건 모델은 현재 실행의 성공이나 새 파일 반영 후 비용을 입증하지 않는다.

Native009는 제품 본문 PASS 뒤 마지막 source 확인에서 720초 제한으로 종료됐으며 미수용 상태다. Native008/009 재실행 금지는 그대로다. 이 도구는 새 제품 실행 허가를 만들지 않는다. P09/A12/A13은 OPEN이고 P10은 시작하지 않았다.

## 다음 구조 변경

마지막 실제 Native009의 입력 3,268개, 물리 크기 199,890,681bytes를 경로 기준으로 분류하면 다음과 같다. 실제 root의 SHA-256은 `3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753`이다.

| 분류 | 파일 수 | 물리 크기 bytes |
| --- | ---: | ---: |
| 제품 소스와 manifest | 792 | 16,465,363 |
| 검증 코드와 시험 | 1,118 | 9,733,167 |
| 증거와 보관 자료 | 1,291 | 141,745,606 |
| 빌드 산출물 | 14 | 30,921,832 |
| fixtures | 31 | 419,982 |
| 기타 | 22 | 604,731 |

이 분류는 제외 목록이 아니다. 실제 worker import 목록은 63개지만, 그 밖의 private loader 입력·부모 admission 의존성도 있어 나머지 검증 코드를 불필요하다고 단정할 수 없다.

다음 변경 대상은 이전 전체 선언과 `q.snapshots`를 반복 합치는 구조다. 실제 실행·판정에 쓰이는 입력, 준비 결과의 의존 입력, 원본 보존용 이력을 사용 근거별로 나누고 변경 시 무효화 범위를 명시해야 한다. 기존 Native 범위나 수용 조건을 경로 접두사만으로 줄이지 않는다. 기존 원본·실패·수용 기록은 보존하고, 현재 제품 입력의 fresh 검사·자원 보호·독립 판정은 계속 요구한다. 단순히 과거 기록을 더 압축하는 작업을 다음 기본 작업으로 삼지 않는다.

### 누적을 강제하는 실제 읽기

`tools/p09/current_queue_successor_runtime.py`의 `current_input_scope`는 직전 candidate의 `bootstrap_metadata.input_pins` 전체를 순회하며 `q.pin`으로 다시 읽는다. `current_queue_successor_binding.py`의 `inherited_scope`도 이전 전체 semantic 범위에 원장과 준비 입력을 합친다. 따라서 기존 분리 도구에 불필요해 보이는 경로만 넘기는 방식으로는 실제 읽기 의존성이 제거되지 않는다.

읽기 전용 감사에서 Native009 **자체**의 bootstrap 선언 3,272개를 당시 75개 대응표로 정규화하면 그 실행의 Native 입력 3,268개와 일치했다. 이 전체를 현재 의존성으로 간주해 분리 도구에 넣으면 후보가 0개라는 조건부 결과는 맞다. 그러나 이 목록을 case165의 `current_input_scope`가 직접 다시 읽는 이전 목록으로 설명한 것은 잘못이었다.

실제 case165의 step이 가리키는 이전 candidate는 case164/run006이며 bootstrap은 450개, 이전 source freeze는 2,963개다. 전체 범위 누적은 `current_queue_successor_binding.inherited_scope`의 이전 semantic 범위 합성과 `native009_parent_scope.inherit_declaration`·추가 union 경로까지 함께 봐야 한다. Native009 자체 목록으로 얻은 0개/가정상422개 수치를 실제 case165 직접 읽기 범위나 최종 제외 목록으로 사용하지 않는다. 실제 연결에서 450개 이전 선언은 현재 descriptor seed와 alias를 포함한 591개 physical membership으로 정규화돼 보존 범위 안에 있음을 확인했다.

이 감사는 고정된 실패 원본과 관련 코드 4개 파일을 전후 읽어 4fresh/final4, 약 6.609초, 시스템 CPU 최고 25.53%, 자체 CPU 최고 1.3513%, cleanup=True로 종료했다. 제품 실행·입력 범위 변경·새 결과 JSON 발행은 없었다.

### 승인된 분리 정책 구현

`tools/p09/batch_verification.py`는 전체 보존 범위와 사례별 현재 범위를 함께 유지한다. 묶음 시작·종료에는 서로 다른 fresh reader로 전체 파일의 바이트와 해시를 확인한다. 이 두 관측이 묶음의 전후 경계이며 각 한 번의 관측을 기존 독립 자격 검사기의 두 번 읽기 완료로 표시하지 않는다. 사례마다 현재 범위에 대한 원래의 실제 Frame·잠금·전후 두 번 전체 읽기·Job 종료·동일성·cleanup 조건을 요구한다. 묶음 종료 감사가 끝나기 전에는 수용이나 원장 진전을 허용하지 않는다. 묶음 수명은 같은 프로세스·스레드에 한정되고 최대 8개 사례까지만 허용한다.

`install_scope`는 고정 SHA의 원 `current_input_scope` 함수 본문에서 세 곳을 연결한다. 직전 bootstrap 전부 재읽기는 묶음 보존 확인으로 바꾸고, 이전 선언에 현재의 승인된 전체 선언을 보강한 뒤, 그중 현재 입력만 선택한다. 선언 보강은 파일 읽기나 freshness 증거가 아니며 파생 입력의 알 수 없는 pin·충돌을 버리지 않고 거부한다. 이전 candidate가 이후에 생긴 정책 코드·증거를 미리 포함하도록 요구하지 않는다. 그 밖의 원 AST를 정확히 역복원해 일치하는지 확인하고 원 함수·모듈은 수정하지 않는다. 기존에 다른 함수 변경이 있으면 이를 덮어쓰지 않고 거부한다. metadata reader는 보존 전용·미선언 입력을 원 IO 전에 거부하며, 압축 증거의 논리 pin과 실제 carrier pin도 구분한다. 예전 선언 주입이 현재 범위에 이력을 다시 넣는 경우에도 중단한다.

현재 보존 후보는 이전 사례의 runtime·acceptance·per-case data 기록만 보수적으로 고른다. 제품 소스·실행 파일·fixtures·검증 코드를 경로만 보고 제외하지 않는다. 실제로 선언된 준비 의존성과 직전 원장·candidate·worker 입력 232개를 우선 보호한다. 이 수는 전체 동적 의존성이 완전히 검증됐다는 뜻이 아니다.

### 실제 선언 검산과 검증 결과

기존 Native009 선언과 고정된 준비 결과·162개 대응표에서 3,280→3,297→3,305개 단계를 재현했다. 최종 논리 377,217,331bytes, 물리 151,728,027bytes, 디렉터리 376개가 원 비용 모델의 입력 수·바이트·디렉터리 수와 정확히 일치했다. 옛 75개 physical alias와 현재 162개 표현의 원본 pin을 유지했고, 충돌한 pin을 새 값으로 덮어쓰지 않았다.

| 선언 | 전체 파일 | 매 사례 파일 | 묶음 보존 이력 |
| --- | ---: | ---: | ---: |
| 기존 고정 범위 분리안 | 3,305 | 2,884 | 421 |
| 앞선 정책 코드·시험 4개 추가 | 3,309 | 2,888 | 421 |
| worker 실행 소스를 포함한 코드·시험 5개 추가 | 3,310 | 2,889 | 421 |
| 현재 코드 5개와 커밋된 과거 설정 1개 명시 추가 | 3,311 | 2,890 | 421 |
| 발행 모듈을 포함한 준비 코드 6개와 설정 1개 | 3,312 | 2,891 | 421 |
| 활성 준비 자료 4개 추가 시 필요한 다음 실행 범위 | 3,316 | 2,895 | 421 |

421개 이력은 18,541,176bytes다. 기존 파일은 하나도 삭제하거나 전체 보존 범위에서 빠뜨리지 않았다. 계획 생성은 `q.snapshots` 전체를 다시 상속하지 않는다. 정책·시험 소스 4개와 `batch_worker_entry.py`·`batch_preparation_package.py`, 아래에서 입증한 과거 설정 1개를 이름으로 명시했다. 활성 manifest·wire·bootstrap·보고서 4개도 다음 실행 범위에 명시적으로 추가해야 하며, 표 마지막 행은 아직 실제 전체 바이트 감사를 통과한 범위가 아니다.

최종 확인은 다음 세 범위를 따로 수행했다. 모든 실행에서 제품·GO·원장 증가·자식 프로세스·새 결과 JSON 발행은 0, cleanup=True였다. 결과는 세션 출력과 이 문서에 남기며 실제 Native 자격 영수증으로 승격하지 않는다.

| 확인 | 결과 | 관측 |
| --- | --- | --- |
| 정책 및 실제 원 함수 본문의 격리 시험 | 87개 통과, 코드 9fresh/final9 | 약 2.345초, 자체 CPU 최고 3.3576%, 전용 24.86MiB |
| 실제 고정 선언 검산 | 10fresh/final10, 부정 검사 4개 통과 | 약 7.602초, 자체 CPU 최고 4.4565%, 전용 39.91MiB |
| 실제 작은 IO 경로 | 4개 파일의 시작·종료 8회 전체 읽기, metadata 1개 최종 해시, 검사 코드 4fresh/final4 | 약 2.006초, 전용 16.88MiB |

부정 검사는 선언 개수 변경, 크기 모델 변경, descriptor 중복, 기존 소스 pin 충돌을 각각 거부했다. CPU/RAM 보호 중단을 예상된 부정 검사 통과로 처리하지 않는다. 초기 시험 실패는 합성 reader의 `read_exact`·`require` 인터페이스 누락으로 수정했고, 원 제품 판정이나 원본 자료는 바꾸지 않았다. 실패 출력은 세션에 보존돼 있다.

### 실제 준비 그래프 연결

실제 고정162 transport의 원 구성·decoder를 필요한 그래프 생성에만 사용하고, 이전 자격 검증 runner나 단위 시험·부정 검사를 다시 실행하지 않았다. 발행 직전 준비 Binding은 논리/physical 현재 입력 2,891개를 정확히 투영하며 이력 재주입이 없었다. 발행된 4개 입력을 포함한 다음 범위는 별도로 연결해야 한다. 원 입력 합성 함수는 private runtime에 연결됐고 전체 AST 역복원이 일치했다. 전체 감사 전 metadata 호출은 실제 IO 전에 거부됐다.

실제 case164 candidate와 원장에서 `inherited_scope`로 파생한 선언도 준비 코드 범위 3,312개 논리 선언과 일치하도록 검산했다. 이 검산은 선언 연결일 뿐 묶음의 실제 시작·종료 감사나 parent metadata admission을 수행한 것은 아니다. 기준 그래프의 context9는 읽기 전용 재구성 자료이며 Native009 재실행 허가가 아니다.

구성 중 namespace 소스 open은 원 reader의 20회/s·종류별1/2MiB/s 제한 안에서 매번 fresh 읽기를 수행한다. 원 loader의 hash·AST 검사는 유지하고 source/hash/AST cache나 전역 Path 변경을 사용하지 않는다. default loader의 pin은 작은 준비 영수증에 없어 전체 고정 선언에서 정확히 찾아 검증했다. 입력 입구의 원 constructor·decoder 복원을 포함한 연결은 namespace 소스42개/104회 읽기·load20회, 전체57fresh/final57·22,455,927bytes·약20.974초·자체 CPU 최고4.0192%·시스템 CPU 최고21.94%·전용67.41MiB·가용 RAM 최저21.45%·cleanup=True로 종료했다. 제품·GO·제품 engine·Job·실제 Frame 인스턴스·worker process·새 결과 JSON 발행·수용 증가는 0이었다. 실제 Native 자격이나 새 engine 구성 완료는 아니다.

### 정확한 parent Frame 클래스와 수명 연결

`Batch.connect_parent`는 기존 parent 생성기를 호출해 만든 정확한 클래스만 연결한다. 기본 Frame 원 메서드 본문과 parent·projected·original 상속 체인을 확인하고 클래스·함수 코드·기본 인자·closure의 변경과 인스턴스 메서드 덮어쓰기를 거부한다. 원 `native_started`의 전체 본문을 private dependency로 복제해 정확타입 비교 대상만 해당 parent 클래스로 지정한다. 기본 Frame 모듈이나 원 gate는 수정하지 않으며, 연결하지 않은 임의 파생 클래스는 계속 거부한다.

연결된 private 클래스의 획득·commit·close 훅은 원 메서드를 호출한다. 시작 감사 전에는 원 획득 전에 중단하고, 획득 후 원 gate로 사례를 시작한다. 원 두 전체읽기·Job 정리·commit이 끝나야 사례 종료를 기록하며 원 반환 행은 재작성하지 않는다. 중도 close는 원 해제와 접근 보호 복구를 유지하면서 batch를 `BROKEN`으로 만든다. 종료 시 클래스·함수·소유자 무결성도 다시 확인한다.

실제162 그래프의 parent 생성기에 실행 시 즉시 실패하는 참조 본문을 제공해 클래스와 수명 훅 설치까지 확인했다. parent 실행 0회·Frame 인스턴스 0개이므로 실제 runner의 수명 통과는 아직 미검증이다. 별도 합성 handle 시험은 자동 사례 시작·종료, 시작 감사 전 획득 거부, 중도 종료, 불완전 commit의 원 실패 보존을 확인했다. 현재 parent 연결은 첫 사례 한 개만 대상으로 한다. 여러 실제 사례의 parent·동적 입력·다음 사례 전달 연결은 아직 구현·검증해야 하며, 기존 최대8개 계약 시험으로 이를 통과 처리하지 않는다.

### 독립 판정과 묶음 종료 경계

`Batch.connect_full_oracle`는 기존 full projector의 원 generator·checker 본문을 유지하고 private metadata `extend` 의존성에 승인된 분리 정책을 연결한다. 기대 범위는 원 독립 판정기가 계산한다. 전체 기대 범위를 Binding으로 정규화한 physical 결과가 선언된 전체 보존 범위와 정확히 같아야 하며, 실제 시작·종료 전체 읽기와 해당 사례의 원 Frame commit이 끝나야 현재 범위를 선택한다. 원 Binding의 현재 범위 증거·비용·공유 decoder·제품 종료 조건은 그대로 실행한다. 후보 행·Frame·카운터는 다시 쓰지 않고, 판정 실패는 원 예외를 보존하며 종료된 batch를 `BROKEN`으로 고정한다.

실제 준비 그래프의 full oracle에 어댑터를 설치하고 원 `current_queue_successor_oracle.connect`를 fresh source loader로 읽어 호출 경로에 연결했다. 이 connector에는 전체 상속 범위를 그대로 넘기며 현재 범위를 후보 관측에서 만들지 않는다. 실제 원 full projector에서 종료 감사 전 호출이 generator 실행·파일 IO 전에 거부됨을 확인했다. 기존 source scope를 선언 검사만으로 감사 완료로 표시하지 않는다.

64개 계약 검사에는 원 full projector 본문을 typed 합성 Binding과 연결한 시험이 포함된다. 전체 기대 범위 누락·추가, 잘못된 현재 행, 종료 감사 전·빈 묶음·Frame 변경, 후보 객체 변경, 독립 범위 검사를 생략한 generator와 원 종료 조건 실패를 거부했다. 이는 실제 physical envelope·과거 validator 전체 family·제품 후보에 대한 통합 통과가 아니다.

### 실제 실행 연결 전 남은 경계

발행 전 3,312개 계획은 아직 `NEW` 상태이며 새 입력 4개를 포함한 범위를 연결해야 한다. 전체 시작·종료 감사, 실제 parent/worker 실행, 현재 동적 의존성의 완전성, 현재 비용과 metadata/Frame 공유 decoder 한도는 검증되지 않았다. 실제 파일 4개 입구 복원과 mock handle Frame 계약을 전체 제품 경로의 통과로 사용하지 않는다. 실제 제품 실행의 속도 향상도 아직 측정하지 않았다.

실제 제품 시험 1회 준비는 아직 미완료다. 정확한 Frame·수명·독립 판정 어댑터와 실제 engine·과거 validator 전체 family의 구성까지 연결했다. 다음은 새 그래프 보고서·외부 입력 패킷·metadata admission·공유 decoder·비용·별도 worker 시작 경로를 연결하는 것이다. 관측 행·카운터·기존 scope 불변조건을 거짓 값으로 바꾸지 않는다. 이 연결과 검증 전에는 준비 결과를 단일 제품 시험의 실행 자격으로 사용하지 않는다.

### 기존 engine 구성과 새 실행 identity

원 `native009_engine_connection_v1.build`는 descriptor 수와 TASK를 먼저 확인하고, 그 다음 기존 Native009 결과가 없을 것을 요구한다. 기존 69→72→73→75 transport는 descriptor 수의 typed constant를 명시적으로 투영했지만 현재162 준비 API는 그 75개 engine 구성기를 그대로 사용할 수 없다. worker 생성기에도 `ONLY165_RUN009_GRAPH`, 기존 bootstrap·declaration·wire 및 TASK의 run009 제약이 남아 있다. 기존 준비 그래프는 새 실행 identity로 자격을 얻은 그래프가 아니다.

2026-10-16의 좁은 격리 확인은 원 engine 소스 9,522bytes와 원 constant 투영 소스 15,741bytes의 고정 SHA 및 전후 바이트 동일성을 확인했다. 원 build 함수 전체 본문과 TASK·ROOT 상수를 유지하고 기존 69→72→73→75 typed inverse를 재현했다. 메타데이터 fixture의 descriptor 수162는 원 첫 guard(`NATIVE009_ENGINE_EXACT_FULL69_RUN009_GRAPH`)에서, 수75는 실제 존재하는 Native009 파일을 확인하는 다음 guard(`NATIVE009_ENGINE_NO_EXISTING_NATIVE009_RECEIPT`)에서 각각 거부됐다. 하위 구성요소 접근·실제 engine 구성·제품 실행·자식 프로세스·수용 증가는 모두0이다. 실제162 engine/worker의 구성 통과를 의미하지 않는다. 최초 격리 harness의 TASK 상수 누락 오류는 원 AST 상수를 포함해 고쳤으며 원 함수나 guard는 수정하지 않았다.

`case165-current-runtime-run009.v1.json`은 실제 존재하며 보존한다. `case165-current-runtime-run010.v1.json`은 이 확인 시점에 없었지만, 미존재는 예약·새 실행 허가·입력 자격을 뜻하지 않는다. 다음 준비는 Native009 guard를 우회하지 않고 별도 identity의 engine/worker/TASK·bootstrap·wire·독립 checker 일치를 갖춰야 한다. 실패009를 보존하는 descriptor의 과거 provenance와 새 실행 identity를 구분하고, 162개 전체 범위·기존 시간/자원 제한을 유지한다. 이 메타데이터 준비는 제품 실행 허가와 별개다.

`prepare_engine_builder`는 고정 engine 소스와 원 runtime factory 전체 코드의 일치를 확인해 case165/run010/descriptor162용 private 구성 함수를 준비한다. 원 `require`·`factory9`·`build` 전체 함수 본문을 유지하며 factory의 run9 한 슬롯과 build의 descriptor69·run9 두 슬롯, private TASK/ROOT 의존성만 변경한다. 역복원은 값 전체 치환이 아니라 원 상수 위치를 복원한다. 따라서 run9→10과 기존 제품10 상수가 겹쳐도 원 10초 제한은 바뀌지 않는다. 원본 Native009 소스·모듈·결과는 수정하지 않는다. 기존 결과 거부·identity 일치·단일 engine 구성·worker 미실행·10초 조건도 원 본문에 남는다.

구성 함수의 추가 6개 계약은 위치별 전체 코드 역복원, 원 runtime factory의 8→10 bound 역복원과 default 보존, 소스·factory 변경 거부, 기존009 TASK/잘못된 수 거부, 새 결과 경로가 이미 있을 때의 원 guard, 전체 원 build 본문의 단일 합성 구성·worker 실행0을 확인했다. 양성 구성 시험은 private 합성 factory/window를 사용했으며 실제 engine 통과가 아니다. 현재009 그래프·wire는 재표기하지 않았다.

### 새 identity wire와 bootstrap 준비

기존 원 wire의 의미 필드는 case·이전 수용 수·manifest·descriptor·이전 원장/후보이며 실행 번호가 직접 포함되지 않는다. `identity_wire`는 원 binary v3 wire를 그대로 내부에 보존하고, 새 작업 이름·case165·run010·내부 wire pin을 닫힌 canonical 헤더에 묶는다. 외부 pin 검증 뒤 정확 identity와 내부 pin을 확인한 후 원 decoder에 내부 바이트와 내부 pin을 전달한다. 원 decoder의 `policy_capsule_bytes`는 내부 바이트 수로 유지하고 외부 transport 바이트 수를 별도 기록한다. 전체 wire16KiB·확장128KiB·원 codec 메모리 제한은 늘리지 않는다.

`prepare_worker_transport`는 원 metadata 연결·worker encoder/decoder·Binding 본문을 유지하고, private run 상한의 위치별 8→10 역복원과 case165/run010 전용 입구를 연결했다. 실제162개 Binding을 encode/decode해 모든 descriptor와 manifest pin이 일치함을 확인했다. 별도 wire15,867bytes와 bootstrap4,903bytes를 메모리에서 만들었고 모두16,384bytes 이하다. bootstrap은 원009 생성용 bootstrap/wire를 참조용 constructor 데이터로 명시하며, 실행 core는 새 작업 이름과 run010 wire pin을 사용한다. 기존 원본·실패009 provenance·성공 원장을 바꾸지 않는다.

실제 메모리 왕복 검증에서 기존009 wire·외부 hash 불일치·외부 hash는 맞지만 작업 이름이009인 헤더를 정확한 원인 코드로 거부했다. 8개 추가 격리 계약은 내부/외부 hash 및 카운터 분리, 변경된 내부 바이트, 원 decoder 예외와 자원 보호 예외 보존, 헤더를 포함한16KiB 상한을 확인했다. 원 decoder 외의 제품 코드는 실행하지 않았다.

별도 worker 프로세스·실제 engine 실행·부모 입력 admission·공유 decoder·GO/dispatch 자격은 아직 미검증이다. 아래에서 실제 파일 발행과 입구 복원을 추가로 확인했지만, 이를 실제 프로세스 통과나 제품 수용으로 사용하지 않는다.

### worker 입력 입구와 복원

wire·입력 처리 코드를 실행 전용 `batch_worker_entry.py`로 분리해 worker가 batch 감사 전체를 기본 import하지 않도록 했다. source pin을 현재 입력에 한 개 명시적으로 추가했으며 보존421개는 변하지 않았다. `reconstruct`는 정확 TASK와 NO-GO bootstrap을 먼저 확인하고, 새 bootstrap·원009 참조 bootstrap·원009 참조 wire·새 wire의 바이트를 각각 pin과 비교한다. 원 constructor로 전체162 참조를 복원한 뒤 새 transport graph와 원 decoder로 새 wire를 복원한다. 새 패킷 생성기나 부정 시험은 입구에서 실행하지 않는다. 원 decoder 내부의 canonical inverse 작업은 유지한다.

실제 프로그램 연결 확인에서 새 bootstrap/wire 두 개는 메모리 시제품, 기존 참조 두 개는 원 paced reader의 fresh 파일 읽기를 사용했다. 원 constructor·새 graph·원 decoder 경로로162개와 manifest가 일치했다. 이는 같은 프로세스 안의 입력 복원이며 물리 입력 네 파일이나 worker 프로세스 시작을 통과했다는 증거가 아니다. `file_reader`에는 원 직접 경로·링크 거부·16KiB 읽기 경계를 유지했고, 아직 새 외부 파일로 이 경로를 실행하지 않았다.

추가9개 계약은 작업 이름/변조된 바이트/GO 플래그/옛 run/잘못된 case/알 수 없는 경로/descriptor 누락과 자원 예외를 확인하고, 합성 파일 경로에서 직접 읽기 범위·링크·16KiB 조건을 검증했다. 분리 직후 준비 코드의 validator 지역 이름 참조 오류는 새 runtime의 검증 함수 호출로 고쳤으며 실패 출력과 원 판정 조건을 보존했다. 다음은 실제 engine·과거 checker family와 새 프로세스 시작 경로의 연결이다. 별도 새 제품 실행 허가는 여전히 필요하다.

현재 확인된 문제는 검증 경로의 연결·종료 조건이다. 새로운 제품 코드 결함은 확인되지 않았고 제품 Rust 코드는 변경하지 않았다. 다음 대상 제품 시험은 case165의 `actual_import::source_review_locations::actual_original_stored_locations_match_direct_graph_without_state_defaults_or_writes` 한 개다. 실행기·독립 판정 연결과 별도 제품 실행 승인을 갖추기 전에는 이 시험도 실행하지 않는다. 추가 검사기나 전체 해시 패스를 늘리는 대신 기존 실행 경로의 직접 연결을 먼저 정리한다.

### 실제 engine과 과거 판정기 구성

`construct_runtime`는 새 run010 engine, 원 worker 함수, parent Frame·batch 훅, 과거 전체 validator family와 독립10초 판정 경로를 실제 원 구성기로 연결했다. 성공 실행에서 worker attempts/calls·parent attempts·Frame 인스턴스는 모두0이고 원 worker 객체가 유지됐다. 구성 당시에는 그래프 보고서가 없어 metadata 의존성을 명시적으로 차단했다. 아래 보고서는 이후 발행됐으며, 기존 차단 callback은 아직 새 자료/범위의 parent admission으로 교체하지 않았다. 실제 parent 실행을 통과했다는 의미는 아니다.

구성 중 project open은 선언된 pin과 대조하고 쓰기를 거부했다. 과거 initializer도 동일 owner의 원 자원 checkpoint를 사용했으며, source 대신 pyc/pyo가 실행되지 않도록 읽기45회를 거부했다. 캐시 파일을 삭제하거나 sys.modules를 숨기지 않았고, 종료 시 profile callback을 복구했다. 선언된 project 입력198개·원 open216회가 관측됐다.

초기 구성은 `case160-run007-graph-config-r388.v1.json` 미선언 읽기에서 중단됐다. 경로를 동적으로 추적한 뒤 커밋된 Git blob `285e193180038bc069934986c4f55e043f6943af`와 현재 원본이 같은 561bytes·SHA256 `227220e7949895b6b2fbd66e4e7b27678100f2b0e8f43034103e049871f14a09`임을 확인했다. 이 설정 한 개만 새 현재 입력으로 명시했다. 기존009 실행의 누락 입력이 소급 자격을 얻거나, 과거 실패가 수용된 것으로 처리하지 않는다.

최종 실제 구성은239fresh/final239·25,423,265bytes·46.260초·자체CPU최고6.3368%·시스템CPU최고19.53%·전용87.96MiB·가용RAM최저20.75%·cleanup=True였다. 이 시간은 준비와 종료 해시까지 포함한 값이며 worker readiness 시간이 아니다. 제품/자식 프로세스/GO/원장 증가/새 결과JSON 발행0이고 Native008/009를 재실행하지 않았다. 관리 소스5개의 pin이 성공 당시와 같음을 확인해 구성을 불필요하게 다시 실행하지 않았다. 실제 제품·입력 전체 감사·원 비용·helper 한도·공유 decoder·새 프로세스 시작 자격은 여전히 미검증이다.

### 실제 NO-GO 준비 자료 발행과 파일 입구

`batch_preparation_package.py`는 원 고정162 manifest를 덮어쓰지 않고, 실제 이전 candidate의 과거 계보를 정확히 보존한 새 manifest를 생성했다. 새 Binding·wire·bootstrap은 그 새 manifest pin에 묶었다. 원 파일에 없던 `historical_predecessor_provenance`를 추가했으며 원009 실패 역할이나 과거 수용 결과는 변경하지 않았다.

새 manifest92,656bytes·wire15,862bytes·bootstrap4,899bytes를 원 exclusive/paced publisher로 발행한 뒤 실제 `file_reader`로 새/기존 metadata 네 파일을 읽었다. 메모리 시제품이 아니라 실제 파일에서 원 constructor·decoder와162개 및 새 manifest pin의 일치를 확인했다. source64개 종료 해시와 실제 guard cleanup 후 그래프 보고서를 발행하고 보고서 자체의 독립 종료 읽기1개를 확인했다. 현재 활성 보고서는 `implementation/p09/evidence/p09-361-case165-successor-run010-graph002.v1.json`(11,673bytes, SHA256 `104a632a894608e33f51e3ea98c9e0080dd226465b3efc92dc410e3e6a899363`)이다.

첫 graph001도 보존했다. 재사용 집계와 명시적 보고서 generation을 보강한 두 번째 준비는 데이터 파일3개를 정확 pin으로 재사용하고 graph002 한 개만 새로 만들었다. 활성4개 합계125,090bytes이며 graph001까지 보존한 총5개는136,728bytes다. 보고서는 source 변경을 숨겨 덮어쓰지 않으며 generation은1~8을 명시한다. 자동 제품 재실행이나 새 Native 허가가 아니다.

두 번째 준비 종료까지23.964초·source64fresh/final64·자체CPU최고5.2719%·시스템CPU최고20.08%·전용71.09MiB·가용RAM최저21.54%·cleanup=True였다. 이후 새 보고서 자체도 검증했다. 제품·worker 프로세스·Native Frame·GO·원장 증가는0이다. 원 정책87개 계약과 별도 발행 generation/결정적 JSON/비유한수 거부/cleanup·종료 해시 미완료 차단5개 격리 계약도 통과했다. 이 5개는 별도 세션 검사이며 원87개 시험 개수를 늘려 표시하지 않는다.

아래 선언·비용 검사에 이어 전체 실제 경계와 원 부모 입력 함수 검증까지 완료했다. 실제 engine callback·원 비용·helper 한도·metadata/Frame 공유 decoder·별도 프로세스 readiness는 다음 단계다. 기존 `inherit_declaration`의 이력 재주입 방지와 실제 제품 oracle이 모두 끝난 결과만 원장에 반영한다. Native008/009 재실행 금지와 새 제품 실행의 별도 허가 경계는 유지한다.

### 큰 검증 전에 실행하는 선언과 비용 검사

`tools/p09/batch_scope_admission.py`는 읽을 원본과 명시적 추가 입력의 선언을 먼저 복원한다. 전체 코퍼스부터 읽고 나중에 비용 초과를 확인하는 순서를 피하며, 기존16/87개 시험·구성기·전달 자료 발행을 다시 수행하지 않는다. 기존 생산코드와 graph002의64개 source pin은 변경하지 않았다.

첫 연결에서는 고정162 준비 영수증 자체가 현재 선언에 빠져 중단됐다. 이 영수증의 source 목록에는 순환을 피하려고 자기 자신이 없지만, 이후 graph002에는 실제 의존 입력으로 기록돼 있었다. 이 고정 경로·크기·SHA256 한 개를 현재 입력으로 명시했다. graph002의 전체 source 목록이나 검사 중 관측한 파일들을 무조건 union하지 않는다. 논리 이름과 이미 선언된 물리 carrier의 정확한 대응도 검산한다.

현재 선언은 전체3,319개, 매 사례2,898개, 묶음보존421개다. 원3,305개에 기존/신규 프로그램8개, 커밋된 legacy설정1개, 활성자료4개, 준비 영수증1개를 추가했다. 과거 보존421개를 현재로 재분류하지 않았다. 이 수치는 실제 전체 파일 바이트 감사가 아니라 고정 기록에서 복원한 선언이다.

원 `scope.cost`와 `held_native_read_views_v1.model`을 호출한 보수적 계산은522.253682/600초다. 실제 두 바이트 패스·획득14/s·물리open20/s·여유60초·PDH2.05초와 기존 추가 항목을 유지하고, 공유decoder5초·마지막 별도표본0.5초·준비15초를 더했다. 제품20→10초의 비용 절감은 사용하지 않았다. 파일 입출력과 대기를 겹친다고 가정하거나 실제 없는 Native duplicate-open 비용을 되살리지 않는다. 계산이 통과해도 실제 engine 연결·Native/Frame·현재 source 자격이나600초 내 완료를 보장하지 않는다.

첫 선언 검사 계약14개는 오류/실패/skip0, 검사기와 시험 소스2개 전후 읽기 일치·cleanup=True였다. 실제 짧은 실행은18fresh/final18·11,150,154bytes·8.169초·자체CPU최고2.9372%·시스템CPU최고28.06%·전용30.48MiB·가용RAM최저17.17%·cleanup=True·자식 프로세스 생성시도0이다. 이 첫 실행은 별도 증거JSON 없이 세션에 남겼고64개 package 의존 전체 fresh 검증·묶음 전체 시작/종료·parent metadata·제품을 포함하지 않았다. 이후 실제 검증은 다음 절의 불변 결과로 구분한다.

### 실제 묶음 경계와 부모 입력 함수 검증

실제 `--metadata` 실행은 전체3,319개를 시작·종료에 각각 한 번씩 새로 읽어 동일성을 확인했다. 각 경계는3,319읽기/152,130,467bytes이며, 둘을 합친 실제 전체 읽기는6,638회/304,260,934bytes다. 원 부모 입력 함수에서는69개 전후 해시 일치·물리142읽기/6,799,206bytes·현재2,898개 선택·이전 bootstrap membership1회를 확인했다. 보존421개가 매 사례 범위로 다시 들어가지 않았다. 최종 상태는 `EMPTY_BATCH_AUDITED_NOT_ACCEPTED`로, 실제 제품 사례는 포함하지 않는다.

실제 패키지 네 파일을 읽고 원162 constructor/decoder와 새 manifest 일치를 확인했다. 전달용 encoder나 부정 qualification 사례는 이 경로에서 실행하지 않는다. 생성 단계의68개 입력을 모두 종료 확인한 뒤 전체 감사를 시작하며, 이후 새 source 입력을 생성 단계 독자에 추가하지 않는다. 단계 설정은 부모 입력 목록에 명시하고, 그 존재와 정확한 current membership을 큰 읽기 전에 검사한다.

처음 기본 reader 경로는77.691초에 시스템CPU81.44%/자체최고2.8529%의 원75% 경고로 중단됐다. 상태는BROKEN·cleanup=True이고 자동 재개하지 않았다. reader 검토에서 이미 검증된 `single_snapshot_source_guard_v1`과 `reusable_audit_chunk_v1`이 이 새 경로에 연결되지 않은 것을 찾아 적용했다. 작은 실제4개 파일의 전후8읽기/107,352bytes에서 fresh stat8회·workspace1개·오류0을 확인했다. 이후 전체 경계도 각각 stat3,319회·ordinary판정3,319회·fallback0·workspace64KiB 한 개·반환 누락0으로 종료했다. stat/바이트/해시/JSON 캐시는 없으며 원 링크 검사 fallback, 모든 읽기·속도 제한·마지막 해시를 유지한다. PC 프리즈 원인이 해결됐다는 뜻은 아니다.

최적화 후 첫 전체 시작 읽기는 완료됐지만 부모 목록의 단계 설정 누락으로 중단됐다. 이 실행은236.581초·source68/final66·전체 시작3,319개·최종 전체감사0·cleanup=True였고, 종료 후 보조 source2개를 추가한 잘못도 드러났다. 당시 driver는25,481bytes/SHA256 `3c8cba20a28607913f173dd91c6af97caf3762e656a28bb73606b76b31233b62`다. 이 실패를 수용하지 않고 단계 설정의 사전 선언과 보조 코드의 종료 전 읽기를 수정했다. 최종 계약26개가 오류/실패/skip0·source2개 전후 일치·cleanup=True로 통과했다. 기존16/87개 시험과 제품은 재실행하지 않았다.

최종 실제 검증은 source68fresh/final68·470.682초·자체CPU최고4.1445%·시스템CPU최고65.81%·전용51.88MiB·가용RAM최저22.59%·모든 단계cleanup=True다. 읽기 전용 구성15.277초, 시작감사와metadata232.807초, 종료감사222.598초를 원600초 guard로 각각 제한했다. 정상 종료·동일 process/thread·미실행 사례·비활성 metadata·parent/Frame 미연결을 확인한 뒤에만 다음 읽기 전용 단계로 전환한다. CPU/시간/IO 실패 뒤 타이머만 새로 만들거나 실제 Native의600/720초 제한을 초기화하는 경로는 없다.

metadata decoder는 원 공유5초 예산에 등록돼5회/0.131626초를 사용했다. Frame등록과Frame decode는0이다. 그러므로 이는 metadata만의 실제 확인이지 metadata+Native 합산 자격은 아니다. 비용 우선 모델은 현재 코드에서522.274030/600초이며 실제 Native 실행 비용·완료 시간 자격은 별도로 남는다. 실제 engine/worker·Native Frame·GO·제품 수용은0이다.

불변 결과는 `implementation/p09/evidence/p09-361-case165-batch-source-metadata-run010-qual001.v1.json`(10,829bytes, SHA256 `8822f82682ad0268d29a64a5060ac59caf5d5ee74c8f4144994cd0389f40b8f5`)이다. 성공 당시 프로그램8개가 여전히 같은지와 원 exclusive publisher를9fresh/final9로 확인한 뒤 발행하고, 새 결과만1fresh/final1로 종료 확인했다. 이 발행은 전체 코퍼스를 다시 읽지 않았다. 이 준비 결과를 실제 Native 증거로 승격하거나, 미래 실행 입력에 자동으로 재귀 union하지 않는다.

### 실행기 연결과 실제 worker 준비

`tools/p09/batch_engine_connection.py`는 위 준비 기록의 원 프로그램8개가 같은지 확인한 뒤 원 engine과 과거 checker를 구성한다. 전체3,319개 감사나 과거 통과 사례를 다시 실행하지 않는다. 원 scope 함수와 현재 callback을 같은 engine/parent 환경에 연결하고, 원 공유 Frame 생성자 코드와 동일한 budget owner만 허용하는 private 연결을 사용한다. 기본 Batch의 정확4클래스 조건은 유지하고 private 공유 경로만 정확5클래스와 원 constructor/closure로 검사한다. 원 worker launch와 readiness 함수의 본문을 유지하며 TASK와 입구만 새 run010으로 지정했다. 구성 중에는 Job·Frame 인스턴스·worker·제품을 실행하지 않는다.

최초 helper 검사 실패에서 `historical_receipt_batch_partition_v1.py`, `phased_preservation_read_gate_v1.py`, `phased_preservation_read_gate_v2.py`의 선언 누락을 확인했다. 모든 누락 이름을 추가 IO 전에 보고하도록 보완하고 이3개와 새 entry/worker2개만 실행 입력으로 명시했다. 관측 파일 전체를 자동 union하지 않는다. 새 선언은 전체3,324개·현재2,903개·보존421개이며 새 전체 Native 감사는 아직 없다. 관련26계약은 오류/실패/skip0·source4fresh/final4·cleanup=True였다.

연결 성공 관측은273fresh/final273·15,992,371bytes·48.062초·시스템CPU최고60.00%·자체최고6.3667%·전용58.82MiB·가용RAM최저20.81%·cleanup=True였다. 실제 metadata IO 전 차단, 원 비용+준비15초 모델508.669647/600초, attempts/calls/Frame/process0을 확인했다. 이 모델은 실제 완료 보장이 아니다. 전체 stdout은 출력 회수 한도로 일부만 보존돼 helper64 등 전체 증거가 필요한 판정에는 재사용하지 않는다. 이후 worker 준비 코드도 변경됐으므로 이 구성 관측을 현행 Native 자격으로 승격하지 않는다.

`tools/p09/batch_worker_launch.py`의 실제 `prepare` 함수는 원 runtime이 선언한 템플릿 source2개를 producer64와 별도로 명시해 구성한다. 원 준비 입구의 TASK/GO/Job/worker 본문은 유지한다. 외부 준비 진단에는 동일 원 guard checkpoint를 전달할 수 있고, 실제 worker의 기본 경로는 원 parent 소유 보호를 따른다. 최초 템플릿 선언 누락 실패는 제품 호출 없이6.520초에 종료했다. 보완 후 첫 진단은 출력 회수 오류로 판정하지 않았고, 관측 가능한 후속 진단에서55fresh/final55·1,490,939bytes·준비8.568902초·전체9.880초·worker calls/attempts0·process0·cleanup=True를 확인했다. 시스템CPU최고52.05%·자체최고3.3671%·전용48.07MiB였다. 같은 프로세스의 준비 측정이므로 별도 소유 worker의 readiness15초 자격은 아니다.

관측과 누락 진단, 최종26계약은 `implementation/p09/evidence/p09-361-case165-batch-engine-worker-run010-qual001.v1.json`(17,015bytes, SHA256 `3e519f416a1416f54f10fdeb9947ad04445bf6858710a7484da1ee623180f352`)에 묶었다. 실제 시험 source와 원 publisher59개를 전후 확인하고 exclusive 발행 후 결과1개를 전후 확인했다. 이 관측 파일을 실행 입력에 재귀 추가하지 않는다. 별도 소유 worker의 NO-GO readiness, 실제 Native의 두 현재 입력 경계와 공유 decoder5초, helper64와 독립 제품/accounting oracle, 별도 새 제품 실행 허가가 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE는 변하지 않았다.

### 별도 worker 준비 신호와 GO 없는 종료

`tools/p09/probe_batch_worker_readiness.py`는 원 production launch와 실제 `batch_worker_launch.py`에 진단 전용 `--probe-no-go`만 추가한다. 진단 child는 실제 stdin 경계에서 원 ReadyReader가 신호를 보내고 EOF를 받은 뒤 원 WORKER_NOT_AUTHORIZED로 종료한다. 비EOF 입력은 원 worker에 전달하기 전에 거부하며 subprocess.Popen/os.system/os.startfile도 OS 생성 전에 모두 거부한다. 부모는 같은 살아 있는 Job 구성원임을 신호 전후 확인하고 입력을 닫는다. Gate.write를 호출하거나 GO 바이트를 쓰지 않으므로 원 Gate의 readiness_confirmed와 제품10초 capture는 미실행으로 남는다. 실제 Native Frame을 합성하지 않는다.

첫 실제 신호는8.092초였다. 이후 TerminateJobObject·accounting·pipe 정리 실패에도 원 KILL_ON_JOB_CLOSE 핸들을 finally에서 닫도록 보완했다. 이 실패에서 종료 프로세스 수를0으로 채우지 않는 계약을 포함한33개 시험이 오류/실패/skip0·source5fresh/final5·cleanup=True로 통과했다. 보완 후 현재 source의 실제 신호는12.709373초/15초였고, 진단 전체는15.028558초였다. 원 worker 함수 attempts/calls는1이지만 제품 생성과 실제 GO 쓰기는0이며 raw policy가 복원됐다. 원162 descriptor와 단계 pin 전후 확인, 자식 기본helper62/64를 확인했다. 이는 원 부모 Native helper 전체 합집합64의 자격이 아니다.

원 Job 읽기값은1코어·BELOW_NORMAL·CPU hard cap6.25%·process16·kill-on-close·breakaway금지와 일치했다. 자식 Job CPU2.391초·peak private50.77MiB·정리 후 active0·Job핸들 닫힘을 확인했다. 부모7fresh/final7·guard cleanup=True·시스템CPU최고71.69%·부모최고0.3769%·부모 private14.29MiB·가용RAM최저19.86%였다. 두 신호 시간의 차이는 관측값이며 원인을 외부 부하로 확정하지 않는다. 전체 PC 프리즈 해결이나 향후15초 완료 보장도 아니다.

불변 기록은 `implementation/p09/evidence/p09-361-case165-batch-worker-readiness-run010-qual001.v1.json`(10,988bytes, SHA256 `af4f76e8e6351b00f2266274e333be9415e9da2e480aba38e0b2e2faffef7695`)이다. 초기 보완 전 관측과 최종 관측을 구분해 보존했고 현재 시험/진단 source와 publisher11개를 전후 확인한 뒤 exclusive 발행·결과1개 전후 확인을 마쳤다. 진단 source/보고서를 Native 실행 범위에 자동 union하지 않는다. 다음 비제품 작업은 독립 제품/accounting oracle과 공유 decoder 연결이며, 실제 Native 경계·원 Gate.write/capture·새 제품 실행은 여전히 별도 자격과 권한이 필요하다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 독립 accounting 판정과 부모 helper 한도

`batch_engine_connection.py`는 기존 `current_queue_successor_lossless_runtime_v4.oracle_namespace`를 원 loader의 한 번뿐인 oracle 의존성에 연결했다. `native009_full75_dispatch_connection_v1`의 원 연결·검사 코드를 그대로 사용하고, 원 전체 제품 판정 뒤에만 metadata/Frame 공유5초와 실제 물리/의미 바이트 accounting을 검사한다. 원 판정 실패 뒤 accounting을 호출하거나 성공으로 바꾸지 않는다. 실제 구성된 checker의 public/family 함수 동일성·원 checker 환경·같은 Binding·원 추가 검사 함수·원10초 window를 확인했다. 후보 자료나 카운터를 만들어 검사하지 않았다.

작은 선언 검사에서 전체162 descriptor의 carrier가 현재2,903개에 정확히 포함되고 보존421개에는0개임을 확인했다. 따라서 모든 원 metadata 매핑 검사와 묶음 보존 정책을 함께 유지한다. 누락/변경 carrier와 빈 매핑은 IO 전에 거부한다. 선언 확인21fresh/final21은 현재 전체 Native 바이트 검증이 아니다.

첫 연결 구성은275fresh/final275로 종료했지만 원 helper_inventory의 합집합76개(default71)로64 한도를 넘었다. 이 결과는 구성 관측이며 Native 자격이 아니다. 원 loader와 guard4개는 고정 source pin 전체를 사용해 private namespace로 구성했다. batch 정책·보존 gate·worker 입구·준비/admission의 원 전체 AST를 명시적 의존성으로 로드하고, late worker/importlib 의존성은 원 override_import로 연결했다. 소스는 전체 범위에 남고 sys.modules 항목은 삭제·가림·교체하지 않는다. 기본 모듈과 importlib 함수가 그대로이며 guard/cleanup과 원 코드가 유지되는 계약을 포함해43개가 오류/실패/skip0·source12fresh/final12·cleanup=True로 통과했다.

최종 실제 구성의 원 helper 합집합은64개(default59)였다. 원 명시 helper6개 중 기존 default와 겹치는1개를 같은 원 함수가 계산한 값이며 임의로 목록을 줄인 수가 아니다.275fresh/final275·16,290,480bytes·45.360856초·cleanup=True·시스템CPU최고56.34%·자체최고6.2500%·private59.09MiB·가용RAM최저21.49%였다. 원 complete 비용+준비15초 모델은508.677105/600초이며 실제 완료 보장은 아니다. 이 변경으로 준비 경로의 실행 시간이 줄었다는 비교 자격도 없다. 실제 Native 실행 중 추가 helper가 생기지 않는지는 아직 확인하지 않았다.

전체 stdout과 현재43계약, 최적화 전76개의 요약 관측은 `implementation/p09/evidence/p09-361-case165-batch-oracle-helper64-run010-qual001.v1.json`(21,138bytes, SHA256 `7379a71cd53a1630ffdfa2f4b781ed7a78ca7c49b500f69f19b2cdc755c9d375`)에 보존했다. 시험/현재 entry와 원 publisher13개를 전후 확인하고 exclusive 발행 후 결과1개를 전후 확인했다. worker 코드는 앞선 실제 NO-GO 신호 확인 때와 같은 pin이며 해당 검사는 반복하지 않았다. 원 프로그램8개를 유지한 기존3,319 전체 감사도 재실행하지 않았다. metadata reader/Frame/Job/worker/product 실행과 GO/수용증가는0이다. 다음은 전체162 매핑의 실제 공유 decoder 작업량 진단이며, live Native 입력 경계·원 Gate.write/capture10·실제 독립 판정과 새 제품 실행 권한은 여전히 남는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE다.

### 공유 디코더 한도 초과와 미적용 zlib 비교

`probe_batch_decoder_budget.py`는 현재162개 carrier를 매번 fresh 읽고, 원 Projection.decode_fresh와 원 DecoderBudget 두 개를 원 SharedBudget에 연결해 역할별 두 번씩 최소648회를 계획한다. 실제 Frame을 만들거나 source_frame 판정 자료를 합성하지 않는다. 이 직접 역할 예산은 실제 metadata admission과 Native Frame의 모든 작업을 포함하지 않는 하한 진단이다. 전체/유일162개·빈 목록/부분집합·중복 의미/물리 경로 거부4개 계약이2fresh/final2·오류/실패/skip0·cleanup=True로 통과했다.

기존 경로는 metadata324회와 Frame 역할164회, 합488회에서 원 STOP_SHARED_METADATA_FRAME_DECODER5로 중단됐다. metadata3.309152초+Frame역할1.691669초=5.000820초이며 다음 실패 시도까지 물리489읽기/77,858,041bytes였다. 시작source75fresh/final75는 완료했지만 carrier 최종확인은0이므로 성공으로 처리하지 않는다. 전체59.779초·시스템CPU최고35.01%·자체최고3.4892%·private51.21MiB·cleanup=True였다. CPU 경고나 RAM 부족으로 중단된 실행이 아니며 동일 실패를 변경 없이 반복하지 않았다.

후보는 저장소에 이미 있는 고정 `runtime_record_envelope_v1.py`의 zlib codec을 사용했다. 현재 원본162개를 기존 Projection/원5초 budget의 한 번씩 fresh 복원한 뒤, 원 encode로 후보를 만들고 매핑마다 metadata2회/Frame역할2회의 새 decode를 원 공유5초 budget으로 수행했다. 매번 후보 물리 SHA와 외부 선언 의미 SHA를 검사했고, 원본 바이트 전체와도 동일했다. 결과는648/648·공유3.386923초(metadata1.692389+Frame역할1.694534)·오류0이다. 기존 단일 pass162회의 별도 원 budget 측정1.598227초는 후보 합산에 넣거나 실패 예산을 초기화한 값이 아니다.

후보 bytes는 메모리에만 있었고 네 decode 사이에 실제 파일을 다시 읽은 증거가 아니다. 구현된 codec 함수 자체는 매번 새로 복원했지만 아직 새 물리 파일·Binding·bootstrap/manifest에 설치하지 않았다. 전체 비교48.410초·원 물리162fresh/final162/51,408,074bytes·source75fresh/final75·시스템CPU최고47.16%·자체최고4.4728%·private57.52MiB·가용RAM최저20.07%·cleanup=True였다. 서로 다른 IO/실행 조건이므로 전체 처리 속도 개선률이나 실제 Native 완료를 주장하지 않는다.

동일162 매핑의 encoded 합계는25,704,037→71,855,107bytes다.46,151,070bytes 증가분을 원2MiB/s로 두 번 읽는 시간만 계산하면44.013090초가 추가된다. 새 code/선언·원본 보존·추가획득·metadata 전체 호출·Native 잠금 비용을 포함한 새 전체 모델은 아직 없다. 다음은 후보를 별도 실제 파일로 발행하고 fresh decode·버전 명시적 매핑과 전체 비용을 검증한 뒤 연결하는 작업이다. 기존 파일/형식은 덮어쓰지 않고 원5초·자원 보호·독립 판정 조건을 유지한다.

실패 원본과 후보의 전체162개 크기/해시 표, 작업량4계약, 실제 비교 실행 코드는 `implementation/p09/evidence/p09-361-case165-batch-decoder-zlib-comparison-run010-attempt001.v1.json`(129,898bytes, SHA256 `ff2589bdd5957fc645205e018a5e4317ba31389768f4759e5c5abe35c79ab687`)에 보존했다. 경로가 없는 것을 확인해 새 관측 파일을 만들었으며 원 exclusive publisher가 발행한 Native 결과가 아니다. 원 terminal JSON의 숫자형5.0도 그대로 보존했고, 원 Reader로 당시 source76개와 결과를77fresh/final77·cleanup=True로 확인했다. 새 보고서는 실행 입력에 자동 union하지 않는다. 제품/worker/Native Frame/GO/수용증가0·공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE다.

### zlib 실제 파일과 원 v2 디코더 검증

새 g001 corpus162개는 Git ignore 대상이 아니었다. 이 묶음만 대상으로 해당 폴더의 `.gitattributes`에 `case165-zlib-g001-*.envelope.v1.json -diff -text`를 추가했다. 파일 추적과 바이트를 유지하며 압축 base64를 긴 텍스트 diff로 처리하지 않도록 한 설정이다. 한 번의 Git 호출에162개 경로를 명시해 diff/text unset162개씩을 확인했고 첫 파일 hash도 그대로였다. 제품/검증 소스나 기존 corpus의 속성은 바꾸지 않았다. 실제 Codex 화면의 CPU/메모리 개선을 측정한 결과는 아니다.

`tools/p09/batch_zlib_mapping.py`는 고정 비교 기록의 원 의미 pin과 기존 physical pin162개가 현재 Binding의 전체162개와 정확히 같아야 후보 표를 만든다. 대상은 그 닫힌 evidence JSON 표뿐이며 일반 소스/EXE/fixtures를 임의로 바꾸지 않는다. 새 physical 경로는 `implementation/p09/evidence/p361-lossless-runtime-inputs/case165-zlib-g001-001.envelope.v1.json`부터162까지다. 인코딩 결과는 앞선 측정의 크기·SHA와 일치해야 하며 기존 경로는 덮어쓰지 않는다. 부분/다른 원본/잘못된 pin·GO자료·다른 generation·표 사본 변조와 실제 v2 복원/변조 거부를 포함한8계약이7fresh/final7·오류/실패/skip0·cleanup=True로 통과했다.

원 Projection의 클래스와 모든 메서드 객체/본문을 그대로 사용하고 private descriptor 의존성만 정확한162개 표로 연결했다. 의미 입력 전체와 일반 EXE는 유지한다. 복원은 앞선 메모리 비교의 v1이 아니라 출력도64KiB마다 checkpoint하는 기존 v2를 사용했다. 데이터 형식/encode는 동일하지만 v2의 원 보호 검사 빈도를 낮추지 않았다. 이 Projection은 아직 현재 제품 Binding/Native에 설치하지 않았다.

원 exclusive publisher로 새162개·71,855,107bytes를 생성하고 매 파일의 비교SHA를 확인했다. 전체 묶음에 원 OwnedPacer 한 개를 공유해 파일마다 쓰기 token을 초기화하지 않았다. 기존 carrier162개와 새 생성파일162개를 각각 fresh/final162로 종료했다. 이어 새 파일을 각 역할/각pass마다 실제 다시 읽고 원 공유5초 budget으로648회 복원했다. 마지막162개 물리 해시까지 포함해810읽기/359,275,535bytes·162fresh/final162였다. decoder는 metadata324회/2.164573초+Frame직접역할324회/2.200512초=4.365085초, sticky error0이다. Frame역할은 원 budget 직접 호출이며 실제 Native Frame이나 전체 metadata admission 증거가 아니다.

source79fresh/final79·전체343.993687초·시스템CPU최고74.63%·자체최고3.6859%·private52.19MiB·가용RAM최저13.16%·cleanup=True였다. 원1코어/낮은우선순위·RAM/commit95%와CPU·IO·5초 보호를 유지했다. 시스템 전체CPU가 검증 자체 CPU와 같다는 뜻이나 PC 프리즈 해결 증거로 해석하지 않는다. source/core와 test 두 입력을 명시한 예상현재2,905개에서 원20초 제품 allowance도 할인하지 않은 보수 screen은566.711015/600초였다. 최종manifest·wire·bootstrap 및 실제Native 소유/잠금/제품 경로 전체비용과 helper 한도는 아직 별도 검증이 필요하다.

현재 결과/새162 descriptor와8계약은 `implementation/p09/evidence/p09-361-case165-batch-zlib-files-run010-qual001.v1.json`(105,093bytes, SHA256 `cfb2795d9dab562ba5a589b5e8b25a3be20db83ac9b9c4e821c852d2fbfa7d83`)에 원 terminal 숫자형까지 보존했다. 보고서는 새 관측 파일로 생성한 뒤 원 Reader로 source79개+보고서80fresh/final80·cleanup=True를 확인했다. 보고서 정리를 위해648회나 실제 파일 묶음을 재검증하지 않았다. 다음은 이 표를 새 Binding·manifest/wire/bootstrap과 독립 oracle에 명시적으로 연결하는 작업이다. 새 자료를 기존162 wire나 Native009 자료로 위장하지 않고 참조 원본을 보존한다. 제품/worker/Native Frame/GO/수용증가0·미적용·새 제품허가 없음·Native008/009 재실행금지·공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE다.

### 새 zlib Binding과 파일 전달 연결

`tools/p09/batch_zlib_binding.py`는 원 run009 bootstrap·wire와 고정162 constructor를 독립 참조로 사용해 새 일반 Binding과 manifest를 구성한다. 종전 초안의 불필요한 run010 패키지 중간 복원은 제거했다. 원 Projection 클래스와 v2 디코더, 나머지 scope·byte·resource 판정 메서드는 유지한다. 원본과 새 물리 경로가 함께 들어오면 양쪽 pin을 정확히 검증한 뒤 동일 의미 입력으로만 합친다.

최초 실제 구성은 과거 실패 이력이 예상6종이 아니라8종이어서 파일 발행 전에 중단됐다. 원 참조의 `legacy149_validation_failures_provenance`와 `legacy154_validation_failure_provenance`까지 닫힌 명시 목록에 포함해8종 모두를 보존했다. 하나라도 누락되면 거부하는 계약을 추가했다. Native009의 실제 제품 실행 후 실패를 미실행이나 성공으로 바꾸지 않는다. 이전 table·부분 table·잘못된 manifest와 alias hash, 잘못된 case/run/cursor·16KiB 초과 packet을 거부하는 관련12계약이 오류·실패·skip0, source11fresh/final11·cleanupTrue로 통과했다.

원 exclusive publisher로 새 manifest `p09-361-case165-successor-run010-zlib-manifest001.v1.json`(99,480bytes), wire `p09-361-case165-successor-worker-capsule010.compact.zlib.v1.json`(15,058bytes), bootstrap `p09-361-case165-successor-worker-bootstrap010.zlib.v1.json`(4,898bytes)을 발행했다. 총119,436bytes이며 기존 자료는 보존했다. 원 entry 함수의 정확한 새 경로2곳만 가역적으로 바꿔 실제 bootstrap·원 참조 bootstrap/wire·새 wire를 각각16KiB 한도로 읽었다. 원 참조를 다시 복원한 별도 Binding에서 전체162개와 새 manifest 일치를 확인했다. wire는 전체 descriptor와 해시를 담으며 원 내부 decoder와 외부 run010 identity 판정도 실행한다. wire의162개 descriptor를 외부 declaration만으로 대체하지 않는다.

최종 실제 구성·발행·파일 복원은 source79fresh/final79·18.829157초·cleanupTrue였다. 자체CPU최고3.926584%·시스템CPU최고44.34%·전용40.36MiB·가용RAM최저21.12%다. 원 run009 constructor/실제162 decode는 부모 구성과 파일 재구성 각1회이며 제품 replay가 아니다. 불변 기록은 `implementation/p09/evidence/p09-361-case165-batch-zlib-binding-run010-qual001.v1.json`(20,096bytes, SHA256 `f90bccb7e10741c5df659193c0b158f98053df0835973dd4c62fe397e64726d2`)이다. 최초 실패·최종 결과·12계약을 묶고 현재 source79개+기록을80fresh/final80로 확인했다. 기록 발행을 위해 기존648회 복원이나3,319개 전체 감사를 다시 돌리지 않았다. 검사 범위가 다르므로 이전344초와의 속도 배율은 산정하지 않는다.

실제 engine·소유 worker에 새 자료와 source를 명시적으로 연결하고 현재 입력 경계, helper·비용, 공유decoder5초, 독립 제품/accounting 판정을 검증해야 한다. 이번 결과는 worker readiness나 Native Frame 자격이 아니다. 제품·worker·Native·GO·수용증가0, 새 제품허가 없음·Native008/009 재실행금지·공식158/249·대기열잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 새 자료를 사용하는 실제 worker 준비

`tools/p09/batch_zlib_runtime.py`는 고정된 새 Binding 자격 기록에서 실제 사용한 코드3개와 자료3개의 정확한 pin만 재사용한다. 이전 기록의 전체79개 source를 현행 worker 자격으로 다시 주장하지 않는다. 기존 producer64 선언은 그대로 두고 새 코드3개·profile·현 worker를 별도로 명시한다. 새 generic Binding과 원 full162 참조 constructor, 원 bounded entry·내부 wire decoder를 실행한 뒤 기존 engine builder·worker factory를 구성한다. 이전 실패 이력8종과 원 scope·byte·resource 판정은 유지한다.

`batch_worker_launch.py`의 기본 경로는 유지하고 새 경로는 `--probe-no-go --zlib`에서만 허용한다. 제품 모드에서 새 flag는 준비 전에 거부하며, 진단 자식은 모든 process 생성과 EOF 아닌 입력을 거부한다. 원 worker main은 동일한 task·attempts/calls·raw policy·step 종료 필드를 생성하고, private JSON 의존성만 실제 준비 자료의 pin과 종료 해시 수를 추가한다. 준비 전 기대값을 실제 증거로 출력하는 경로는 거부한다. 변경된 worker·probe와 새 profile 관련23계약은 오류·실패·skip0·source11fresh/final11·cleanupTrue다. 무관한 SharedContracts를 초기화 자료 없이 호출한 최초 시험 실행기 오류는 기록에 보존했으며 해당 오류를 제품 결과로 분류하지 않는다.

첫 새 경로의 실제 신호9.120483초는 자료 식별 출력 추가 전 관측으로만 보존했다. 출력 보완 후 새 코드에서 단 한 번 실행한 worker는9.123349초/15초에 실제 event를 보냈다. 자식은 새 manifest(99,480bytes)·wire(15,058)·bootstrap(4,898), 실제 entry4읽기,61fresh/final61과 profile 코드5개 pin을 보고했다. 부모도 같은5개 source를 fresh 읽어 일치시켰다. 원 EOF는 WORKER_NOT_AUTHORIZED·attempts/calls1·제품생성/GO0·raw policy복원·step전후확인·기본helper63/64로 종료했다. 원1코어·BelowNormal·CPU6.25%·process16·kill-on-close·breakaway금지 Job을 실제 읽어 확인했다. Job CPU2.219초·peak private51.08MiB·정리 후active0·핸들닫힘, 전체11.464466초·부모 source11fresh/final11·cleanupTrue였다. 시스템CPU최고42.72%·부모CPU최고0.357874%·부모 private14.62MiB·가용RAM최저26.91%였으며 이는 PC 프리즈 해결 증거가 아니다.

최종 결과·최초 관측·시험 실행기 오류·23계약은 `implementation/p09/evidence/p09-361-case165-batch-zlib-worker-run010-qual001.v1.json`(16,077bytes, SHA256 `d8baaa8fb0dec56a37c1bd420fe7444fddd56828f85878bb707ff701e5e36061`)에 묶었다. 최종 시험·부모·자식의 공통 source19개와 기록을20fresh/final20로 확인했다. 기록 발행을 위해 worker·648회 corpus·3,319개 전체 감사를 반복하지 않았다.

부모의 기존 graph002는 아직 이전 manifest를 가리킨다. 새 부모 graph와 정확한 새 물리 입력 선언·비용을 구성한 뒤 실제 부모 callback·독립 oracle·동일 worker profile을 연결해야 한다. 이번 실제 준비 신호는 원 Gate의 readiness_confirmed나 GO→capture10초, 전체 Native Frame·공유decoder5초, 부모 helper64와 제품수용 자격이 아니다. 새 제품허가 없음·Native008/009 재실행금지·공식158/249·대기열잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 새 부모 graph와 입력 범위

`tools/p09/batch_zlib_engine.py`는 원 producer64에 이름으로 지정한 실행기·worker·정책 helper·새 자료 연결 코드를 추가한다. 관측 파일 전체를 실행 입력으로 합치지 않으며 테스트 모듈은 새 실행 입력으로 추가하지 않는다. 새 부모 graph의 입력74개는 준비 Reader의 전체87fresh/final87에 포함돼 종료 일치를 확인했다. 실제 준비는20.528216초·자체CPU최고2.711646%·시스템59.74%·private33.89MiB·cleanupTrue였다. 원 stdout의 숫자형을 보존한 graph를 `implementation/p09/evidence/p09-361-case165-successor-run010-zlib-graph001.v1.json`(24,042bytes, SHA256 `bfc3eee14ce322b993d02f63ea26cf20e9d02ee79bc3fa55134b30a6f58f8901`)으로 저장했다.

원 의미 입력162개와 보존421개를 유지하면서 정확한 새 물리 carrier만 선택한다. 실제 선언 변환은 전체3,334개·매사례2,913개·보존421개였다. 이는 해당 파일 전체의 실제 해시나 Native 자격이 아니라 입력 선언 확인이다. 일부 table, 의미 pin 변경, carrier 충돌, 잘못된 alias hash, 보존 항목 재분류를 거부하며 부모의 private launch 의존성은 준비 검증을 통과한 `--probe-no-go --zlib`만 선택한다. 관련8계약은 오류·실패·skip0·source9fresh/final9·cleanupTrue로 통과했다. 원 engine·callback·shared Frame·독립 checker의 본문을 재사용하지만 실제 연결 완료는 아래 보호중단으로 판정하지 않는다.

실제 부모 구성 시도는17.406939초에 `STOP_TERMINAL_METADATA_WARNING_BEFORE_MORE_WORK`로 종료됐다. 원 `terminal_metadata_pressure_v1.py`는 전체 시스템CPU 한 표본이75% 이상이면 중단을 고정하며, 이 시도는 시스템최고80.5%·자체최고3.101599%·private40.08MiB였다. source122개를 읽었지만 종료 해시는0이고 정리는cleanupTrue, 프로세스 생성 시도와 제품/GO는0이다. 중단 경로의 원 guard·fresh reader·pacer·구성 audit를 검토했으며 단일 시스템 경고라는 점을 확인했다. 사후 짧은 관측에서 Git 사용률이 보였지만 중단 당시 원인으로 단정하지 않는다. 전체 부하의 원인은 UNRESOLVED다. 보호를 완화하거나 중단된 동일 연결을 자동 재실행하지 않았다.

준비·보호중단·8계약은 `implementation/p09/evidence/p09-361-case165-batch-zlib-parent-run010-attempt001.v1.json`(42,368bytes, SHA256 `09379bc692b65a41d520ef9b94233c4805f511273cf524080e57c7b3b679816a`)에 묶었다. 기록·graph·준비 source87개를89fresh/final89로 확인했다. 이 기록 검사는 부모 연결이나 worker,648회 corpus,3,319개 전체 감사를 반복하지 않았다. 실제 부모 callback·독립 oracle·비용/helper64·현재 전체 경계·Native Frame/공유decoder5초는 미자격으로 남는다. 새 제품허가 없음·Native008/009 재실행금지·공식158/249·대기열잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 승인된 준비 정책과 부모 구성 완료

사용자의 직접 답변 ‘준비 단계에만 적용’에 따라 `tools/p09/batch_zlib_preparation.py`에서 기존 준비 전용 CPU 정책을 선택한다. 전체 시스템90%는 즉시 중단하고75% 이상은 연속4개 새 표본·최소1.5초 지속 시 중단한다. 자체 부하·RAM/commit95%·원 hard guard·1코어/BelowNormal·입출력·기한은 유지하며 Native·worker·제품 guard는 변경하지 않는다. 원 CPU 설계20계약과 실제 no-child probe의 source를 원75% guard 아래 먼저 확인해33fresh/final33·cleanupTrue로 닫았다. connection30 기록은 검증 함수 source를 식별하는 데만 사용하며 과거77개 전체나 Native를 현재 자격으로 승격하지 않는다.

부모 main 본문은 원 `batch_zlib_engine.py`의 전체 code/defaults/closure를 유지한다. 최초 guard 묶음에서만 private 의존성을 선택하고 즉시 원 loader.load를 복원한다. 복원 누락으로 발생한 AST loader 원본 검사 실패와, 그 수정 뒤 마지막 해시 중90.44%로 중단된 시도(source297/final218·52.642386초·cleanupTrue)는 새 기록에 그대로 보존했다. graph001~003과 과거 실패 자료도 덮어쓰지 않았다. 이후 원 read/checkpoint·pacing·parse·hash·종료읽기를 유지하는 기존 fresh stat와64KiB readinto workspace를 준비 reader에 연결했다. 내용·해시·JSON·stat cache나 기본 reader 변경은 없다. 변경 연결8계약은 오류·실패·skip0·source12fresh/final12·cleanupTrue다.

최종 graph004는 source83개를 포함하며 전체 준비96fresh/final96·20.799309초·cleanupTrue로 닫았다. `implementation/p09/evidence/p09-361-case165-successor-run010-zlib-graph004.v1.json`은25,512bytes, SHA256 `4a370ee49b0f5b7c694ec357ecf65c174809460931dd51c54a0c7a12c2a83769`이다. 원 의미 입력162개·보존421개를 유지한 선언은 전체3,335개·현재2,914개다.

실제 부모 engine·metadata callback·원공유 Frame 생성자/owner·readiness context·독립 checker와 추가 accounting oracle 구성이297fresh/final297·55.448089초·cleanupTrue로 통과했다. 감사 전 callback은 원 준비 guard로 IO 전에 거부됐으며 worker/parent/Frame 실행은0이다. 실제 helper 기본59개·명시 집합 포함64개를 확인했다. 원 complete cost에 준비15초를 더한 값은553.570881/600초이고 원 margin60을 유지한다. 이 값은 모델이며 실제 Native 완료 시간 자격은 아니다. fresh stat760회/일반경로760/fallback0, 동일64KiB workspace1개·lease760/return760·fresh readinto1,835회·27,769,127bytes를 확인했다. 시스템CPU최고68.16%·자체최고6.183373%·private60.20MiB였다. 다른 시점의90.44% 중단과 직접 성능 배율을 계산하거나 PC 프리즈 해결로 판단하지 않는다.

준비·최종 구성·변경8계약·이전 실패2회는 `implementation/p09/evidence/p09-361-case165-batch-zlib-parent-run010-qual002.v1.json`(240,818bytes, SHA256 `dc384a425ceba63dfc0296868e0ad8f5aefcfc3828fa1efd41534d2c5e7a1399`)에 원 stdout 숫자형을 보존해 묶었다. 발행 뒤 기록·graph·변경 code만17fresh/final17로 확인했다. 이미 닫힌297개 구성이나 worker·648회 corpus·전체3,335개를 기록 정리를 위해 반복하지 않았다.

전체3,335개 시작/종료 경계와 현재2,914개 실제 metadata, 원 Native Frame/공유decoder5초·자원/입력소유, 동일 부모 worker 경계는 별도 자격이 남는다. 제품/worker/Native/GO/수용증가0·새 제품허가 없음·Native008/009 재실행금지·공식158/249·대기열잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 실제 metadata 준비 경로와 자원 중단

`tools/p09/batch_zlib_metadata.py --metadata`는 원 부모 구성과 실제 engine의 BuildReader·metadata callback을 사용한 뒤 전체 시작·종료 경계를 확인하는 읽기전용 경로다. 제품·GO 모드는 없고 프로세스 생성은 영구 차단한다. 기존 `batch_scope_admission.ReadOnlyEpochs`는 그대로 유지한다. 새 전환기는 부모 연결을 숨기거나 제거하지 않고 실제 engine/parent 실행 횟수0, Frame 목록0, Job/worker/readiness 실행0, 같은 프로세스·스레드, 원 Frame 클래스·메서드 불변, 비활성 metadata/공유 decoder와 실패 없는 상태를 확인한다. 세 순차 준비 단계에만 별도 소유 guard를 사용하며 실패 후 재시도나 Native 기한 초기화는 없다. 기존 준비 source·graph004·제품 코드와 Native guard는 변경하지 않았다.

공통 사전검사의 private bootstrap에도 사용자가 승인한 준비 정책을 선택했다. 원 설계·probe witness와 종료 해시는 유지하고 기본 admission의 정책은 바꾸지 않는다. 이전75% 즉시중단과 승인 정책90% 중단 원본은 보존했다. 초기 실패에서도 실제 CPU 표본·정리 결과를 회수하도록 보완했다. 변경16계약은 오류·실패·skip0, source8fresh/final8·cleanupTrue다. 최종 짧은 검사의 시스템CPU최고64.98%·자체최고0.888464%·private19.48MiB는 이 계약 실행의 관측값이며 실제 metadata 성능 수치가 아니다.

실제 준비 시도는 구성 중 `STOP_PREPARATION_SUSTAINED_SYSTEM_PRESSURE75`로11.846192초에 종료됐다. 시스템최고88.13%·자체최고3.246391%·private37.11MiB·가용RAM최저13.72%였고 source99개를 읽었지만 종료 해시는0이다. 자원 잠금은cleanupTrue로 해제됐고 프로세스 생성 시도0이다. 전체 시작·종료와 metadata 본체에 진입하지 않았으므로 source99개나 작성된 연결 코드를 실제 metadata 통과로 판정하지 않는다. 해당 실행은 자동 재시도하지 않았다.

별도 짧은 계약 검사에서도 실행 시작 전 시스템CPU99.82%·검사 자체0.0%·private16.21MiB 표본으로 중단됐다. 이후2026-10-16 13:52:16 UTC에 약1초 간격 프로세스 CPU 차이를16개 논리 CPU 기준으로 환산했을 때 victoria3가56.63%, explorer가8.94%, Git 한 개가4.12%였다. 이 관측은 그때의 부하 주체를 보여줄 뿐 모든 보호중단이나 과거 PC 프리즈의 원인을 확정하지 않는다. 다른 프로세스를 종료하거나 Windows·Defender·WSL 설정을 변경하지 않았다.

최종16계약·현재 중단·앞선 사전검사 중단4건·짧은 프로세스 관측은 `implementation/p09/evidence/p09-361-case165-batch-zlib-metadata-run010-attempt001.v1.json`(20,949bytes, SHA256 `5b6bf75f1ed85908fadafd32a8f3b2c542eddbbbb960d4de2fc83f6e8c376db3`)에 보존했다. 기록과 변경 code/guard만9fresh/final9·cleanupTrue로 확인했으며 기록 발행을 위해 이전297개 부모 구성·worker·648회 corpus·전체 감사를 반복하지 않았다. 다음 새 읽기전용 검증은 자원 압력을 다시 확인하고 시작한다. 실제 metadata/현재 전체 경계·Native Frame/공유5초·동일 worker 경계는 미자격이며 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 게임 사용 중 긴 검증 보류

사용자의 직접 답변 ‘사용 중 — 당분간 긴 검증 보류’를 적용한다. 게임 사용 중 긴 metadata·전체 입력 시작/종료 감사·빌드·제품/Native 실행은 시작하지 않는다. 목표 전체는ACTIVE로 유지하며 코드 읽기와 작은 정리만 진행한다. 자동 목표 이어가기는 이 보류를 해제하는 사용자 답변으로 취급하지 않는다. 다른 앱 종료나 Windows·Defender·WSL 설정 변경도 하지 않는다.

보류 전 본체 없이 수행한 자원 확인은2026-10-16 13:57:53~54 UTC에 시스템CPU72.66→70.53→90.86%로 측정돼 `STOP_PREPARATION_SYSTEM_PRESSURE90`로 종료됐다. 확인 프로세스CPU는 세 표본 모두0.0%, private13.74MiB였고cleanupTrue다. 현행 metadata 코드와16계약 파일 두 개의 SHA256만 직전 검증과 대조했으며 시험·빌드·metadata·전체 감사는 실행하지 않았다. 이 결과와 사용자 범위는 `implementation/p09/evidence/p09-361-case165-batch-zlib-metadata-run010-deferral001.v1.json`에 보존한다. 이전 attempt001은 변경하지 않으며 metadata/전체 경계·Native의 현재 자격은 계속 미완료다. 공식158/249·잔여91·P09 OPEN·P10미시작을 유지한다.

### 코드 검토 중 종료 증거 확인 강화

긴 검증 보류를 유지한 채 `batch_zlib_metadata.idle`의 보조 판정을 강화했다. NEW는 아직 시작·종료 증거와 시작 Reader가 없어야 한다. READY 또는 완료 상태는 실제 전체 시작 pin과 시작 Reader의 snapshots·읽기 횟수·바이트 합계가 선언 전체와 일치해야 한다. 완료 상태는 종료 pin도 같은 전체와 정확히 일치해야 한다. 상태 이름만 바꾸거나 시작/종료 목록·회계가 누락된 경우에는 거부한다. 원 Batch.begin/finish의 전체 실제 읽기와 기존 자원·소유·Frame·Job·실패 잠금 검사는 유지한다.

시험에 허위 READY와 시작 pin/Reader 회계 불일치, 종료 pin 누락·변경 사례를 추가했다. 변경된 공통 fixture를 포함한 현행19개 조건 검사를 가짜 메모리 입력으로만 실행해 오류·실패·skip0, source8fresh/final8·cleanupTrue로 확인했다. 기존 CPU/RAM 보호와1코어·BelowNormal은 유지했다. 시험 본문은0.002605초, 자원/소스 확인을 포함한 전체 명령은2.812054초였으며 자체CPU최고0.370020%·private19.94MiB·시스템CPU최고27.11%다. 이전16개 PASS는 수정 전 source에 한정하고, 현행19개 통과를 실제 metadata/전체 경계/Native 통과로 확대하지 않는다.

코드18,546bytes의 SHA256은 `cdf3c1e7cc09ea69f309a943a6f3770eb38335a5f12d70f64fb40217102a12f7`, 시험11,266bytes는 `e78875c967e242a06a1c463c92afa712c964277a9a8d4f97f287b7e213894a42`다. 현행19개 결과는 `implementation/p09/evidence/p09-361-case165-batch-zlib-metadata-boundary-code001.v1.json`(4,433bytes, SHA256 `cf815fdd383f341afa818431480edb5e9b6b03efd33b902648ce0f3e2b0a037a`)에 보존하고 기록의 JSON 내용과 해시를 확인했다. 기록 확인을 위해 시험이나 과거297개 부모 구성·worker·648회 corpus·전체 감사를 재실행하지 않았다. 긴 검증 보류는 유효하며 빌드·제품·worker·Frame·GO·실제 metadata·전체 파일 감사는 실행하지 않았다. 공식158/249·잔여91·P09 OPEN·목표ACTIVE를 유지한다.

### 긴 검증 재개와 실제 metadata 관측

사용자의 직접 답변 ‘이제 재개해도 됨’에 따라 긴 읽기전용 검증을 재개했다. 이는 제품·GO 또는 Native008/009 재실행 허가가 아니다. 현행 코드와19개 검사 파일의 해시가 기존 자격과 같음을 확인해 단위검사는 반복하지 않았다. 원 CPU90% 즉시/75% 연속4표본·최소1.5초, RAM/commit95%, 1코어/BelowNormal, 입출력·원본·실패 보호를 유지했다.

실제 구성299fresh/final299, helper64와 원모델+준비15초553.659996/600초를 확인했다. 실제 전체 시작 경계는3,336개/198,597,628bytes를 모두 읽었다. 같은 실제 engine의 BuildReader와 callback은 metadata254fresh/final254·물리512읽기/151,649,799bytes·현재입력2,915개/Rust787개를 확인했다. 원162개 의미 mapping을 실제 읽고325회 새 decode를 수행했으며 metadata decoder2.295531/5초, Frame등록0·오류없음이다. 이는 metadata 함수의 관측값이며 실제 Native Frame과 합산한 공유5초 자격은 아니다.

전체 종료 경계는1,603개를 완료하고1,604번째 읽기 중 `STOP_PREPARATION_SYSTEM_PRESSURE90`로 중단됐다. 전체462.365114초·시스템CPU최고90.23%·자체최고6.249996%·private78.38MiB·cleanupTrue, batch BROKEN이다. 따라서 전체 시작/종료 묶음이나 Native·제품 수용은 통과하지 않았다. 중간 독립1초 관측의 같은 PID19540/생성시각 확인에서 자체CPU0.187%·private60.98MiB였으나 이를 중단 당시 표본이나 전체 최고치로 쓰지 않는다. 제품·Frame·worker·GO 실행0이며 부분 종료를 새 소유자의 완전한 종료 증거로 바꾸거나 같은 실행을 재시작하지 않았다.

원 terminal JSON 숫자형을 보존해 `implementation/p09/evidence/p09-361-case165-batch-zlib-metadata-run010-attempt002.v1.json`(75,351bytes, SHA256 `d5bf21062e05456f4d2ee7e485ef63e7502dae3d008682cf8293447ebb437f3e`)에 저장하고 JSON 내용과 해시를 확인했다. 기록 발행을 위해 구성299개나 실제 경계를 재실행하지 않았다. 다음은 정확한 중단 단계의 code/소유 자원 관측 검토와 현재 전체 경계 자격, 실제 Native Frame·metadata 공유5초, 같은 부모의 worker 경계와 독립 제품 수용이다.

사용자 잔여항목 질문에 맞춰 이전105개 이름 원장(gzip 원 길이/해시 확인)과 현재112~164 수용 구간, 고정249개 test listing을 대조했다. 잔여91개는 일반165~249의85개와 별도corpus47~52의6개다. corpus는 원16개 보호거부, 현16개 signed noop/만료승인 거부, 원36개 전체후보·철회, 변경16개 비교자 변조, 원16개 수치파생 signed 변경/철회, 변경+현32개 보호거부 시험이다. 이 목록 확인은 시험 실행이 아니다. full249·signed16·whole reconciliation 및 P09/A12/A13은 계속 미자격이며91을 전체 P09 업무수로 표현하지 않는다. 공식158/249·next165·P10미시작·목표ACTIVE를 유지한다.

### 실제 현재 전체 경계와 metadata 완료

직전 종료 감사90.23% STOP의 `weighted_audit_io.reserve` 대기 루프, 실제 AcceptanceReader의1/2MiB/s 선택, source/64KiB workspace와 준비 CPU 판정을 검토했다. 중단 당시 자체 부하를 aggregate 최고치에서 추정하지 않도록 기존 단계 표본의 마지막8개만 복사·출력하는 `epoch_evidence`를 추가했다. 새 query·sampler·thread·한도 변경은 없다. 원표본과None/missing을 그대로 보존하고 임의 추가 field는 출력하지 않는다. 변경22계약은 오류·실패·skip0·source8fresh/final8·cleanupTrue다. 코드19,240bytes의 SHA256은 `c8611aada02a99d9d82d29c3823d67bc835332ec053006f6706fea1785bf8115`, 시험12,784bytes는 `f45b8ed42982064796d4c1d370c43c49324302302e94619e97965619d079b32c`다.

새 읽기전용 실행은 실제 부모 구성299fresh/final299 후 전체 시작·종료 경계에서 각각3,336개/198,598,322bytes를 완전히 읽고 같은 pin을 확인했다. 실제 engine의 BuildReader/callback은254fresh/final254, 물리512읽기/151,651,187bytes, 원162개 의미 mapping과현재2,915개/Rust787개를 확인했다. metadata325새decode·물리145,511,581bytes/의미506,953,168bytes, 원 shared budget에서 metadata2.182627/5초·Frame미등록·오류없음이다. 의미복원 byte를 물리 counter에 더하지 않았으며 byte/hash/JSON cache는 없다. 모든 실제 전체 경계의 source stat은 fresh3,336회/fallback0, Reader마다64KiB workspace1개와 같은 수의 lease/return을 유지했다.

원 의미162개·보존421개·현재2,915개·helper64를 유지했고 준비15초를 포함한 원모델553.660658/600초를 확인했다. 모델은 실제 Native 완료 시간 자격이 아니다. 전체645.807866초는 세 순차 읽기전용 준비 epoch의 합이며 각 원600초 guard를 정상 종료·정리한 뒤 전환했다. 실제 Native/Frame timer를 시작·초기화하거나 제품을 실행하지 않았다. 구성63.762957초, 전체시작+metadata329.181948초, 종료252.862087초 모두cleanupTrue다. 실제 빈 Batch는 `EMPTY_BATCH_AUDITED_NOT_ACCEPTED`이고 실제 product cases0·queue advance 권한false다.

시스템CPU최고85.86%·자체최고6.25%·private75.68MiB·가용RAM최저30.94%였다. 시작+metadata 단계의75% 경고2표본은 원 승인된 연속4표본/최소1.5초 조건에 이르지 않았고90% 즉시중단·자체과부하·RAM/commit95%·Native 보호는 유지했다. 같은 PID41360의 별도 중간1초 관측은 CPU0.191%·private60.96MiB였으며 guard 전체최고치로 대체하지 않는다. 단계 원표본1,259개 중 마지막8개씩만 기록했다. 이 실행이 과거 PC 프리즈 원인이나 해결을 확정하지는 않는다.

원 terminal JSON 숫자형과22계약을 `implementation/p09/evidence/p09-361-case165-batch-zlib-metadata-run010-qual001.v1.json`(89,027bytes, SHA256 `be34eb8dc398b6f84158cd6f7c50d99077183f70cb21eb98524c215662f201e5`)에 보존했다. 시험 source8개가 실제299개 종료 source와 모두 일치함을 대조하고 기록+그8개만9fresh/final9·cleanupTrue로 확인했다. 발행 때문에 전체 감사·metadata·299개 구성이나 worker·648회 corpus·통과제품을 재실행하지 않았다. 이전 attempt001/002와원본은 그대로 보존했다.

이번 자격은 현재 전체 시작/종료와 실제 engine metadata에 한정한다. 원 Native Frame/입력소유와 두 실제 byte 경계, metadata+Frame 합산5초, 같은 부모의 worker readiness/Job·정리, 실제 동적helper/전체 시간과 독립 제품 수용은 별도다. 제품·worker·Frame·GO·수용증가0·새 제품허가 없음·Native008/009 재실행금지·공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 실제 부모의 실행 직전 차단 연결

2026-10-17 추가한 `tools/p09/batch_pre_go_stop.py`는 원 Gate가 실제 준비 신호·같은 살아 있는 Job 소유·기존 Frame checkpoint를 확인한 뒤 호출하는 전송 의존성에서 `BATCH_PRE_GO_DIAGNOSTIC_STOP`을 발생시킨다. 원 Gate의 write/flush, 제품10초 Input과 준비15초·clock·Job·Frame 메서드는 수정하지 않는다. 연결 검토에서는 완전한 Frame commit이 두 실제 byte 경계와 실제 Job cleanup을 요구하므로, 제품 없는 진단을 전체 Native 통과로 처리할 수 없음을 확인했다. 차단기의 검사30개는 실제 원 Gate·strict10·connection과 합성 process/event/Job/Frame을 사용한 코드 계약이며 실제 Native 자격이 아니다.

`connect_parent`는 실제 원 부모 Context의 component.connect를 함수 code·globals·defaults 및 다른 closure cell 전부가 같은 함수로 연결하고 `connection` 의존성 한 칸만 바꾼다. 생성된 실제 process는 차단기 설치에 실패해도 원 실행기에 반환해 정리할 수 있으며 그 경우에도 write/flush는 거부한다. 준비·소유·자원·시간 초과, 설정 오류, pipe close 실패는 정상 차단으로 판정하지 않는다. 실제 부모의 실행 횟수·입력 잠금 상태를 만들거나 변경하지 않으며, 실행 후 증거 판정은 원 부모 실행 횟수1을 별도로 요구한다. 원 부모 scope가 닫히기 전에는 연결을 복구하지 않는다.

새 `tools/p09/batch_zlib_frame_probe.py`는 `--connect-only`만 받는다. 고정된 `batch_zlib_metadata.py`(19,240bytes/SHA256c8611aada02a99d9d82d29c3823d67bc835332ec053006f6706fea1785bf8115)는 수정하지 않고 private namespace로 사용한다. 진단 프로그램과 차단기 두 소스만 현재 선언에 명시 추가하며 기존 projection과 의미162·보존421을 유지한다. 다른 실행 인자는 bootstrap 전에 거부한다. 이 진입점의6계약도 오류·실패·skip0·source9fresh/final9·cleanupTrue로 통과했다. 변경한 차단기는10,898bytes/SHA256aed9cb21eab18611b1acec81eaacd7080c32a068c90cfa9d810c3fac822abab6, 진입점은8,012bytes/SHA256f94c1b6f5a7f149faa3e925a653a1e89ee62088f61953584fdb88c3ec09cf768이다.

첫 실제 구성은 변경 불가능한 pin mapping을 일반 dict와 엄격한 타입 비교에 넣어 `CURRENT_EPOCH_ACCEPT_EXPLICIT_NEW_DIAGNOSTIC_INPUT`으로 종료됐다. 원 결과301fresh/final0·cleanupTrue를 실패로 보존했다. 당시 프로그램7,554bytes의 전체 원본은 `implementation/p09/evidence/p09-361-case165-pre-go-parent-connection001-preimage/batch_zlib_frame_probe.py`에 보존했고 SHA25629794cc7fe9c7542bdc05a4b0ed3d2370bfeba977aa50b7df34607df59d48bcb로 당시 pin과 일치한다. 읽기전용 pin을 plain dict로 복사한 뒤 원 strict comparator를 적용하도록 고쳤으며, boolean/숫자 혼동과 scope 충돌 거부는 유지했다.

수정 뒤 실제 구성에서 원 부모에 연결 설치·복구, 원 Frame 클래스·메서드 유지, 새 소스의 정확한 현재 membership,301fresh/final301과 helper64를 확인했다. 실제64.615321초·시스템CPU최고83.8%·자체최고6.249975%·private61.007813MiB·가용RAM최저31.326756%·원표본125개·cleanupTrue다. 새 선언은 전체3,338개=현재2,917개+보존421개이며 원모델+준비15초553.821549/600초는 구성상의 비용 모델이지 실제 Native 완료 시간은 아니다. 부모 실행·Job·Frame·worker·GO·제품은 모두0이다. 새3,338개 전체 경계와 metadata, 실제 Frame·readiness·합산decoder5초는 이번에 실행하지 않았다.

결과와30+6계약·첫 실패는 `implementation/p09/evidence/p09-361-case165-pre-go-parent-connection001.v1.json`(133,483bytes, SHA256 `74a2bcdc5f4312742c68273713e58a47c7099f2db2bac3f273a589bf078a3daf`)에 원 terminal 숫자형으로 묶었다. 별도 확인은 기록·현행코드·실패 프로그램 원본·직전 metadata 증거13fresh/final13·cleanupTrue다. 기록 발행을 위해301개 구성이나 기존 전체3,336개/metadata·worker·648회 corpus·통과제품을 반복하지 않았다.

다음 경계는 canonical Native010 실행 결과와 구분된 진단 전용 결과경로를 준비한 뒤 실제 원 부모의 Frame 첫 byte 경계·같은 Job의 원 readiness·GO 전 차단·실제 정리를 연결하는 것이다. 실행 후 둘째 byte 경계와 Frame commit을 완료한 것으로 처리하지 않는다. 새 제품실행권한 없음·Native008/009 재실행금지·기존 자원/입력/시간 보호·원본/실패 보존·공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 진단 결과경로 분리와 보호 콜백 인계

`tools/p09/batch_pre_go_receipt.py`는 원 `post_product_recovery_connection_v1.receipt_namespace`를 재사용한다. 원 실행 함수의 결과경로 prefix 한 곳만 진단 prefix로 바꾸고 코드 전체의 역복원을 확인한다. 그 함수를 보유한 closure 경로만 같은 code·globals·defaults 및 다른 cell 전부를 유지해 재구성한다. private recovery의 원 strict-window 연결 전에 이 engine을 전달하므로 이후 원 부모와 Frame이 보관하는 original reference도 이 실제 engine을 가리킨다. worker 함수·task·입력·보호·실행 카운터는 바꾸지 않는다. 탐색은 최대64함수·깊이12로 제한하며 중복 경로·순환·다중 literal·기존 진단 literal·잘못된 projector를 거부하는14계약이 통과했다.

`tools/p09/batch_pre_go_namespace_probe.py --connect-only`는 직전 자격 진입점 `batch_zlib_frame_probe.py`의 전체 main code·defaults·closure를 유지하고 bootstrap·명시 source·직렬화 의존성만 연결한다. 원 진입점8,012bytes/SHA256f94c1b6f5a7f149faa3e925a653a1e89ee62088f61953584fdb88c3ec09cf768은 수정하지 않았다. 다른 실행 모드는 bootstrap 전에 거부하며 실제 연결 상태가 없으면 성공 직렬화를 거부하는6계약도 통과했다. 새 helper6,836bytes/SHA2568f4c89832c98a401cb2c459564fb68732a564b8a76d6bd855e779779e306ff28과 진입점3,927bytes/SHA2566b960b4bf6a577b3e02b26c59c4427110920d0ea05686e3bfdfd6213c6fcf2a2만 명시 추가한다.

실제 연결은303fresh/final303·62.900599초·helper64·cleanupTrue다. 대상 literal은 실제 `run_case112_current_stored.py`의 run_owned에서 한 곳 발견됐고, closure 함수3개를 검사해 `reviewed_runtime_attempt_v1.py`의 original cell 경로 하나를 재구성했다. 선언은 전체3,340개=현재2,919개+보존421개이며 원 의미162개를 유지했다. 원모델+준비15초553.974671/600초는 비용 모델이고 실제 Native 시간 자격이 아니다. 시스템CPU최고54.88%·자체최고6.054669%·private60.753906MiB·가용RAM최저35.588063%였다. 현재3,340개 전체감사·metadata·실제 Frame·Job·worker·GO·제품은 실행하지 않았다.

원 실행기는 metadata reader를 만들 때 원 Native guard를 받지만 metadata 보호 객체가 그 reader.checkpoint를 일시 대체하고 finally에서 정확한 원 콜백으로 복구한다. 닫힌 준비 guard를 계속 호출하거나 이미 비활성화된 metadata 보호 객체를 저장해 계속 호출하면 실제 실행 연결이 실패한다. `tools/p09/batch_native_checkpoint.py`의 일방향 인계 코드는 실제 전체 시작감사와 두 준비 owner의 종료를 요구한 뒤 원 engine에 등록된 정확한 metadata reader 한 개만 받는다. 원 metadata 보호가 살아 있을 때는 그 객체를 그대로 호출하고 정상 복구 뒤에는 정확한 원 콜백을 호출한다. 원 Native의75% metadata failfast·hard guard·deadline을 대체하거나 준비용 CPU 정책을 Native에 적용하지 않는다.

인계 코드20계약은 원 metadata pressure 클래스를 사용하되 owner·reader·부모 상태는 합성 환경이다. 닫힌 준비 owner 재사용·다른 reader/부모/guard·중복 인계·복구 전후 handler 교체·재귀 호출·오류 후 재개를 거부하고 원 오류 identity를 보존했다. 이 코드는5,743bytes/SHA2568295901ed4345141ca4417651fc172afc342a3da6dab5f0fb0701a30be299994이며 실제 Native에 아직 연결하지 않았다. 따라서 실제 인계·새 Native 범위·준비시간·Frame 자격으로 해석하지 않는다.

결과와 이번14+6+20계약은 `implementation/p09/evidence/p09-361-case165-pre-go-namespace-and-handoff-code001.v1.json`(84,579bytes, SHA256 `cceeaae1701d30af21d724ac2d1142f030bc6501cff8a9103d13950542e110cf`)에 원 terminal 숫자형으로 보존했다. 별도 확인은 기록·현행코드·직전 차단연결 증거20fresh/final20·cleanupTrue다. 발행을 위해303개 구성·기존 전체경계·metadata·worker·648회 corpus·통과제품을 재실행하지 않았다. Native010 일반결과와 `p09-361-case165-pre-go-runtime-diagnostic001-run010.v1.json`, 진단001 intent는 모두 부재를 확인했으며 생성하지 않았다.

다음은 인계와 경로분리·실행직전 차단기를 진단 전용 실행기에 함께 연결하고 새 전체시작감사 후 실제 원 Frame 첫 byte 경계·같은 Job의 원 readiness·GO 직전 차단·실제 정리를 검증하는 단계다. 둘째 byte 경계·Frame commit·제품 수용은 별도이며 이번 변경은 새 제품실행허가가 아니다. Native008/009 재실행금지·원본/실패 보존·공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 실제 입력 획득 진단과 원 소스의 현재 의존성 수정

`tools/p09/batch_pre_go_runtime.py`에 원 부모·원 Native 보호·입력 Frame·Job·worker 준비·차단기의 진단 경로를 연결했다. 자식은 `--probe-no-go --zlib`만 허용하고 원 worker 자체의 제품 process 차단도 유지한다. Windows Python의 실제 감사 이벤트는 argv 목록이 아닌 `list2cmdline` 처리 후 문자열을 받음을 로컬 표준 라이브러리에서 확인했고, 정확한 명령·경로·event handle·task만 허용한다. `--connect-only`는 구성만 수행하고 `--diagnose-no-go`도 GO/제품/큐 수용 권한을 주지 않는다.

진단001은 전체시작3,341개를 완료했지만 원 metadata callback의 lazy 소스 의존성이 종료된 준비 reader의 콜백을 잡고 있어 `ZLIB_METADATA_LIVE_SAME_OWNER_PREPARATION`으로 종료됐다. 원 결과는8,467bytes/SHA256aee64c4c47dfb4e630bf06237e02fdd2a79ebce1a5738d0eb537d86f4f147c68이며 Frame/Job/worker0·cleanupTrue다. source reader를 생성할 때부터 일방향 인계를 연결하도록 수정했다. 그 첫 수정본은 구성 profiler가 reader checkpoint를 재호출할 때 인계의 재귀 보호와 충돌했다. 구성 단계에서는 원 준비 guard를 직접 호출하고 실제 Native에서는 변경하지 않은 `Handoff.check`를 호출하는 `source_checkpoint`로 연결했다. 원 profile 호출과 자원 검사는 생략하지 않으며 Native 재귀 차단은 유지한다. 해당 구성 실패는 본문/intent 실행 전이었다. 원본은 diagnostic001-review001과 diagnostic002-construction-review001 및 각 preimage 폴더에 보존했다.

그 뒤 실제 진단002는 전체시작3,341개/198,648,429bytes와 Native metadata351읽기를 수행하고 regular2,922개+directory374개의3,296핸들을 원14/s 획득 제한 아래 모두 획득했다. 원 분리 Gate가 `PHASED_READ_GATE_EXACT_LIVE_NATIVE_SCOPE`로 차단해 첫 byte 경계·Job·worker에 도달하지 못했다. 실제 부모 상태를 원 성공으로 바꾸거나 현재 범위를 줄이지 않았다. 원 Native298.45초·표본586개에서 시스템CPU최고88.45%·자체최고5.165190%·private최고72.644531MiB이며 CPU 보호 중단이 아니다. 준비를 포함한 전체602.505803초는 Native timer 한도를 늘린 값이 아니다. source warning·native pressure latch는0이고 핸들3,296개 전부해제·남은핸들/reader/stream/close실패0·raw open함수복구·cleanupTrue다. 원 결과2,399,278bytes/SHA2565c91597af2622ce8dccb45195dd5e0f83840b626acb94874fded5af0aa4ebe60과 진단002 intent는 보존했다.

제품·Frame을 실행하지 않는 별도 구성으로 원 실제 physical scope와 선언을 대조했다.305fresh/final305·별도 원 결과1fresh/final1·cleanupTrue이며 차이는 정확히 case112 run001(3,720bytes/SHA2568c26646fe69111b5429f33ee53f13c044d2d3d45828d8141e15c3f7252e3f7e2)과 run003(56,097bytes/SHA2561fd05236e9c1a56be7402a708e4372e154f957e617cf6286bd1ef0ef6356c470) 두 개였다. missing/changed는0이다. `run_case112_current_stored.py`의 고정 원 소스23,159bytes/SHA2566f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713은 callback 뒤 이 두 실패 기록을 읽어 상태·정리를 확인한다. 따라서 보존전용이 아니라 매 사례 현재 의존성이다.

새 `engine_dependency_pins`는 그 고정 소스의 `FAILED_FIRST_PIN`/`FAILED_STOP_PIN` 선언만 추출한다. `require_current_dependencies`는 실제 부모/묶음 시작 전 이 두 원 pin이 전체·보존 목록에 정확히 존재하는지 확인한 뒤 현재로 옮긴 새 계획을 만든다. 관측 reader 전체를 union하지 않고 전체 pin·logical table·원 source body·Frame/분리 Gate·원본·기타 보존419개를 유지한다. 실제 생성된 engine의 동일한 두 global pin도 확인한다. 새 계획은 전체3,341개=현재2,922개+보존419개이며 범위 축소가 아니다. 최초 새 단위시험 fixture의 임의 보존 파일명은 원 Batch 규칙에 의해 거부됐으므로 실제 허용된 prior-receipt 모양으로 fixture만 고쳤다. 원 Batch 검사는 수정하지 않았다.

최종31계약은 실패·오류·skip0·source22fresh/final22·cleanupTrue다. 실제 수정 구성도306fresh/final306·56.404033초·helper64·cleanupTrue이며 원모델+준비15초554.269106/600초다. 이 모델은 완료 보장이 아니고 새 전체경계/Native 자격도 아니다. 현재 코드22,410bytes의 SHA256은d2a1e52f43bf66f02d3f39fd401fcdd8b93c04268d5274dc68a9d2dec51b5054, 시험18,226bytes는57e50762644ebcdf0aac9d297c0f9c3e65454d9a7d59c94fe5043064f2a0345c이다. 진단001/002의 당시 코드·시험은 바이트와 SHA를 확인한 별도 preimage로 보존했다.

최신 검토는 `implementation/p09/evidence/p09-361-case165-pre-go-runtime-diagnostic002-scope-review001.v1.json`(164,053bytes, SHA256 `e80cda522147bdf6d6f29ddc104dd103a57d2443c64a72533848006be9088340`)이다. 기록·원 결과/intent·실패 프로그램들·원 선언 소스·현행코드·수정구성 기록을31fresh/final31로 확인했다. 발행 때문에 전체3,341개 감사·잠금 획득·과거 통과제품·648회 corpus를 재실행하지 않았다.

다음은 별도 진단003에서 새 현재 의존성을 포함한 전체 시작감사 후 실제 첫 byte 경계·동일 Job의 worker readiness·GO 전 차단·정리까지 검증하는 것이다. 진단003 intent/본문은 아직 실행하지 않았다. 둘째 byte 경계·Frame commit·공유decoder의 실제 Frame 작업·제품 수용은 미완료다. 일반 Native010 결과는 부재이며 Native008/009 재실행금지·새 제품실행권한 없음·CPU/RAM/IO/시간 보호·원본/실패 보존·공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 실제 첫 입력 경계와 동일 Job 준비 확인

진단003은 현재 입력2,922개/180,170,862bytes의 실제 첫 전체 바이트 경계를 완료하고 원 Job을 만들었지만 worker 생성 전에 `OWNED_RUNNER_FAILURE`로 종료됐다. 원 Native406.96초·시스템CPU최고63.2%·부모CPU최고3.6391%·private73.9961MiB였으며 CPU 중단은 아니다. 핸들3,296개 전부해제·Job비어있음·cleanupTrue이며 원 실패는 보존한다. 원 결과3,446,249bytes/SHA25647306f2ce9692019e2f55e8613459ad86929b5ba4a98c08aed08b35b32685b4c와 당시 프로그램/시험의 정확한 preimage를 `p09-361-case165-pre-go-runtime-diagnostic003-entry-review001.v1.json`(169,077bytes/SHA256bb9fedd2458bfd99bffb025dee7a2c4025cdd7e7eb4355d77852be6a95803a0b)에 연결했다.

원 `current_queue_successor_runtime.compose_parent`가 넣는 SELF/TEST 진입점 정보를 별도 Batch 부모 구성에서 누락했다. 실제 부모는 이전 flat-v18 진입점을 유지했지만 변경하지 않은 launcher는 current successor 진입점을 요구했다. 원 launcher와 합성 event/factory를 사용한 제품 없는 재현에서 이전 진입점은 OS process 생성 전 정확한 명령 검사로 거부됐고, 올바른 진입점은 그 검사를 통과해 의도한 factory 차단점에 도달했다. 원 실패의 상세 예외는 원 runner가 일반 코드로 축약했으므로, 이 원인은 당시 원 예외 trace를 직접 관측한 결과가 아니라 실제 환경·원 소스·원 launcher 재현에 근거한다.

`bind_parent_entry`는 실행 전 동일한 private engine/worker 환경의 SELF/TEST만 원 successor 값으로 복구한다. 원 함수 객체·본문·defaults·closure·launcher 명령 검사·Frame/Job 메서드와 기본 모듈은 유지한다. 복구 뒤 실제 helper 목록도 다시 계산해64개 이하 및 현재 입력 선언의 정확한 membership을 확인한다. 현행33계약은 실패/오류/skip0·source22fresh/final22·cleanupTrue이며, 실제 수정 구성도307fresh/final307·helper64·cleanupTrue다. 구성 결과만으로 worker/Native 자격을 주장하지 않았다.

별도 진단004는 원 부모를 한 번 호출했다. 현재 구성307개와 전체 시작3,341개/198,654,827bytes를 실제 읽은 뒤 원 Native로 일방향 인계했다. 현재 입력2,922개와 조상 디렉터리374개의 핸들3,296개를 모두 획득하고, 현재 입력180,173,468bytes의 실제 첫 바이트 경계1회를 완료했다. 원 Job에 속한 실제 worker의 준비 신호는8.970553초로 원15초 제한 이내였다. 원 Frame checkpoint147회와 원 Job1개·소유범위복구1회를 확인했다. metadata163개·Frame162개의 실제 decoder 작업 합은1.427016+1.056166=2.483182초로 공유5초 이내였다. 이 값은 metadata와 첫 경계 작업이며 아직 둘째 경계를 포함하지 않는다.

원 준비 Gate가 실제 준비·동일 Job·살아 있는 Frame을 확인한 뒤 전송 의존성에서 `BATCH_PRE_GO_DIAGNOSTIC_STOP`으로 차단됐다. 실제 GO쓰기/capture/제품시계시작/제품자식/수용증가는0이다. 원 결과의 `DEFERRED_NOT_STARTED`와 실패 판정은 그대로이며, 외부 진단의 PASS는 이 의도한 차단과 실제 정리에 한정한다. Frame은 CLOSED·미commit, Batch는 BROKEN·cases0이고 전체 종료감사는 수행하지 않았다. 핸들3,296개 전부해제·남은핸들/reader/stream/close실패0·Job비어있음·원 raw open함수와 소유범위복구를 확인했다.

진단004 원 Native는418.3초·811표본이다. 시스템CPU최고80.71%, 부모CPU최고3.664308%, 부모private최고75.09375MiB, 가용RAM최저30.344509%, commit최고56.322949%였다. 부모CPU 첫 표본1개는 미측정으로 보존하고 numeric 표본810개로 최고치를 계산했다. 준비 포함 전체734.281508초는 순차 준비·실제 Native·종료 관측의 합이며 Native600초/전체720초의 원 실행 타이머를 초기화하거나 늘리지 않았다. 실제 제품을 포함한 부하와 PC 프리즈 해결은 미확정이다.

원 결과는 `p09-361-case165-pre-go-runtime-diagnostic004-run010.v1.json`(3,458,529bytes/SHA256de7e5b1236166dcbecd7d3f644166186edcff9318f2e39cd039c4be1a697e191)이다. 원 terminal 숫자형을 보존한 자격 기록은 `p09-361-case165-pre-go-runtime-diagnostic004-qual001.v1.json`(99,015bytes/SHA25617465b58d98956a138033702451a7321d59848f43c44f052b98ae7f16354b35b)이다. 기록·원 결과/intent·진단003 실패/당시 프로그램·원 launcher 재현 소스·현행 코드37개를 전후 읽어 일치시켰고 cleanupTrue였다. 검토 중 원 serializer가 추가하는 정확한 두 필드를 빠뜨린 비교와 첫 CPU 미측정값의 집계 오류는 기록 비교에서 수정했다. 원 검증 조건·표본·제품 코드는 바꾸지 않았으며 실패와 수정된 재현 명령은 `p09-361-case165-pre-go-runtime-diagnostic004-publication-review001.v1.json`에 보존했다. 발행 때문에33계약·307구성·전체3,341개·Frame/worker·과거 통과제품·corpus를 재실행하지 않았다.

다음은 별도 제품 경로에 원 첫/둘째 입력 경계·Frame commit·원10초 capture·독립 제품 판정과 묶음 전체 종료감사를 연결하는 단계다. 이번 NO-GO 자격은 새 제품 실행을 승인하지 않으며 원 진단004를 제품 실행으로 재사용하거나 덮어쓰지 않는다. 일반 Native010 결과는 부재이고 Native008/009 재실행금지·원본/실패 보존·CPU/RAM/IO/시간 보호·공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### Native 종료 후 전체 종료감사와 원 판정기 연결

`tools/p09/batch_post_native.py`는 모든 reader/loader가 콜백을 캡처하기 전에 원 checkpoint를 전달받는 일방향 연결이다. 준비와 실제 Native 동안에는 기존 콜백과 원 Handoff 검사를 그대로 호출한다. 실제 Native가 종료되고 동일 부모의 Frame 두 경계·commit, Job 소유범위와 핸들 정리·raw 정책 및 metadata 압력 복구를 확인한 뒤에만 읽기전용 종료 guard 하나를 만든다. Native 타이머/한도와 실패 latch를 초기화하지 않으며 NO-GO 중단이나 미완료 Frame은 새 guard 생성 전에 거부한다.

전체 종료는 원 `Batch.finish`의 fresh 전체 읽기를 한 번 호출한다. 이 reader에 불필요한 세 번째 전체 읽기를 추가하지 않는다. 원 묶음·사례 종료 조건이 충족된 뒤 별도의 fresh reader로 동일한 전체·추가 lossless 회계 판정기를 호출하고 원 최종 fresh 확인과 guard 정리를 마쳐야 반환한다. 후보 행·입력 인자·원 반환값과 원 Frame/Job 메서드는 바꾸지 않는다. 판정기 함수의 동일성·본문·globals·defaults·closure도 호출 전후에 확인한다. 종료감사부터 판정·마지막 확인까지 guard 하나를 유지하며 그 안의 시계나 소유자를 교체하지 않는다. 자원·정책·최종 확인 실패 시 오류를 보존하고 cleanup은 압력 조건에 막히지 않는다. 이 연결에는 큐 writer나 제품 실행 함수가 없다.

현행19계약은 원 Batch/Frame 본문과 합성 IO/Job/guard를 사용했다. 준비 콜백 전달, 두 실제 경계를 요구하는 원 commit 조건, 전체 종료 전 판정 거부, 미완료/변조/누락 입력, 재사용 reader, 후보 flag/summary 변조, 교체·본문 변조 판정기, 원 판정 및 마지막 fresh 실패, 자원 오류와 cleanup 실패, 다른 owner·재시도 거부를 확인했다. 오류/실패/skip0·source10fresh/final10·cleanupTrue·process생성0이며 본문1.005321초다. 자체CPU최고0.3864%·private최고17.96875MiB는 이 짧은 계약 실행의 관측이며 실제 제품 부하가 아니다. 현행 프로그램10,793bytes의 SHA256은827aa1ee0411111cea08ac555e46eab3c7bcc4caf16051d4f171979a5499ea51, 시험13,678bytes는c5aa3e8d24679226a5c11afade48469997e2617bd8d31498dc59f1487fdef519다.

실제 현재 그래프에 연결을 설치한 별도 읽기전용 구성은307fresh/final307·57.036004초·helper64·cleanupTrue였다. 새 프로그램 소스 한 개만 현재 입력에 명시해 전체3,342개=현재2,923개+보존419개를 구성했으며 관측 입력 union은 사용하지 않았다. 원 전체 checker·추가 lossless 회계·공유decoder5·제품10초의 기존 연결을 보존했다. 원 모델+준비15초554.353313/600초는 실제 Native 완료 보장이나 새 종료감사/독립 판정 비용 자격이 아니다. Native/Job/Frame/worker/GO와 종료 guard·oracle 호출은 모두0이다. 따라서 이 구성은 종료 본문 실행이나 새 전체3,342개 바이트 경계를 검증하지 않는다.

현재 `batch_zlib_engine.diagnostic_launch`는 실제 명령에 `--probe-no-go --zlib`를 넣고, 원 worker의 `preparation_profile`은 probe 없는 zlib를 거부한다. 이번 종료 연결로 이 보호를 제거하거나 진단004를 제품 실행으로 바꾸지 않는다. 다음은 별도 제품모드 entry/launch를 원 준비15초·제품10초·동일 Job/Frame에 연결하고, 새 실행 입력 및 실제 종료감사/전체 독립 판정 자격을 확인하는 단계다. 실제 제품 실행에는 별도 권한이 필요하다.

원 terminal 숫자형과 재현 명령을 보존한 기록은 `p09-361-case165-post-native-connection001.v1.json`(73,247bytes/SHA256defea8c353e08ee8f6dca037e9d4885809a3b5c086f6af21f643e1667b6da9a8)이다. 기록·현행 코드·기존 진단004 자격13개를 전후 읽어 일치시켰고 cleanupTrue였다. 이 발행 확인을 위해19계약·307구성·기존 전체3,341개·Frame/worker·과거 통과제품·코퍼스를 반복하지 않았다. 기존 실패/진단004 원본은 보존하며 일반 Native010 결과는 부재다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE·Native008/009 재실행금지와 기존 CPU/RAM/IO/시간 보호를 유지한다.

### 별도 제품 진입점과 실제 소유 worker 준비 확인

`tools/p09/batch_product_worker.py`는 기존 `batch_worker_launch.py`와 `batch_zlib_runtime.py`의 고정 소스를 재사용하는 별도 진입점이다. 원 native009 entry의 main·execute·ReadyReader·인자·원 worker 본문은 유지하고 현재 task/경로와 준비 함수만 private 환경에서 연결한다. 준비 실패는 즉시 기록해 같은 API의 준비 재시도를 거부한다. 실제 EOF와 폐쇄형 실패 메타데이터도 원 main으로 처리한다. 이 모듈은 Native dispatcher나 실행 승인 도구가 아니다.

기존 진단용 `preparation_profile`의 probe 없는 zlib 거부 조건과 `diagnostic_launch`는 수정하지 않았다. 새 제품 진입점은 zlib 준비를 직접 선택하며, 명시적인 `--probe-no-go` 모드에서는 process 생성 감사를 영구 차단하고 원 NoGoInput으로 실제 EOF만 허용한다. 진단을 위해 GO를 보내거나 가짜 EOF/준비 신호를 만들지 않는다. `batch_product_launch.py`는 원 launcher의 정확한 명령·파일pin·파이프·우선순위·상속 event·동일 Job·준비15초·제품10초 조건을 유지한다. 별도 부모의 private WORKER 및 loader 의존성만 새 파일로 연결하며 기본/기존 진단 모듈은 그대로다.

첫 조건 검사15개 중6개는 시험용 설정에서 기본15초 창을 넘겨 `READINESS_CONNECTION_ORIGINAL_WINDOW10_AND_GO`로 거부됐다. 당시 시험10,877bytes/SHA256a345f229d4ea321fa25e5ebd215e46bc7278f95d30b1d45d0971b77989050aea는 `product-entry-preimage001/test_batch_product_worker.py`로 보존했다. 기존 `tighten_window`를 시험 설정에 적용한 뒤 현행15계약이 오류/실패/skip0·12fresh/final12·cleanupTrue·process생성0으로 통과했다. 원 10초 검사나 제품 코드는 완화하지 않았다. 새 worker4,818bytes의 SHA256은45ff19b23f16e930e796e0b17d48da9661afc85e4673e4b3fa9adffaea53c1e3, launcher3,590bytes는33c4d7dc489bae347357844a44241dce41c18bbb49d56424595a391f7e428492, 현행 시험11,024bytes는da17a4a860bf156663131f62fe95b39e0a0f12676cef52c9a5ea1570531d0a77이다.

실제 준비 함수는61fresh/final61·8.813779초에 원162 descriptor와 준비15초/제품10초 구성을 만들었다. 별도 외부 source6fresh/final6·cleanupTrue이며 worker 호출/시도·Job·Frame·자식·GO·제품은0이다. 이 시간은 같은 프로세스의 준비 본문이고 실제 자식 준비 신호로 대신하지 않는다.

그 뒤 새 worker pin과 이전 종료 연결을 실제 부모 구성에 함께 설치했다.309fresh/final309·59.442418초·helper64·cleanupTrue이며 원 전체·추가 lossless 회계·공유decoder5·제품10초 판정기를 유지했다. 명시 소스 두 개를 추가한 전체3,344개=현재2,925개+보존419개이고 관측 입력을 union하지 않았다. 원 모델+준비15초554.504189/600초는 실제 Native나 후속 전체 종료감사/독립 판정 시간 자격이 아니다. 이 구성에서는 Native/Job/Frame/worker·종료guard/oracle·제품을 실행하지 않았다.

변경하지 않은 `probe_batch_worker_readiness.run`을 재사용해 새 진입점의 실제 worker 한 개를 원 Job에 배정했다. 부모는 정확한 새 파일·probe 인자·task·상속 event·cwd·env에 맞는 process 한 개만 허용했다. 실제 준비 신호는9.077825초로15초 이내였고, 신호 전후 동일 Job의 살아 있는 구성원임을 확인한 뒤 stdin을 닫아 실제 EOF를 전달했다. 원 worker는1회 진입하고 `WORKER_NOT_AUTHORIZED`로 종료했으며 GO쓰기와 제품 생성은0이다. 원 source-step 전후 확인·raw정책복구, 자식helper62, zlib 준비61fresh/final61·metadata byte admission4회와 부모/자식의 동일 source5를 확인했다.

이 작은 소유 worker 검사는 전체11.871549초·외부14fresh/final14·cleanupTrue다. Job CPU2.047초·private최고51.05MiB·active process0·Job handle닫힘을 확인했다. 기존 부모 표본23개에서 시스템CPU최고39.65%·부모CPU최고0.193605%·부모private최고15.402344MiB·가용RAM최저33.875554%였다. 이 수치를 실제 제품 부하나 PC 프리즈 해결 증거로 확대하지 않는다. 원 Gate.write/10초 capture·Native Frame 두 경계와 전체3344 바이트·종료감사/독립 수용은 미검증이다.

원 숫자형과 네 재현 명령, 첫 시험 실패 및 정확한 preimage를 `p09-361-case165-product-entry-qualification001.v1.json`(116,030bytes/SHA256672349e8b095b7a5da4d9d93ab15774e9133ee47a0a422f5e7594dc5565f244d)에 보존했다. 기록·현행 소스·새 패키지3파일·원 시험·이전 post-native/진단004 자격75개를 전후 읽어 일치시켰고 cleanupTrue였다. 발행 때문에15계약·61준비·309부모·실제 worker나 과거 전체감사·통과제품·코퍼스를 반복하지 않았다.

다음은 별도 Native010 dispatcher에 새 제품 entry/launch와 종료 연결을 설치하고, 새 전체 입력·원10초 capture·실제 둘째 경계/Frame commit·묶음 종료감사·전체 독립 판정을 검증하는 단계다. 실제 새 제품 실행은 별도 권한이 필요하다. 일반 Native010 결과는 부재이며 기존 Native008/009와 실패·진단 원본은 보존하고 재실행하지 않는다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE 및 기존 CPU/RAM/IO/시간 보호를 유지한다.

### Native010 실행기 통합과 준비 표본 재진입 수정

`tools/p09/batch_product_runtime.py`는 새 worker/launch와 종료 연결을 원 부모·Frame·Job·준비15초/제품10초·Native 입력600초/원 실행 한도 아래 통합한다. `--connect-only`는 process·intent·Native 결과를 만들지 않는다. 명시적인 `--run-product`는 현재 자격 자료와 코드·시험·실제 구성의 일치를 요구하며, 자격 자료만으로 실행 권한을 얻지 않는다. 제품 intent와 결과는 원 exclusive publisher를 사용한다. 기존 canonical/intent/결과가 있으면 거부하고 Native는 원 `run_owned(1)` 한 번만 호출한다. 큐 수용 writer는 호출하지 않는다.

원 전체 시작 읽기가 완료되고 준비 소유자가 닫힌 뒤에만 Native를 허용한다. Native 성공 후 같은 실제 Frame의 두 바이트 경계·commit·Job/핸들/정책 정리를 확인하고 전체 종료감사, 원 전체/추가 회계 판정과 마지막 fresh 확인을 수행한다. 실패 시에는 원 Native 기록을 별도 짧은 읽기전용 소유자로 관측해 정리를 확인하며 제품을 재시도하지 않는다. 확인하지 못한 정리는 확인된 것으로 표시하지 않는다. 한 복구 작업이 실패해도 다른 복구 작업은 계속 호출한다. 원 판정 반환값은 기존 lossless carrier로 보존하며 원 Native 기록을 덮어쓰지 않는다.

실제 판정 입력의 읽기 순서를 맞추기 위해 `batch_post_native.Closing.verify`에 명시적인 reader 소유 입력 loader를 추가했다. 전체 종료 전이나 재사용 reader에서는 loader를 호출하지 않는다. 통과한 같은 fresh reader로 원 후보·고정 listing·원 body·fresh 자료를 읽고 기존 context 함수를 호출한 뒤, 원 판정기에 같은 객체를 전달한다. 원 직접 입력 방식과 함수 동일성·완료·최종 fresh 조건은 유지했다. 이전19계약은 수정 전 소스에 한정하며 현행22계약은 오류/실패/skip0·10fresh/final10·cleanupTrue다. 이전 프로그램/시험은 `native010-driver-preimage001`에 정확히 보존했다.

첫 실행기 구성은27.519417초에 `PREPARATION_CPU_FRESH_SAMPLE_SEQUENCE`로 중단됐다. 준비 표본54개와 cleanupTrue이며 process/Native/worker/GO/제품0·intent 미생성이다. 이는 CPU 과부하 판정이 아니며 마지막8표본만으로 전체 최고치를 주장하지 않는다. 당시 실행기21,642bytes/SHA256dfc115ad6db59c0827f60990e82dc4787467135250518d4be6f79fe1b256240c와 시험16,596bytes/SHA2560985c86dc4a5d5fd5fba3025402ec9f2bdaa93f1e331597d95f9f7475b3a4b07은 `native010-profile-failure-preimage001`에 보존했다.

원 고정 `batch_verification.construct_runtime.profile`의 동일 AST 본문과 원 `preparation_attributed_cpu_v1.State`를 사용한 작은 합성 재현에서 같은 순서 오류가 발생했다. 새 감사 콜백의 process와 무관한 호출도 원 프로파일러의 자원 확인 대상이며, 표본이 완전히 관측되기 전에 같은 guard 확인이 재진입할 수 있다. 재현에는 OS Job/Frame/process/제품이나 실제 CPU 압력이 없다. 실제 실패의 상세 중첩 stack 전체를 직접 관측한 증거로 확대하거나 과거 PC 프리즈 원인으로 단정하지 않는다.

`preparation_checkpoint_owner.py`는 준비 단계의 동일 직렬 소유자에 한해 원 자원 확인이 처리 중일 때 정확한 원 프로파일러의 같은 reader 요청만 합친다. 원 콜백은 계속 실행된다. 전체 고정 소스63,495bytes/SHA256296b4fe1070a6e5e4cfb882ba0ad9ca252edc702fc2441e970292cf5ad76dff9에서 프로파일러 본문을 추출하고 code shape·closure의 reader/audit state·실제 호출 frame을 확인한다. 임의 재귀·다른 reader/프로파일러·다른 owner는 거부한다. 원 sampler와 State·CPU/RAM/시간/표본 순서 검사는 수정하지 않는다. 원 외부 확인이 끝나기 전에 IO를 재개하지 않으며 실제 Native checkpoint는 원 재진입 차단까지 그대로 전달한다. 관련9계약은 오류/실패/skip0·5fresh/final5·cleanupTrue다.

수정 실행기24계약은 오류/실패/skip0·10fresh/final10·cleanupTrue다. 현재 실행기23,001bytes의 SHA256은149dba3ac0f825bba81b9acf7e57f98756594836bba12eae97017ef4880860af, 시험16,791bytes는e4d9eacaef4754db648d5fbc5e21231d1c72789406aa590bb70fc6a8114f2cd1이다. checkpoint 연결5,731bytes는2ef536c53e0e2a82df44f0917783cf7f9fcd67e8d5dcd3d28d17d458c5285078이다. 변경한 Closing11,267bytes는cd386dba0aef5f55a31cf221bf5cf524da67c97b5973bced5f3aacf6a386b961, 시험15,532bytes는668d3b1c1642ef3e6d9bde7208ba6d8b978139258ead3c53fc8b00c51796ef15다. 이 조건 검사는 합성 Native/IO/Job을 포함하며 제품 실행 증거가 아니다.

수정본의 실제 `--connect-only`는312fresh/final312·58.548372초·helper64·cleanupTrue다. 전체3,346개=현재2,927개+보존419개를 명시 선언했고 관측 입력 union은 없다. 원 모델+준비15초554.674899/600초는 완료 보장이 아니다. 원 자원 표본115개와 CPU 판정115개가 일치하고 중단/경고는0이다. 기존 콜백 요청 중 준비 중복36,600회를 합쳤다. 연결의 원 준비 확인 호출1,445,302회는 캐시된 같은 guard 확인을 포함한 논리 호출 수이며115개의 실제 표본과 혼동하지 않는다. Native checkpoint/부모 실행·Job·Frame·worker·제품·종료guard/oracle는0이다. 실제 Native 또는 전체 새 바이트 경계는 이번에 실행하지 않았다.

자격 기록은 `p09-361-case165-native010-dispatch-qualification001.v1.json`(88,787bytes/SHA2569d9c65d027b518316e26d32af8a2c8a5b50728a35efb7940f040a5a6bf9dea9c)이다. 실제 dispatcher의 읽기전용 `admit_qualification`도 호출해 현재 코드·시험·구성 기록·실패 원본·이전 worker 자격26개를 전후 읽어 일치시켰고 cleanupTrue였다. 발행 때문에24/22/9계약·312구성·기존 실제 EOF worker·전체감사를 반복하지 않았다. 이전 worker/launch/EOF의 변경 없는 범위만 재사용하며 수정 전 parent/Closing 자격을 현재 소스 자격으로 간주하지 않는다.

다음은 별도 권한을 받은 case165 Native010 제품 시험1회다. 제품 모드에서는 자격 기록을 현재 입력 한 개로 명시 추가해 실제 비용과 전체 범위를 다시 계산하고 원 전체 시작/종료·10초 capture·둘째 입력 경계·Frame commit·전체 독립 판정을 통과해야 한다. 새 제품 실행 승인은 아직 없고 canonical/intent/제품 결과는 부재다. 이전 Native008/009와 실패 원본의 재실행·자동 재시도는 금지한다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE·기존 CPU/RAM/IO/시간 보호·PC프리즈해결미확정을 유지한다.

### 제품 종료 뒤 원 자원 검사 연결

원 실행기의 `write`는 `c.run`의 Job 정리가 끝난 뒤 같은 Windows sampler를 사용하는 `post_guard`를 `owner.checkpoint_io`에 설치한다. 원 metadata pressure의 복구된 reader에는 이전 `guarded`가 남는다. 새 batch commit의 자원 검사까지 기존 Handoff만 따라가면 그 옛 closure를 호출할 수 있다. 원 `conservative_maintenance.observe`는 참인 Job 값이 남아 있으면 accounting을 조회하므로, 이 연결은 제품 성공 후 종료 확인을 실패시킬 위험이 있다.

`batch_post_job_checkpoint.py`는 기존 Handoff의 opt-in 하위 클래스다. 전체 고정 실행기23,159bytes/SHA2566f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713을 실행하지 않고 compile해 원 writer/post_guard/sampled 코드 형상을 확인한다. metadata pressure의 원 복구와 실제 같은 context·Frame·owner·Windows instance·deadline, 원 writer의 완전한 제품 capture와 positive cleanup을 확인한 경우에만 원 post_guard를 그대로 호출한다. 그 전 준비/Native 검사는 기존 Handoff에 전달한다. 원 클래스/실행기·표본0.5초·CPU/RAM/commit·720/600초·실패 latch와 정리 경로를 바꾸지 않는다. 코드 형상은 최초 결합 때 확인하고 이후에는 같은 코드 객체인지 확인한다.

새16계약은 원 writer/post_guard/sampled 바이트코드를 합성 Job/IO/Frame 환경에서 실행한다. 이전 연결은 옛 Job 검사 sentinel 실패로 STOPPED_NOT_ACCEPTED가 되고, 새 연결은 원 post_guard와 sampler를 따라간다. 원 deadline·자원 실패·재귀·변조·다른 owner/Frame/context·잘못된 복구·callback 재사용 거부도 확인했다. 기존 Handoff20계약을 새 하위 클래스에 적용해 합계36 PASS,6fresh/final6·cleanupTrue·process0이다. 이것은 실제 OS의 닫힌 Job 조회나 실제 Native Frame/제품 성공 증거가 아니며 과거 PC 프리즈 원인으로 확대하지 않는다.

첫 합성 시험은 정규식 모듈을 fixture globals에 넣지 않아 예외 처리에서12개 오류가 발생했다. 원 시험10,206bytes/SHA2569b3201ba282e4557e8d3dd4f471682cf241e9b815c65a4cb2c25ac69196916ea를 보존하고 fixture에 re만 추가한11계약을 통과한 뒤 위 negative/inherited 범위까지 확장했다. 현행 adapter8,140bytes/SHA256c8e57c6a09b8b144f8d8832ea1527b1f965e801dca8206b6c34e15996f79c3f3, 시험13,099bytes/SHA2560dbe3c512858622f509e89f5a0e693bf4f6dd14bb7c702bfb4bfff7e83c4f5dc다.

실행기는 이 dependency를 현재 입력에 명시하고 새 Handoff를 lazy reader 구성 전에 만든다. 현행 실행기24계약과 준비9계약을 확인했고, 변경하지 않은 Closing22계약은 이전 자격의 원 source pins와 함께 재사용했다. 원 worker/launch/EOF와 과거 전체 감사·통과 제품은 반복하지 않았다. 실행기23,931bytes/SHA256c98a4c734cdd7293fc8fbe6225480b0746d300df95944d65a366788f3e910a99, 시험17,173bytes/SHA2568ae8905e50a6aa95bb69fd0f1a94f7d42b6f84fbb4c13a8db85819d1fbdee5fc다.

첫 비제품 구성은313fresh/final313·58.458772초에 통과했다. 이어 만든 자격002는 root의 Closing22 결과 대신 같은 이름의 재현 명령 문자열을 선택한 기록 오류로 실제 admission이 거부했다. 이84,603bytes 원본(SHA256766a38b6c288755eebef08599a4133fd31c5d08368511aa44c0dbd188de849e8)은 덮어쓰지 않았다. 자격003을 가리키도록 변경한 실행기와 시험을 확인하고 비제품 구성을 한 번 새로 확인했다. 현행 구성은313fresh/final313·60.578107초·helper64·cleanupTrue이며 원 표본119개·경고/중단0이다. 선언전체3,347=현재2,928+보존419, 원모델+준비15초554.754977/600초는 실제 전체 바이트/Native 완료 자격이 아니다.

현재 자격은 `p09-361-case165-native010-dispatch-qualification003.v1.json`(86,403bytes/SHA256dcba93bf121aee655a78ff98c15b620996d0d6b437bd79d2a0186b0bdce51d33)이다. 실제 실행기의 읽기전용 admission과 현행 code·이전 자격·실패 기록·정확한 preimage33개 전후 일치·cleanupTrue를 `p09-361-case165-post-job-qualification-review001.v1.json`에 보존했다. 발행 때문에 구성이나 계약 시험을 다시 실행하지 않았다.

실제 Native/Job/Frame/worker/GO/제품 실행과 수용 증가 모두0이다. 다음은 별도 승인을 받은 Native010 case165 제품 시험1회이며, 자격003을 현재 입력 한 개로 추가한 비용/전체 경계와 원10초 capture·둘째 입력 경계·Frame commit·묶음 종료감사·독립 판정이 남는다. 자격은 실행 승인이 아니며 Native008/009 재실행·자동 재시도는 금지한다. 공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·목표ACTIVE·PC프리즈해결미확정을 유지한다.

### 캡션 화면 문제의 대조 문서 준비

기존96DPI 전체 페이지 이미지에서 사각형은 번호/문구만 보이고 수식 캡션은 좁게 여러 줄로 배치된다. 새 PDF render나 한글 실행은 하지 않았다. 이미지 해시는 이번 관측에 묶었지만 기존 PNG를 원 PDF와 새로 재현한 identity 증거 또는 calibrated render 판정으로 삼지 않는다.

원 seed·numbered 입력·saved·reopened의 사각형/수식 layout 속성을9fresh/final9·cleanupTrue로 확인했다. 사각형 curSz는10800×5400에서 저장 후0×0이지만 원 P08 trace에 output 해시가 묶인 정상 OBJ-001/019 readback도0×0이다. 따라서 curSz만으로 원인을 설명하지 않는다. P09 사각형 seed에는 P08 참조의 lineShape/shadow가 없으며 P09 저장본에는 매우 큰 lineShape width1485632276이 관측된다. 이것은 source 표현/모양의 차이이며 번호 삽입의 독립적인 인과 증거가 아니다.

P08 참조 비교는4fresh/final4·cleanupTrue다. P08 OBJ-019 input은fb85ed1ee72c98f24e81009c55d32d3be340c42c3fe308d3c17819ce28e1ef55로, P09 seed659b31bc1f5f86ee46756ea683258e03ba75515179af2f5377a953a108eafbf7와 다르다. 그러므로 그 PDF를 동일 입력의 baseline으로 대신 쓰지 않는다. 수식에는 원 caption seed의 width1200/fullSz0을 복사했고 equation sz2230이 유지되며 saved/reopened lastWidth가2230이 된다. 폭/배치 상속도 아직 원인 후보이며 폭 수정의 target 결과는 없다.

`prepare_caption_isolation_controls.py`는 보존된 번호 입력에서19 제어 하나만 역변환한다. 원 manifest42a9d18eb18dac2d34185297fb8cf0b18b10658e3e5b327839a14c770fb22a48의 삽입 전 section 해시와 정확히 같아야 하며, 원 사각형의 NONE→PICTURE와 수식의 캡션 복사 외에는 원 source와 일치해야 한다. 이는 대조 fixture 준비이며 제품 번호 삭제·캡션 생성 API가 아니다. ZIP은 새 파일에 결정적으로 작성하고 모든 비section expanded parts를 보존한다. 기존 원본·qualified Rust와 실행기/자격은 바꾸지 않는다.

순수9계약은 원 해시 불일치·번호 누락/중복·잘못된 cache·활성 XML·선언 외 source 변경·미지원 case·archive 경로 이탈·자원 중단 전파를 확인했다. 실제 준비는12fresh/final12·2.510165초·cleanupTrue·process0이며 시스템 CPU최고9.78%·자체최고0.193225%·private최고14.645MiB·가용RAM최저36.118285%·commit최고52.737516%다. 이 다섯 표본은 이번 작은 준비의 관측이며 PC 프리즈 해결 증거가 아니다.

새 고정 폴더 `fixtures/target-build/p09-19-caption-isolation-controls-20261017-01`에는 다음 두 대조 문서와 `control-manifest.v1.json`만 발행했다.

- 사각형7,775bytes/SHA256c49a98ae95bf2d88cca4fd7d389dc1f1c118809a35250314665816b497d6fd3b. 원 삽입 전 section은bc019f02ba25bd5a01b03b6fa9c18d9b6d0ddb0b267e20046ab31c7b27abea20.
- 수식12,331bytes/SHA256194af7b1b9f99a5178253c2b24af52b47cda5ec3fbbfdbd70d8217f005ba6df8. 원 삽입 전 section은c49ae42162153432e307ecb3726a2cc7ff733a956d002b8ecc491ed910ca8ea3.

전체 원 숫자형/관측·계약·명령과 준비 결과는 `evidence/p09-361-caption-render-isolation-preparation001.v1.json`에 보존했다. 두 대조 문서는 아직 한글에서 실행하지 않았고 semantic/render/differential/green은 미자격이다. 별도 승인된 exact-target 검증에서 번호 입력과 비교해야 번호 삽입 효과를 분리할 수 있다. Native010 case165의 제품1회 승인도 아직 없으며, 이번 준비는 그 실행이나 재시도 권한이 아니다. 공식158/249·잔여91·P09/A12/A13 OPEN·P10미시작·목표ACTIVE를 유지한다.

### 승인된 Native010 시도의 중단과 자원 분석

사용자의 `Native010 1회 실행 허용` 응답에 따라 현행 실행기의 제품 모드를 정확히 한 번 실행했다. 이 승인은 원 CPU/RAM/입력 보호를 유지하고 Native008/009 재실행·자동 재시도·한글 접근 허용 검증을 제외한다. 실행기와 자격003을 변경하거나 이미 통과한 계약 시험을 반복하지 않았다. 실제 구성318fresh/final318을 거쳤고 전체 선언은3,348개=현재2,929개+보존419개다. 묶음 시작 단계는 다음 Native 단계로 진행했으나 실패 경로에는 완전한 시작 바이트 통계가 반환되지 않았으므로 선언 수를 실제 바이트 감사의 요약으로 대신하지 않는다.

입력 잠금 중 기존 단일 자원 표본에서 전체 CPU90.62%를 관측했고 원90% 획득 경고가 일방향 중단을 걸었다. 원 상태는 DEFERRED_NOT_STARTED, 중단 사유는 STOP_NATIVE_OPEN_AFTER_HOST_SATURATION이다. 실행기 전체544.729372초·원 Native160.46초이며 worker_created/job_assigned/writer_authorized는 모두false, process creation0·제품 본문 관측false·완료 바이트 경계0이다. Job 종료 후 검사 연결은 이번에 실행되지 않았으므로 실제 자격으로 승격하지 않는다.

원308표본의 검증 부모 CPU는 최고2.668585 machine%·private최고73.230469MiB다. 전체90.62% 표본에서 부모 CPU는0%였고 가용RAM은25.757372%·commit은56.596545%였다. 전체 표본의 가용RAM최저25.451060%·commit최고56.596545%로 메모리95% 중단은 아니다. 검증 부모가 직접 전체 CPU를 소모한 설명은 이 표본으로 지지되지 않지만 파일 검사에 따른 간접 유발과 당시 외부 점유 주체는 아직 미확정이다.

관련 획득 checkpoint·속도 제한·읽기 코드를 재검토했다. 원 단일 sampler를 재사용하고 중단 latch 뒤에는 재개하지 않는다. 속도 제한은 실제 sleep과 그 전후 보호 검사를 쓰며 busy loop가 아니다. 잠금 중단까지94.562389초 중 요청 대기89.844762초이고 metadata 검사1,294회는 합계0.060691초였다. 이미 bound된 pin은 해당 snapshot을 재사용한다. 이 경로를 더 빠르게 만들기 위해 보호 검사·입력 잠금·실제 바이트 확인을 제거하거나 속도 상한을 높이지 않았다. 추가 envelope/wrapper도 만들지 않았다. 실행기/제품 소스와 Windows/Defender 설정은 그대로다.

원 Frame은 CLOSED이고 핸들1,294개 모두 닫힘·잔여0·활성 reader/byte stream0·cleanupTrue·소유 프로세스 트리 비어 있음을 확인했다. 중단 후 다른 Python/Git 활동이 관측됐고 한 Python의 부모 chain은 pwsh→Codex였지만 프로젝트 식별은 확정하지 않았다. 별도 시점의 전체CPU26%·Defender0.94%를 중단 시점의 원인이나 무관함 증거로 소급하지 않는다. 다른 프로세스를 종료하지 않았다.

불변 원 기록은 `p09-361-case165-current-runtime-run010.v1.json`(2,312,978bytes/SHA256b617ea54f3c4ffa2a4317cde0772a45fc77d6763409b99bcd377d2b516c67d63), dispatcher 결과는 `p09-361-case165-native010-product-dispatch001.v1.json`(81,022bytes/SHA25667e7de0841f6e9c2b53296e470bd0c92c2af05a2ea08d4a737699ce41b5bff61)이다. intent001(2,416bytes/SHA25672e97ae43aaf17e00faf86dfef1dc86cc2ed31310cf9c2c55e285bc6b184a1f0)은 소비됐다. 첫 사후 읽기전용 검사는 준비75% 지속 압력으로 중단됐고 시스템26% 관측 후 새 진단 읽기는1fresh/final1·cleanupTrue로 완료했다. 이는 제품 재시도가 아니다. 분석은 `p09-361-case165-native010-terminal-review001.v1.json`에 보존한다.

공식158/249·잔여91·next165·P09/A12/A13 OPEN·P10미시작·PC프리즈해결미확정이다. 기존 목표 도구의 조회 상태는 blocked였고 이번 제한된 실행 승인을 ACTIVE로 자동 치환하지 않았다. Native010은 다시 실행하지 않으며 새 제품 시도에는 별도 식별자와 권한이 필요하다. Native011은 승인되지 않았다. 남은 원 제품10초 capture·두 입력 바이트 경계·Frame commit·묶음 종료감사·독립 판정은 이 중단으로 통과하지 않았다. 위 절의 승인 대기/산출물 부재는 실행 전 이력으로 보존한다.
