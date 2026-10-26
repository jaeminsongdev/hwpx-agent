# 기존 Native 스냅샷의 단일 쪽·상대 위치731~736

2026-10-26. 직전726~730의 원본 유도 이름/본문 oracle·새8검사·기존32파일 새 의미 판정은 progress다. 전체 P09~P20 목표와 P09 Gate를 유지한다.

## 근거와 경계

기존 캡처 ports는 owner를 확인한 뒤 Hwp.PageCount를 읽고 전체 페이지를 CreatePageImage로 저장하며 마지막 PageCount도 같음을 확인했다. 732는693/730의 정확한 이전 receipt와 trace/HWPX/image SHA·같은 Native owner·종료 기록에 결속해 case1/2/7/8의 initial/reopened8스냅샷이 실제 한 쪽임을 재사용했다. 293/293 fresh·cleanup=true·64.594초·CPU12.93%·가용RAM38.3785%·원guard129표본이다. 한글은 실행하지 않았다.

준비 receipt: evidence/p09-361-single-page732-inspection001.v1.json,42966B,SHA256 6174a25e5cda3df1dde466a0584700ae864327e33c9feef0db4b0469f8f68b1b. 입력 manifest: evidence/p09-361-single-page732-inputs.v1.json.

731은 명시적인 미인증 page-count observation을 받는 조건부 해석이다. source SHA·한 쪽의 전체 page index·원래 source/command/target·직접 본문 문단의 단일 lineseg·쪽 시작/단 구성과 좌표 한도를 확인한다. 첫 쪽 십진1·한국어 위 방향의 제한된 profile이며 아래 방향/다중 쪽/좌표 중첩·줄 정보 누락·다른 번호 시작은 미자격이다. API는 producer/locale/일반 DocumentFlow/실행/공개/revision 권한을 반환하지 않는다. 실제 producer 결속은 732/736의 고정 스냅샷 증거와 구분한다. 기존730의 기본 NeedsDocumentFlow 응답도 유지한다.

중간 saved 파일은 initial과 Contents/content.hpf가 다르며 spine의 읽기 참여 설정 차이도 관측됐다. 이를 지워 같게 만들거나 initial의 PageCount를 saved로 전파하지 않는다. Saved4관측과 candidate4관측은 명시적으로 extent 미확정으로 유지한다.

준비 batch의 기본 items_per_kind=1000000만으로 큰 결과 Vec를 미리 확보하던 경로는 실제 기대값 객체 크기×개수를 output budget과 먼저 비교하도록 바꿨다. 원 CPU/RAM 보호를 유지한 메모리 제한 보완이다. 기존 helper728에는 읽기 fixture 접근 함수만 추가했고 기존8검사는 새 실행에서 선택하지 않는다. 변경 전3파일은 source-archive/p361-single-page731에 보존했다.

## 검증 계약

새8검사: 쪽1 조건부 일치/잘못된 cache 불일치, 독립 줄 좌표의 위 방향, 다른 파일 extent 차단, 불완전/중복/다중 페이지 차단, 임의 page-count로 후보 자격 승격 금지, 번호 재시작/좌표 중첩 미자격, 아래 방향 추정 금지, batch 결과 메모리 상한의 선검사.

일반 실행 파일은 case1/2/7/8 × candidate/initial/saved/reopened16파일을 새 코드로 읽었다. 첫 실행에서 새8검사·일반 빌드·실제16파일 판정이 모두 통과했고 경고/컴파일 오류는 없다. 정확히 producer-bound initial/reopened8조건부 일치, saved4/candidate4 extent 미확정으로 나왔다. 기존730/725/721/713/249 검사와 Native 실행은 반복하지 않았다.

## 검증736 결과

- receipt: evidence/p09-361-single-page736-product001.v1.json
- 상태: QUALIFIED736_EXISTING_NATIVE_EXTENT_BOUND_SINGLE_PAGE8_SAVED4_CANDIDATE4_MISSING_NOT_GENERAL_FLOW_OR_F11
- 166680 bytes,SHA256 0c420358460ddfd1d78d6ced17a3bf7d352820541e4e707b23a984a58a9c8f81.
- 입력 fresh/final1238/1238,실제 test/example executable·dep-info4개 final SHA 확인,cleanup=true.
- 원guard566표본 무손실 보존. CPU 최고17.05%,가용RAM 최저32.69126863032014%,보호중단0,전체285.359초.
- 컴파일/새8검사42.469초,일반 빌드1.484초. 컴파일 private 최고2085.79MiB(PC 물리RAM 대비6.5465%),실제16파일 reader는 owned CPU1.5초/private 최고21.87MiB. 모든 Job 종료 후 active_processes=0,observer cleanup=true.
- 단계 표본 startup2/input_binding210/build85/binary_binding28/readback3/final_binary26/final_source211/final_resource1. 표본 개수는 정확한 단계별 소요시간이 아니다.
- 원문: evidence/private/p09-361-single-page736-product001-forensic/manifest.v1.json.
- 첫 실행 성공. 한글/접근 허용 실행0,과거 통과730/725/721/713/249 검사 재실행0. 730의 기본 NeedsDocumentFlow·693의 이전 미자격 기록은 수정하지 않는다.

새 API의 MatchesUnderObservation은 명시적인 외부 관측 아래의 조건부 판정이다. 이것만으로 Native/locale/일반 flow 자격이 생기지 않는다. 736은 별도로732의 정확한 현재 HWPX/trace/전체 page image SHA와 기존 닫힌 Native 생산자 증거를 결합한 고정 스냅샷8개 범위다. 일반 호출자가 page_count=1이라고 말하는 경우와 구분한다. 따라서 P09-C04나 F11 전체 완료가 아니다.

Saved4파일은 uncompressed payload를 초기 스냅샷과 비교해 Contents/content.hpf 차이가 남음을 확인했다. 문서 구성 파일 차이를 정규화해서 지우거나 페이지 수를 전파하지 않았다. Candidate4도 대응하는 독립적인 render-bound extent가 없다. 이8개는 Native/page 기능8개 미구현이라는 작업 집계가 아니라16개 관측 중 남은 범위다.

## 다음 실제 작업

- Saved4의 정확한 스냅샷 extent,아래 방향/다중 쪽·이동/다른 필요한 target의 흐름 근거와 이름 변경·내부 hyperlink/탐색 검증을 모은다. 기존 초기/재열기8개 성공을 작은 Native 재시도로 반복하지 않는다.
- 이 기능별 증거와 원래 RouteUnqualified 조건을 충족하는 실제 로컬 host 진입·통제된 결과 출력·현재 head 채택을 연결한다. 범용 SQL/OAuth/원격운영/key custody 전체를 P09 선행 조건으로 확장하지 않는다.

목표ACTIVE·외부명령현재없음·684/690소비·P09/A12/A13 OPEN·31 closure묶음/65기능·공식158/249·next165·새P10미시작 유지. 과거713 CPU100% 원인이나 PC 프리즈 해결을 이번 낮은 부하로 판정하지 않는다.
