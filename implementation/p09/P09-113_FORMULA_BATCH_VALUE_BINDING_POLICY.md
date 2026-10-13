# P09-113 — 실제 필드 위치에 따른 계산 결과 대응

## 제품 경로와 권위 경계

P112의 실제 source import → field ranges → meanings → original math → preserving patch/writer →
whole candidate re-import 경로를 유지한다. 호출자가 map/value/offset/raw XML/권한을 주입하는 새 경로는 없다.
이번 변경은 같은 경로의 다중 표·다중 구역 결과 검증 오류를 수정한다.
전체 field compiler/product envelope/durable issuer/atomic publication/native 검증은 여전히 미완료다.

## 결함과 수정 조건

source anchor/LogicalId는 정확한 한 source version에만 유효하다. source package/part/span hash를 포함하므로
계산 결과 leaf가 달라지면 표 anchor hash와 BTreeMap 순서도 달라질 수 있다.
이 순서의 두 values vector를 zip하면 서로 다른 표의 같은 좌표를 비교하거나 정상 출력을 잘못 거부한다.

원래 field importer가 실제 spine/element 위치로 정렬한 paired range를 사용하며 다음을 검증한다.

- 각 원본/출력 anchor는 자기 source package에서 독립적으로 resolve되어야 한다.
- begin/end/parameters의 실제 part path와 XML element index가 같아야 한다.
- native kind/begin ID/header/end attributes가 같아야 한다.
- 각 버전의 range reference ID에 대응하는 계산값과 owner coordinate가 같아야 한다.
- 원래 AST/format/grid/출력 Unverified cache 및 whole package expected leaf-edit 바이트 검사는 그대로 수행한다.

정규화된 inline ordinal은 identity로 비교하지 않는다. 빈 result text를 채우면 원래 TextFlowReader의
빈 text atom이 실제 text atom으로 바뀌어 ordinal이 합법적으로 달라진다.
실제 range 요소 위치 및 선언된 result leaf 외 전체 바이트 동일성은 반드시 유지한다.
이는 native 보호 승인이나 metadata 의미를 추정하는 것이 아니다.

## 검증 자료

immutable P77 actual36 manifest/type/bytes/SHA 입장을 그대로 사용한다.
실제 첫 표는2행4열8cell, original formula owner D2임을 관측한 뒤 in-memory derivative만 만든다.
A1 numeric, B1=D2+1, D2=A1+1의 actual native tuple와 original AST serializer로 의존성을 연결한다.
다른 구역의 표도 source-derived OPF item/itemref/name/namespace context와 기존 package closure로 구성한다.
이 자료는 native 한글에서 새로 저장한 capture가 아니라 파생 검증 자료다.

여러 구역에서 값이 다른 경우, current/changed 섞임, closed/self-closing empty result, 보호된 current/changed
필드, stale source, invalid numeric dependency를 검사한다. writer 한도·원래 parser·ID sentinel 규칙을 바꾸지 않는다.
원본·실패·private 증거 및 사용자 dirty는 유지하며 PLANS.md는 재생성하지 않는다.

## 다음 경계

original full operation compiler/product envelope와 batch source result의 권위 있는 연결,
fresh authenticated stored multi-section consumption, durable integration/issuer/publication,
native save/reopen/render/differential 의미 검증이 남는다.
최소6 coarse 잔여 묶음 중 이번에 닫힌 묶음은0이다. P09 Gate/A12/A13 OPEN, native34 NOT_RUN,
P26 failed_semantic_non_green, P62/P84_SQL UNRESOLVED, product false/no P10/전체 목표active를 유지한다.
