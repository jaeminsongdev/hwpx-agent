> 현재 기준(2026-10-25): [로컬 생성 후보716~721](P09_LOCAL_GENERATED_PREVIEW_716.md) 검증 완료. 비공개 후보 저장·재열기16검사/실제8조합 성공,source1194/1194·artifact32 final·cleanup=true. 원guard737표본,CPU최고18.95%·가용RAM최저35.3551%·보호중단0. 기존713/Native/249 재실행0. 실제host요청·workspace권한·공개결과/현재revision채택·남은F11 미완료. 과거713 CPU100%원인·프리즈해결 미확정. 목표ACTIVE·외부명령현재없음·684/690소비·P09/A12/A13 OPEN·31묶음/65기능·158/249·next165·새P10미시작. 아래는 이전 이력이다.

# 단계별 자원 표본 보존714

2026-10-25. 이전 턴710/713은 새 삽입 요청/공통 진입점·고유13조건/실제8조합을 검증한 progress다. 전체 P09~P20 목표와 P09/A12/A13 OPEN·새P10미시작을 유지한다.

## 대상과 검증 방법

713의 CPU100% 집계는 시점·횟수·검증 단계가 없어 원인을 복원할 수 없다. 기존 metadata_cpu_observer620은75% 이상에서 추가 프로세스 조회를 생략한다. 이 보호 동작과 기존 단일 system sampler·CPU/RAM/commit 판단·주기·baseline은 바꾸지 않는다.

새 resource_bundle714는 같은 guard Windows instance에만620을 연결하고 원 표본에 고정 phase·순서·monotonic 관측 시각/간격을 추가한다. phase 전환이 별도 표본/프로세스 조회를 발생시키지 않는다. 최종 guard.samples 전체(후속 parent/job 필드 포함)를 row-shape 방식으로 무손실 보존하고, key 부재/명시적 None을 구분한다.4096표본/256phase/2MiB 출력 예산을 넘으면 거부하며 표본을 잘라내지 않는다. 과거713의 표본을 만들어내거나 CPU100/프리즈 원인을 해결했다고 주장하지 않는다.

새9모형은 원 sampler 횟수/값, hot CPU100·조회 unavailable 보존, 원 오류 전파, phase 비강제 sampling, late field·missing/None 무손실, instance 복원/cleanup 실패·중복 연결·원본 예산 거부를 확인한다. 이어 새 빌드/제품 실행 없이 실제 guard의 가벼운 모형/입력·backend source 읽기에 연결한다.713 성공·Native/249를 재실행하지 않는다. 기존620/핵심 guard 코드는 수정하지 않는다.

## 검증 결과715

`evidence/p09-361-resource-bundle715-audit003.v1.json`은 `QUALIFIED715_LOSSLESS_PHASE_RESOURCES_NEW9_LIVE_ORIGINAL_GUARD_BACKEND_SOURCE_ONLY`,35,565B, SHA `ce7f14dd440342af0299ef50d344f7079d8376b143b83f5dda7e2714505d71fe`다.280fresh/final280·Python 실행기1final·cleanup=true·37.14초·CPU최고13.33%·가용RAM최저38.9341%다. Cargo/제품/SQL/Native·성공713·과거620 모형20개는 실행하지 않았다.

최초 audit001에서 unittest discover 실행은 exit0이었으나 개별 결과 이름 수집이 실패해 원 감사는 FAILED로 보존했다. 수집 정규식이 Windows CRLF 끝문자를 허용하지 않는 결함을 코드에서 확인했다. 원 stderr는1,643B/SHA로만 보존돼 당시 문자별 원문을 복원할 수는 없다. 같은 코드·입력·로더에서 현재 발견되는9개 시험 ID를 **실행 없이** 확인해 최초 exit0과 결속했다. 개별 시험 이름이 최초 원본에 수집됐다고 주장하지 않는다. audit002는 목록 확인용 자식 코드의 newline escaping 오류로 실패했고 모형을 실행하지 않았다. 최종003은 줄 조합으로 교정해 이름 목록을 JSON으로 읽으며 command exit/출력 SHA를 해석 전에 기록한다.001/002 영수증·private metadata·source archive는 보존했다.9모형을 다시 실행하지 않았다.

실제 원 guard 표본74개를 보존했다.표본이 있는 단계는 startup2/input_binding35/model_checks1/final_source35/final_resource1이고, backend_inspection/final_binary는 원래0.5초 cadence 안에 끝나 표본0이다. phase-change marker로 수행 경계를 남겼으며 CPU 값을 만들어 채우지 않았다. 원래 guard가 추가한 parent CPU/메모리 필드와620 kernel/user·process 진단을 그대로 무손실 row-shape로 저장했다.

기존620/V4의 조회6회·측정5회, 추가 측정 총/최대 약0.015초·cleanup confirmed를 기록했다. 경고 CPU75% 이상의 추가 프로세스 조회 생략은 유지한다. 현재 관측이 낮았다는 사실은 과거713 CPU100%의 원인/프리즈 해결 증거가 아니다. 과거 원인은 계속 미확정이며 새 표본으로 옛 표본을 대체하지 않는다.

새 helper는 명시적으로 연결한 한 guard instance에만 작동한다. 다음 새 검증 실행기에서는 시작 전에714를 연결하고, phase를 표시한 뒤 최종 원본 표본/observer cleanup까지 보존해야 한다. 과거 소비된 실행기·전역 Windows 클래스·Defender/시스템 설정·보호된 runtime/trust DB는 변경하지 않았다. 표본/출력 예산을 넘으면 실패하며 성공으로 게시하거나 표본을 잘라내지 않는다. caller는 실패 시 메모리에 남은 원 guard.samples도 기존 forensic 보존 예산 안에서 보존해야 한다.

## 실제 backend 경계 확인과 다음 구현

같은 감사에서 local-workflow/local-companion-daemon Cargo·구현과 MCP server/프로토콜6파일을 source-only로 읽고 끝에 동일성을 확인했다. local-workflow는 현재 open/materialize/diff/publish를 제공하며 기존 입력을 관리 slot으로 복사한다. 두 crate 모두 제품 요청 라이브러리 의존성이 없다. 즉710 새 요청 → 생성된 후보 → 관리 slot/지속 출력으로 이어지는 실행 단계는 아직 없다. 이 소스 관측을 실제 backend 실행 수용으로 바꾸지 않는다.

다음 순서는 다음과 같다.

1. 기존 local-workflow의 source/output 동일성·링크 거부·길이 제한·create-new·실패 보존 경계를 사용해, **신뢰된 host 내부에서 검증된 생성 후보를 받는 단계**를 추가한다. 공개 요청에서 raw bytes/XML/경로를 받지 않는다.
2.710 제품의 현재 원본/ACL/head 확인과 최종 writer callback을 이 단계에 연결한다. 원 source SHA·선택/계획·candidate SHA 및 현재 권한을 결속하고 실제 파일 재열기·실패/변조/덮어쓰기/다른 source 부정을 검증한다. 격리 memory/scanner/키를 운영 권한으로 승격하지 않는다.
3. 현재 로컬 사용자/설정의 허용 실행·지속 출력·현재 revision 채택 계약을 명시해 실제 host/bridge 경로를 연결한다. 승인/registry/CAS·부분 source의 full-context 경계를 우회하지 않는다. 원격/범용 SQL 전체를 새 P09 선행 조건으로 넣지 않는다.
4. 이미 확보한 고정8종 캡처를 재사용하고 남은F11 대상·이동/이름 변경·내부 hyperlink/의미 검증을 묶어 준비한다. 실제 Native가 필요해지면 기존 명령을 재실행하지 않고 새 자격/범위로 인계한다.

목표 ACTIVE·현재 외부 명령 없음. 실제 로컬 생성/지속 출력/head 채택·F11/P09는 미완료이며 P09/A12/A13 OPEN·31 closure 묶음/65기능·공식158/249·next165·새P10미시작을 유지한다.
