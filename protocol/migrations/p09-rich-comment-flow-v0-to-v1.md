# P09-108 rich comment Flow additive binding

이전 P93 및 stored comment 경로와 native/partial importer의 의미는 변경하지 않는다.
원래 parent source/test에 각각 신규 module declaration만 추가한다.
CommentOperationContext의 admission/selector/compiler/guards 또는 기존 테스트를 수정하지 않는다.

새 API는 완전한 caller-qualified graph/state와 명시적 body 전체를 받아 actual typed Flow
digest 및 정확한 root metadata view를 연결한다. native subList/plain cache digest와
같다고 가정하지 않는다. 일부 native 관찰값을 기본 author/time/coordinates로 채우지 않는다.
기존 caller request parsing/CommentBuilder 및 final graph compiler를 사용하며 삽입 시
final body metadata 반영 후 compiler의 target_graph_sha256을 새 최종 지문으로 갱신한다.

문서 본문과 review body를 혼합하지 않는다. 별도 disposable graph의 section append는
검증 전용이며 output graph에는 기존 main content를 그대로 보존한다.
body protection flag 검사는 보수적인 caller convention이며 native protection 판정이 아니다.
old graph/state/body/request의 stale binding은 fresh replay로 거부한다.

이 변경은 actual source/native/full product/durable SQL/issuer/atomic publication/Gate로
승격하지 않는다. 기존 route는 계속 unqualified다. P11 삭제 capability도 추가하지 않는다.
검증 실패의 source/실행 파일 및 원래 parent whole preimages는 별도 exact archive로 보존한다.
기존 증거와 원장은 재작성하지 않고 P108 보고서·evidence에 새 결과를 추가한다.
