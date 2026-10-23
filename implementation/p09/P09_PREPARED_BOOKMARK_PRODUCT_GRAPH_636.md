# 현재 책갈피 8종·24문서 제품/의미 그래프 읽기 — 636

## 확인한 범위

[audit005](evidence/p09-361-prepared-bookmark636-product-graph005.v1.json)은 현재 준비된 책갈피 4표시×hyperlink 2종의 Native initial/saved/reopened **24개 HWPX**를 실제 Rust 제품 경로로 읽었다. 새 Native/COM/문서 쓰기·접근 허용·소비된 실행 재시도는 0회다. 이전 통과 시험 전체를 재실행하지 않았다.

- `ReferenceValidationProductOperation::read_source_bookmark_crossrefs`: 현재 문서의 Command·표시 종류·hyperlink·정확한 대상 이름 해시와 source-local 책갈피 결속.
- `assess_package_source`: 대상/전체 Field 범위/지원 의미/계산 없이 읽은 표시 캐시. CROSSREF 표시 해시는 별도 XML 관측633의 결과와 일치했다.
- `ImportedDocumentFieldSemantics`: CROSSREF 의미와 제품 결속의 동일성, 실제 같은 문서의 책갈피 wrapper를 가리키는 그래프 edge, 전체 source/form/field/semantic graph 재구성.
- `DocumentGraph::from_json`: 각 의미 그래프의 canonical JSON 직렬화·재열기 후 전체 모델/직렬화 동일성.
- 각 조합의 initial/saved/reopened 사이에서 Command·대상 이름·표시 종류·hyperlink·표시 캐시 해시/UTF-8 길이의 의미 projection이 동일했다. 서로 다른 HWPX의 전체 byte/graph SHA가 같다고 요구하거나 주장하지 않는다.

원본에는 이미 `HYPERLINK` 필드1개가 있다. 새 CROSSREF만 골라 나머지를 무시하지 않았다. 원본 전체 필드 의미/캐시를 읽고, 현재 문서의 나머지 필드가 원본과 같은 native ID·종류·매개변수 fingerprint·typed meaning·표시 해시/길이·tab/line break를 유지함을24문서 모두 확인했다. run 분할 수는 표시 의미와 별개이며, 렌더/서식 보존은 아래 미검증 범위에 남는다. 비공개 URI/필드 값은 메모리에서만 비교하고 공개 결과에는 aggregate SHA만 남겼다.

| 검증 | 결과 |
| --- | --- |
| 현재 조합 / 실제 문서 | 8 / 24 |
| 실행 입력 fresh / final | 917 / 917 |
| 검사 실행 파일·dep-info fresh / final | 2 / 2 |
| 새 검사기 빌드 / 실행 | exit0 / exit0 |
| 빌드 경고·오류 | 0 |
| 정리 | cleanup=true |
| 경과 | 141.172초 |
| 시스템 CPU 최고 | 15.98% |
| 가용 RAM 최저 | 55.4597% |
| 보호 중단 / 새 Native | 0 / 0 |

영수증은80,822bytes / SHA256 `92eb413e2293318b4e7f32630baf2aeba720646b400dbf662c229ead3fcedd86`다. 검사 실행 파일은8,517,632bytes / SHA256 `47e1c3012b2b1858c783e401953689049c5bf8f22b9a5a9149c1c6e7d6cd75ca`다. 실행 파일의 dep-info 직접 입력2개는 새 example/고정 manifest이며, workspace Rust 소스·Cargo 입력과 로드된 검증 도구는 별도로 시작/종료 해시에 포함했다. 이 수치를 외부 의존성 전체 공급망 검증으로 확대하지 않는다.

## 실패와 수정 보존

1. audit001: 일반 관측 영수증에632 전용 복구 decoder를 선택한 사전검사 오류. 빌드/제품 실행 전 실패했고 [실패 영수증](evidence/p09-361-prepared-bookmark636-product-graph001.v1.json)을 보존했다.
2. audit002: 새 example의 `ReferenceAuxiliaryLimits::default()` 두 곳이 E0599로 컴파일 실패했다. 실패 메타데이터의 tuple을 일반 JSON으로 정규화하지 않아 게시도 `XREF_LOSSLESS610_SCALAR_TYPE`으로 실패했다. audit002 영수증은 **생성되지 않았으며 성공으로 복구/대체하지 않았다**. 당시 검증기 소스를 보존했다. 후속 실행은 기존615의 canonical normalization/원자료 선보존 경로를 사용한다.
3. audit003: [E0599 컴파일 실패를 정상 기록](evidence/p09-361-prepared-bookmark636-product-graph003.v1.json)했다. 생성자 `new(ReferenceAuxiliaryLimitConfig::default())`로 수정했으며 제한값이나 보호 조건을 낮추지 않았다.
4. audit004: [실제 제품 검사 실패](evidence/p09-361-prepared-bookmark636-product-graph004.v1.json). 새 검사기의 전체 Field1개 가정이 틀렸다. 실제 원본 HYPERLINK1개를 독립 확인하고 기존 필드 전체 보존 조건을 추가했다. 제품 코드를 임의로 바꾸거나 기존 필드를 제거하지 않았다.
5. audit005: 위 수정 후 현재24문서 전체 조건을 실제 실행해 통과했다. 기존001/003/004 실패를 PASS로 덮어쓰지 않았다.

실패 시점의 검증기/example은 `source-archive/p361-prepared-bookmark636-audit001`~`audit004`에 보존했다. 영수증이 존재하는 실패001/003/004의 대응 source SHA5개는 archive와 일치한다. audit003/004/005 원자료는 private forensic에 선보존했다. 새 코드는 [고정 입력 manifest](evidence/p09-361-prepared-bookmark636-product-inputs.v1.json), [Rust 제품 검사기](../../crates/product-cli/examples/p09_prepared_bookmark_graph636.rs), [자원 보호 실행기](../../tools/p09/verify_prepared_bookmark636_graph.py)다.

## 아직 닫지 않은 범위

이 결과는 **현재24문서의 source-bound 제품 의미/대상/캐시/그래프 읽기와 그래프 JSON 재열기**만 증명한다. 새로운 HWPX writer 출력의 의미 재열기, Native의 새 대상 탐색·재평가, 렌더/geometry/서식 전체 보존, 대상 이동·이름 변경·없음/중복/깨짐, 다른 대상 family, 계획/권한/backend/새 출력 전체 경계 또는 REF-035 전체 PASS는 아니다.

다음은 확보된 PDF2종/BMP6종의 페이지·글자·geometry·의도하지 않은 변경 비교다. 이후 현재 로컬 제품 출력 경계와 이동/이름 변경·다른 대상 family를 진행한다. 다른 매체를 무조건 동등하다고 하지 않는다. 사용자 명령·접근 허용은 현재 필요 없다. P09/A12/A13 OPEN, 미마감31묶음/65기능과 전체 P09~P20 목표를 유지하고 새 P10을 시작하지 않는다.
