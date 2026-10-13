# P09-80 원본 글꼴 선언·문자 참조 연결

2026-10-04. 상태: **원본 글꼴 선언·7개 언어 축·fresh 저장 서비스 COMPONENT PASS / 전체 importer·제품 실행·native·P09 Gate OPEN**.

## 실제 구현

원래 `CharacterStyleCatalogReader`의 FontFace 전체를 변경 없이 사용한다. 실제 HH fontface/font/fontRef 위치와 언어별 native ID를 원래 source anchor에 결합한다. 같은 숫자 ID가 다른 언어에 있으면 별도 논리 font ID다. source font styles와 character font links만 추가하고 기반 catalog/body/field/form/note/resource/security 전체를 보존한다. 추가 stage 정보를 제거하면 원래 graph 전체가 동일하다.

fresh 검증은 원래 전체 source/catalog 검증을 먼저 수행하고 전체 새 graph·typed declarations·links·receipt를 재구성해 비교한다. 저장 서비스는 생성·재사용 전 original full catalog verify, 이후 original authenticated whole source checkpoint를 유지한다. 실제 tenant/subject/project/branch/document/read scope/head/ACL/quarantine/AEAD 거부 경계가 같다. 반복 읽기는 atomic CAS/DB 잠금이나 새 committed source lineage가 아니다.

source font profile/scope는 각각 단독으로 full-document context를 거부한다. 기존 guard/reader/parser/원래 테스트 본문을 약화하지 않았다. 전체 원문 역변환5개는 두 catalog module 선언, 새 test module pair, 기존 테스트의 fixture sibling 가시성, 새 partial-denial helper/call만 제거하면 정확한 원문 SHA와 같다. 기존 module 순서는 그대로다.

## 실제 원본과 검증

| 증거 | 결과와 범위 |
|---|---|
| 잠긴 기존 문서 | 36개, 언어별 font group252, font definition504, character font link1771, whole original graph inverse36 |
| typed declaration | 원래 전체 FontFace와 동일. 실제 typeInfo 선언504, embedded flag0, substitute0; 설치·메트릭·대체·binary resolution 수락 아님 |
| 독립 실제 소비 | 현재 executable 두 process의 전체 payload exact; build24a885/d35a83, process9978d2/6457d8 및32dda1/25c7a9 |
| 새 package 검사 | 7 PASS: actual36·원래26 prefix·전 언어 native ID·전체 선언/anchors/graph inverse/fresh, 언어 ID 충돌 차단, 원본 변경 거부·redaction, 기존 dangling/count/duplicate/foreign/missing 축 거부, unknown native attr 원래 typed reader 거부 |
| embedding 파생 검사 | 별도 메모리 파생만: 선언 flag/binary reference 보존. binary가 실제로 존재·설치·실행됨을 증명하지 않음 |
| 새 service 검사 | 5 PASS: actual36 direct/stored whole equality·무 ingest/head write, 생성/cached AEAD·ACL·head·quarantine 거부, scope5 거부, 각 partial qualifier 독립 거부, original read-scope bind 거부 |
| 현재 named 회귀 | CLI147/12 targets + package928/94 targets = **1075 PASS/106 targets**; failed/ignored/filtered0. 새7+5는 이 합계에 포함되며 다시 더하지 않음 |
| strict lint | 5 crates lib/tests/examples `-D warnings`, bbf55d exit0; allow/skip 추가 없음 |
| format/diff | 새8파일만 rustfmt skip_children/check 및 git diff --check,1336f1 exit0; 전체 formatter 미실행 |

현재 actual executable:6041088 bytes/SHA `365b68346da4a5c342e611e7ff960f63271b0696f2a49f4c67dea1bceccbb9d2`.

전체 CLI/package 명령10827은95ac7f exit0였다. 다만 package stdout19398tokens 중9398tokens가 수집 한계로 잘렸다. CLI147 기록은 온전하며 package만 동일 source·전체 lib/tests를 quiet 출력으로 다시 실행했다(69295/a806db exit0). package94 targets/928 전체 rows를 별도 receipt로 보관했다. 검사 필터나 기대값을 바꾸지 않았다. P79 domain593은 이전 source epoch의 역사적 증거이며 이번 current1075에 더하지 않는다. 전체 workspace/ordinary Python/원래 전체 qualification CLI는 이번 named 회귀와 별개다.

## 실패와 원본 보존

새 helper의 존재하지 않는 Properties.get, 새 테스트의 full_span API, 반환형이 다른 service 테스트 match, 중복 fixture module/boolean lint를 whole archives와 failure receipt에 보존했다. 원래 API를 바꾸지 않고 새 코드만 수정했으며, 기존 frozen input loader를 재사용하도록 test-only sibling 가시성만 추가했다. 앞선 focused 테스트가 실제 실행 중일 때 전체 명령이 같은 executable을 다시 링크하려다 LNK1104로 실패했다(3d838f). focused25380의 terminal exit0(bc0913) 및 exact-name process0을 확인한 다음 새 whole run을 실행했다. 강제 종료/삭제/검사 제외는 없다.

보존 audit13de6a/ea9caa exit0: P59–P79 선언 pin5101, whole originals1551/51047460 bytes, native originals75 exact. P79 sources508 중 현재502 unchanged이며 변경5·삭제1의 whole pre-change originals는 archive에 있다. 새 whole source archives는6 originals+4 failing source snapshots다. 원래 전체 qualification CLI 재실행이나 현재 old frozen guard PASS를 뜻하지 않는다.

사용자가 root PLANS 삭제를 명시했다. root `PLANS.md`는 없고 재생성하지 않았다. 삭제 전45435 bytes/SHA `97508d73925c4f1f24336b786f51626dfc4255061930f3a50ab9467c86f56c47`의 exact copy는 `source-archive/p09-80-pre-source-fonts/PLANS.md`에 있다. 역사적 receipts/guards의 root PLANS 참조는 그대로 남아 있으며 이를 새 current PASS로 바꾸지 않는다. 이후 진행 상태는 단계 report/receipts와 다른 제품 문서에서 관리한다.

## 메모 진단과 미완료 경계

같은 잠긴36을 원본 진단4be6b5와 현재 독립 재조회e8e918에서 확인했다. memoProperties/memoPr/MEMO field ranges/hiddenComment 모두0, section memo 참조44다. 실제 메모 양성 사례가 없으므로 저자·시간·표시·해결 상태 기본값을 추론하거나 메모 완료로 세지 않았다.

이번 A11의 글꼴 source 연결·저장 service·검사 범위는 닫혔다. 전체 catalog/settings/security 의미 및 모든 partial stage의 완전한 importer 결합, 다른 field/reference/comment 의미, authoritative policy/scanner/issuer, actual committed Source/Result/IR·previous-result input lineage, ExecutionManifest/publication/idempotency, IR lifecycle/concurrency/crash/recovery/load, whole qualification/current admission은 남아 있다. 글꼴 설치·가용성·대체 선택·embedded binary 해석·native layout/render는 이번 source 범위 밖이며 검증했다고 주장하지 않는다.

P26 failed_semantic_non_green/P62 16fde8 UNRESOLVED/current admission INPUT_CHANGED_RE_ADMISSION_REQUIRED/full34 NOT_RUN·0green/P09 Gate OPEN/Goal ACTIVE/no P10 유지. 한글/COM/UI/native dispatcher/접근허용·trust/config/system/dependency 변경·stage/commit/push 없음. 이번 유일한 삭제는 사용자가 요청한 root PLANS이며 정확한 보존본으로 복구 가능하다.

## 증거 위치

- [정책](P09-80_DOCUMENT_IMPORT_FONTS_POLICY.md)
- [실제 소비](evidence/p09-80-document-import-fonts.actual-consumer.v1.json)
- [현재 회귀](evidence/p09-80-document-import-fonts.source-regression.v1.json)
- [출력 수집 보완](evidence/p09-80-document-import-fonts.regression-output-recovery.v1.json)
- [초기 실패](evidence/p09-80-document-import-fonts.initial-failures.v1.json)
- [원본 보존](evidence/p09-80-document-import-fonts.preservation.v1.json)
- [현재 source checkpoint](evidence/p09-80-document-import-fonts.source-progress.v1.json)
- [최종 raw binding 감사](evidence/p09-80-document-import-fonts.final-audit.v1.json)
