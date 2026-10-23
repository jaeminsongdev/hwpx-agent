# P09 책갈피 reference graph 연결과 저장 서비스 검증

책갈피 CROSSREF의 source-local 대상 해석을 의미 graph의 실제 `Reference.target_node_id`로 연결했다. 대상은 같은 원본 package의 책갈피 wrapper node이며, 대상 없음·중복이면 연결을 만들지 않는다. 실제010 저장·재열기 산출물의 CROSSREF16개와 인증된 저장 서비스 코드에서 이 연결을 확인했다. **source graph 연결 구현·검증은 완료됐지만 Native 표시·이동 검증과 P09 전체 Gate는 미완료다.** 목표는 ACTIVE, P10은 미시작 상태다.

## 연결 범위와 원본 보존

`ImportedDocumentFieldSemantics::import`가 원래 field reference와 typed `BookmarkCrossReference`의 reference ID를 대조하고, Bound 대상이 원래 bookmark inventory에 있을 때만 그 wrapper node를 연결한다. Missing/Ambiguous는 target None을 유지한다. 부분 의미 graph profile을 partial-v3으로 올리고 receipt에 `bound_bookmark_edges`를 추가했다. source별 ID를 서로 다른 저장본 사이의 동일 ID라고 간주하지 않는다.

기존 package/field graph, cached text, opaque 자료, 책갈피 자체 reference, 관계없는 필드와 note/table 구조는 보존한다. 새 의미·metadata와 의도한 target 연결만 되돌리면 원래 graph와 완전히 같다는 delta 시험을 통과했다. 원본 package에는 쓰지 않는다. 원래 fresh reconstruction과 별도 original 객체 거부도 유지한다. 기존 graph 구성의 clone을 유지하면서 원본 reference·bookmark 맵을 한 번 만들어 찾으며, field마다 전체 graph를 복제하거나 대상 목록을 전수검색하지 않는다.

`SourceFieldMeaningIndex`의 의미 값과 추가 graph clone0 조건, 공개 field-meaning v2와 주 Source/CLI v14는 유지된다. 주 Source의 미해결4개와 Incomplete 판정을 바꾸지 않았다.

## 저장 서비스와 부분 문서 권한 보호

작은 독립 시험 묶음에서 실제 `StoredFormProvider → import_actual_forms → import_field_ranges → import_semantics → verify` 코드를 실행했다. 저장 graph·receipt는 같은 source의 직접 import와 일치하고, 재검증은 기존의 인증된 새 읽기2회를 수행하며 revision head를 쓰지 않는다. ACL 취소와 AEAD 암호문 변조 후에는 보존된 의미 graph와 새 의미 import 모두 거부된다. 미검증 scan 결과도 거부된다. 저장소는 인메모리, scanner와 키는 시험용 모형이며 외부 scanner·DB 배포·Native/서명 route의 자격 검증으로 취급하지 않는다.

`FullDocumentFormContext::bind`는 `field_semantics_import_profile` 또는 `field_semantics_import_scope` 예약키가 남아 있으면 값의 버전·형식에 관계없이 partial projection으로 거부한다. 이로써 현재 버전만 검사하다 과거 partial-v1/v2를 놓치는 구분을 막았다. v1/v2/v3·미래 버전·과거/현재 scope·잘못된 값 형식 각각의 단독 marker 거부와 marker가 없는 caller-full-IR 대조군을 확인했다. 이 조건 외의 기존 보안·부분 import·graph 검사는 전체 본문 inverse가 일치한다.

## 검증 근거

[최종 audit003](evidence/p09-361-bookmark-reference-edges618-audit003.v1.json)은 **28시험 조건, 930fresh/final930, compiled artifact8개 전후 일치, cleanup true**다. 동일 제품 코드에서 통과한 저장 서비스3·영향 시험17을 코드·입력·시험 본문·산출물 동일성으로 유지하고, 강화된 graph delta 보조 함수를 사용하는8개를 현재 실행했다. 현재 step은 exit0·diagnostic0·cleanup true다.

[audit002](evidence/p09-361-bookmark-reference-edges618-audit002.v1.json)는 수정 실패1개와 영향 시험17개를 실행하고 새 시험10개를 동일성으로 유지해28조건·927fresh/final927을 닫았다. 최종 검토에서 delta 보조 함수가 모든 reference target을 원복해 관계없는 대상 변경까지 가릴 수 있는 빈틈을 발견했다. audit003은 Bound CROSSREF만 원복을 허용하고, 책갈피 자체·관계없는 reference·Missing/Ambiguous 대상은 원복 전에 정확한 동일성을 요구한다. 제품 코드는 변경하지 않았으며 보강과 무관한20개를 반복하지 않았다.

새11조건은 표시/hyperlink8조합, Missing/Ambiguous, 다중 reference와 관계없는 필드 보존, note/table 소유 관계, source/target/document 변경·foreign reconstruction 거부, 비수식 의미와 cache 비평가, 과거/현재 partial marker 거부, 실제010 산출물24개의 graph delta, 저장 서비스 동등성·권한 취소·AEAD/scan 거부를 포함한다. 기존 영향17개는616통합9·주 Source 실물24개 시험1·기존 HTTPS/수식/graph 의미 시험7이며 실제 수식16개도 포함한다.

실제010의 opened8개에는 새 CROSSREF 연결0개, saved8·reopened8개에는 각각1개씩 총16개가 있다. 원래010 trace8개와40산출물을 재해시해 확인했지만, trace의 probe는 source 관측이고 SDK 호출은 반환 기록이다. 직접적인 Native 표시값·이동 성공·평가 결과를 입증하지 않으며 원래 `effect_unknown=true` 8개와 자격 false 표시는 그대로 보존했다.

최종 검증은219.297초, 시스템 CPU 관측최고20.77%, 가용RAM 최저43.951%다. 초기 시도를 포함한 세 검증에서 관측한 최고 CPU는28.91%, 가용RAM 최저는39.9996%였고 보호 중단은 없었다. CPU/RAM/commit/Job 보호·단일 작업·낮은 우선순위·debug assertions/overflow checks와 기존 CLI package의 codegen-units2를 유지했다. 새 한글/COM/Native·공식249 전체·큰 `form_stored_provider` 시험 묶음은 실행하지 않았고 Windows/Defender 설정도 바꾸지 않았다.

[초기 audit001](evidence/p09-361-bookmark-reference-edges618-audit001.v1.json)은 새11개 중10통과·1실패였다. 합성 시험의 DATE id7이 앞선 필드와 중복돼 원래 source admission이 거부했다. duplicate 입력의 거부를 시험에 남기고 DATE id9의 정상 입력으로 graph 보존을 확인하도록 수정했다. unused import 경고도 제거했다. 원래 실패 영수증과 시험/검증기는 `source-archive/p361-bookmark-edges618/`에 보존했으며 FAILED를 PASS로 바꾸지 않았다.

최종 원문300298B/SHAa8ce1b8bdbd0fb2912a15dc51bc6d02199618fb6ca74c1f8ebd1b94973259d73은 immutable private forensic spool에 먼저 저장했다. 무손실 packet101103B/SHAc3df72e55540f7bec6d8e3c49d48f4d1c6ed350ec2234e97e7239db35a2adeb8이며 원래256KiB publisher/4MiB 복원 한도를 유지했다. 소비된010 probe 바이너리와 기존 Native 원본은 변경하거나 재실행하지 않았다.

## 남은 작업

Native 대상 해석·페이지/상대위치·캐시/표시·재평가, 다른 객체·각주/미주 CROSSREF의 typed 의미, 전체 reference edge와 문서 flow/auxiliary state가 남는다. 다음에는 보존된 저장본에서 cached field text를 source와 정확히 구분해 읽을 수 있는지 확인하고, 기존 기록으로 가능한 비교와 추가 Native 관측이 필요한 범위를 나눈다. 캐시 관측을 계산·화면 표시의 정답으로 승격하지 않는다.

공식249 큐는158수용/잔여91/next165이며 이번 수용 증가0이다. P09/A12/A13 Gate가 실제로 닫히기 전 P10을 시작하지 않는다.
