# HancomDesktopAutomationBackend

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**


## 역할

실제 Windows 한/글 응용 프로그램의 공식 오토메이션 객체·Action·ParameterSet을 사용해 Direct HWPX만으로 보장하기 어려운 기능을 실행한다.

## 핵심 구성

- `WorkerAgent`: job lease, file staging, process lifecycle.
- `HancomSession`: application object 생성·종료, document handle 관리.
- `SecurityModule`: 공식 파일 경로 보안 승인 모듈 연계.
- `ActionRegistry`: semantic capability → versioned action/parameter binding.
- `ExecutionInterpreter`: OperationPlan을 registry sequence로 실행.
- `ModalWatchdog`: unexpected dialog 탐지, known dialog policy, timeout.
- `StateProbe`: cursor/selection/document/control/property readback.
- `SaveReopenOracle`: 저장 후 새 process/session으로 재검증.

## binding 생성 절차

1. 대상 build별 공식 ActionTable, ParameterSetTable, HwpAutomation, Event 자료 checksum 고정.
2. parser/importer로 candidate action/parameter records 생성.
3. macro recording 또는 공식 샘플을 이용해 UI operation과 candidate binding 연결.
4. 최소 synthetic document에서 action 실행.
5. pre/post semantic snapshot과 property readback 비교.
6. 성공 binding을 signed registry file로 승격.
7. build 변경 시 전체 probe를 재실행하고 diff report 생성.

LLM이 action 이름을 선택하지 않는다. operation interpreter는 signed registry key만 허용한다.

## process safety

- worker당 동시 한/글 session 수를 제한한다.
- job timeout과 heartbeat.
- process tree kill 및 desktop/session cleanup.
- unexpected modal은 screenshot/log metadata를 남기고 fail-closed.
- clipboard 공유 금지 또는 worker-local clipboard only.
- recent files, temp, auto-recovery, printer spool cleanup.
- network deny unless capability explicitly requires external service.

## save policy

source는 read-only copy로 열고 output temp path에 저장한다. save-as format과 옵션은 registry binding으로 고정한다. output을 닫고 새 process에서 reopen하기 전에는 success로 간주하지 않는다.
