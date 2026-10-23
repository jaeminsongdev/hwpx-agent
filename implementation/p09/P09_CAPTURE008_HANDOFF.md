> 최신 2026-10-22 / 외부008 실제 실패 확인·새009 saved 선행 잠금 수정 및 로컬 준비 완료·외부 결과 대기 PAUSED. 008은 원본 결속/SDK true/저장/새 세션 Open 반환 뒤 fresh_saved_open 관측에서 ARTIFACT_FAILED_NO_RAW_VALUES로 실패했다. opened/saved 산출물2·완료0/8·수용0·cleanup true이며 원본124049B/SHAa16e2642e4ed5d115879f4328fdce1ba00ee6e130e71b0bb8106823c6903ecc8를 보존한다. CPU 보호 중단이 아니다. 새009는 고정 saved 파일의 Read/FileShare.Read·held digest를 원래 fresh Open 전에 확보하고 case 완료/정리 finally까지 유지한다. Windows 공유 충돌 모델을 재현했지만008 내부 예외는 축약돼 실제 원인 확정은 보류한다. 원래 IO·문서/owner 결속·보호·전후 hash는 유지하고 File.Open 오류 분류만 닫힌 코드로 보강했다. Python경로5/Rust4·Python모델50/Windows40·READY거부(Native생성trap0)·공개loader245fresh/final245·cleanup true를 확인했다. 입력 동일한 application19는 재실행하지 않았다. 실제009/claim/run/spool/8종/의미결속은 NOT_RUN이다. 명령 전달 후 자동 구현/검증 중지(PAUSED),001~008/Native008~010 재실행·Native011 금지. P09/A12/A13 OPEN·P10미시작·249큐158수용/91대기는 그대로다. [009 인계](P09_CAPTURE009_HANDOFF.md). 아래008 NOT_RUN/대기 표현은 이전 관측 이력으로 원문 보존.

# P09 CROSSREF008 실행 인계

상태: 로컬 수정·준비 검증 완료 / 실제008 NOT_RUN / P09 Gate OPEN / 외부 실행 대기·목표 PAUSED.

## 007 실제 결과

원본 [007 결과](evidence/p09-361-external-qualified-fixed-eight-run007.v1.json)는117315B, SHA-256 `8d5cf7c58b6e9d8346eb1131c5403644c68a3a22087b84449d8ec7cec439d518`이며 별도 raw spool 재조립과 동일하다. 현재 세션 검사 후 첫 사례 source_bind에서 `P09_XREF_BIND_CAPTURE_SEVEN_APPLICATION_REAL_WINDOWS`로 실패했다. 원본 Read/FileShare.Read 잠금·원래 Open 반환·잠금 해제는 성공했다. 완료0/8·산출물0·producer event0·새 수용0·cleanup true·worker IO join을 확인했다. CPU최고60.55%/가용RAM최저41.870%로 자원 보호 중단이 아니다.

이 오류는 Document.Application.XHwpWindows getter 반환이 null 또는 COM 객체가 아니라는 뜻이다. 어느 쪽인지는 원본이 구분하지 않는다. 그 뒤에 위치했던 컬렉션/문서 IUnknown 동일성 검사는 아직 입증되지 않았다. 다른 프로세스 연결이나 특정 COM 래퍼 문제로 확정하지 않는다. 007 실패와001~006 원본은 변경하지 않는다.

## 008 수정 범위

`tools/p09/run_external_crossref_fixed_batch008.py`와 전용 namespace/worker/readonly probe/publisher를 분리했다. 원래 source observer의 문서 애플리케이션 술어 한 줄만 process-local 교체하며 나머지 원본 함수는 전체 역변환으로 대조한다.

- 반환 Document.Application은 실제 COM이어야 하고, 그 XHwpDocuments 및 Active_XHwpDocument가 **각각 고정 owner 컬렉션·문서와 동일 IUnknown**이어야 한다. 두 동일성 검사를 먼저 실행하며 불일치 시 fallback 없이 거부한다.
- 반환 애플리케이션이 전체 창 API/Version을 제공한다고 가정하지 않는다. 대신 이미 소유권이 검증된 Owner.hwp에서 XHwpWindows/Item(0)/Version을 읽어, held owner 윈도우 컬렉션·윈도우 동일성, 비영 Int32 HWND 동일성, HWND의 실제 PID, 단일 문서1 및 버전11.0.0.9136을 모두 요구한다.
- 원래 owner PID/생성시각/세션/exe, root application/collection/active document 식별, modified/path/digest·paired 관측·마지막 source/owner 재확인·원본 no-write/no-delete lease는 유지한다. 추가 IUnknown은 기존64개 ledger 예산과 AddRef당1회 Release를 유지하고 빌린 RCW를 FinalRelease하지 않는다.
- root pointer alias나 반환 객체의 미지원 창 getter를 다른 객체의 소속 증명으로 사용하지 않는다. 문서 소속은 직접 동일 컬렉션·문서 연결로, 프로세스/창 소유권은 owned root로 각각 증명한다. 아무 조건도 무조건 true/fallback/optional 처리하지 않는다.
- 원 CPU/RAM/commit95%·1코어·낮은 우선순위·Native Job 보호·정확한 owner·non-killing 종료 정책은 유지한다. 시스템/Defender 설정은 바꾸지 않는다.

반환 앱의 실제 컬렉션/문서 identity, 이후 SaveAs·재열기·8종 참조 의미 결속의 런타임 호환성은 **NOT_RUN**이다. 로컬 모델 통과만으로 실제 수정 성공·세션 자격·P09 Gate PASS를 주장하지 않는다.

## 로컬 검증 근거

| 결과 | 범위 |
| --- | --- |
| [595](evidence/p09-361-capture008-namespace595-validated.v1.json) | 새 Python 경로5/Rust4 통과·854fresh/final854·cleanup true·새 probe5151744B/SHA f63c2a3559cc853f8076258cd2ece0b28a2178234f1bf4980209a9705be70592. 기존 parser/요약/재독 본문은 보존 |
| [596](evidence/p09-361-capture008-entry-code596.v1.json) | 현재 입력260fresh/final260·Python50/Windows30 통과 근거·cleanup true |
| [사전검사](evidence/p09-361-external-qualified-generation008-preflight.v1.json) |242fresh/final242·cleanup true. Codex 부모 Job 종료정책 하나만 예상 거부, Hancom/COM/claim0 |
| [597](evidence/p09-361-capture008-entry-ready597.v1.json) | 265fresh/final265·cleanup true. 현재 READY 요청을 실제 거부한 worker/IO/Job 정리 증거. Native constructor trap0·실제 사례0·세션 자격 아님 |
| [598](evidence/p09-361-capture008-handoff598.v1.json) | 244fresh/final244·cleanup true·CPU최고15.08%/가용RAM최저53.972%. 수정하지 않은 실제 공개008 loader로 현재 code/ready/고정 입력 마감. 실제008 실행·claim/run/spool 없음 |

595 최초 검사에서는 새 Rust 테스트 블록 끝을 이전 세대로 잘못 지정해 테스트 수를 거부했다. Rust/Python 본문 실행 전 실패였고 원래 FAILED receipt를 보존한 뒤 새 결과 경로에서 수정 범위를 확인했다. 596 최초 검사에서는 Python49/Windows30이 실제 통과했지만 임시 publication 시험1개의 세대 값7이 남아 whole FAILED였다. 실패 원본·시험/실행기 전사본을 보존하고 그 값 하나만8로 수정했다. 다른 모델의 모든 부모 입력·실행기·PS 이미지가 현재 동일함을 fresh 대조해 통과49/30의 body 결과만 유지하고 수정한1개만 실행했다. 기존 whole FAILED를 PASS로 바꾸거나 과거 제품 본문을 재실행하지 않았다.

595 준비 CPU최고83.52%는 시스템 전체 관측이며 owned worker 단독 사용률이나 보호 중단을 뜻하지 않는다. 596 마감 CPU최고18.45%/가용RAM최저53.648%·보호 중단 없음. 나머지 자원 표본과 SHA는 각 원본 receipt에 보존했다.

## 실행 명령

Codex 내부 터미널이 아닌 **별도로 연 PowerShell**에서 한 번만 실행한다. 관리자 권한은 필요 없다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_external_crossref_fixed_batch008.py' --execute-generation-008-fixed-eight
```

현재 외부 부모·현재 세션 자격을 통과해야 고정8종에 진입한다. 한글 접근허용 창이 나오면 사용자가 직접 누른다. 성공/실패/중단/정리 대기 어느 경우에도 같은008을 재실행하지 않는다.001~007·Native008~010 재실행/Native011은 포함하지 않는다. 마지막 JSON만 전달한다.

사용자 요청대로 명령 전달 후 자동 구현·검증을 중지한다. 목표 상태는 PAUSED이며 완료로 표시하지 않는다. P09/A12/A13 OPEN·P10미시작·공식249 큐158수용/91대기·새 수용0은 그대로다. 이전 문서 본문은 새 머리말 아래 원문으로 보존하며 전사 전 SHA/크기는 `source-archive/p361-capture008-handoff598/document-preimages.v1.json`에 기록한다.
