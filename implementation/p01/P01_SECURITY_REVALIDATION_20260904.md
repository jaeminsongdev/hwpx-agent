# P01 security revalidation reliability report

- Date: 2026-09-04
- Scope: current-PC local development and exact-commit clean-clone validation
- Decision: `harness_pass_actual_registry_audit_unverified_timeout`
- Reasoning effort: `max`

## Trigger and outcome

The exact `aee2818` clean clone passed `linux-core`, `windows-worker`, `widget` and `docs`, but its
security lane did not pass. `pnpm audit --audit-level high --json` reached its own registry timeout
twice. The other security checks passed on both runs. A minimal unauthenticated POST to the same npm
audit endpoint also returned no bytes before a 15-second client timeout on this PC. This proves only
the observed current-PC network path; it is not represented as a global npm incident.

The security runner now bounds the audit to 60 seconds per attempt and at most three attempts. It
retries only a safely cleaned timeout or a recognized transient network failure. A vulnerability
result, another non-transient failure, or unproven process-tree cleanup is never retried. The audit
arguments and `high` threshold are unchanged, and a final exit code of zero from a real audit is
still mandatory for the security lane to pass.

Each run now publishes to a new `implementation/p01/evidence/security-runs/<run-id>/` directory.
Both `report.json` and `sbom.cdx.json` are run-bound; the report is created with exclusive-create
semantics. This stops later validation from overwriting earlier security evidence. The legacy fixed
paths remain in place for historical compatibility and are no longer written by the runner.

## Validation

| Evidence | Result |
|---|---|
| Retry, audit-result classification, cleanup and no-overwrite unit tests | pass, 8/8 |
| P01 Python compilation | pass |
| Complete docs lane after final self-review | pass, `8.305s` |
| Actual current security lane before no-overwrite publication | fail-closed, `196.716s` |
| Actual current security lane with final no-overwrite publication | fail-closed, `191.381s` |
| Actual pnpm audit attempts | 3/3 timed out at 60 seconds; cleanup reported true for every attempt |
| Other actual security checks | pass: secrets, Rust advisories/policy, Node licenses, both NuGet checks, SBOM |
| Residual audit/security processes | 0 after the run |
| Minimal audit-endpoint POST | no bytes, client timeout at 15 seconds |

The ignored failed report and SBOM were copied without deletion to
`implementation/p01/evidence/security-runs/legacy-20260904T001205900596Z-77266114/` before the
fixed-path writer was retired. Their SHA-256 values are respectively
`772661145a954256615b7081127a8c8a5f9f3fbc79f816766f4ef8217a5b6a10` and
`e09eaa95625cacc3faca5b7175f5a733187a6d5e52f1395330a69209f4400c3a`.

The final runner created ignored run `c836c56a3ec9446a8e42c0888399352c`. Its `report.json` is 1,666
bytes with SHA-256 `6a5de07b57342a2c6cd1ae311cc33405eaff2ca1c210090e90f8b675dd1c7581`;
its SBOM is 635,548 bytes with SHA-256
`567c80e1eeb3e4ad53ebb3ac34a569fac2922fa27744d3e6ff3699294e69bdeb`. The legacy fixed files
retained their pre-run hashes, and residual `pnpm audit`/security-runner processes were zero.

The exact code commit is `5fe8c8e7223b0ac6951d5faac2e6ff039e3a327d`. A fresh no-hardlink
detached clone at that commit passed the docs lane in `6.494s` and remained Git-clean. Its security
lane failed in `191.335s` only because all three bounded npm audit attempts timed out; every attempt
reported successful cleanup, the other security checks passed, and residual processes were zero.
Ignored clean-clone run `3152f73f46014731a6e4a2699cc3953f` contains a 1,666-byte report with
SHA-256 `cd177cc4da1bc65d63e5846a19bb6b5784ec98f1a7b2e19d02f4f4435c7ee4e9` and a
301,074-byte SBOM with SHA-256
`ec062621d8da5bd2aee01143b52028050b454589b8f2e25e3d06d8279a093646`.

## Gate boundary

This change improves failure containment and evidence durability; it does not turn the failed audit
into a pass. The exact-commit clean-clone FULL result remains unproven until the endpoint returns a
real successful audit response and all five lanes pass on the same reviewed source. No
`--ignore-registry-errors`, cached vulnerability substitution or partial-lane promotion is allowed.

The next product implementation remains P10-09 timeout/recycle and unknown-outcome reconciliation at
reasoning effort `max`. P05-07 actual rendering remains a separate user-approval dependency.
