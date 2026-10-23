# P09 원본 폰트 참조 치환 계약

`hwpx-agent.source-font-reference-replacement/v1`은 SEARCH-024의 원본 편집 기반이다.
입력은 원본 불변 수입 객체, 전체 fresh 원본 바이트와 언어/from_native_id/to_native_id 매핑이다.
같은 원본·언어의 기존 선언만 허용하며 외부 폰트 파일, 새 선언, caller XML이나 실행 영수증은 받지 않는다.

## 적용과 보존

매핑은 원본 참조에 동시에 적용한다. 중복 source 매핑은 대상이 같아도 거부한다.
자기 자신 매핑은 NoChange, 모든 매핑에 해당하는 참조가 없으면 NoMatches다.
최대128개 매핑과4096개 변경 참조를 허용하며 한도를 넘는 부분 후보는 반환하지 않는다.
현재 구현은 공유 charPr의 fontRef 전체를 대상으로 한다. 이름 검색·정규식·스타일 필터·
SearchScopeSelector·preview_only를 대신하지 않으며 이 기능들을 지원한다고 표시하지 않는다.

원본 전체 바이트 일치와 관측 보호 신호 거부, 기존 patch/writer를 유지한다. 별도 font-binary/v10은
shape/v6의 불변 규칙에 font/substFont 바이너리 참조만 추가하며 기존 프로필은 바꾸지 않는다.
출력은 한 번 재수입하고 기존 선언 및 전체 글자 모양의 기대값과 비교한다. 변경한 속성 값 밖의
header 바이트와 나머지 패키지 멤버를 보존한다. 선언된 바이너리 참조는 실제 manifest/비어 있지 않은
binary part와 결속해야 하며 누락·XML 또는 text/* 미디어·spine/infrastructure 대상은 거부한다.
보존용 합성 바이너리를 사용한24개 시험은 실제 폰트 유효성·설치·활성화나 Native 임베딩 지원 증거가 아니다.
[별도 ID 프로필 계약](p09-font-binary-id-profile-v10.md)을 따른다.

## 영수증과 권한

영수증은 원본/출력 package SHA, 원본/출력 font link 지문, 원본 영수증과 정렬된 매핑의 SHA,
변경 참조·글자 모양 수를 결속한다. 폰트 이름·XML·리소스 내용은 포함하지 않는다.
후보의 byte 전달은 writer 무결성만 확인한다. 저장 adapter는 현재 권한·ACL/head·격리/AEAD와
실행 자격을 별도로 확인해야 하며 이 후보나 영수증이 그 권한을 대신하지 않는다.

기존 API/프로필을 자동 이관하지 않는다. scope/name/fallback/Native/full-protection/execution
자격은 false다. 실제 제품 요청·통합 저장·target 증거와 P09 Gate는 미완료다.

검증과 다음 작업은 [진행 현황](../../implementation/p09/P09_FONT_REFERENCE_REPLACEMENT_PROGRESS.md)을 따른다.

별도 [이름·선택 범위 후보](p09-scoped-font-name-replacement-v1.md)는 기존 공유 정의를 수정하지 않고
복사본과 선택된 run/text 참조를 연결한다. 이 전역 매핑 API를 selector 지원으로 자동 승격하지 않으며
해당 경로의 현재 저장/전체 제품/Native 자격도 별도로 남는다.
