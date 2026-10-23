# 개인정보 선택 마스킹의 변경 owner와 공통 계획

SEARCH-019의 [저장 및 제품 요청](p09-personal-info-mask-product-v1.md)을 공통23번째 변경 family에 연결한다.
기존22개 순서·원 strict parser/오류·현재 권한·writer/전달 경계와 Form/Formula·기존 preview는 유지한다.
컴파일된 계획은 데이터이며 실제 실행·저장·게시 또는 문서 전체 익명화 권한이 아니다.

## 변경과 미리보기의 타입 분리

StoredPersonalInfoMaskMutationRequest는 preview_only=true를 원본 읽기 전에 거부한다.
PreparedStoredPersonalInfoMaskMutation만 원본 source owner와 edit inventory의 compiler view를 제공한다.
공통 PersonalInfoMaskPreview는 별도 opaque 타입이며 JSON만 전달한다. bytes/inventory/compiler API나
mutation으로의 역변환이 없다. malformed/unknown schema·누락 mode·부적합 정책은 원본 읽기 전에 거부한다.

## 실제 원본 편집 위치와 계획 결속

SourcePersonalInfoMaskEditInventory는 기존 writer/readback 계획의 실제 변경 hp:t anchor만 보관한다.
단일 text의 여러 마스킹 성분은 하나의 anchor이며 여러 run의 text는 별도 anchor다. scalar 수를 operation
수로 대체하지 않는다. inventory는 source SHA·output SHA·전체 공개 receipt SHA·순서 있는 anchor 목록과
profile을 SHA로 결속한다. 원문·개인정보 값별 해시는 없고 Debug는 redacted다. 원본 scope/보호/마스킹/
writer/readback와 기존 receipt/출력 bytes는 변경하지 않았다.

공통 projection의 selected_mask_text_splices는 변경 text anchor 목록이다. 전체 scalar patch를 직렬화한
새 실행 레시피가 아니다. 현재 candidate output과 source를 검증한 뒤 원본 graph의 실제 구조 owner를
기존 SelectorSnapshot/OperationPlanCompiler로 선택한다. 기존12개 잠금 인자에 원본 anchor·source/output/
receipt/inventory·request 지문을 결속하며 원본 읽기 이후의 최종 head를 확인한다. 폰트 v1/v2의15개 자원
인자와 실행 manifest/registry 경계는 변경하지 않는다.

보관 verify/bytes 전달은 기존 현재 source/access/writer·consumer 최종 head를 사용하며 마스킹/writer/
compiler를 반복하지 않는다. opaque receipt나 compiled plan은 현재 권한이나 멱등 claim·CAS·실행 허가가 아니다.

## 원 실패와 현재 검증

[367](../../implementation/p09/evidence/p09-361-compiled-personal-info-mask367.v1.json)은 빌드 단계 시스템CPU99.13%로
보호 중단·시험 시작 미관측·최종 입력 확인 미완료·cleanupTrue다.
[368](../../implementation/p09/evidence/p09-361-compiled-mask-post-stop-observation368.v1.json)의 중단 후4개 표본
CPU4~20%와 Job cap6.25%/active0/empty/closed는 peak 원인을 귀속하지 않는다. Defender 제외 목록은 실제 경로로
읽히지 않아 적용 여부 UNAVAILABLE이며 설정을 변경하지 않았다. 값 비노출 Debug와 유한한 시험명 조기 검사를
추가했고, [369](../../implementation/p09/evidence/p09-361-compiled-personal-info-mask-recovery369.v1.json)의 없는 tests
키 KeyError·시험0·864fresh/final864·cleanupTrue도 보존했다. 원 자원 보호·시험·입력 정책을 약화하지 않았다.

[370](../../implementation/p09/evidence/p09-361-compiled-personal-info-mask-metadata-recovery370.v1.json)은 신규19+
영향13=32pass·866fresh/final866·cleanupTrue다. 테스트의 미사용 hash import 경고2는 원본에 남겼다.
독립 serde JSON receipt SHA 단언을 보강한 [371](../../implementation/p09/evidence/p09-361-compiled-personal-info-mask-receipt-hash371.v1.json)은
그 영향1개만 통과·이전31개 보존·868fresh/final868·진단/경고없음·cleanupTrue다. 현재 고유32개이며 단일33개
실행이 아니다. source25/제품33 전체·공식249는 반복하지 않았다.

원본 위치/구조 owner·12개 잠금 인자·23개 순서·두 정책과 부분 선택·metadata 비노출·권한 철회/복구·격리/
암호문 변조·source/head·최종 compile/verify/delivery 경합·preview 차단·원본/ingest/head 보존을 검증했다.
370 전체208.359초·시스템CPU최고35.67%·private최고1896.81MiB/5.9534%·가용RAM최저37.6257%와 네 Job 정리를
확인했다. 원 한 코어·BelowNormal·CPU cap6.25%·private8%/stop7%·RAM/commit95%를 유지했다. 프리즈 해결 증거는 아니다.

## 남은 제품 경계

whole_package_personal_data_removed=false다. SEARCH-020 탐지/읽기 전용 선택·전체 개인정보 정책·실제 실행/저장/
게시와 신뢰 registry·target의 match_set/semantic_diff/reopen·Native/Gate는 남는다.
공식158/249·잔여91·next165·P09/A12/A13 OPEN·목표ACTIVE·P10 미시작·CROSSREF8종 NOT_RUN·Native011 미승인/미실행·
문자 스타일6종 선택 대기·RouteUnqualified/P02 routing_allowed=false·source API v12 incomplete/미해결4/report없음/exit3를 유지한다.
