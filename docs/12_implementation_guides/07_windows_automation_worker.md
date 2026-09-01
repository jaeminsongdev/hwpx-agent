# Windows 한/글 오토메이션 워커 구현

> 기준일: 2026-08-31  
> 프로젝트 코드명: `hwpx-agent`  
> 문서 세트 버전: `2.0-design`  
> 규범 키워드: **MUST/SHALL=필수**, **SHOULD=권장**, **MAY=선택**

## 언어·프로세스 결정

Windows COM/STA lifecycle, typed interop, event sink, desktop/process watchdog를 담당하는 worker는 **C#/.NET 별도 프로세스**로 구현한다. Rust control plane과는 versioned protobuf/gRPC 계약으로만 통신한다. 한/글 응용 프로그램과 같은 process에 control-plane 코드를 넣지 않는다.

## 토폴로지

```text
Rust Job Orchestrator
  -> outbound lease queue / authenticated gRPC
Windows Agent service
  -> stage artifact into job sandbox
  -> create isolated interactive desktop/session
  -> spawn one Hancom STA Worker process
  -> local named-pipe protobuf
Hancom STA Worker
  -> HwpObject + event sink + modal watchdog
  -> output temp artifact + trace
Windows Agent
  -> kill/cleanup/reopen oracle/upload evidence
```

worker는 외부에서 직접 들어오는 public RPC를 받지 않는다. agent가 outbound로 job을 lease하는 구조를 우선한다.

## STA worker main loop

```csharp
[STAThread]
static int Main(string[] args) {
    using var pipe = ConnectAuthenticatedNamedPipe(args);
    using var desktop = VerifyAssignedDesktop(args);
    var session = HancomSession.Create(targetProfile);
    try {
        foreach (var command in pipe.ReadCommands()) {
            var receipt = ExecuteAllowlisted(command, session);
            pipe.Write(receipt);
            PumpWindowsMessages();
        }
    } finally {
        session.CloseWithoutPrompts();
        KillOwnedProcessTreeIfNeeded();
    }
}
```

실제 구현은 UI message pump와 cancellation safe point를 보장해야 한다.

## 보안

- job별 Windows 사용자/프로필 또는 disposable VM/containerized desktop.
- source는 read-only staging, output은 별도 경로.
- 공식 file-path security approval module을 target 정책에 맞게 적용.
- network default deny; translation/cloud/save-to-service capability만 allowlist.
- clipboard, recent files, temp, recovery, printer, registry/profile residue cleanup.
- scripts/macros/OLE activation 금지. 필요 시 별도 high-risk product tier와 ADR.
- screenshot/log에 문서 본문을 기본 포함하지 않고 metadata/redaction 정책 적용.

## modal watchdog

known dialog에는 versioned fingerprint와 처리 정책이 있다. unknown modal은 자동 버튼 클릭하지 않는다.

```text
modal detected
 -> collect process/window title/class/hash (redacted)
 -> match allowlisted dialog fingerprint
 -> if expected: execute declared response
 -> else: suspend command, capture diagnostic, fail closed
 -> terminate/recycle process after evidence flush
```

## action executor

public 입력에는 action string이 없다. `binding_id`를 signed registry에서 resolve한다. ParameterSet field와 타입은 generated C# models로 검증하고, unknown field/enum/out-of-range를 COM 호출 전에 거부한다.

## timeout·재시도

- command timeout과 job timeout을 분리한다.
- timeout 후 동일 session에서 무조건 재실행하지 않는다.
- output 존재, process state, action trace, readback을 reconciliation한다.
- uncertain execution은 `UNKNOWN_OUTCOME`; fresh worker에서 source부터 재시도하되 idempotency policy를 따른다.
- 일정 job 수, memory threshold, crash 후에는 process/image를 recycle한다.

## health probe

제품/build/locale/bitness, automation availability, security module, font set, save formats, printer profile, known action sample, open/save smoke를 보고한다. profile과 불일치하면 job lease를 받지 않는다.

## 완료 기준

- open/save/readback, event, timeout, unknown modal, crash, cancellation, process leak test.
- worker에 raw generic action endpoint 없음.
- job 종료 후 source/output 외 사용자 데이터 residue 없음.
- 같은 fixture를 반복 실행해 semantic receipt가 결정적임.
