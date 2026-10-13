# P09-89 메모 모양의 기존 source catalog·assembly 연결 결과

## 구현 결과

기존 ImportedDocumentCatalog의 native header definition/index/Style graph에 memoProperties/memoPr를 연결했다. 절의 실제 memoShapeIDRef와 header style ID를 결속하고, original assembly와 authenticated stored catalog/assembly 경로에서도 같은 source 관계를 제공한다.

원래 mapper/catalog/source anchor resolver/domain graph validator를 재사용했다. 별도 문서 importer나 full CommentState를 만들어 source metadata의 빈 부분을 채우지 않았다. 원래 stored-service 소스, assembly combine/receipt guards와 기존 exact oracle은 수정하지 않았다.

원래 native MemoShapeType.cpp는 lineWidth를 mm 문자열이 아니라 unsigned enum ordinal로 쓰며 enumdef.h의 ordinal0..15를 사용한다. color converter의 none/six-hex 형태, lineType18/memoType4 및 itemCnt/ID/duplicate/child shape를 검사한다. width/색/원래 token과 추가 namespace attrs는 보존하며 constructor defaults를 사용하지 않는다. 이 source subset 판정이 native 렌더 의미나 메모 스타일 변경 제품 acceptance는 아니다.

## 실제 입력 및 연결 경계

현재 locked actual36의 memoPr 정의는0개, 명시적 절 메모 참조는44개다. 44개 모두 UnresolvedMissingDefinition으로 보존한다. 특히 native ID0을 임의 default Style로 만들지 않았다. 해당 그래프는 기존 whole-source/exact oracle을 그대로 통과했다.

원본에 정의가 실제 있으면 같은 catalog style ID로 절 관계를 연결한다. MEMO 본문은 실제 source section ID를 참조하고 complete section metadata는 catalog에 한 번만 둔다. hidden explanation에 메모 상자 모양을 추측하지 않는다. resolved/absent/unresolved 상태는 서로 다르며 현재 full-document operation/activation denial을 그대로 유지한다.

Positive 사례는 원래 Hancom2020Vs0Builder의 in-memory synthetic derivatives다. actual positive native memo capture, author/time/visibility/resolution 또는 native memo-box rendering은 검증하지 않았다.

## 현재 소스 검증

| 범위 | 결과 |
| --- | --- |
| package integration18 targets | 166 PASS |
| catalog/assembly private tests | 5 PASS |
| product4 targets | 152 PASS; provider125 포함 |
| original domain comment public/private | 11 PASS |
| 전체 scoped 합계 | 334 PASS, 0 FAIL |
| strict5crate lib/tests/examples lint | PASS |
| 신규5file nonrecursive format / diff check | PASS |
| 원래 comment contract | FAIL: implementation_digest |
| 원래 comment Python tests | 4 PASS / 1 FAIL |
| 원래 conformance | FAIL: matrix_drift |

신규11개(public6/private1/stored4)는 합계에 포함한다. P88보다 범위가 넓어진 original catalog/fonts/security/settings/formula legacy34개도 합계에 포함한다. 원래 AES-GCM ArtifactService를 실행했으나 metadata/revision/blob/scanner/actor는 in-memory fixture다. 이번 actual PostgreSQL/native/UI/external issuer 실행이나 full workspace107target batch는 없다.

Native line widths16/line types18/memo types4 및 malformed enum/count/duplicate/style/body/reference, missing defaults, private cached binding/receipt mutation, source style/reference drift, service ACL/AEAD/head/quarantine/scope 변경을 검사했다. raw getter/receipt 자체를 현재 권한으로 취급하지 않는다.

## 실패·보존

초기 internal fixture alias compile과 stale copied fixture test compile 오류를 그대로 기록하고 failed source4개를 whole archive로 보존했다. 공유 fixture는 원래 builder를 직접 사용하며 obsolete 새 copied test만 제거했다. 원래 P88 test는 그대로다. 초기 lint의 documentation/let-chain/boolean 표현3개를 의미 동등하게 수정했고 guard/budget/lint를 약화하지 않았다. section ID 최적화 후 신규 assertion formatting 실패도 기록하고 final format을 통과했다.

원래 comment component/tests 및 shared lib.rs는 P88과 동일하다. 기존 지문·matrix drift를 현재 구현 성공으로 바꾸지 않았다. P59~P88 raw declared pins11192, original source1551 files/51047460 bytes/native originals75를 현재 파일 또는 whole archives로 확인했다. P88source625 중621개 동일/parent4개 exact preimages 보존, scoped 추가를 역산한 전체 parent text inverse도 동일하다. 과거 qualification을 전부 재실행한 것은 아니다.

## 남은 원래 제품 범위

이 단계에서 완료한 것은 메모 모양 원본 읽기·참조 연결이다. original CommentBuilder를 쓰는 style/insert/show/resolve 실제 제품 mutation/lowering, qualified native author/time/state/style 및 exact-target save/reopen/render, 나머지 fields/notes/references/TOC/citation/mailmerge 의미, source re-admission/full-document admission/trusted issuer/atomic execution/publication과 P09 Gate는 남아 있다. comment_delete는 P11이다.

P09 Gate/A12/A13 OPEN. P26 failed_semantic_non_green/P62 UNRESOLVED/native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN 유지. 한글/COM/UI/접근 허용/운영 및 trust DB/stage/commit/push는 실행하지 않았다. PLANS.md 부재, 목표 active, P10 새 구현 없음.

정책: P09-89_MEMO_CATALOG_POLICY.md. raw source/actual/official pins 및 실행 결과: evidence/p09-89-memo-catalog.*.v1.json.
