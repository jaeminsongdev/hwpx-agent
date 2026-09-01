# 용어집

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


- **HWPX**: XML 파일이 ZIP package를 이루는 OWPML 기반 한/글 문서 형식.
- **HWP**: 한/글 binary 문서 형식. 제품 canonical이 아니며 import/export backend를 통해 처리.
- **OWPML**: Open Word-Processor Markup Language, KS X 6101.
- **DocumentGraph**: 문서 의미·리소스·레이아웃·검토·보안을 표현하는 내부 IR.
- **OperationPlan**: stable capability와 selector로 구성된 원자적 편집 계획.
- **Capability**: 사용자 관점의 한 가지 의미 기능.
- **Binding**: 특정 backend/build에서 capability를 실행하는 concrete action/XML mapping.
- **TargetProfile**: 한/글 제품/build/OS/locale/font/driver/catalog 묶음.
- **DirectHWPX**: HWPX package를 직접 parse/write하는 Rust backend.
- **Desktop Automation**: Windows에 설치된 한/글의 공식 automation API 경로.
- **WebHWP**: 웹한글 기안기/관련 웹 API를 사용하는 선택 backend.
- **Oracle**: 실제 한/글에서 open/save/render/export하여 호환성을 판정하는 검증 backend.
- **Surgical preserve**: 수정되지 않은 package/subtree를 최대한 그대로 유지하는 편집 모드.
- **Opaque bag**: 해석하지 못하지만 round-trip을 위해 보존하는 XML/part/attribute.
- **Evidence**: 검증 실행과 결과를 재현할 수 있는 immutable 기록.
- **Native equation**: 한/글 수식 편집기로 다시 편집 가능한 equation object.
- **Semantic diff**: bytes가 아니라 문서 객체/속성 의미 단위의 차이.
