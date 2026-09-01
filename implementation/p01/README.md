# P01 Repository·CI·Security Foundation

P01-01~09의 source, test, runbook과 Gate 근거를 묶는다. 이 phase는 한글/COM/UI를 실행하지 않고 현재 PC의 core 개발 기반만 만든다.

## 경계

- Rust `domain-ir`은 XML/ZIP/COM/MCP/DB를 의존하지 않는다.
- `hwpx-agent-foundation`은 secure workdir와 allowlisted/redacted logging만 소유한다.
- C# Windows worker는 semantic protobuf와 checksum-addressed artifact만 받으며 generic HAction/ParameterSet 실행 surface가 없다.
- TypeScript widget은 public schema package만 의존한다.
- `protocol/proto`와 `protocol/json-schema`가 source, `protocol/generated`가 generated output이다.
- private host evidence, licensed fixture binary, 사용자 문서, build output은 Git에서 제외한다.

## 명령

```powershell
.\tools\bootstrap.ps1
```

task별 acceptance와 최종 판정은 `P01_GATE_REPORT.md`를 따른다. 재현 절차는 `docs/10_operations/09_p01_bootstrap_runbook.md`에 있다.
