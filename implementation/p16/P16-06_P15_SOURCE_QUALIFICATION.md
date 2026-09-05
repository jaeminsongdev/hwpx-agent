# P16 composed-source qualification for P15

This is an exact source-binding successor only. It does not rewrite any P14, P15 or P16 predecessor
contract and does not claim a P15/P16 phase PASS, actual Hangul execution, registered-host coverage,
another PC/version, production readiness or deployment permission.

The successor composes two already-audited source snapshots: P16 Plan authorization at `9c120ac` and
the disposable PostgreSQL adapter at `217ba56`. The PostgreSQL qualification must still validate its
two independent actual receipts and all 21 runtime source hashes. The two Plan authorization sources
must still match their exact Git blobs. All predecessor contract bytes and historical predecessor
source hashes are checked before a replacement is admitted.

Ten closed contexts are exposed:

- P15 artifact delivery: exact root dependency, artifact repository and Plan authorization source
  replacements only.
- P15 handler, async jobs, error mapping and quota: exact Plan authorization source replacements
  only.
- P14 cancel cleanup and P15 authentication: the exact repository-store and validator integration
  replacements needed to preserve that historical chain.
- P15 Inspector: exact root dependency and validator-integration replacements only.
- P15 telemetry: exact Plan authorization control-plane sources only.
- P16 widget: the exact Inspector-validator and widget-contract-builder replacements required to
  reconstruct the immutable predecessor contract without changing its bytes.

Every replacement is a pair of predecessor and successor SHA-256 values. The existing P15 validators
still perform their semantic, source-order, historical-source and higher-successor checks. A new
widget successor requires the original widget validator to report only its expected `contract.exact`
difference, then proves that the reconstructed contract differs solely in the declared Inspector
validator hash. Unknown paths, partial evidence, changed guards and promoted claims reject closed.

Required verification is the new mutation suite, all existing P14/P15/P16 relevant unit tests,
current and independent source checks, Rust regressions, FULL validation, security scanning and
STRICT review. Until those complete, the source successor and affected phase Gates remain open.
Next reasoning: `max`.
