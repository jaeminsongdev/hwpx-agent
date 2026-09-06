# P17 current workspace source qualification v2

Date: 2026-09-06
Scope: current-PC source-binding successor only
Decision: **qualified for the exact P17-06 implementation commit; no phase or runtime PASS**

The v1 qualification contract remains byte-for-byte unchanged and is an explicit predecessor of
this successor. The immutable P15 Inspector, P16 PostgreSQL, P16 main-integration and P16 widget
contracts also remain exact prerequisites. This v2 layer advances only their current source view to
clean commit `54c6c144c90fffb7a850967d43014771ee04aae1`; it does not rewrite any predecessor receipt.

Independent acceptance run `6cc220553ca8460281f58d5db10ac7ea` passed all 11 checks. Its
canonical receipt SHA-256 is
`ff149e89fa9f12cb7b1882ee4be280f9408edd553579c9a77e1cd43782545fc3`. Exactly fourteen
successors were required. Thirteen retained their v1-qualified current digests and `Cargo.lock`
advanced to the exact Git blob at the P17-06 commit because `local-sync` now uses the already locked
`zeroize` package. No package version or network-fetched dependency was introduced.

`cargo metadata --locked --offline --no-deps` still resolves 23 declared workspace members. The
new projected metadata digest is
`d956979b62019ff5b89a3c6b2ab506a7f102ae0fcb4f86ce70717ac2fca2d51d`. The existing exact
`hwpx-package` diagnostic-development-edge checks remain in force.

This qualification restores the P15/P16 composed source validators after the intentional lockfile
advance. It is source identity evidence only. It does not claim actual remote transport,
credential custody, registered-host execution, Hangul execution, production readiness, another
PC/version or phase completion.
