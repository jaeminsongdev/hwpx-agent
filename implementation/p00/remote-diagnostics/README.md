# Hancom 2020+ Remote Diagnostic Kit

이 폴더는 다른 Windows PC에 설치된 한글 2020 이상을 **발견, 진단, build별 qualification**하기 위한 P00 전용 오프라인 도구다. 제품 automation worker가 아니며 P01/P10 구현을 앞당기지 않는다.

## 목표

- 2020·2022·2024와 이후 버전을 같은 데이터 계약으로 처리한다.
- release 이름이 아니라 exact `Hwp.exe` build, bitness, SHA-256, COM 등록, runtime receipt를 증거로 사용한다.
- 다른 PC의 오류를 `request_id`와 `run_id`로 재현 가능하게 묶는다.
- 수집 bundle을 네트워크로 자동 전송하지 않고 사용자가 직접 전달한다.
- 사용자 문서, 본문, 클립보드, raw Event Log message, dump content를 기본 수집하지 않는다.

## 모드

| 모드 | 동작 | 상태 승격 |
|---|---|---|
| `discover` | 설치/COM/OS/font/printer/error-event metadata만 수집. 한글 실행 없음 | `discovered_unqualified` |
| `probe` | exact profile preflight 뒤 무문서 COM `Version`/`Quit()` 실행 | 조건 충족 시 `pass` |

`probe`는 expected major release, exact file version, executable SHA-256가 모두 request에 있어야 한다. discovery 결과를 검토해 새 request를 만든 뒤 probe한다. 미래 버전의 release 연도가 설치 경로나 파일 설명에서 식별되지 않아도 discovery bundle은 만들 수 있지만, 공식 제품 식별을 확인하기 전에는 `probe` request를 만들거나 qualification할 수 없다.

## 오류·로그 체계

한 세션은 아래를 동일한 `run_id`로 묶는다.

1. OS build/locale/interactive session과 product/COM fingerprint.
2. `Hwp.exe` 및 automation DLL/TLB/help fingerprint. 설치 파일은 복사하지 않는다.
3. bounded child process의 exit/timeout/stdout·stderr byte count와 SHA-256. 원문 stderr는 저장하지 않는다.
4. probe가 관찰한 `Hwp.exe` PID/session/path match/command-line classification/lifecycle.
5. Application Error, Application Hang, Windows Error Reporting, .NET Runtime 이벤트의 allowlisted metadata. raw message는 저장하지 않는다.
6. 새 crash dump의 이름/크기/시간 metadata. dump bytes는 별도 명시 동의 전에는 복사하거나 hash하지 않는다.
7. known font fingerprint와 allowlisted local printer profile.
8. bundle 내부 파일별 SHA-256 manifest와 request challenge nonce.

문서별 재현이 필요한 단계는 이 P00 kit가 아니라 향후 P10 sandbox worker에서 생성된 비사용자 fixture로 수행한다. 실제 사용자 문서가 필요하면 별도 동의와 secure channel을 요구한다.

### 먼저 보는 필드

| 위치 | 의미 | 판단 |
|---|---|---|
| `session.json / state` | 전체 수집·probe 결과 | `pass`, `discovered_unqualified`, `failed`, `blocked` |
| `session.json / collector_phase` | 성공 종료 또는 예외 발생 단계 | 타 PC 재현 시 첫 분기점 |
| `session.json / error_code` | 안정적인 기계 판독 오류 코드 | 원문 exception 대신 사용 |
| `session.json / exception` | 예외 형식·단계·메시지 SHA-256 | 같은 실패 재발 여부 비교용이며 원문은 미수집 |
| `session.json / runtime_probe` | timeout, version, Quit, process cleanup | qualification의 직접 증거 |
| `events.json` | allowlisted Application event metadata | raw message와 문서 내용 없음 |
| `inventory.json / crash_dump_metadata` | 새 dump의 이름·크기·시간 | dump bytes 미수집 |
| `manifest.json` | 내부 파일 size/SHA-256 | 운반 중 변조·혼입 탐지 |

### 주요 오류 코드

| 오류 | 의미 | 다음 조치 |
|---|---|---|
| `TARGET_NOT_INSTALLED_OR_COM_NOT_REGISTERED` | canonical ProgID의 실행 가능한 등록을 찾지 못함 | 설치/edition/등록 상태를 사용자 또는 관리자에게 확인 |
| `AMBIGUOUS_COM_TARGET` | 한 image에서 둘 이상의 실행 파일 후보가 발견됨 | image를 release/build별로 분리 |
| `TARGET_MAJOR_RELEASE_UNVERIFIED_OR_BELOW_MINIMUM` | probe에서 2020+ 제품 식별을 확정하지 못함 | 공식 제품/update identity를 먼저 잠금 |
| `TARGET_PROFILE_MISMATCH` | expected release/build/SHA-256 중 하나가 다름 | discovery 결과로 새 profile/request를 만들고 기존 증거 재사용 금지 |
| `PREEXISTING_HWP_PROCESS` | 실행 전 한글 프로세스가 존재함 | 사용자가 한글을 닫은 뒤 새 run 수행 |
| `AUTOMATION_INITIALIZATION_TIMEOUT` | bounded COM child가 시간 안에 끝나지 않음 | event metadata 확인, 화면이 필요하면 사용자 표시 후 screenshot만 캡처 |
| `COM_CLIENT_EXCEPTION` | COM 생성·Version·Quit 중 예외 | exception type/HRESULT와 Event metadata를 같은 `run_id`로 대조 |
| `AUTOMATION_VERSION_MISMATCH` | COM `Version`과 pinned build가 다름 | qualification 거부, target profile 재검토 |
| `AUTOMATION_PROCESS_REMAINED` | probe 소유 process 정리 실패 또는 다른 Hwp 발견 | worker 격리·recycle, 자동으로 타 process 종료하지 않음 |
| `COLLECTOR_EXCEPTION` | inventory/post-processing 예외 | `collector_phase`, exception type, message hash로 동일 결함 여부 확인 |

Verifier의 `bundle_state=valid`는 ZIP 계약과 privacy/integrity가 유효하다는 뜻이고, `qualification_state=pass`만 해당 exact build의 runtime qualification이다. Discovery, failed probe, 다른 build의 PASS를 대신 사용할 수 없다.

## 타 PC 절차

1. 이 폴더 전체와 생성된 request JSON을 대상 PC로 복사한다.
2. 한글 창을 모두 닫는다. UI 선택이 필요하면 사용자가 직접 처리한다.
3. 일반 권한 PowerShell에서 collector를 실행한다.
4. 생성된 ZIP만 원래 개발 PC로 가져온다.
5. verifier가 path traversal, 크기, schema, challenge, manifest hash, privacy invariant, runtime invariant를 검사한다.
6. 화면 확인이 필요하면 사용자가 창을 앞으로 띄우고 Computer Use는 screenshot만 캡처한다.

```powershell
# discovery request 생성
.\tools\New-HancomDiagnosticRequest.ps1 `
  -Mode Discover `
  -ProfileId hancom-hangul-auto-discovery `
  -OutputPath .\request.discover.json

# 타 PC에서 수집
.\tools\Collect-HancomDiagnostics.ps1 `
  -RequestPath .\request.discover.json `
  -OutputDirectory .\diagnostic-output

# 개발 PC에서 검증
.\tools\Test-HancomDiagnosticBundle.ps1 `
  -BundlePath .\diagnostic-output\<run-id>.zip
```

Discovery에서 exact hash를 얻은 뒤 `Probe` request를 생성한다. `Probe` 실행은 문서를 열지 않지만 숨김 automation process를 만들고 종료한다.

타 PC에서 Codex가 실행되는 경우에도 위 PowerShell과 JSON만으로 먼저 진단한다. UI click/type, privacy 선택, 제품 activation, 관리자 권한 작업이 필요하면 자동 진행하지 않고 사용자에게 정확한 화면·조치를 요청한다.

현재 준비된 일회성 discovery request는 아래에 있다.

- 2024: `../evidence/remote-diagnostics/requests/discover.hancom-hangul-2024.remote-pending.20260901.v3.json`
- 2022: `../evidence/remote-diagnostics/requests/discover.hancom-hangul-2022.remote-pending.20260901.v3.json`

각 request는 한 PC의 한 run에만 사용하고, 재시도나 다른 PC에는 `New-HancomDiagnosticRequest.ps1`로 새 UUID/challenge를 만든다. Request의 `collector_sha256`와 대상 PC에 복사한 collector hash가 다르면 수집기는 실행을 거부한다.

## Fail-closed 규칙

- 2020 미만, ambiguous COM registration, expected mismatch, pre-existing `Hwp.exe`, timeout, cleanup refusal/error는 qualification 실패다.
- 알려지지 않은 이후 release를 파일 version 공식만으로 추정하지 않는다.
- discovery bundle의 challenge와 manifest는 accidental corruption·request mix-up을 탐지하지만 서명된 원격 호스트 신원은 증명하지 않는다. signed agent identity는 P10 범위다.
- build별 독립 image가 없으면 다른 release의 증거를 재사용하지 않는다.
- bundle integrity가 유효해도 runtime이 실패할 수 있다. verifier는 `bundle_state`와 `qualification_state`를 분리한다.
- collector는 upload, update, registry/security/privacy 설정 변경, UI click/type, 문서 open을 수행하지 않는다.

## P10 인계 경계

이 kit의 계약은 P10 worker의 health probe와 incident bundle 입력이 된다. P10에서는 signed agent identity, authenticated outbound lease, named-pipe protocol, modal watchdog, generated fixture open/save/render/export, worker recycle을 추가한다. P00 kit 자체를 production worker로 승격하지 않는다.
