# 아키텍처 결정 요약

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


1. **Rust control plane**: 스키마, IR, transaction, state, policy, router, validation을 Rust가 소유한다.
2. **HWPX canonical**: 저장·교환 기본은 HWPX, HWP는 automation/export capability다.
3. **다중 백엔드**: Direct HWPX, Desktop Automation, WebHWP, Oracle을 병렬 제공한다.
4. **Capability Registry**: 버전별 지원 정보를 데이터로 관리하며 코드·문서·테스트를 생성한다.
5. **세 편집 모드**: normalized authoring, surgical preserve, native automation.
6. **Semantic OperationPlan**: LLM은 의미 연산만 만들고 backend binding은 서버가 결정한다.
7. **Native equation**: EqEdit 기반 편집 가능한 수식이 필수이며 silent raster fallback을 금지한다.
8. **Immutable revision**: 원본을 변경하지 않고 content-addressed artifact와 revision DAG를 사용한다.
9. **Evidence-based validation**: schema 통과, reopen, semantic compare, render, real-Hancom oracle을 구분한다.
10. **Version-scoped parity**: 특정 한/글 빌드와 공식 자료 버전을 고정해야만 parity를 선언한다.
11. **License gate**: 상업 오토메이션 승인을 production 선행 조건으로 둔다.
12. **Standards-first plugin UI**: MCP Apps bridge가 기본, ChatGPT 전용 API는 feature detection 후 사용한다.
