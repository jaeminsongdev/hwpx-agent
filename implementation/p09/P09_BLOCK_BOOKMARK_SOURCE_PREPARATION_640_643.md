# P09 블록 책갈피 원본 준비 — 640~643

## 결과와 한계

639의 실제 제품 표시 admission은 유지한다. 보통 책갈피의 Content 거부를 해제하거나 잘못된 `?` 표시를 양성으로 승격하지 않았다. 이번 변경은 기존 자료의 제한된 조회, SDK 원문/설치 선언 확인, 고정 원본 캡처 계획까지다. 실제 블록 책갈피 HWPX, Native 실행 진입점, block-content 양성 구현은 아직 없다.

P09/A12/A13 OPEN, 31미마감 묶음/65기능, official249의158수용/91대기/다음165를 유지한다. 묶음 수는 세부 작업 수나 진행률이 아니다. 새 P10 구현·소비된 Native 재실행·249전체 재검증은 하지 않았다. 목표는 ACTIVE이며 현재 사용자 실행 명령은 필요하지 않다.

## 640 — 기존 원본 조회

`fixtures`, `implementation/p09/evidence/private`, `implementation/p08/evidence/private`에서9,418개 메타데이터 항목과 HWPX2,752개를 집계했다. 직접 캡처 추적 표식이 있는 디렉터리의142개/2,241,584bytes만 파싱했고 block BOOKMARK 범위 후보는0개였다. 나머지2,610개는 파싱하지 않았다. 따라서 저장소 전체에 블록 원본이 없다고 결론 내리지 않는다. 추적 표식 자체도 Native 생성 출처의 충분한 증거가 아니다.

첫001은 메타데이터 발견 수의2048상한에서 멈췄다. CPU 최고4.38%였으며 과부하 중단이 아니다. 실패 원본/당시 코드를 보존하고 범위 선택을 좁힌002에서 기존 제어7개는 재실행하지 않고 새 선택 제어2개를 검사했다. 선택된 파일은 fresh/final149/149, 메타데이터 목록도 종료 시 비교했다.

## 641~642 — 원문과 현재 설치 선언

PDF skill에 따라 보존된 SDK 원문을 페이지 이미지로 렌더링하고 직접 확인했다.

- `ParameterSetTable_2504.pdf` p.4: parameter set `BookMark`; `Name:PIT_BSTR`, `Type:PIT_UI`의0=보통/1=블록, `Command:PIT_UI`의0=생성/1=이동/2=편집.
- `ActionTable_2504.pdf` p.2: action ID는 `Bookmark`, parameter set ID는 `BookMark`로 대소문자가 다르다. p.10의 검색 관련 항목은 생성 action 결속 근거로 사용하지 않는다.
- 2504 SDK는 현재 설치 Hancom2020보다 최신 문서다. 원문 구문을 확인했어도 정확한2020 동작이나 HWPX 이름/범위 표현을 확인한 것은 아니다.
- 현재 `11.0.0.9136`의 등록된 type library를 `LoadTypeLibEx(REGKIND_NONE)`로 읽었다. COM 서버를 활성화하지 않았고 registry는 읽기 전용이며 Hwp PID 집합도 불변이다.
- 설치 선언에서 `HBookMark.Command`의 UInt32 setter와 `HSet`은 관측했지만 `Name`/`Type` 직접 setter는 관측하지 못했다. 이것만으로 동적 호출이 불가능하다고 단정하지 않는다. 계획은 선언된 `HSet.SetItem(BSTR, VARIANT)` 경로를 사용한다. 이 메서드의 반환은 BOOL이 아니라 VOID다.
- `HAction.GetDefault/Execute`의2인수 서명과 `IDHwpAction`의 다른 서명을 혼동하지 않는다. `SelectText`는4개 INT32 인수, BOOL 반환 선언이다. 실제 호출 결과는 아직 없다.

SDK review001의 action 텍스트 탐색 실패는 원본대로 보존했다.002는 parameter 페이지를 재렌더링하지 않고 PDF의 글자 간 공백에 맞춘 action 탐색만 수정했다. 원 PDF와 파생 PNG는 로컬에 보존한다.

## 643 — 고정 원본 계획과 코드 검증

고정 합성 문서1개에 서로 다른8개 블록 범위를 만들고 생성 세션1개와 독립 재열기 세션1개로 관측하는 계획이다. 범위별로 한글을8번 다시 시작하지 않는다. 한글/영문/공백/경계/특수문자 사례를 포함하되 모두 BMP·단일 문단 범위다.

`block_bookmark_source_plan643.py`는 프로세스/COM/파일쓰기 API가 없는 순수 계획 모델이다. 이름·텍스트·좌표·경로가 고정되어 있으며 다음 순서를 선언한다.

`GetDefault("Bookmark") → HSet.SetItem(Name) → SetItem(Type=UInt32(1)) → Command=UInt32(0) → SelectText → owner/선택/매개변수 확인 → Execute 1회`

선택은 GetDefault 뒤에 수행한다. Python 문자열 범위 검증은 Native의 실제 문단/위치 원점·개행 처리·선택 반환을 증명하지 않는다. HWPX 범위/이름 매핑은 `UNOBSERVED_CAPTURE_FIRST_DO_NOT_GUESS`로 남긴다.

새 모델 제어10개가001에서 통과했지만 계획 게시 단계가 receipt root `state` 누락으로 실패했다. 실패와 당시 드라이버를 보존했다.002는 모델/시험이 byte-identical임을 결속해10개를 다시 실행하지 않고, `state`가 있는 계획 packet의 게시→재읽기→전체 round-trip을 확인했다. 계획은 실행 허가가 아니며 `native_entry_implemented=false`, `native_execution_authorized=false`다.

## 검증·자원 결과

| 결과 | fresh/final | 시간 | CPU 최고 | 가용 RAM 최저 | cleanup |
| --- | ---: | ---: | ---: | ---: | --- |
| 640 run002 제한 조회 | 149/149 | 21.016s | 40.62% | 50.86% | true |
| 641 review002 SDK 페이지 | 8/8 + renderer122/122 | 55.172s | 11.20% | 50.86% | true |
| 642 inspection001 설치 선언 | 3/3 + shell1 | 3.5s | 8.01% | 50.84% | true |
| 643 audit002 계획 게시 | 16/16 | 8.563s | 4.47% | 51.13% | true |

1논리CPU/BelowNormal, 기존 CPU 보호와 RAM/commit95% 보호를 유지했다. 보호 중단·새 Native 실행은0회다. 새 Rust 제품 빌드나 과거 수용 시험 전체를 재실행하지 않았다.

## 다음 구현 경계

1. 기존 P09 owned-session/host/CPU·RAM·입력 보호를 재사용하는 **고정 블록 원본 worker와 adapter**를 구현하고, Native 없이 순서·실패·정리 경계를 시험한다. 범용 P10 호스트 전체를 만들지 않는다.
2. 실제 Native 시작 전 현재 owner/세션/입력 자격과 실행 허가를 별도로 확인한다. 아직 명령어를 전달할 준비가 된 것은 아니다.
3. 실제 저장/독립 재열기 HWPX의 범위·이름·텍스트를 관측한 뒤에만 제품 block-target 모델/작성·Content 양성을 구현한다. XML을 추측하거나 caller flag로 출처를 대체하지 않는다.
4. 유효 point 경로의 로컬 backend/새 출력·이름 변경/이동·다른 P09 대상 및 필수 의미 검증은 별도 미마감으로 유지한다.

## 증거

- [640 제한 조회](evidence/p09-361-block-bookmark-source-query640-run002.v1.json), [원 실패](evidence/p09-361-block-bookmark-source-query640-run001.v1.json)
- [641 SDK 페이지](evidence/p09-361-block-bookmark-sdk641-review002.v1.json), [원 탐색 실패](evidence/p09-361-block-bookmark-sdk641-review001.v1.json)
- [642 설치 선언](evidence/p09-361-block-bookmark-typelib642-inspection001.v1.json)
- [643 고정 계획](evidence/p09-361-block-bookmark-source-plan643.v1.json): 3726bytes, SHA256 `856cb37d5ca7d32c398017ed2072bb07597b2aeb1c10c80b8f926adf960cebff`
- [643 검증](evidence/p09-361-block-bookmark-source-plan643-audit002.v1.json), [원 게시 실패](evidence/p09-361-block-bookmark-source-plan643-audit001.v1.json)
