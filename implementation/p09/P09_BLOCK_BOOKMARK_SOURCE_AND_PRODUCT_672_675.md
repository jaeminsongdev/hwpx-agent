# P09 블록 책갈피 원본과 제품 읽기 모델

2026-10-25. P09/A12/A13 OPEN, 31개 closure 묶음/65기능과 official249의158수용·91대기·next165는 유지한다.670은 소비된 성공 시험으로 재실행하지 않는다. 새 P10 구현은 시작하지 않는다.

## 완료된 Native670 source capture

[670 최종 영수증](evidence/p09-361-block-bookmark-source670-native001.v1.json)은 `CAPTURED670_FIXED_BLOCK_SOURCE_PRODUCER_BOUND_SEMANTICS_UNQUALIFIED`, source_capture_executed=true, cleanup=true다.141370바이트·SHA `eb475304ebc05fabd77a84dc46b0b780dafea98cc864bc55f0c5774220b53b7d`를 확인했다.55요청·두 owned session·고정8범위·16회 좌표와 텍스트 재확인·최종 source324/324·image1/1·shell1/1·runtime2/2가 닫혔다.394.172초·CPU 최고36.91%·가용 RAM 최저47.4301%이며 자원 보호 중단이 아니다.

668이 관측한 문단별 실제 시작점은 첫 문단 `[0,0,16]`, 나머지 문단은 `[0,index,0]`이다. 고정 숫자를 더하는 대신 각 문단에서 관측한 시작점으로 변환하는 방식이 이번 실제 source capture에서 동작했다. 원래650/655/660/664 실패 기록은 보존한다.

## 실제 XML 결속673

[673 readback](evidence/p09-361-block-bookmark-source673-readback001.v1.json)은 source12/12·12개 검사·cleanup=true,9.516초·CPU 최고16.16%·가용 RAM 최저48.5975%다. 기존 Native는 재실행하지 않았다. 두 HWPX에서 각각8개의 이름·논리적 범위·선택 텍스트와 producer를 확인했고 저장·재열기 후 동일하다.

| 항목 | 관측한 source profile |
|---|---|
| 시작 | `hp:ctrl/hp:fieldBegin`, `type=BOOKMARK`, source `name` |
| 블록 parameter | `hp:parameters cnt=1 name=''`의 유일한 `integerParam name=Prop`, 값2 |
| 끝 | `hp:ctrl/hp:fieldEnd` |
| 결속 기준 | `fieldBegin.id`와 `fieldEnd.beginIDRef` |
| 주의 |8범위가 같은 `fieldid`를 공유하므로 `fieldid`를 고유 ID로 사용하지 않음 |
| 선택 내용 | 고정 ASCII·공백·한글·XML 특수문자·혼합문자 등8범위의 정확한 텍스트 |

created.hwpx는17331바이트·SHA `aa0ae8f3042a0b3be43733deb0196488bdd1bac14e6025f7785915cca5660076`, reopened.hwpx는17269바이트·SHA `783ee3372fe44d8c9b6f6f6e65b5088226ea11ac920f97c76915b4c1181b6699`다. 원본은 private 폴더에 유지한다. 공개 영수증에는 원문 이름·텍스트 대신 해시와 제한된 구조 값만 남겼다.

## 제품 코드674와 검증675

`crates/hwpx-package/src/document_import/fields/block_bookmarks.rs`는 기존 전체 source field-range 검사와 최적화된 cached-inline 분석을 한 번씩 재사용한다. 새로운 point marker를 가정하거나 `fieldid`로 연결하지 않는다. 기존 필드의 정확한 시작·끝 source anchor, 문단 ID, source 이름과 선택 내용 관측을 결속한다. 중복 이름은 ambiguous로 유지하며 이름을 정규화하거나 첫 결과를 택하지 않는다. 새로운 import 객체는 역직렬화나 실행 권한을 제공하지 않는다.

오류 메시지와 Debug는 이름·텍스트를 숨긴다. 한도 초과, 다른 parameter profile, 구조화된 선택 내용은 명시적으로 거부한다. 이 첫 profile 외의 블록 구조를 지원했다고 주장하지 않는다. `verify_source`는 fresh bytes로 전체 원본 fields를 재구성한 뒤 파생 inventory를 비교한다. 기존 POINT authoring의 Content 거부 경계는 바꾸지 않았다.

675의 최초 product001은 테스트의 `ReferenceAuxiliaryLimits::default()` 생성 오류(E0599)로 테스트 실행 전 중단됐다. 제품 라이브러리 컴파일은 통과했지만 제품 검사 PASS는 아니었다. product002는 보관 사본의 끝에 추가된 LF1바이트 때문에 정확한 전체 파일 대조에서 중단됐고 compile/test는 실행하지 않았다. 두 실패와 사본은 유지한다. 후속 검증은 원본 길이·SHA로 원본 모든 바이트를 확인하고 추가 LF를 별도 구분한다. 검사 조건이나 제품 결과를 완화하지 않는다.

product003에서 실제 두 Native 파일의 블록8개씩 읽기·선택 텍스트 해시·fresh source 재구성을 포함한10개 검사는 통과했다. 나머지1개는 잘못된 parameter가 원래 forms importer에서 더 일찍 거부된 것을 테스트가 오류로 전파한 fixture 문제였다. 제품 라이브러리는 변경하지 않았다. 실패 기록과 해당 코드도 보존한다.

[675 product004](evidence/p09-361-block-bookmark-import675-product004.v1.json)은 기존 통과10개의 source 동일성을 확인하고 실패한 fixture1개만 수정·실행했다. 고유11조건·source907/907·실행 파일과 dep-info2final·cleanup=true다.128.469초·CPU 최고38.28%·가용 RAM 최저47.3422%다. actual670 두 파일의8범위씩은 제품의 원래 forms/fields importer와 새 block inventory를 통과했으며 선택 텍스트의 UTF8 해시·길이와 source 재구성이 일치한다. Native/기존 통과10조건/249 대기열은 재실행하지 않았다. 상태는 `QUALIFIED675_PRODUCT_BLOCK_BOOKMARK_SOURCE_IMPORT_NOT_AUTHORING_CONTENT_OR_F11`이다. source 읽기 모델 완료이며 저장 서비스/authoring/Content 양성 완료가 아니다.

## 다음 P09 작업

블록 target을 source 참조 인벤토리·공통 선택/권한/현재 head 경계에 연결하고, 원본 범위를 보존하는 제품 작성 경로와 블록 Content 양성을 검증해야 한다. POINT 책갈피 결과, 블록 원본 확보, source 읽기 모델을 전체 CROSSREF·F11/P09 PASS로 승격하지 않는다. Native가 필요 없는 다음 구현은 계속 진행하며, 새 외부 실행이 필요해지면 명령을 안내하고 사용자 조건부 지시대로 일시정지한다.
