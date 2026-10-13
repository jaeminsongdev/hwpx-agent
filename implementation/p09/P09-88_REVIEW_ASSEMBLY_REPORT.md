# P09-88 기존 문서 조립·저장 서비스의 댓글 본문 연결 결과

## 결과

기존 ImportedDocumentAssembly가 P09-87 source review bodies를 실제로 포함하도록 구현했다. 원래 assembly → authenticated stored-assembly 경로에 자동으로 연결하며 기존 stored-service 소스, 원래 combine 및 예전 exact oracle은 바꾸지 않았다.

댓글 source observation 전체/원래 body/anchors/attributes를 보존하고, 원래 catalog binder로 body paragraph/run style을 연결한다. source body와 일반 본문·표시용 field cache는 분리한다. native author/time/visibility/resolution/MEMO-box style은 unverified이며 full CommentState로 승격하지 않는다.

## 변경 사항

원래 source review reader에 immutable original fields 재사용 helper와 bounded digest+size helper를 추가했다. 원래 paired field collector와 body mapper, 8MiB budget은 그대로다. assembly는 원래 font/security/settings/formula graph 위에 review entry만 결속하고 raw observation/typed catalog sidecar digest를 추가한다.

전체 raw source/graph/observations/sidecars/receipts fresh equality를 검사한다. source graph, raw/typed body, style uses, digest, metadata 및 forged native-qualified flag 변조를 거부한다. temporary whole graph validation은 실제 반환 본문에 댓글 텍스트를 섞지 않는다.

기존 authenticated 서비스의 ACL/quarantine/AEAD/head와 document/branch/project/subject/tenant 범위 검사를 새 branch도 그대로 사용한다. original partial FullDocumentFormContext 및 activation denial은 유지한다. artifact/head publication을 추가하지 않았다.

## 현재 검증

| 검사 | 현재 결과 |
| --- | --- |
| package integration12 targets | 126 PASS |
| original assembly private tests | 4 PASS |
| stored product4 targets | 148 PASS; provider121 포함 |
| original domain comment public/private | 11 PASS |
| 합계 | 289 PASS, 0 FAIL; 신규9개 포함 |
| strict5crate lib/tests/examples lint | PASS, 경고 허용 없음 |
| 신규5 Rust 파일 nonrecursive format / diff check | PASS |
| 원래 comment contract | FAIL: implementation_digest |
| 원래 comment Python tests | 4 PASS / 1 FAIL |
| 원래 conformance | FAIL: matrix_drift |

신규9개는 public assembly3/private2/stored4다. 실제 locked input36개 및 기존 zero-review whole graph oracle의 회귀 검사를 다시 통과했다. positive body 사례는 원래 builder의 in-memory synthetic derivative이며 실제 네이티브 댓글 acceptance가 아니다. 원래 ArtifactService AES-GCM을 실행했지만 metadata/revision/blob/scanner/actor는 in-memory fixture다. 이번에 actual PostgreSQL, external issuer/scanner, native/UI 검증을 실행하지 않았다.

P87 counts-only diagnostic의 실제36개에서 positive review body는 없었다. 기존 diagnostic binary/pins는 보존하지만 이번 소스의 새 네이티브/diagnostic 실행 결과로 세지 않는다. 지난 SQL/assembly probe3개도 exact historical binary로 보존하며 이번 SQL 실행으로 세지 않는다.

## 실패와 보존

초기 lint의 assigning_clones 및 semicolon_if_nothing_returned를 source3개 whole archive와 함께 기록했다. clone_from/semicolon으로 수정했고 budget/guard/lint를 약화하지 않았다. 최종 수정 이후 strict lint를 다시 통과했다.

기존 comment 계약 및 conformance의 지문·matrix 실패는 그대로 기록한다. 오래된 qualification/matrix를 갱신해 PASS로 만들지 않았다. 공유 lib.rs drift는 P87과 동일하고 원래 comment model/tests는 보존되어 있다.

P59~P87 declared raw pins10427, 원본 소스1551개/51047460 bytes, native originals75를 확인했다. P87source614 중611개는 그대로이고 이번 parent3개는 whole raw preimages로 보존했다. scoped addition을 역산해 parent3개의 전체 원래 텍스트가 동일함도 확인했다. 모든 과거 qualification을 재실행한 것은 아니다.

## 남은 제품 범위

실제 native 댓글 author/time/state/box-style 의미와 insert/style/show/resolve 제품 실행 및 저장·재열기/render 검증, 나머지 field/MEMO metaTag/nested semantics, full-document admission/trusted issuer/atomic execution/publication, 원래 conformance source re-admission과 Gate가 남는다. comment_delete는 P11이다.

P09 Gate/A12/A13 OPEN, P26 failed_semantic_non_green/P62 UNRESOLVED/native INPUT_CHANGED_RE_ADMISSION_REQUIRED/full native34 NOT_RUN 유지. P10 새 구현 없음. 한글/COM/UI/접근 허용, 운영/trust DB, stage/commit/push를 실행하지 않았다. root PLANS.md는 부재 유지하며 목표는 active다.

정책: P09-88_REVIEW_ASSEMBLY_POLICY.md. 재검토 가능한 scoped raw 지문 및 실행 결과는 evidence/p09-88-review-assembly.*.v1.json에 기록한다.
