# P10-05 Hancom file-path security core report

- Generated: 2026-09-03
- Implementation commit: `b830f746bdac0db0d3e17d1cb72ef94361e06993`
- State: `core_ready_actual_security_module_pending`
- Target scope: current PC, licensed Hangul 2020 `11.0.0.9136` x86
- Reasoning/review mode: `max` / STRICT path, lease, module, TOCTOU and cleanup audit

P10-05 connects the P10-02 Agent sandbox to the P10-04 `HancomSession` through a single-use,
immutable private security lease. The public bridge continues to carry only an opaque
`sandbox_handle`; the Agent verifies the staged artifact, creates a fixed-name read-only HWPX working
copy inside the owned sandbox, and writes an execution/fencing/profile/policy/artifact/module-bound
lease. The production Worker requires that lease before it can start.

The Worker reads only the exact HKCU Registry32 HwpAutomation module registration. It rejects a
missing or non-string registration, relative/reparse/unbounded/non-DLL files, digest drift and
non-x86 PE files. It holds the verified module file against writes during `RegisterModule` and holds
the approved document against writes across open and close. It never creates or edits the registry.

This is not the final P10-05 actual target report. The current-PC read-only probe found the exact
Registry32 key but zero registered modules, so no expected module file or digest is available for an
actual `RegisterModule("FilePathCheckDLL", ...)` acceptance run. The module was not downloaded,
installed or registered, and component evidence is not promoted to actual module evidence.

## Core acceptance result

| Criterion | Result | Evidence |
|---|---|---|
| Agent staging connection | pass_component | immutable assignment clone, exact staged input digest/size, fixed private HWPX copy, 30-minute-or-shorter lease |
| Public path boundary | pass_component | protocol remains path-free; opaque handle is distinct from the private filesystem filename |
| Lease authority | pass_component | execution/session UUID, fencing token, exact target profile, file/open policy, artifact identity and module pin are bound and single-use |
| Module admission | pass_component | HKCU Registry32 read-only lookup, absolute regular bounded DLL, exact SHA-256, x86 PE and write guard |
| Safe open | pass_component | lease/command identity match, exact sandbox marker, read-only input, digest/size recheck and retained input guard |
| Failure cleanup | pass_component | start/open/close failures release module/input guards and shut down the owned session fail-closed |
| Current-PC module registration | actual_pending | Registry32 key present, registration count 0, expected registration absent; no registry or system change |

## Validation evidence

- Windows Agent staging/security/lease/fencing/upload/auth smoke passed `12/12`.
- Windows Worker allowed/denied security smoke passed `10/10`; it includes missing/expired/overlong,
  unknown-field, marker drift, mutable input, identity mismatch, replay, module hash/architecture,
  relative module path, registration failure, close failure and file-guard cases.
- P10-04 lifecycle regression smoke passed `8/8`; static lifecycle checks passed `24/24` and P10-05
  static checks passed `29/29`.
- Both lifecycle and security smokes passed under this PC's installed 32-bit .NET runtime.
- The current checkout and an exact clean clone at implementation commit `b830f74` passed all five
  lanes: `linux-core`, `windows-worker`, `widget`, `docs`, and `security`.
- Clean-clone security checks reported no failed checks and an SBOM with 365 components. The exact
  clean clone remained Git-clean after validation.
- The private current-PC probe evidence reports `state=not_ready`, `registration_count=0`,
  `expected_registration_present=false`, path/registry-value disclosure false, network false and
  registry/system-setting change false.

## Strict self-review

- Change risk: high; the code authorizes local file open and loads a registered native security DLL
  into the actual Hangul automation process.
- Review result: APPROVE for the bounded component/core scope only.
- Final blocker/major/minor findings after remediation: `0/0/0` for that component scope.
- Remediation covered module hash-to-register write races, failed-open guard ownership, failed-start
  cleanup, sandbox marker revalidation, protocol-handle/private-filename incompatibility, mutable
  assignment rebinding, failed-close input guard leakage and relative registered module paths.

## Unverified boundary

The evidence does not prove a real registered Hancom security module, successful actual
`RegisterModule`, prompt-free file open, a vendor module digest/license/distribution decision,
hostile same-user registry isolation, P10-06 action execution, another PC or Hangul version, or
production/commercial use. Those claims remain closed.

## Next exact task

Implement P10-06 as a signed, version-scoped binding executor with a finite typed ParameterSet
surface. Reject unknown/raw HAction and parameter names before COM dispatch; bind the signed bundle,
target profile, capability, execution/fencing identity and operation-plan artifact; then prove exact
typed values, unknown rejection, replay safety and cleanup under the current x86 Worker. Continue at
reasoning effort `max`.
