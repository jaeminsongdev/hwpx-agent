> 현재 기준(2026-10-26): [로컬 세션·작업 폴더/제품 연결722~725](P09_LOCAL_BOOKMARK_HOST_722.md) 검증 완료. in-process private/v5 인증·허용 workspace→원래 제품→실제 비공개 파일 경로의 새8검사(실제681 source1건 포함)가 통과했다. source1217/1217·실행산출물2 final·cleanup=true,원guard569표본·CPU최고12.32%·가용RAM최저36.2263%·보호중단0. 001의 기존3개 실행은 보존하되004에서 반복/전체 자격 승격하지 않았고001~003 실패도 유지했다. 설치된daemon/IPC/MCP 활성화·공개결과/현재revision채택·Native 의미수용/F11은 미완료. 기존721/713/Native/249 재실행0. 목표ACTIVE·외부명령현재없음·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10미시작. 아래는 이전 이력이다.

# 현재 원본에 결속한 로컬 생성 후보 보관716~721

2026-10-25. 이전 턴714/715는 원 guard74표본·phase 무손실 보존/9모형 실행·대상 결속/실제 guard 연결로 progress다. 전체 P09~P20 목표와 P09 Gate 선행 조건을 유지한다.

## 변경 대상과 검증 계약

기존 local-workflow는 입력 파일 materialize/diff/publish만 제공했다. 신뢰된 host 내부에서 생성한 후보를 관리 source SHA에 결속해 별도 `generated-preview.hwpx`로 보관하는 단계와 읽기 전용 재열기 확인을 추가한다. 공개 JSON/도구에 raw bytes/XML/경로를 추가하지 않는다. 기존 publish가 읽는 candidate.hwpx와 다른 비공개 slot이므로 이 경로를 통한 자동 공개/등록/현재 revision 채택은 없다.

source/candidate SHA·길이·링크/경로·create-new·sync/readback을 확인하고 Windows source/preview handle은 쓰기/삭제 공유를 거부한다. 실패한 비공개 부분 파일은 보존하며 재시도에서 덮어쓰지 않는다. 기존 materialize/publish·Git/승인·daemon/MCP schema는 변경하지 않는다.

710 제품은 원래 최종 ACL/head/AEAD callback 안에서 이 I/O를 수행하고 파일 재열기 뒤 현재 권한/source를 다시 확인한다. source graph/출력 재-import·재-lowering/전체 clone을 추가하지 않는다. 후속 실패는 비공개 미수용 파일로 보존하며 성공 receipt/공개 결과로 바꾸지 않는다. 결과 receipt는 경로/이름/본문 없는 해시와 관측이다. 저장소·scanner·키·commit fixture는 여전히 운영 자격이 아니다.

검증은 새 파일 I/O·제품 연결/권한·원본/변조/덮어쓰기/재열기·미공개 negative와 직접 영향받는 기존 workflow 일부 및 실제681 source8조합의 디스크 readback에 한정한다. 기존713/Native8/249 전체 재실행은 하지 않으며, 새검증기는714를 시작 전에 연결하고 원 phase 표본을 보존한다. 원래 CPU/RAM/commit·1코어/낮은 우선순위 보호를 유지한다.

## 검증 결과721

첫 실행에서 새 I/O6·제품 연결/권한7·기존 workflow3 총16검사가 통과했다. 실제681 source의 표시4종 × hyperlink2종을 공통 제품 요청으로 처리해8개 비공개 후보를 저장·재열기했다. 후보 SHA는 기존681과 같고 원본·현재 head는 유지됐다. output은 비었고 기존 publish/diff가 요구하는 candidate.hwpx는 없다.

- receipt: implementation/p09/evidence/p09-361-local-stage721-product001.v1.json
- 상태: QUALIFIED721_CURRENT_PRODUCT_PRIVATE_GENERATED_FILES_CORE6_PRODUCT7_OLD3_ACTUAL8_NOT_PUBLICATION_OR_REVISION
- source fresh/final1194/1194; 실행파일/의존성정보8개+생성HWPX24개 총32 artifact final SHA 확인.
- 원guard 단계·시각·후속필드 포함737표본 무손실 보존. CPU 최고18.95%, 가용RAM 최저35.35508027750005%, cleanup=true, 보호중단0, 실행377.125초.
- receipt183208 bytes, SHA256 47f1ac80035ccb8a0341caa46cf53f39711ce480caeee6b3cb631cee7e27db92.
- 원문: private/p09-361-local-stage721-product001-forensic/manifest.v1.json.
- 생성: private/p09-361-local-stage720-generated001/c01..c08의 input/source.hwpx·관리 source.hwpx·generated-preview.hwpx 총24개. 예제720/검증721 소비, 재실행 금지.

권한 회수·AEAD 변조·head 변경·다른 문서·잘못된 source/digest·빈/과대 출력·덮어쓰기·hardlink 목적지·저장 후 변경을 거부했다. 저장 뒤 head 변경 시 성공 receipt를 반환하지 않고 비공개 미수용 파일을 보존한다. 기존 공개 출력 API로 새 비공개 파일을 가져갈 수 없는 것도 확인했다. CPU/RAM/commit·1코어/낮은 우선순위를 유지했고 기존713/Native8/249는 재실행하지 않았다.

## 남은 경계와 다음 순서

완료 범위는 현재 원본/권한에 결속한 제품 내부 호출과 실제 관리 파일의 저장·재열기다. 저장소·scanner·키·commit은 fixture다. 실제 daemon/MCP 요청 연결, 운영 workspace OS ACL·tenant 정책, 허용된 공개 결과/현재 revision 채택, registry/CAS 실행 자격, Native 의미 수용은 미검증이다. PartialSource/Graph/RouteUnqualified 차단도 유지한다.

다음은 현재 허용된 로컬 host/bridge에서 workspace 권한과 요청을 연결하고 통제된 결과 출력·현재 revision 채택을 구현·검증한 뒤 남은F11을 진행한다. 범용 SQL/OAuth/원격배포/key custody 전체를 새 P09 선행 조건으로 확장하지 않는다. 이번 낮은 CPU는 과거713 CPU100% 원인/지속시간이나 PC 프리즈 해결의 증거가 아니다.

목표ACTIVE·외부명령현재불필요·P09/A12/A13 OPEN·31 closure묶음/65기능·공식158/249·next165·새P10미시작 유지。
