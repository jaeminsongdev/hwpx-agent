> 현재 기준(2026-10-26): [원본 대상의 초기 결과 oracle726~730](P09_BOOKMARK_RESULT_ORACLE_726.md) 완료. 새8검사와 기존32파일의 새 의미 판정이 첫 실행 통과했다. 원본에서 유도한 책갈피 이름/본문은 Native 저장본12관측과 일치,후보4관측은 임시표시 불일치,Page/Relative16관측은 NeedsDocumentFlow 유지다. 관측 수를 기능/잔여 작업 수로 세지 않는다. source1226/1226·실행산출물4 final·cleanup=true,원guard566표본·CPU최고18.95%·가용RAM최저32.8390%·보호중단0. 기존725/721/713/Native/249 재실행0. 실제배치/다른대상·이동/탐색·실제host/출력/head·F11은 미완료. 목표ACTIVE·외부명령현재없음·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10미시작. 아래는 이전 이력이다.

# 로컬 세션·작업 폴더와 상호참조 제품 연결722~725

2026-10-25. 직전716~721의 실제 비공개 파일 저장·재열기 구현/검증은 progress다. P09~P20 전체 목표, P09 선행 Gate, 원본·실패 증거와 기존 성공 결과를 유지한다.

## 변경 범위

local-companion-daemon의 새 private/v5 `stage_bookmark_preview`를 신뢰된 embedding host가 제공하는 제품 runtime에 연결한다. 기존 세션 토큰 확인 뒤 정확한 요청 모양·중복 키·허용 workspace/operation ID를 검사한다. caller JSON은 root/파일 경로/생성 bytes/XML/키/승인 비트를 전달할 수 없다. 제품 요청은 원문 JSON 문자열로 전달해 내부 중복 키도 기존 strict parser가 거부한다.

host의 workspace binding은 config SHA와 workspace ID에 결속하며 다른 설정/작업 폴더에 재사용하지 않는다. 현재 StoredFormProvider와 원래 공통 제품 dispatcher 및716~718 I/O를 사용한다. 저장 전후 ACL/head/AEAD 검사, create-new와 원본 확인을 유지한다. 반환값은 제한된 해시·길이·ID만 포함하며 공개 출력/현재 revision 채택 권한은 항상 false다.

기본 `handle`에는 runtime이 없으므로 새 operation을 거부한다. 신뢰된 host가 `handle_with_bookmark_runtime`에 실제 provider를 연결한 경우에만 새 dispatch가 작동한다. 설치된 daemon 실행 파일·live config·보호된 runtime/trust DB·MCP 도구는 변경하지 않았다. 따라서 이 구현을 live 설치 완료나 OS ACL/tenant 정책 전체 검증으로 보고하지 않는다.

## 검증 계약

새 host 검사8개: 실제681 source1건의 인증된 wire→제품→관리 파일 생성 및 기존 후보와 SHA 일치, 기본 off/인증/허용 폴더/버전 거부, 중복·알 수 없는 필드·과대·경로 입력 거부, config/workspace 바꿔치기 차단, 제품 중복 키/XML/다른 문서 차단, ACL/AEAD/head 실패 차단, 반복 저장 덮어쓰기 금지, managed source 불일치 차단.

직접 영향받는 기존 daemon의 인증·프로토콜·workflow 검사3개만 함께 실행한다. 기존721의16개/실제8개와 Native/249를 다시 실행하지 않는다. 단일 코어·낮은 우선순위·원 CPU/RAM/commit 보호를 유지하고714에 원 guard의 단계별 표본을 보존한다. 변경 전 파일5개는 source-archive/p361-local-host722에 정확히 보존했다.

## 보존한 준비 실패

2026-10-26 기준 001은 기존 daemon3검사가 exit0/개별ok였으나 새 context의 Debug 경고로 전체 묶음은 실패했다. 002는 검사 준비 코드에서 set_permissions의 u64 반환값과 다른 분기의 unit 반환값이 맞지 않아 E0308로 컴파일 실패했다. 003은001 당시 검사 파일과 수정된 현재 파일의 버전 매핑이 잘못되어 입력 결속에서 실패했다. 002/003에서는 새 host 검사가 실행되지 않았다. 세 실패 모두 cleanup=true이고 CPU 보호 중단은 없었다.

Debug는 문맥/host의 본문·경로·provider를 노출하지 않는 고정 문자열로 구현했다. 반환값 타입과 historical source의 정확한 archive 매핑을 수정했고, 변경 파일 버전 결속23건을 별도 읽기 확인해 모두 exact임을 확인한 뒤004를 시작했다. 실패 receipt와 원문/변경 전 파일은 삭제하거나 PASS로 바꾸지 않았다. 001의 기존3개 실행 관측은 보존하되 전체 묶음 자격이나 현재 binary/source 최종 검증으로 승격하지 않았고 재실행하지 않았다.

## 검증004 결과

2026-10-26. 새 host8개가 모두 통과했고 경고/컴파일 오류는 없다. 실제681 source1건이 인증된 private protocol의 in-process bytes dispatch → 원래 strict 공통 제품 요청 → 현재 source/권한 확인 → 비공개 관리 파일 저장·readback으로 이어졌고 기존681 bookmark_name/false 후보 SHA와 같았다. 다른 문서/설정/작업 폴더·중복/과대/알 수 없는 입력·권한/AEAD/head 실패·source 불일치를 거부하고 성공 뒤 재호출도 덮어쓰거나 현재 head를 바꾸지 않았다.

- receipt: implementation/p09/evidence/p09-361-local-host725-product004.v1.json
- 상태: QUALIFIED725_AUTHENTICATED_DAEMON_WIRE_CURRENT_PRODUCT_PRIVATE_STAGE8_RETAINED_PRIOR3_NOT_LIVE_INSTALL_OR_PUBLICATION_REVISION
- 158864 bytes, SHA256 b2bf632ecb739eb8e8add2f9ade9ec6551e873c9cb199e4f34caa991d3137e6e.
- source fresh/final1217/1217, 실제 test executable와 dep-info 총2개 final SHA 확인, cleanup=true.
- 기존3개는001 실행 관측으로 보존했으며004에서 재실행하지 않았다. 004의 현재 자격은 새8검사이고 현재11검사를 실행했다는 의미가 아니다. 기존721/713·Native·249도 재실행하지 않았다.
- 원guard569표본 무손실 보존. CPU 최고12.32%, 가용RAM 최저36.2263352866064%, 보호중단0.
- 전체288.406초, 컴파일·새 검사 실행 단계4.219초. 나머지는 주로 원본/실행 파일 결속 및 최종 fresh 확인이다. phase 표본: startup2/input_binding208/build8/binary_binding71/final_binary71/final_source208/final_resource1. 표본 개수는 정확한 단계별 소요시간과 같지 않다.
- owned Job CPU4.078초, private 메모리 최고865.04MiB(PC 물리RAM 대비2.7150%). 프로세스 attribution 추가시간 합0.079초, 최고0.016초, cleanup=true. 원 자원 보호는 변경하지 않았다.
- 원문 증거: private/p09-361-local-host725-product004-forensic/manifest.v1.json. 001~003 실패와 각 변경 전 source/driver를 그대로 보존했다.

## 남은 범위

이 결과는 Rust library의 인증된 private protocol dispatch와 현재 제품/실제 파일 연결 자격이다. 설치된 daemon 프로세스/IPC/MCP endpoint에서 새 runtime을 활성화한 결과가 아니며 기본 handle은 계속 새 method를 거부한다. provider의 repository/scanner/키/commit은 fixture다. 운영 OS ACL·tenant 정책, 공용 출력/현재 revision 채택·idempotency claim/registry/CAS·Native 초기 의미/평가 수용·F11/P09 전체를 완료 처리하지 않는다.

다음은 원래 RouteUnqualified 및 기능별 의미 수용 조건에서 P09에 필요한 로컬 실행 허용 근거를 확인해 실제 host entry/output/head와 F11을 연결하는 것이다. 이미 완료된 private staging이나 성공8조합/Native 검사를 반복해 늘리지 않는다. 범용 SQL/OAuth/원격운영/key custody 전체를 P09 선행 조건으로 추가하지 않는다.

목표ACTIVE·외부명령현재없음·684/690소비·P09/A12/A13 OPEN·31 closure묶음/65기능·공식158/249·next165·새P10미시작 유지.
