# P09 블록 책갈피 원본 생성 함수 — 644~645

## 현재 결과

643의 고정 계획을 실제 생성 호출을 담은 PowerShell 함수로 구현했다. `block-bookmark-source645-ports.ps1`는 함수 라이브러리이며 launcher, COM 활성화, 파일쓰기, Native 실행 허가를 제공하지 않는다. 아직 worker/host 채널·저장/재열기에 연결하지 않았고 실제 블록 HWPX도 없다. 제품 block-target/Content 양성이나 F11/P09 PASS가 아니다. 최신 실제 제품 근거는639 그대로다.

## 644 설치 선언

현재2020 `11.0.0.9136`의 동일 type library를 원 P50 관측기의 읽기 전용 projection으로 확인했다. COM 서버 활성화·등록 변경·Native 메서드 호출은 없었고 Hwp PID 집합은 불변이다.

`IHwpObject.GetSelectedPos`는 DISPID30105, BOOL 반환, `slist/spara/spos/elist/epara/epos` 순서의6개 OUT pointer 선언이다. 포인터 대상 타입을 새로 해석한 것은 아니며 실제 PowerShell `[ref] int` marshalling은 Native에서 아직 미검증이다. 선언 관측은 실행 성공이 아니다. GetTextFile의 선언도 관측했으나 의미가 미확인인 옵션을 추측해 사용하지 않았다.

## 645 새 함수

- 고정 seed 텍스트는1회 `InsertText`로 넣는다. 새로운 미저장·미수정 단일 문서와 admitted owner를 요구한다. source/library에는 activation이나 임의 문서 열기/저장 경로가 없다.
- 고정8개 이름/문단/선택 좌표는643 계획과 canonical JSON으로 대조했다. Windows PowerShell5.1에서도 소스 인코딩에 따라 한글 리터럴이 달라지지 않도록 ASCII 소스의 Unicode 문자 코드로 구성했다.
- action `Bookmark`의 GetDefault 뒤에 Name/Type/Command를 설정하고 범위를 선택한다. `HSet.SetItem`의 VOID 반환을 BOOL 성공 조건으로 오해하지 않는다.
- SelectText의 BOOL 외에도 SelectionMode와 GetSelectedPos의 두 list·문단·위치를 확인한다. Execute 직전 호스트 checkpoint 뒤에 선택·매개변수 readback을 다시 확인한다. 이 작은 현재 상태 확인은 과거 시험 전체 재검증이 아니다.
- 준비/선택/실행 전후 host checkpoint와 기존 preassigned owner anchor/P58 PID 확인을 요구한다. 실제 호스트 연결은 아직 없다. callback의 BOOL 결과는 이전 가능한 Native 허가가 아니다.
- 실패는 latch하고 seed/범위를 다시 실행하지 않는다. 일부2범위 후 중단된 모델에서도 추가 Execute를 차단한다. parameter 참조는 정리하고 정리 실패가 원 실패를 가리지 않게 한다. Native owner 자체의 종료는 이 함수가 하지 않으며 기존 owned-session 경계에 연결해야 한다.

## 시험과 발견된 실제 결함

001에서 실제 함수 본문을 in-memory API 모델로 실행한22조건은 통과했다. 고정 순서/8범위, seed 재시도 거부, 미seed·dirty 문서·위치 실패, GetDefault false/비BOOL, 잘못된 이름/타입, 선택 false/비선택/다른 list·좌표·OUT 실패, Execute 직전 상태 변경, Execute false, host 중단과 no-retry, owner 변경·누락 checkpoint·참조 정리 실패/원 실패 보존을 포함한다.

이후 교차 언어 대조가 한글3개 사례에서 실패했다. PowerShell stdout의 기본 code page를 UTF-8로 해석해 문자가 깨진 전송 문제였다. 원001 영수증/당시 test와 driver를 보존했다. 실제 생성 함수는 바꾸지 않았다.

002는 test script에 명시적 UTF-8 출력과 WireOnly 분기만 추가했다. 수정 전후 전체 본문 변환 일치를 확인하고 함수/계획/선언의 원 pin을 재결속했다. **22모델과643의10모델은 재실행하지 않고 보존**했다. 새 WireOnly 실행에서8개 텍스트/숫자 타입/좌표의 canonical JSON 일치를 확인했다.

이 모델 시험은 실제 COM identity·PID/창·Native 선택/범위 생성·저장·재열기·참조 release를 실행한 결과가 아니다. owner 검사와 COM release 외부 포트는 모델로 대체했다. 실제 함수의 선택/동작 본문은 시험했지만 전체 실제 호스트 연결은 미검증이다.

| 실행 | 결과 | fresh/final | 시간 | CPU 최고 | 가용 RAM 최저 |
| --- | --- | ---: | ---: | ---: | ---: |
| 644 inspection001 | 설치 선택 선언 관측 | 3/3 + shell1 | 3.516s | 14.51% | 50.53% |
| 645 code001 | 22모델 통과, Unicode 전송 대조 실패 | 10/0 | 2.656s | 5.83% | 51.17% |
| 645 code002 | 기존22보존 + UTF-8 전송 대조 통과 | 13/13 + shell1 | 4.078s | 7.99% | 51.28% |

각 실행 cleanup=true다. 실패001의 final0을 PASS로 바꾸지 않는다. 기존1논리CPU/BelowNormal·CPU·RAM/commit95% 보호를 유지했고 새 Native/249재실행/자원 보호 중단은0회다.

## 다음 작업

고정 P09 source worker·host 채널에 이 함수를 연결한다. 현재 단일 미저장 document의 실제 identity와 getter 참조 수명, host의 정확한 단계/owner/실패 정리, 생성→저장→독립 재열기 경계를 offline에서 추가 검사해야 한다. 그 뒤 현재 세션 자격·실행 허가를 확인하고 실제 Native 원본을 캡처한다. 아직 사용자에게 전달할 실행 명령은 없다.

실제 HWPX 범위/이름/텍스트를 관측한 뒤에만 제품 block-target 및 Content 양성을 구현한다. 31묶음/65기능과 P09/A12/A13 OPEN, 목표 ACTIVE를 유지한다. 범용 P10 host 전체 구축이나 consumed Native 재실행으로 넓히지 않는다.

## 근거

- [644 선언 영수증](evidence/p09-361-block-bookmark-selection644-inspection001.v1.json):2454bytes, SHA256 `2c7e40e5d54b79f0473774cd71bf06cb42b294b8084a9c7e09376e419657d943`
- [645 최초 실패](evidence/p09-361-block-bookmark-source645-code001.v1.json):3124bytes, SHA256 `00a0d737501c59c1b833a6d33acae1ea8faf7ecbed998742d240c85ba9c27ad0`
- [645 최종 코드/전송 검사](evidence/p09-361-block-bookmark-source645-code002.v1.json):3602bytes, SHA256 `2c525189425dc4df57500b098565843db3fccf16f6c5d33c7fed342b3bf9c7c0`
- [보존된643 원본 계획](P09_BLOCK_BOOKMARK_SOURCE_PREPARATION_640_643.md)
