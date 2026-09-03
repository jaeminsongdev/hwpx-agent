# P10-06 trusted offline binding-bundle builder policy

- Scope: current-PC licensed Hangul 2020 `11.0.0.9136` x86 only
- Input authority: exact hash-pinned P02 Ed25519 envelope plus its P02 trust anchor
- Output authority: separately signed private P10 execution bundle
- Reasoning/review mode: `max`

## Admission boundary

The builder verifies the complete P02 envelope signature, embedded source-registry digest,
qualification coverage, exact target identity and local-development release policy before looking at
any private Action identifier. It independently locks the current capability-contract registry and
requires every projected semantic capability to exist there.

Only a P02 row with `runtime_support_state=verified_current_target`, a `verified` probe disposition,
a passed independently verified runtime run, an observed semantic effect and matching
request/trace/receipt digests may enter the P10 payload. Failed, risk-blocked, unavailable and not-run
rows are omitted. A parameter-bearing source candidate is rejected until a finite typed P10 argument
projection has its own evidence; an empty guessed map is never promoted.

The currently signed P02 registry qualifies only the parameterless undo/redo disposable canaries.
This is evidence-bounded admission, not a claim that the remaining product capability set is
unsupported.

## Signing and publication

P10 uses a separate Ed25519 key pair from P02. Its private key and signed bundle remain under the
Git-ignored `implementation/p10/evidence/` boundary. The public key and non-production trust policy
are committed under `implementation/p10/trust/`. Both construction and independent verification
consume that exact hash-pinned policy and reject key, source path, source digest or target drift. The
signature covers the exact canonical UTF-8 payload bytes consumed by the Windows worker.

All input files are regular bounded files, hash checked before use and checked again before
publication. Output is no-overwrite and path confined. The safe receipt contains only target
identity, counts and SHA-256 identities; it contains no Action, ParameterSet, item-name or private-key
value.

## Deferred boundary

A valid bundle authorizes only its exact semantic capabilities and target build. It does not prove
that the production Agent/Worker executed an action, that an actual P10-05 file-access security
module is registered, that modal supervision is complete, or that another Hancom version/PC works.
Those claims require their own actual runs and Gates.
