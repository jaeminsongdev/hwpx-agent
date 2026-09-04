# P10-09 timeout and process-recycle report

- Date: 2026-09-04
- Implementation commits: `c1ed4b2` + `4fa4711`
- Target: current licensed Hangul 2020 `11.0.0.9136` x86 PC
- Decision: `pass_scoped_current_pc_local`
- Review: `STRICT / max`, blocker/major/minor `0/0/0`

## Delivered

- Mandatory, bounded `WorkerSupervisorPolicyPin` and a supervised executor contract for startup
  recovery, cancellation, reconciliation and recycle.
- Independent command/job deadlines, exact one-time executor-entry tracking, deterministic terminal
  journal replay and no automatic same-execution retry.
- Fail-closed reconciliation over source immutability, output presence/digest, action-trace terminal
  state, semantic readback, worker process state, completed-job count and private memory.
- Startup recovery before lease acquisition, preservation-only quarantine of exact marked sandbox
  residue, and rejection of ambiguous/unmarked/reparse residue without a partial move.
- A Windows Job Object owner that digest-pins an absolute executable, creates it suspended, assigns
  `KILL_ON_JOB_CLOSE`, verifies the launched image again, resumes only after assignment, and waits for
  zero active descendants after termination.
- Strict Draft 2020-12 policy/audit schemas, negative tests, a bounded no-overwrite current-host audit
  and Windows CI integration.

## Actual current-PC evidence

The authoritative Git-ignored audit is
`implementation/p10/evidence/p10-09-current-worker-supervisor-audit-20260904T011249571Z.json`:

- bytes: `2146`
- SHA-256: `940e6e9209c2d28f09335ff5cb3dfb5ba12ea8e9dbb819854b58e31bcff70f3f`
- exact source revision: `4fa471115eb5a61a24f2eb87ad0d07858ec84f40`
- Release Agent smoke assembly SHA-256:
  `4abf6a89dfa57da527daf2f8d52a2125334b6e6762dc32b34c2accc82bacfa66`
- policy SHA-256: `07a24389635bd326e79db7f9967457095a99dad88fe0609827aaf5cc40f497bd`
- P00 host-baseline digest:
  `7fbf6559fc3372b9da6c0b0ca53d9f4eb78b76a79df248c37ff009c13376adc0`

The audit began and ended with `Hwp.exe=0`; it did not open or scan a user document. The integrated
hang test used a disposable two-process test tree. A one-second hard timeout fired while the
executor ignored cooperative cancellation, reconciliation retained effect uncertainty, the Job
Object terminated both the root and descendant, and a second lease delivery replayed the identical
terminal receipt with one total executor invocation. A separate negative case proved a complete
no-effect observation yields a retryable failure rather than an unsafe unknown-effect retry.

Earlier P10-09 audit files remain immutable but are superseded: the first lacked exact source-revision
binding, and the second preceded the integrated timeout-to-real-process-tree test. Neither is used as
the accepted Gate evidence.

## Validation

| Check | Result |
|---|---|
| Agent Release build | pass, warnings 0 / errors 0 |
| Agent smoke | pass, 28/28 |
| Integrated hard-timeout to actual process-tree recycle and identical replay | pass |
| Direct suspended-start Job Object root/descendant termination | pass |
| P10-09 static invariants | pass, 28/28 |
| Supervisor policy/audit unit tests | pass, 10/10 |
| All P10 Python schema tests | pass, 29/29 |
| P10-09 policy validation | pass, Draft 2020-12 |
| Exact current-host audit validation | pass, exact policy/source/target binding |
| Complete Windows Worker lane on final reviewed source | pass, `55.105s` |
| Agent-only Release regression after integration tightening | pass, 28/28 |
| Docs lane on final reviewed docs | pass, `8.322s`; P10 Python tests 29/29 |
| Residual `Hwp.exe` / smoke process after audit | pass, 0 / 0 |

The first Windows-lane attempt failed because a prior ad-hoc `PlatformTarget=x86` build had reused the
shared Release output folder and left the common protocol DLL architecture-specific. A bounded
`Rebuild` restored the normal AnyCPU output, and the unchanged full Windows lane then passed. Source
and package lockfiles were not modified by that environmental correction.

## Strict Gate decision

P10-09's required supervisor exists, and the hang/retry/no-duplicate-effect criterion is proven by a
single integrated current-PC execution that reaches actual Windows process-tree termination. The
P10-09 roadmap checkbox may be checked for the stated local scope.

This does not close P10 or promote P10-05/P10-06/P10-08. It does not prove a timeout against a real
Hangul document, production isolation, another machine or Hangul 2022/2024. Those remain explicitly
unverified. The next task is P10-10 runtime probe at reasoning effort `max`; P05-07 actual render
acceptance remains independently pending.
