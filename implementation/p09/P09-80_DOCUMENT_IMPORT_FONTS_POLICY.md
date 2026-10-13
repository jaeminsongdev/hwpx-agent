# P09-80 원본 글꼴 선언·7개 언어별 문자 참조 정책

## 목적과 범위

원래 `CharacterStyleCatalogReader`가 읽은 글꼴 선언을 변경하지 않고 원본 `Contents/header.xml`의 정확한 위치에 연결한다. HANGUL/LATIN/HANJA/JAPANESE/OTHER/SYMBOL/USER 각 공간의 native ID를 독립적으로 다루고 모든 실제 `fontRef` 언어 축을 연결한다. 원본 이름·type·embedding flag·binary reference·substitute·typeInfo는 선언 데이터다.

이는 글꼴 설치·가용성·대체 선택·embedded binary 해석·글꼴 메트릭·한글 레이아웃/렌더 또는 실행 승인이 아니다. 원본에서 누락된 값이나 플랫폼 기본값을 만들어 넣지 않는다. 일반 글꼴 설치 및 시스템 설정 변경은 범위 밖이다.

## 보존과 실패 경계

- 원래 source/XML/character reader/catalog/field/body/security 검사는 그대로 사용한다. count/ID/namespace/duplicate/missing/dangling 오류를 opaque 성공으로 바꾸지 않는다.
- immutable source anchor와 원래 typed font ID/language가 정확히 일치해야 한다. 다른 언어의 같은 숫자 ID는 같은 논리 글꼴이 아니다.
- 완전한 원본 source graph를 보존하고 선언·참조만 추가한다. 추가 font styles/character links 및 stage metadata를 제거하면 원래 catalog graph 전체가 동일해야 한다.
- work 8,000,000과 evidence serialization 16MiB의 유한 한계를 유지한다. 원본 readers/graph의 기존 한계도 유지한다.
- fresh 검증은 원래 전체 source/catalog 검증과 선언·참조·전체 graph·receipt 재구성의 동일성을 확인한다.
- 저장 서비스는 원래 실제 read scope/tenant/subject/project/branch/document/head/ACL/quarantine/AEAD/source 검사를 전후 유지한다. 반복 읽기를 atomic CAS나 DB 잠금으로 주장하지 않는다.
- 새 profile/scope 각각 단독으로도 full-document context 승격을 거부한다. caller JSON, 공개 raw XML/action, signed route 또는 publication 권위는 추가하지 않는다.
- receipt/debug에는 실제 글꼴 이름·substitution 값·문서 본문을 내보내지 않는다. API의 typed declarations는 원래 데이터이며 실행 지시가 아니다.

## 증거 분리

잠긴 기존 실제 문서36과 별도 메모리 파생 negative/embedding-declaration 사례를 구분한다. 파생 파일을 원본에 쓰거나 native positive evidence로 세지 않는다. 글꼴 source 성공을 전체 importer/정책/scanner/issuer/lineage/manifest/publication/lifecycle/native/P09 Gate PASS로 승격하지 않는다.

현재 메모 진단에서 같은36에는 MEMO body/style/hiddenComment 양성 사례가 없고 section memo 참조44만 있다. 이를 메모 의미 처리 성공으로 세거나 작성자·시간·표시·해결 상태를 추론하지 않는다.

## 사용자 지시

한글/COM/UI/native dispatcher/접근허용은 실행하지 않는다. root `PLANS.md`는 사용자의 명시적 삭제 요청에 따라 부재를 유지하며 재생성하지 않는다. 삭제 전45435 bytes의 정확한 원문은 `source-archive/p09-80-pre-source-fonts/PLANS.md`에 보존한다. 역사적 source receipt/guard는 수정하지 않는다. 원장 갱신 의무는 이번 단계의 report/receipts와 나머지 제품 문서에 적용한다.
