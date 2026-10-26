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

현재003은 동일 제품/검사 본문을 결속한 깨끗한 test/example 빌드와 기존32파일＋이름변경8파일의 새로운 의미 판정을 진행한다. 40개 모두8 block typed meaning·unsupported0·공통 API/graph/주 Source 일치·전체 fresh reconstruction·원본 불변을 확인하되, 주 Source의 Incomplete/validation_report 없음/미해결4~5개는 유지해야 한다. 새 삽입1건의 HWPX byte가 이전 candidate와 같은지도 최초13검사에서 관측했다.

원guard·단일 CPU·낮은 우선순위·CPU/RAM/commit 보호와714 단계 표본을 유지한다. Native/공식249 및 기존748~713 시험은 반복하지 않는다. 현재 묶음은 진행 중이며 완료로 주장하지 않는다.

변경 전 핵심5파일은 `source-archive/p361-block-bookmark-meaning749`, 001/002 수정 전 파일은 `source-archive/p361-block-bookmark-meaning754-001`/`002`에 보존했다.
