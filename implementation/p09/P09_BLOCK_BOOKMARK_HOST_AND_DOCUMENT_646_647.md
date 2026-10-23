# P09 블록 원본 문서 검사·호스트 연결 — 646~647

## 결과와 범위

고정 원본1문서·8블록 범위·2세션의 host adapter와 문서 검사 successor를 구현하고 새25제어를 검사했다. 기존645의 생성 함수22모델과 UTF-8 전달 결과는 원 pin을 재결속해 보존했으며 다시 실행하지 않았다.

아직 PowerShell worker/채널·실제 저장/독립 재열기·Native 실행 진입점은 연결되지 않았다. 실제 COM/프로세스에서 생성한 블록 HWPX나 제품 block-content 양성도 없다. P09/A12/A13 OPEN·31미마감묶음/65기능·최신 실제 제품639를 유지한다. 새 P10/249시험/소비된 Native는 실행하지 않았다. 목표 ACTIVE·현재 사용자 실행 명령 불필요다.

## 646 문서/참조 검사

645의 기존 문서 guard는 `GetIUnknownForObject`의 AddRef는 해제했지만 `XHwpDocuments`/`Active_XHwpDocument` getter RCW 획득은 명시적으로 해제하지 않았다. 실제 누적량이나 PC 프리즈 원인으로 확인한 것은 아니다. 반복 검사 전에 수명 경계를 보완했다.

새 `block-bookmark-source646-document.ps1`는 기존645 파일을 바꾸지 않는 명시적 successor다. 향후 고정 worker만645 뒤에 로드한다. admitted/아직 close하지 않은 owner의 실제 P58 확인, 동일 collection/document IUnknown, 단일 미저장 편집 문서, getter 전후 owner를 확인한다. BOOL/INT 선언 타입을 섞어 허용하지 않는다.

IUnknown 포인터와 getter로 얻은 문서/collection 참조를 모두 정리하며 owner의 보유 alias를 FinalRelease하지 않는다. 정리 실패는 성공으로 처리하지 않고 원 검사 실패가 있으면 보존한다. 현재 source의643 고정 생성 계획은 그대로다.

새13모델은 위 실제 guard 본문을 실행한다. 정확한 owner·참조 정리 순서, 미admit/비BOOL/종료시도, 검사 중 owner 소실, collection/active document 불일치, 문서 수/타입, 저장된 경로, 비편집 모드, 정리 실패/원 실패 보존을 포함한다. 네이티브 포인터/RCW/프로세스 API는 모델로 대체했으므로 실제 COM reference count나 owner가 qualified된 것은 아니다.

## 647 고정 호스트 adapter

`block_bookmark_source647_host.py`의 Host는 기존 FixedEightHost의 **live 일회용 handoff, worker kernel lease, PreassignedSessionScope, 원 CPU/RAM/정확한 PID·창 보호**를 합성한다. 저장된 영수증이나 순수 Schedule 모델은 live handoff를 발행하지 못한다. 모델 handoff를 실제 Host 생성자에 넣는 시험은 거부된다.

원16 checkpoint는 자원/owner 관리 순서로만 재사용한다. 과거 source_open/sdk_insert 등의 이름을 실제 수행했다는 뜻으로 사용하지 않는다. 새 의미 단계는 미저장 문서 결속→seed→책갈피8개→created 저장/이미지/결속→종료→독립 재열기→reopened 저장/이미지→종료다. 현재는 host 순서만 구현한 것이며 실제 worker 동작 결과가 아니다.

고정 wire는16 checkpoint+2 owner admission+35범위 pulse+1 finish=54개 요청이다. seed3개와 각 범위의 준비/선택/실행/반환4개가 정확한 순서여야 한다. case_index는 INT1만 받고 경로/명령/authority 추가 키·BOOL 좌표·중복 JSON 키는 거부한다. owner descriptor는 생성 응답2개에서만 검증해 허용한다.

각 pulse는 같은 kernel worker를 관측하고, 현재 입력 경계 안의 admitted save owner에 원 Native observe를 호출한다. 과거 이력 전체를 pulse마다 해시하지 않는다. 재열기/마지막 종료 전에는 기존45초 guarded drain을 사용한다. 자원 오류·프로토콜 오류 후 새 작업을 금지하고 실패 finish만1회 허용한다. 원 강제종료 금지/불확실한 owner handle 보존 정책을 유지한다.

새12모델은 전체54요청·8범위/2세션, 닫힌 schema/중복 키, range 순서/누락, 조기 성공 거부, 실패 후 정리1회, descriptor/authority, 재실행 금지, 예외 값 비노출과 **실제 Host adapter 본문**의 worker/Native 관측·원 checkpoint 변환/drain 호출·가짜 handoff 거부를 검사했다. 이들은 모델 시험이며 실제 Job/Native 연결 증거가 아니다.

## 실행 근거와 다음 작업

[647 code001](evidence/p09-361-block-bookmark-source647-code001.v1.json): 4132bytes, SHA256 `b954c2a38c1fe316981bf785b1e667ad6ff22ff0ad6d167726cb07fee1502c7d`.

- 새 guard13 + host12 통과; 기존645의22 재실행0.
- fresh/final26/26, shell final1, cleanup=true, Hwp PID 집합 불변.
- 5.968초, CPU 최고6.61%, 가용 RAM 최저50.9936%; 보호 중단0.
- 원1논리CPU/BelowNormal/CPU/RAM·commit95% 보호 유지; 새 Native0.

다음은 이 host와646 guard를 사용하도록 고정 PowerShell worker·채널을 연결하고, 저장/재열기·현재 응답 진단·실패 정리를 Native 없이 시험하는 일이다. 이후 실행 경로 전체의 현재 입력·세션 자격/허가·소유권을 검증한 뒤에만 실제 원본 캡처를 할 수 있다. 실제 HWPX 범위/이름/텍스트 관측 전에는 제품 block-target XML을 추측하지 않는다.
