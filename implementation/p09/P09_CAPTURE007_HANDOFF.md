> 최신 2026-10-22 / 외부007 실제 FAILED 확인·새008 수정/로컬 준비 완료·외부 실행 대기 PAUSED. 007은 case1 source_bind / P09_XREF_BIND_CAPTURE_SEVEN_APPLICATION_REAL_WINDOWS, 완료0/8·산출물0·cleanup true이며 원본117315B/SHA8d5cf7c58b6e9d8346eb1131c5403644c68a3a22087b84449d8ec7cec439d518와 raw spool을 보존했다. 새008은 반환 Document.Application을 동일 owner 문서컬렉션·활성문서 IUnknown으로 직접 결속하고, 창/버전은 verified Owner.hwp에서 읽어 held 윈도우·HWND/PID·버전·문서수 검사를 모두 유지한다. 원본 잠금/owner/paired 입력/CPU·RAM 보호·non-killing 정리는 유지했다. 새 Python 경로5/Rust4·Python 모델50/Windows30, READY 실제거부·Native생성trap0 및 공개 loader244fresh/final244·cleanup true를 확인했다. 수정한 publication 시험1개만 재실행하고 기존 통과49/30의 입력 동일성을 fresh 확인해 유지했으며 원 whole FAILED는 보존했다. 실제008/claim/run/spool/8종/의미결속은 NOT_RUN이며 준비 PASS는 Native/P09 PASS가 아니다. 외부 PowerShell 명령 전달 후 자동 구현·검증 중지(PAUSED).001~007/Native008~010 재실행·Native011 금지. P09/A12/A13 OPEN·P10미시작·249 큐158수용/91대기는 그대로다. [008 인계](P09_CAPTURE008_HANDOFF.md). 아래 NOT_RUN/007대기 표현은 이전 관측 이력으로 원문 보존.

# P09 CROSSREF007 실행 인계

상태: 로컬 수정·준비 완료 / 실제007 NOT_RUN / P09 Gate OPEN / 명령 전달 후 목표 PAUSED.

## 006 원본과 문제 구분

- [006 최종 결과](evidence/p09-361-external-qualified-fixed-eight-run006.v1.json):117146B, SHA-256 `33455bc9d69b95ce2940f494383d0ed4aa749d5991f029ced2a7f8789d98703a`. 사용자 결과 및 별도 raw spool과 일치한다.
- 원본 Read/FileShare.Read 잠금 확보, 잠금 하 원래 Open 반환, 마지막 잠금 해제가 모두 성공했다. 따라서005에서 막힌 원본 sharing lease는006에서 실제 통과했다.
- case1 source_bind에서 `P09_XREF_BIND_SOURCE_DOCUMENT_APPLICATION_IDENTITY_MISMATCH`. completed0/8·수용0·산출물0, case2~8 NOT_RUN. cleanup true·원 owned 한글 정상 종료·잔여 Hwp/HwpTray0을 확인했다.
- 006의 원본 전체 final freshness는 성립하지 않았으며 실패를 PASS로 바꾸지 않는다. 최대 시스템CPU68.95%/최소 가용RAM39.910%, CPU 보호 중단이 아니다.
- 실제로 다른 논리 애플리케이션이 반환됐는지 COM 래퍼/인스턴스 관계 때문인지는 미확정이다. 006을 재실행하거나 관측 없이 특정 원인으로 단정하지 않는다.

## 수정 근거와 소속 확인 계약

공식 원본 `implementation/p00/source-archive/original/automation/HwpAutomation_2504.pdf`(988629B, SHA `917142de2704ae037b0132f5a344ce5331b1fd96cc19dd574666aaacfbf0268c`)의47쪽 전체를 렌더링해 직접 확인했다. IXHwpDocument.Application은 읽기 전용 최상위 IHwpObject 반환으로 설명되어 있다. 설치된2020 선언은 해당 속성을 VT_DISPATCH로 선언한다. 이 문구만으로 특정 두 COM 인스턴스의 IUnknown이 같다고 보장하지 않으며, 실제 반환 객체의 소속을 별도로 검증해야 한다.

새 `crossref-capture007-application-binding.ps1`은 원래 관측 함수의 문서 애플리케이션 술어1줄만 process-local 교체한다. 나머지 원본 함수 전체가 역변환으로 동일함을 검사한다. 반환 객체에 대해 다음 조건을 **항상 모두** 요구하며 기존 포인터가 같다는 이유로 건너뛰는 경로도 없다.

| 조건 | 실제 확인 대상 |
| --- | --- |
| returned_application_is_com | 반환값이 실제 COM 객체 |
| collection_bound | 반환 객체의 XHwpDocuments가 고정 owner 컬렉션과 동일 IUnknown |
| document_bound | 그 컬렉션의 활성 문서가 고정 Document와 동일 IUnknown |
| windows_bound | 반환 객체의 XHwpWindows가 고정 owner 윈도우 컬렉션과 동일 IUnknown |
| window_bound | 해당 Item(0)이 고정 owner 윈도우와 동일 IUnknown |
| window_handle_matches | 정확한 비영 Int32 HWND가 owner HWND와 일치 |
| window_pid_matches | HWND의 실제 PID가 owner PID와 일치 |
| single_document | 정확한 Int32 Count1 |
| version_matches | 정규화 버전11.0.0.9136 |

별도로 기존 owner의 PID/생성시각/세션/exe 확인, owner Application/컬렉션/활성 문서 식별, 원본 경로·digest·modified·버전·paired 관측·최종 owner 재확인은 그대로 유지한다. 추가 획득한 IUnknown도 원래 ledger에 AddRef당1회 Release되며64개 예산을 유지한다. 빌린 RCW alias를 FinalRelease하지 않는다.

단일 루트 포인터 비교를 무조건 참으로 만들거나 검사를 삭제한 것이 아니다. 연결이 잘못되거나 getter/타입/개별 조건이 하나라도 다르면 거부한다. 임의 COM 활성화·다른 프로세스 연결·문서 쓰기·추정 Open 옵션·ReadWrite 공유 허용·CPU/RAM 보호 완화는 없다. 원006 코드/receipt/probe는 보존한다.

**실제 한글의 반환 객체가 이 graph를 만족하는지, SaveAs·재열기·활성 산출물 lease가 호환되는지는 NOT_RUN이다. 새007 결과로 확인해야 하며, 준비 모델을 Native/Gate PASS로 승격하지 않는다.**

## 준비 검증

| 근거 | 결과와 범위 |
| --- | --- |
| [591](evidence/p09-361-capture007-namespace591.v1.json) | 새 Python5/Rust4·853fresh/final853·cleanup true. 새 readonly probe5151232B/SHA614077e81603807133782c35679993e78fab96d9953e4a20cec935b61194ee1c |
| [592](evidence/p09-361-capture007-entry-code592.v1.json) | Python50/Windows27·260fresh/final260·cleanup true. Windows는 graph16·원본잠금6·namespace5 |
| [사전검사](evidence/p09-361-external-qualified-generation007-preflight.v1.json) |242fresh/final242·cleanup true. 한글/claim0, Codex 상위 Job의 caller_lifecycle_native_safe 한 조건만 예상 거부 |
| [593](evidence/p09-361-capture007-entry-ready593.v1.json) |265fresh/final265·cleanup true. 준비 요청1을 실제로 거부, 사례0·Native 생성 trap0·정확한 worker/IO/Job 정리. 실제 세션 자격은 아님 |
| [594](evidence/p09-361-capture007-handoff594.v1.json) | 실제 수정 없는 공개 loader로244fresh/final244·cleanup true. CPU최고13.84%/가용RAM최저43.791%, 기존006 probe byte-exact, 한글0 |

- Graph16/원본잠금6 body PASS는 해당 PS/실제 의존파일·현재 PS 실행 이미지·동일한 owned 실행기/환경을 fresh 대조해 유지했으며 다시 실행하지 않았다. 원본 body PASS와 최종592 사이 부모/모델 Python217개의 bytes/SHA도 모두 동일했다.
- namespace 준비 중 세대 문자열이 고정 파일SHA 내부까지 치환된 오류를 원래 불변SHA로 바로잡았다. 이후 결과 보존기의 미실행 필드 접근도 수정했다. 실패 audit001~002와 최초 실행기 원문은 그대로 남겼으며 그 whole 실패를 PASS로 바꾸지 않았다.
- 249 큐·과거 통과 제품 본문·Native008~010·외부001~006은 재실행하지 않았다.
- 007의 claim/run/spool/실물 사례/의미결속은0/NOT_RUN이다. P09/A12/A13 OPEN·P10미시작·공식대기열158수용/91대기 유지.

주요 SHA:
- 591: `3f2f61321fa428f782385daf4ff665fcc29cf46c9a53a17e459dd16be1bb43a8`
- 592: `aaa518f6f7cd342d7a71b1b159519e9796a9076bd164f2ceb95244ceff9f101f`
- 593: `13e0a4f2371a5374263baf8389b69cfb63ec3aa8374afcfe0c7365ae734a8f96`
- 594: `dfb040fc38dcb790a3f0bf7565c0c61a656ad907dd996fca5bb43d9ecc998231`

## 사용자 실행 명령

Codex 내부 터미널이 아닌 **별도로 연 PowerShell**에서 한 번만 실행한다. 관리자 권한은 필요 없다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_external_crossref_fixed_batch007.py' --execute-generation-007-fixed-eight
```

현재 외부 부모·현재 세션 자격이 통과할 때만 고정8종으로 진입한다. 접근허용 창이 나오면 사용자가 직접 눌러야 할 수 있다. 끝나면 마지막 JSON과 필요한 창 종류만 전달한다. 전체 로그·비밀정보는 전달하지 않는다.

성공·실패·중단·cleanup 대기 어느 경우에도 같은007 명령을 재실행하지 않는다.001~006/Native008~010 재실행·Native011 실행 허가는 포함되지 않는다. 에이전트는007을 실행하지 않았다.

명령 전달 후 사용자 요청대로 목표를 **PAUSED**로 두고 구현·자동검증을 중지한다. 이전 다섯 문서의 원문은 `source-archive/p361-capture007-ready593-docs/`에 보존했다.
