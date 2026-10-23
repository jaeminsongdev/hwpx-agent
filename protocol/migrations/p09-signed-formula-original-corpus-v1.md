# P09 원본 결합 서명 수식 소비 corpus v1

P119 실제 Ed25519/AEAD/strict claims/current root/metadata/source/target/product 경로는 변경하지 않는다.
기존 P77 frozen input manifest의36개 원본을 읽기 전용으로 사용하며, 원본 경로/size/SHA를 기존
immutable loader로 검사한다. 원본 파일, P119 tests/guards/SQL/운영 설정은 재작성하지 않는다.

## 원본과 승인

서버/issuer/root/clock/metadata repository는 P119의 explicit synthetic test 구현이다.
실제 원본36 중 TableFormula16개/수식 없는20개/actual formula targets16/observed source-cell
bindings128을 각각 전체 검사한다. 원본 승인 데이터와 signing input은 기존 P118 validated record에서
생성하며 실제 Ed25519 및 기존 ArtifactService Evidence ingest/ACL/AEAD를 실행한다.

수식 없는20개는 policy/proof/결과를 만들지 못하며 initial artifact2/head만 유지한다.
수식16개는 현재 원본을 실제 재계산한 결과 모두 NoChange16/Changed0였다. 이는 기존 캐시를
권한으로 채택한 것이 아니라 original source evaluator 및 원래 보호 검사 뒤의 정확한 NoChange다.
이 관측을 실제 원본의 변경된 수식 결과 경로 또는 native recalculation 성공으로 확대하지 않는다.

## 전체 후보·보호·최신 승인

새 signed consumer 후보와 원래 direct source importer/evaluator/lowerer의 전체 후보를 비교한다.
압축을 푼 전체 part inventory를 대조하고, 변경된 section이 있으면 validated original spine/sec
역할과 namespace를 확인한다. 모든 원래 node 이름/parent/attributes와3개 결과 leaf 이외 bytes를
독립적으로 재구성·대조한다. 원래 scalar calculator는 공유하므로 별도의 독립 수학/native oracle는 아니다.
원본 corpus는 모두 NoChange여서 outside-leaf 변경 비교의 populated branch는 이 원본들에서
실행되지 않는다. 기존 P119 generated changed tests는 별도 범위로 유지한다.

각 실제 수식 원본에서 최신 승인 철회 후 prepared callback과 fresh prepare를 거부한다.
16개 current in-memory inputs는 이번 관측상 original과 같은 bytes며 새 원본16개로 세지 않는다.
각각 정확한 NoChange bytes/만료 시각 거부/새 정책 세대의 명시적 deny/old product 거부를 확인한다.
수식 원본16 및 current16의 in-memory cell-protect 변형32개는 유효한 allow 서명에도 product가 거부한다.
모든 경우 head 및 Result는 발행되지 않으며, candidate는 RAM에만 존재한다.

## 공개 증거와 다음 경계

receipt는 index/source digest/candidate digest/closed outcome/target counts와 component qualifier만
남긴다. 원문 XML/숫자/claims/key/서명/actor/문서명은 출력하지 않는다. 비교 실패도 byte vectors나
전체 원본 corpus를 로그에 덤프하지 않고 closed failure code/index만 출력하도록 새 테스트를 구성한다.

현재 시험은 역사적 frozen input의 signed SOURCE consumer/no-op/접근철회/보호 구성요소 범위다.
다음은16개 원본의 numeric input을 메모리에서 바꾼 actual-source-derived Changed 전수 경로와
독립 outside-leaf comparator의 populated branch를 검증한다. 운영 issuer/key custody/승인 registry/
실제 SQL/lease/idempotency/publication/CLI·HTTP/native/full document 의미/P09 Gate는 별도 미완료다.
