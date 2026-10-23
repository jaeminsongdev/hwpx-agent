> 최신 2026-10-22:006은 이미 실행되어 SOURCE_DOCUMENT_APPLICATION_IDENTITY_MISMATCH로 실패·cleanup true·수용0이다. 006 명령을 다시 실행하지 않는다. 잠금 하 원본 Open은 성공했고 새007의 소속 검사 수정·code592/READY593/handoff594 준비를 마쳤다. 최신 명령은 [007 인계](P09_CAPTURE007_HANDOFF.md)에 있으며 실제007은 NOT_RUN, 목표는 사용자 요청에 따른 PAUSED다. 아래006 준비/명령은 변경 전 이력으로 보존한다.

# P09 CROSSREF006 외부 실행 인계

상태: 준비 완료 / 외부006 실물 NOT_RUN / P09 Gate OPEN / 목표 PAUSED(사용자 지정 외부006 결과 대기).

사용자는 BLOCKED를 요청했지만 해당 도구가 신뢰된 CCA 실행 맥락 부재로 거절했다. 자동진행을 멈추는 사용자 의도에 따라 지원되는 목표 일시정지(PAUSED)를 적용한다. 차단 전환 성공으로 보고하지 않는다.

## 005 확인 결과

- 정식 최종 receipt의 크기115450B와 SHA-256 `05f1d0e2c5d38a9aa41fc358e2d9cbef8b584d7f08c1ace0d244651297b3e1db`가 사용자 결과와 일치하고, 별도 private raw spool의 정규 원문도 동일하다.
- case1의 source_open 뒤 source_bind에서 `P09_XREF_BIND_SOURCE_READ_LEASE_FAILED_SHARING_VIOLATION`이 기록됐다. completed0/8·수용0, case2~8 NOT_RUN, cleanup true, Hwp/HwpTray0을 확인했다. 최종 전체 source boundary/final freshness는 성립하지 않았으며 실패를 PASS로 바꾸지 않는다.
- CPU최고34.38%/가용RAM최저44.093%였고 이 실패는 CPU 보호 중단이 아니다.
- Windows에서 새 공유 모드는 기존 핸들의 접근 모드와도 호환되어야 한다([Microsoft CreateFile](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)). 기존 writable 핸들만으로 Read/FileShare.Read가 거절될 수 있다. 실제005의 충돌 핸들을 어느 PID가 소유했는지는 독립적으로 확정하지 않았다.

## 변경과 남은 검증 경계

- `crossref-capture006-source-guard.ps1`: 고정 원본의 regular/no-reparse/14425B 경계를 확인하고 Read/FileShare.Read를 **원래 Open보다 먼저** 확보한다. held stream SHA를 확인한 뒤 원래 Open을 그대로 호출한다. 사례 최종 원본 검사 및 owned-session 정리까지 유지하고 정리 실패 시에도 finally에서 해제한다.
- ReadWrite 공유·원본 복사/교체·권한/파일 속성 변경·추정 HWPX Open 옵션·CPU/RAM 보호 완화·원본 owner/COM/SaveAs/소스 관측 생략은 없다.
- 열린 파일의 앞뒤 checksum만으로 기존 쓰기 차단을 대체하지 않는다. 사전 중복 Get-FileHash를 제거했지만, 원래 Open의 기존 원본 검사는 잠금을 보유한 상태에서 그대로 실행한다.
- 새006 전용 probe/worker/namespace/공개 entry/정식 publisher를 분리했다. 기존001~005와 Native008~010은 재실행하지 않으며 Native011 허가도 없다.
- **실제 한글이 이 제한적 잠금 하에서 Open할 수 있는지, 이후 SaveAs/재열기/활성 산출물의 read lease가 호환되는지는 NOT_RUN이다.** 실패하면 현재006 원본을 남기고 같은006을 다시 실행하지 않는다.
- 8종 캡처 완료 자체도 CROSSREF 의미결속·249대기열·P09 Gate 완료가 아니다.

## 준비 근거

| 구분 | 결과와 경계 |
| --- | --- |
| 586 readonly probe | 새 Python5/Rust4,853fresh/final853,cleanup true. 소비한 Native나 과거 통과 본문 재실행 아님 |
| 588 code | Python50/Windows11,259fresh/final259,cleanup true. Python50·잠금6은 현재 동일 입력으로 body PASS 보존, 실패 audit001~009 원 상태 보존 |
| 006 공개 사전검사 |241fresh/final241,cleanup true. `caller_lifecycle_native_safe`만 거부. Codex 상위 Job 경계의 예상 거부이며 한글/claim/실물0 |
| 589 READY 거부 |264fresh/final264,cleanup true. READY요청1,Native constructor trap0,사례0,정확한 worker/IO/Job 정리 확인. **실제 세션 자격 아님** |
| 590 공개 loader fresh |243fresh/final243,cleanup true,CPU최고13.79%/가용RAM최저46.360%. code588/ready589의 실제 loader 통과, 기존005 binary 동일,한글0 |

- [586](evidence/p09-361-capture006-namespace586.v1.json) SHA `b0766295356546532c09ceaecec716f903f8c93be7a38bf16fd87cca22872151`
- [588](evidence/p09-361-capture006-entry-code588.v1.json) SHA `076c5c6d4547adee3f4f2b02114e5cc482652ac4a58635021b3e6e6be2e9ffeb`
- [589](evidence/p09-361-capture006-entry-ready589.v1.json) SHA `d72b2d4ba718e3a676f948c41bbc5a56293207f86918ad12369d19cbae464666`
- [590](evidence/p09-361-capture006-handoff590.v1.json) SHA `3a39c94c29d25c66b631acd87a83207cb7793fc723899cb5cdd4f83ba0e3ce39`

## 사용자가 실행할 새006 명령

**Codex 안의 터미널이 아닌 별도로 연 PowerShell**에서 아래를 한 번만 실행한다. 관리자 권한은 필요 없다.

```powershell
& (Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe') -B 'D:\개발\hwpx-agent\tools\p09\run_external_crossref_fixed_batch006.py' --execute-generation-006-fixed-eight
```

현재 외부 부모/세션 자격이 통과할 때만 고정8종으로 진입한다. 과거 자격/승인 receipt를 현재 Native 실행 권한으로 재사용하지 않는다. 접근허용 창은 사용자가 직접 눌러야 할 수 있다.

- 끝나면 마지막 JSON만 전달한다. 전체 로그·문서 내용·비밀정보는 전달하지 않는다.
- `WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL`은 실물 진행이 아니라 cleanup 대기일 수 있다. 현재 상태와 보이는 창 종류를 전달하고 같은 명령을 재실행하지 않는다.
- 성공·실패·중단·cleanup 대기 어느 경우에도 같은006을 재실행하거나001~005로 되돌리지 않는다.
- 에이전트는006을 실행하지 않았다. 이 명령 전달 후 목표를 PAUSED로 두고 구현·자동재검증을 중지한다. 외부006 결과를 사용자가 전달할 때 다음 조치를 판단한다.

이전 네 문서의 byte-exact 원문은 `source-archive/p361-capture006-ready589-docs/`에 보존했다. P09/A12/A13 OPEN·P10미시작·249대기열158수용/91대기는 변경하지 않았다.
