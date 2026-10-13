# P09-75 원본 point-bookmark anchor 가져오기 정책

## 지원 범위

실제 source XML의 HP namespace `ctrl/bookmark` 빈 point marker를 기존 P13 `bookmark_projection`으로 읽는다. 기존 projection/parser/typed lowering/domain name 검증은 바꾸지 않는다. 새 source-only envelope는 원본 name과 실제 wrapper/paragraph element 위치만 반환한다. native paragraph ordinal, 이름 normalization/대소문자 의미, native jump 권위나 내부 hyperlink parameters를 만들어내지 않는다.

원래 opaque wrapper node/common/type/resource/properties 및 paragraph ControlRef를 보존하고 `BookmarkAnchor`와 source-derived Reference를 추가한다. Reference.target_node_id는 이 marker의 실제 wrapper node이며 내부 링크 목적지가 해석됐다는 뜻이 아니다. marker/paragraph/inline stream 위치와 reference ID는 source package/document/part/span에 결합한다. 같은 name 또는 같은 XML을 가진 다른 source 위치도 서로 다른 source-local identity를 갖는다. 이 identity는 편집 후 지속/native-global identity가 아니다.

spine의 모든 HP bookmark marker와 typed 관찰의 anchor 집합이 일치해야 한다. 잘못된 parent/wrapper/attributes/nonempty marker/빈 이름/원래 XML 문자·name byte 한도 위반, 숨겨진 미표현 marker는 거부한다. foreign namespace marker는 opaque 원본으로 보존할 뿐 typed 책갈피로 승격하지 않는다. 기존 source/domain depth/node/reference/inline/string 한도는 유지한다.

## 이름 선택과 필드 연결

raw observed name을 있는 그대로 저장한다. whitespace/NFC/대소문자를 바꾸거나 native name business 규칙을 관찰 성공으로 증명하지 않는다. 이름 선택은 raw exact equality로 정확히 하나의 source 관찰이 있을 때만 허용한다. 없거나 두 개 이상이면 같은 redacted Selection error로 거부한다. catalog를 버리거나 임의의 첫 항목을 고르지 않는다.

기존 fields 의미 가져오기는 실제 source bookmark reference ID와 target wrapper를 별도로 확인하고 fields만 의미를 부착한다. 전체 reference 수는 source fields+source bookmarks와 정확히 일치해야 한다. source-derived 책갈피 외 임의 reference를 허용하는 완화가 아니다. 날짜는 Unsupported, 기존 HTTPS/수식 의미는 원래 profile 그대로다. 새 source BookmarkAnchor는 기존 run segments에 반영되며 native character position이나 렌더링 의미로 해석하지 않는다.

stored observed-name selection은 원래 `fresh_source`를 호출해 tenant/subject/project/branch/document scope/head/node/read ACL/scanner/quarantine/AEAD/digest와 whole source graph를 재확인한다. cached model의 scope 바꿔치기는 거부한다. 독립적으로 권한 있는 별도 provider의 신규 source 읽기와 기존 model 재사용을 혼동하지 않는다. READ audit 외 ingest/CAS/seal/commit/publication을 수행하지 않는다. 두 head reads는 atomic CAS/idempotency가 아니다.

## 증거와 실행 경계

현재 bounded metadata inventory에서 기존 P13 HP bookmark 문법 또는 BOOKMARK/CROSSREF field의 positive native 사례를 확인하지 못했다. 따라서 positive 증거는 **생성된 whole HWPX 패키지**에 대한 source import와 in-memory authenticated stored service 테스트다. 실제 HYPERLINK 캡처는 책갈피가 없다는 negative control일 뿐이다. native capture acceptance/한글 name lookup/내부 링크 형식과 동작/서명된 실행·제품 Gate를 증명하지 않는다.

새 `bookmark_import_profile` 또는 `bookmark_import_scope` 하나만 있어도 full product context를 거부한다. 다른 partial markers를 제거해도 typed anchor 관찰로 full importer나 native/security 권위를 승격할 수 없다. 원래 P13 static integration 및 P74 note native failures/P73 HTTPS·formula/P71 durable form evidence는 각각의 historical scope 그대로 보존한다.

다른 필드·참조·주석/catalog/security, 평가·승인, committed Source/Result/IR lineage/issuer/ExecutionManifest/publication/IR lifecycle/concurrency/crash/recovery/whole qualification/current admission/P62 cause는 OPEN이다. Goal ACTIVE/P09 Gate OPEN/no P10/full34 NOT_RUN/0green을 유지한다. 접근허용 금지 동안 Hangul/COM/UI/native dispatcher를 실행하지 않는다.
