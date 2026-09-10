# P17 frozen durable Git mirror push qualification v15

Date: 2026-09-10

Decision: **immutable current-PC runtime qualification verifier PASS; P17-06 remains open**

The frozen verifier reads the exact v15 contract, current projection and 27-check receipt from Git
commit `162c143d6942a8d648dc25e8986122a61813b8d4`, then validates all thirty-nine runtime
sources against implementation commit `2b0a74e68107931fce9a2a2f6985f5b081ad078f` and all three
qualification guards against the qualification commit. It removes repository-selection variables,
rejects replace refs and lazy object fetching through the inherited bounded Git reader, and does not
load the mutable qualification generator or read product files from the working tree.

The committed receipt blob is verified byte-for-byte, including its original line endings. Its
earned scope remains PostgreSQL 18.4 in a disposable loopback container, an ephemeral local bare
Git repository, authenticated loopback dispatch, plan-before-effect, exact replay, committed-effect
recovery, divergent-ref preservation, drift rejection and owned-resource cleanup.

No remote Git service or network, durable pull, persistent credential custody, registered host,
Hangul execution, production operation, P17-06 completion or product completion is claimed.
