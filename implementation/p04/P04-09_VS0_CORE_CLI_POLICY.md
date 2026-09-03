# P04-09 VS-0 core CLI policy

- Contract: `hwpx-agent.vs0-create-request/v1` → `hwpx-agent.vs0-create-result/v1`
- Scope: licensed current-PC Hangul 2020 `11.0.0.9136` x86, personal local development
- Execution route: `document.create_vs0` / `direct-hwpx-vs0`

## Accepted request

The request MUST contain only the versioned schema, idempotency/project/document/base-revision
identities, expected head generation `1`, page preset `a4_portrait`, style `default`, and one nonempty
NFC-normalizable text value. Identifiers and text are bounded. Multiline text, disallowed controls,
noncharacters, unknown fields, stale generation and key reuse with any binding drift MUST fail closed.
Raw XML, COM/HAction strings, filesystem destinations and backend choice are not public inputs.

## Execution contract

1. Construct and validate one backend-neutral `DocumentGraph` and resolve the create target through
   the P04 selector and compiler contracts.
2. Admit only the repository-pinned Ed25519-verified exact-build direct route. Missing, modified,
   expired, weaker or ambiguous evidence MUST NOT synthesize a fallback route.
3. Build one deterministic A4 portrait package with exactly one section, paragraph and default style.
   The package contains the fixed 11-part Hancom-2020-compatible closure, no personal metadata, and
   is reopened through the P03 bounded package graph and typed ID validation before publication.
4. Execute through the P04 workspace transaction: private staging, complete validation, checksum
   artifact identity, no overwrite, revision CAS, and absent/quarantined/complete failure outcomes.
5. Claim and commit the exact request/manifest/head through P04 idempotency. An identical retry in
   the same reference-service lifetime replays the byte-identical terminal receipt and existing
   artifact without a second publication or revision. Crash-persistent and cross-process replay is
   deliberately deferred to P14's durable `IdempotencyStore` implementation.

## Runtime evidence policy

Only a disposable generated fixture may be opened by Hangul. The x86 PowerShell child MUST run STA,
confirm exact build `11.0.0.9136`, verify input digest and size before COM open, read back the expected
single-paragraph digest and length, close the document without save, invoke `Quit()`, and leave no
Hangul or child process. Input mutation, output save, external network and registry/system-setting
changes MUST all remain false.

Public verification output contains only schemas, target/build identifiers, digests, byte counts and
booleans. Request text, local paths, exception messages and signing private keys stay in ignored
private evidence. The independent verifier rejects duplicate/unknown JSON fields, archive expansion,
entry/order/encoding drift, semantic text drift, personal metadata, phase drift and incomplete
progress. User documents are outside scope and MUST NOT be opened or modified.

## Gate boundary

Passing P04-09 proves the current-PC VS-0 creation vertical and actual read-only open/readback on the
exact installed Hangul 2020 build. It does not prove general HWPX lifting/lowering, visual fidelity,
save/render/PDF equivalence, durable multi-process idempotency, production/provider use, another PC,
or Hangul 2022/2024 compatibility.
