# 블록 책갈피 의미를 공통 필드 API·그래프에 연결749~754

2026-10-26. P09-F09/F11의 실제 BOOKMARK 대상 의미와 C02/C03의 공통 source/graph 결속을 잇는다. 전체 P09~P20 목표와 P09/A12/A13 OPEN을 유지한다.

## 구현

기존 `ImportedBlockBookmarks`는 Native670에서 관측한 BOOKMARK Prop=2의 실제 begin/end·이름·선택 내용 hash를 이미 확인했지만, 공통 `ImportedFieldMeaning`에는 그 결과가 없어 같은8범위가 Unsupported였다. 새 `BlockBookmarkRange`는 검증된 reader의 결과만 사용한다. 이름 SHA/UTF8 길이·시작/끝 fingerprint·원본 선택 내용 snapshot을 가지며 point marker·Native 평가·실행 권한을 뜻하지 않는다. 원본 이름/본문/Command를 새 metadata에 내보내지 않는다.

CROSSREF reader는 이미 해석한 block inventory를 공통 의미 reader에 넘긴다. field마다 cache/source를 다시 순회하지 않는다. 같은 source의 fields/index/graph/공통 API는 동일한 reference ID·meaning SHA에 결속한다. 기존 실제 begin node로 향하던 CROSSREF edge를 유지하고 새 point node나 임의 target map을 만들지 않는다. 중복 이름은 각 범위의 의미가 있어도 상호참조 대상은 Ambiguous로 남는다.

지원되지 않는 BOOKMARK profile은 임의 Prop=2로 해석하지 않는다. CROSSREF가 없는 미지원/혼합 inventory는 기존 Unsupported 상태를 보존하고, 엄격한 CROSSREF target reader의 미지원 거부는 유지한다. 깨진 pairing/coverage·source/budget 실패는 빈 inventory로 바꾸지 않는다. 구조화된 선택 내용 등 기존 block reader가 수용하지 않는 범위까지 지원했다고 주장하지 않는다.

## 프로파일 이행

| 응답/모델 | 지원 block이 없을 때 | 지원 Prop2 block이 있을 때 |
|---|---|---|
| 공통 field graph | `partial-v3` 유지 | `partial-v4` |
| 복제 없는 meaning index | `partial-v2` 유지 | `partial-v3` |
| 제품 field 의미 응답 | `reference-source-field-meanings/v2` 유지 | `/v3` |
| 주 Source 응답 | `/v15` 유지 | `/v17` |
| 조건부 제목 선언이 있는 Source 응답 | `/v16` 유지 | `/v18` |

`block_bookmarks` count는0일 때 직렬화하지 않아 기존 receipt의 shape를 유지한다. 새 버전의 소비자는 `block_bookmark_range`를 처리해야 하며 구 버전 oracle을 새 의미의 자격으로 재사용하지 않는다. 기존 HWPX 형식이나 원본 파일을 마이그레이션하는 변경이 아니다. Native/일반 flow·전체 auxiliary state·원래 RouteUnqualified·현재 host/output/head의 미완료 상태를 유지한다.

과거693/699/700 등에서 Unsupported8을 기록한 영수증과 source는 그대로 보존한다. 새 해석은 별도 현재 영수증으로만 기록한다. 해당 과거 관측을 당시의 typed-meaning 성공으로 고치지 않는다.

## 검증과 실패 보존

001에서 새9+직접영향4(HTTPS 의미·Source/버전 결속·unknown/출력한도·실제16 table formula AST)의 13검사가 첫 실행에 모두 성공했다. 다만 테스트 함수 이름2개의 경고 때문에 묶음은 실패했다. 검사 본문을 그대로 두고 함수 이름만 고쳤다. 002의 테스트 compile-only 빌드는 경고 없이 성공했으나 일반 example이 테스트 전용 CLI 환경 매크로 모듈을 함께 포함해 컴파일 실패했다. 해당 모듈을 `cfg(test)`로 한정했다. 13성공 관측은 보존하고 반복하지 않으며 실패한001/002를 전체 검증 성공으로 승격하지 않는다.

003은 동일 제품/검사 본문을 결속한 깨끗한 test/example 빌드와 기존32파일＋이름변경8파일의 새로운 의미 판정을 완료했다. 40개 모두8 block typed meaning·unsupported0·공통 API/graph/주 Source 일치·전체 fresh reconstruction·원본 불변을 확인했다. 주 Source의 Incomplete/validation_report 없음/미해결4~5개는 유지했다. 새 삽입1건의 HWPX byte가 이전 candidate와 같은지도 최초13검사에서 관측했다.

원guard·단일 CPU·낮은 우선순위·CPU/RAM/commit 보호와714 단계 표본을 유지했다. Native/공식249 및 기존748~713 시험은 반복하지 않았다.

변경 전 핵심5파일은 `source-archive/p361-block-bookmark-meaning749`, 001/002 수정 전 파일은 `source-archive/p361-block-bookmark-meaning754-001`/`002`에 보존했다.

## 현재 결과와 다음 경계

[754-product003 영수증](evidence/p09-361-block-bookmark-meaning754-product003.v1.json): `QUALIFIED754_COMMON_BLOCK_BOOKMARK_MEANING_RETAINED13_CLEAN_BUILD_EXISTING40_STILL_INCOMPLETE_NOT_NATIVE_OR_F11`, 172534 bytes, SHA256 `0ce3ccfad2bf535ea0050700ddd6899edf89193a9c1d64c65ead8e04d3e227fb`.

- 현재 input1300/1300·test/example 및 dep-info4 final hash·cleanup=true. 290.141초, 원guard572표본·시스템CPU최고15.53%·가용RAM최저36.7637%·보호중단0. 한글 process 집합은 동일하고 새 Native 실행은 없다. 과거 프리즈 원인의 해결을 의미하지 않는다.
- 001의 13개 실행 성공 관측과 현재 경고 없는 compile-only test build·ordinary example build·40개 새 판정을 구분한다. 현재 테스트 실행 수는0이며, 001의 종료 source hash0을 전체 묶음 성공으로 승격하지 않는다. 제품 코드는 동일하고 테스트는 함수 이름2개와 일반 빌드에서만 제외할 테스트 전용 module guard 외에는 그대로다.
- 기존32파일의 모든 Command SHA는 이전 manifest와 일치하며, 이름변경8파일은 실제 새 대상의 이름 SHA에 결속한다. 공통 모델과 독립 block reader의 이름/시작/끝/선택 내용이 같고 현재 graph 직렬화 재열기 및 전체 reconstruction이 일치한다. 원본·기존 Native/실패 영수증은 수정하지 않았다.
- 이것은 지원되는 source 범위의 의미 누락을 해결한 결과다. 필드의 초기 표시 평가·실제 한글 cursor/링크·저장/재열기 수용, 정확한 Saved extent와 필요한 다른 대상/flow, 현재 local host·지속 출력·현재 head 채택은 남았다. F09의 실제 책갈피 생성/삭제 마감이나 F11/P09 전체 완료로 세지 않는다.

다음 새 검증기에서는 test `--no-run`과 일반 example 빌드를 모두 깨끗하게 끝내고 실행 이미지/dep-info를 결속한 뒤 실제 검사를 실행한다. 함수 이름·외부 테스트의 비공개 token API 사용·테스트 전용 CLI 환경 모듈 포함 여부도 비용 큰 묶음 전에 확인해 이번 준비 오류를 줄인다. 이 순서 개선은 기존 검사를 생략하거나 원 source/자원 보호를 약화하는 정책이 아니다.

문서 수정 전9파일은 `source-archive/p361-block-bookmark-meaning754-docs`에 보존했다. 현재 사용자 실행 명령은 없고 목표는 ACTIVE다. P09/A12/A13 OPEN·31 closure packages/65 features·공식158/249·91대기·next165·새P10 미시작을 유지한다.
