# Formula result source-position binding v0 → v1 (P09-113)

Public field/result API 및 기존 저장 DB/schema/권한 모델은 변경하지 않는다.
기존 readback의 hash-sorted value-vector zip을 원래 source-sorted field range와 실제 part/element 위치에 따른
버전별 계산값 대응으로 바꾼다. 원본 source anchor는 출력 버전에 재사용하지 않는다.

native kind/IDs/header/end attributes, actual begin/end/parameter 위치, math 값/좌표, 기존 AST/format/grid,
Unverified cache 및 exact whole expected leaf bytes를 검증한다.
빈 결과를 채울 때 합법적으로 변하는 normalized inline ordinal을 지속 identity로 취급하지 않는다.

출력은 여전히 immutable candidate일 뿐 execution/publication/issuer/native permission이 아니다.
재승인되지 않은 native/SQL/product/Gate는 여전히 unverified/NOT_RUN/UNRESOLVED다.
원래 실제 자료·private locks/실패 증거와 P00~P08/사용자 변경을 보존한다.
