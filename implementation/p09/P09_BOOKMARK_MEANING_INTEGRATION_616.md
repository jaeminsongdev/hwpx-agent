# P09 책갈피 CROSSREF 필드 의미·제품 API 통합 616

상태: **source-local 의미 통합 검증 완료 / P09·A12·A13 OPEN / 목표 ACTIVE / P10 미시작**.

## 구현

- 기존 `ImportedFieldMeaning`에 `BookmarkCrossReference`를 추가했다. 614의 실제 Command parser/SDK 정규 역구성/동일 source target index를 재사용한다. 표시4종·hyperlink2종 및 Bound/Missing/Ambiguous를 typed 의미로 유지한다. 명령·대상 이름 원문 대신 해시와 source-local ID를 쓴다.
- `ImportedDocumentFieldSemantics`는 이 의미를 원래 field node/reference의 `source_derived_meaning`에 연결한다. 원래 graph/field가 변하지 않으며, fresh whole-source/원래 import identity/전체 의미·graph·receipt 비교를 유지한다.
- `SourceFieldMeaningIndex`는 추가 DocumentGraph clone 없이 같은 의미와 해시를 반환한다. CROSSREF가 있는 문서에 한해서만 target index를 문서당 한 번 만들고 기존 이름 인덱스로 찾는다. HTTPS/FORMULA reader 및 aggregate work ceiling은 유지했다.
- 공개 Rust 제품 API `assess_package_field_semantics`에서 `BookmarkCrossReference` selector와 결속된 meaning SHA를 반환한다. 일반 필드 의미/인덱스 profile과 공개 field-meaning JSON을 명시적으로 v2로 올리고 bookmark 수를 추가했다. status는 Incomplete, complete-reference/external approval은 false다.
- 책갈피 아닌 대상 종류와 parameters/정확한 Command key가 없는 CROSSREF는 일반 의미 API에서 명시적인 Unsupported로 남는다. keyed 책갈피 명령의 malformed/type/namespace/comment 오류를 Unsupported 성공으로 숨기지 않는다. 원래 엄격한 `read_source_bookmark_crossrefs`는 다른 대상 종류가 섞인 경우 여전히 전체 거부한다. subset 전용 내부 경로를 공개 whole-CROSSREF report로 내보내지 않는다.
- 텍스트 예산 초과는 Limit로 분리했다. CPU/RAM/Job 보호·단일 작업·낮은 우선순위·debug assertions/overflow checks는 유지했다. 이전에 검증한 CLI package의 codegen-units=2만 재사용하며 전역 Cargo/Windows/Defender 설정을 바꾸지 않았다.

## 검증과 보존

| 근거 | 결과와 제한 |
| --- | --- |
| [audit001](evidence/p09-361-bookmark-meaning-integration616-audit001.v1.json) | 수식 manifest의 파일 pin에 추가 관측 속성이 포함됐는데 dict 전체 동일성을 요구해 사전검사 실패. Rust/Native 미실행, cleanup true. 원래 source archive와 실패 증거 보존. 파일 자체는 bytes/SHA로 대조하도록 수정 |
| [audit002](evidence/p09-361-bookmark-meaning-integration616-audit002.v1.json) | 컴파일 성공·새9시험 중8통과/1실패. 실제 문서의 전체 필드 목록에 다른 정상 필드도 있는데 시험이 CROSSREF만 있다고 가정한 오류. CPU최고25%, 가용RAM최저38.206%, cleanup true. 원래 FAILED 영수증은 변경하지 않음 |
| [최종 audit003](evidence/p09-361-bookmark-meaning-integration616-audit003.v1.json) | 수정 실패1 + 영향 있는 기존23을 현재 실행해24통과. 새 시험의 나머지8은 전체 helper/시험 body와 실제 compiled input의 동일성을 fresh 대조해 유지. 합계32조건·913fresh/final913·4step exit0/diagnostic0/cleanup true |

새9조건: 8표시/hyperlink 조합의 의미·graph 연결, 혼합 다른 종류/unknown key, Missing/Ambiguous, malformed supported command, source/target 변경·foreign reconstruction 거부, 예산/SHA 거부, 출력/Debug 비밀 원문 비노출, 실제010의24개 opened/saved/reopened 출력, 기존 주 Source v13의 미해결4개 유지다. 실제 문서에서는 전체 fields 길이와 의미 count 합계를 비교하고 CROSSREF selector만 따로 찾아 검증한다. 다른 필드를 생략해 시험 기대값을 맞추지 않는다.

영향 있는 기존23조건: 엄격한 책갈피 API10(실제24자료 포함), 의미 인덱스3+기존 HTTPS/graph 관련4, 공개 field-meaning API6(기존 실제 수식16개 포함). 공식249 큐·한글/COM·외부010/Native008~011·기존010 probe는 실행하지 않았다. 소비된010 probe의 바이너리는 hash가 그대로다.

최종248.36초, 시스템 CPU 관측최고30.5%, 가용RAM최저37.606%. 자원 보호 중단 없음. 원래 코드4개와 실패002 시험/검증기를 `source-archive/p361-bookmark-semantics616/`에 보존했다. 결과322456B/SHA0c7c4f76456501a868a50d0ef185eec39265ebc4451b146982bdf5304a02cbd4는 immutable private forensic spool에 먼저 보존했으며, 104427B self-contained lossless packet의 SHA는4e6fbcb08be4c894fd66b9db2738b15b5f86b461d4dc1a66edd979824b67e57f다. 원256KiB publisher/4MiB 복원 한도를 유지했다.

## 아직 완료하지 않은 범위

1. 주 공개 `assess_package_source`/CLI의 v13 본문은 이번에 변경하지 않았다. 새 통합은 공개 **field-meaning API v2**까지다. 다음은 새 selector/meaning receipt를 주 Source assessment/CLI 흐름에 실제 연결하는 작업이다. 주 Source의 미해결4개를 아직 닫지 않는다.
2. source-local 책갈피 결속은 Native 대상 해석/페이지·상대위치·cached display/레이아웃·재평가·외부 링크 승인이나 실행 허가가 아니다. 객체/각주·미주 CROSSREF 등 다른 대상 종류의 typed 의미도 미완료다.
3. 공식249 큐158수용/잔여91/next165, 나머지 P09 운영 경로·통합 감사·Gate는 그대로 남는다. 이번 수용 증가0이며, 기존 실패·미실행·사용자 승인 경계를 보존한다. P09가 닫히기 전 P10은 시작하지 않는다.
