# P09 책갈피 CROSSREF 변경 후보·저장 원본·공통 compiler 연결

책갈피 상호참조의 실제 원본 Command를 변경하는 후보를 기존 저장 서비스와
`OperationPlanCompiler`에 연결했다. 선택한 명령 외 바이트와 저장 캐시는 보존하며,
컴파일된 계획을 등록·revision 반영·한글 실행 권한으로 취급하지 않는다.
P09/A12/A13은 OPEN, 목표는 ACTIVE이며 P10은 시작하지 않았다.

## 제품 구현과 재사용

1. **621 원본 변경:** source field ID/정확한 fingerprint/meaning SHA와 같은 원본의
   책갈피 target ID, typed 표시/하이퍼링크 옵션만 받는다. 원래 fresh 전체 복원 proof,
   전체 필드 coverage, lock/review/table 보호, 보존 patch/writer와 의미 readback을
   사용한다. 중복·stale·미지원·잘못된 대상·no-op·한도 초과는 배치 전체를 거부한다.
   명령을 선택적으로 바꾸되 캐시를 갱신하거나 Native 결과를 합성하지 않는다.
2. **622 저장 원본:** 현재 provider scope/head/Result descriptor와 실제 ACL/AEAD,
   격리/scan 상태·전체 원본 bytes·폼 복원 proof를 재확인한다. `DocumentWrite` token
   scope는 필요하지만 원자적 프로젝트 쓰기 권한/lease/CAS 증명은 아니다. 매 전달의
   writer callback 안에서도 ACL/전체 원본/head를 확인하고 관측한 거부를 영구 고정한다.
3. **623 공통 compiler:** 이미 import한 필드에서 선택한 앵커만 보관한다. 기존 공통
   `resolve_original_source_owners`, `SelectorSnapshot`, `OperationPlanCompiler`를
   그대로 사용한다. 원본의 실제 구조적 owner·revision·graph와 source/output/receipt,
   field/meaning/command/target/request hash를 계획에 결속한다. candidate를 이동해
   graph/출력 clone, field/meaning 재수입, lowerer/writer replay를 추가하지 않는다.
   컴파일 전과 후의 현재 권한을 확인하고, 전달 때는 원래 최종 검사를 재사용한다.

로컬 compiler capability `ref.crossref_command_edit`는 기존 명령 편집이다.
REF-035 `ref.crossref_insert`의 새 삽입을 구현했다고 주장하지 않는다. 이 로컬 정의는
공개 609기능 catalog/신뢰 registry의 새 지원 선언이나 실행 route가 아니다.
원본 command/책갈피 이름/캐시 내용은 계획 인자·receipt·Debug에 노출하지 않는다.
주 Source v15/field-meaning v2/의미 graph partial-v3와 미해결4개는 유지했다.

구현:

- `crates/hwpx-package/src/document_import/fields/semantics/source_index/bookmark_updates.rs`
- `crates/product-cli/src/reference_validation_product/source_crossref/bookmark_updates.rs`
- `crates/product-cli/src/form_stored_provider/actual_import/bookmark_command_output.rs`
- `crates/product-cli/src/form_stored_provider/actual_import/bookmark_command_output/compiled.rs`

계약: [source/stored/compiler v1](../../protocol/migrations/p09-source-stored-bookmark-command-update-v1.md).

## 검증된 범위

| 단계 | 현재 근거 | 실제 확인 | 완료로 승격하지 않은 경계 |
| --- | --- | --- | --- |
| 621 | [audit006](evidence/p09-361-bookmark-command-updates621-audit006.v1.json) | 9조건: 동일 입력·본문의 기존 통과8 유지+수정1 실행. 일반 빌드에서 실제 saved/reopened16개에 변경 후보 생성. 969fresh/final969·cleanup true | Native 캐시 갱신/실제 이동·표시, 서비스 등록/게시 |
| 622 | [audit002](evidence/p09-361-stored-bookmark-commands622-audit002.v1.json) | 저장 서비스12조건과 실제 캡처 원본1개, 원본/head/등록 불변. 919fresh/final919·cleanup true | 운영 SQL/실제 scanner·key custody/원자적 CAS/route |
| 623 | [audit004](evidence/p09-361-compiled-bookmark623-audit004.v1.json) | 새 compiler8+직접 영향 저장12의 고유20조건, 일반 실행 빌드의 실제 캡처1개. 최종 실행은19동일성 유지+수정1. 928fresh/final928·artifact4final·cleanup true | 등록된 executor, 변경 결과 ingest/revision CAS, Native, P09 Gate |

623은 첫 시험 본문 실행에서19개가 통과했다. 실패한 복수 필드 사례의 fixture만
바뀌었고, 통과19의 제품·공통 함수·시험 본문·원본/실행 입력 동일성을 대조했다.
그 fixture는 정의와 실패 사례의 호출 한 곳에서만 쓰인다. 최종 전체 입력 확인을
별도 현재 audit004로 닫았으며, 과거 audit002/003의 FAILED/finalfresh0은 변경하지
않았다. 같은 제품 본문19개를 다시 실행하지 않았다.

신규8조건은 실제 캡처의 일반 경로, 계획의 원 revision/graph·해시/12개 인자·canonical
round-trip·비노출, 역순3필드/2문단의 실제 서로 다른 ctrl owner, 읽기 scope/ACL/격리/
암호문/head 거부, 전달 거부의 sticky poison, 컴파일 후 head 변경/실제 ACL 철회,
compiled writer callback의 최종 head 거부를 확인했다. owner 시험은 제품의 부모 맵이
아닌 독립적인 원본 source-span 포함 관계로 가장 가까운 owner를 대조한다.

실제 캡처는 원010 고정8종 중 case3 saved 한 파일이며 원본 자체는 읽기 전후 불변이다.
실제 ArtifactService ACL/AEAD와 RevisionService를 사용하지만 repository/scanner/키는
격리 fixture다. 운영 SQL·장기 보관·신뢰 worker를 실행한 증거는 아니다. 실제 값은
제품 출력 bytes에서 읽었고 원본/head/결과 ingest/route와 P09 완료 플래그는 false다.

일반 EXE `target/debug/examples/p09_compiled_bookmark623.exe`는8954880B,
SHA256 `01d89caac98735e1598fd8df7f6a4e7b20190d3fb5f26540ddc7cfc1b66ca31c`다.
시험/일반 빌드의 실제 dep-info 입력을 사전에 결속하고 바이너리/dep-info4개를 최종
재확인했다. 원 consumed010 probe는 재빌드/실행하지 않았고 기존 SHA가 동일하다.

## 실패 원본과 수정

- 621 audit001~005: 비공개 getter 접근 컴파일 오류와 시험 privacy/보호 판정의 잘못된
  기대를 원본에 보존했다. 제품 parser의 거부를 완화하지 않았다. 보호7조건은 invalid
  source의 초기 거부와 change-specific 보호 거부를 구분하며 원 실패는 PASS가 아니다.
- 622 audit001: 시험 읽기 helper의 `Result` error type 표기 누락으로 컴파일 실패,
  시험 본문0. 제품 라이브러리는 컴파일됐으며 시험 타입만 수정했다.
- 623 audit001: SDK 요청 enum과 source 관측 enum을 시험에서 혼용한 E0308 두 곳,
  시험 본문0. 제품 compiler는 변경하지 않고 관측용 enum으로 비교했다.
- 623 audit002:19pass/1fail. 복수 필드 fixture가 bookmark ctrl을 run 밖에 둬 import
  거부됐다. fixture만 유효한 run 안으로 수정했다.
- 623 audit003: 수정1만 실행했으며 import 후 Output 거부. 최소 `<header/>` fixture에
  존재하지 않는 글자 모양0을 `charPrIDRef`로 참조하고 있었다. 실제 ID 규칙/patch를
  완화하지 않고 서식이 필요 없는 owner fixture의 그 잘못된 참조만 제거했다.
- 623 audit004: 같은 강도의3필드/역순/독립 owner oracle을 유지한 수정1과 보존19,
  일반 빌드/고정 실물 원본 및 최종 입력 확인까지 마감했다. 실패 audit001~003은
  `source-archive/p361-bookmark-compiler623/` preimage와 별도 receipt/raw spool로 보존한다.

## 자원과 원본 보존

623 최종182.110초·시스템 CPU 관측최고26.15%·가용RAM최저38.658%였다.
앞 세 시도 CPU최고16.48/12.11/25.59%, 가용RAM최저37.324/38.523/38.892%였으며
보호 중단은 없었다. 마지막 Job readback은1코어·머신CPU6.25% hard cap·낮은 우선순위·
breakaway disabled·기존 RAM/commit95% 보호다. peak Job private는 시험760.78MiB,
일반 빌드758.42MiB, 고정 원본 관측54.78MiB이고 종료 후 active_processes는 모두0이다.

기존 K32 CPU/RAM 표본352회와 별도 process query24회(비교23), 누적 추가 비용95ms,
최대16ms를 기록했다. 기존 보호 판단은 대체하지 않았고 새 sampler thread/process,
WMI/PDH·관리자 권한·시스템 설정 변경은 없다. unavailable을0으로 바꾸지 않으며,
이 결과로 Defender/다른 앱의 인과나 PC 프리즈 해결을 확정하지 않는다.

최종 packet121311B/SHA256 `37b3212d0c87fafd7f473f088107553b9cc12bd60e6b3cf026f06fee4d6da7d6`,
private 원문437147B/SHA256 `1f3e8d055b7a111deffa0474988e1d06646632a5b004a50a39a31402e47f97cb`다.
원문을 먼저 immutable spool에 보존했고 publisher256KiB/복원4MiB 한도는 유지했다.
621/622 증거도 새 입력으로 덮어쓰지 않았다. 현재 상태 문서는 최신 prefix를 추가하되
기존 본문 suffix의 bytes/SHA를 전후 대조한다.

## 남은 연결과 Gate

다음 직접 작업은 이 후보의 owned/strict 요청·공통 선택 경로를 기존 manifest/job/저장
bridge에 연결하고 결과 검사/등록/CAS의 실제 경계를 검증하는 것이다. 컴파일이 끝났다는
이유로 RouteUnqualified를 해제하지 않는다. 다른 참조 대상/보조 상태/문서 흐름,
실제 Native 갱신·이동·표시·저장/재열기 및 통합 Gate도 남는다.

공식249큐158수용/91대기/next165·새수용0은 그대로이며 전체 P09 잔여 개수/완료율이
아니다. 이번 작업에서 한글/COM/Native·SQL·249·기존 Native008~010·외부001~010을
실행하지 않았고 Native011도 실행하지 않았다. 원본·과거 실패·허가 경계를 보존한다.
P09와 후속 단계의 공통 운영 완료 조건은 원래 phase 소유권과 대조할 필요가 있지만,
이번 변경으로 Gate 조건을 제거·완화하거나 P09를 완료 처리하지 않았다.
