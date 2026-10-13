# P09-66 실제 HWPX importer 원본 연결 결과

- 상태: **actual whole-package source-stage component PASS / typed DocumentGraph importer·실제 저장 계보·제품 실행·native·Gate 미완료**.
- 정책: [P09-66_DOCUMENT_IMPORT_SOURCE_POLICY.md](P09-66_DOCUMENT_IMPORT_SOURCE_POLICY.md).
- 변경: package root module declaration 1줄, `document_import.rs`, 새 integration test와 fresh-process probe. 기존 parser/guard/lock/assertion 및 dependency/Cargo.lock 수정 없음.
- 실제 original ZIP과 모든 admitted XML token tree를 private immutable 유지한다. 모든 part/element에 document/package/part/exact span-bound source anchor 생성. caller fake graph/native ID가 아니다.

## 검증

| 검증 | 실행 근거 | 결과/범위 |
|---|---|---|
| 새 integration | a5f9f1 | 10 PASS; whole part/element/topology/exact subtree/unknown/doc+package binding/forgery/stale/limits/unsafe XML+media+closure/privacy |
| 기존 package 회귀 | ef445e | 143 PASS: lib35/binding1/color10/package output19/package17/value22/root12/graph8/preservation7/text12 |
| 제품 CLI lib/tests | 9e373b/e27ec4/8d19dd | 86 PASS; 실제 importer→typed product 연결 증거는 아님 |
| 독립 actual probe | 211761 | 2 fresh processes/같은 executable SHA `085ce70e3c0a02be8a13fcd13dbe21c40a0f9901103e7f0799d41d0fd709a3f6`/모든 receipt exact |
| probe 입력과 범위 | 같은 실행 | locked5쌍/HWPX10 cases/part anchors118/XML element anchors8130/tokens10822, all anchors resolve/각 source fresh full reimport |
| strict lint | 2b0ea4/164bbf | new example/integration 및 package/CLI/artifact/revision lib/tests `-D warnings` PASS; allow/skip 없음 |
| original root exact | a31112 | 추가 module declaration만 제거한 전체 텍스트가 whole archived source와 exact |
| 이전 보존 | 7f303b | P59~P65 pins339/original P48 graph1551 files·51047460 bytes via20 explicit origins/native75 files exact |
| 포맷/공백 | bf4bba | new3 Rust source rustfmt/scoped git diff check PASS |

실제 테스트 합계 new10+package143+CLI86=239. 동일 digest의 일부 source/output도 manifest의 정확한 각 path/bytes/SHA로 읽었다. 10 cases/8130 anchors는 native 실행 횟수나 기능 완료율이 아니다. 문서 ID가 다르면 anchor가 달라지는 계약이다.

## 실패 보존

- 88c4fa initial lint: doc backticks/type complexity2. 새 source의 doc syntax/type alias만 수정, initial source whole archive 유지.
- a286fc integration4PASS/6FAIL: 새 positive fixture CDATA가 원래 safe_xml_cdata_forbidden에 의해 거부됐다. parser 수정 없이 escaped text로 fixture 수정하고 CDATA rejection negative case 추가. 실패 fixture whole archive 유지.
- 474ddf integration9PASS/1FAIL: sorted first part 실제 asset SHA를 다시 동일 asset SHA로 바꾸고 위조라 부른 잘못된 새 oracle. 실제 다른 part fingerprint로 수정; 기존 거부 기대값/API 그대로. 실패 fixture whole archive 유지.
- 6d1ffa preservation diagnostic: pins339/native75 exact, old graph lib1 mismatch/25bytes 증가. 새 lib archive를 P48 resolver에도 명시해야 했던 새 진단 누락. origin 추가 후7f303b original1551/51047460 exact. old manifests/hash/guard 변경 없음.
- b03703 CLI package name 오타 hwpx-product-cli. 실제 Cargo name hwpx-agent-cli로 재실행; 소스/테스트 변경 없음.
- 첫 PLANS patch는 뒤섞인 hunks 순서로 거부됨, 파일126줄 원문 그대로 확인. 두 번째 편집 준비는122줄 bound를 넘겨 apply 전 중단. 최종120줄 snapshot: risk entries 보존/blank6줄 압축/중복 P58 checkpoint2줄 제거. P58 상세는 immutable report와 기존 next actions에 유지.

P09-62 이전16fde8 미해결 실패는 해결했다고 주장하지 않는다. P65 DB receipt는 이번 source 변경 후 새 whole admission 없이 current execution으로 재사용하지 않는다. 전체 과거 qualification CLI replay는 이번에 실행하지 않았다.

## 다음 실제 작업

typed paragraph/table/object/equation/form/note/reference/style/resource/security 변환과 실제 원본 anchor 연결·unknown exact preservation·fresh import parity·제품 provider 연동을 구현해야 한다. 모든 XML 구조를 보존한 사실은 typed 의미/readback을 증명하지 않는다.

그 뒤 실제 Source/Result/IR provenance/previous-result→input chain, issuer/ExecutionManifest/idempotent publication/IR lifecycle/whole replay+current admission/licensed native가 남는다. 원본·private evidence·실패 삭제 없음. COM/UI/Hwp 실행/접근 허용창/DB 생성/commit/push 없음. Goal ACTIVE/P09 open/no P10/full34 NOT_RUN/0green.
