# P17-08 exact Git approval binding v3

Date: 2026-09-06
Scope: current-PC local workflow and private daemon preparation boundary
Decision: **exact target/plan binding implemented; P17-08 remains in progress**

The local workflow now derives two domain-separated SHA-256 values for approval. The target digest
binds the canonical workspace root without returning the path. The plan digest binds the output
pathspec, expected output digest, current Git object ID, symbolic branch reference or detached state,
and bounded commit message. Every field is length-prefixed with an unsigned 64-bit big-endian length,
and a checked-in fixed vector protects cross-process implementations from silent encoding drift.

Private daemon protocol v3 adds only `prepare_git_commit_approval`. It accepts path-free identifiers,
rebuilds the plan from the current output and Git metadata, and returns the exact approval digests
with `executed=false`. Protocol v1/v2 behavior is preserved, while older versions reject the v3
method and v3 rejects the older workflow mutation methods. Output drift fails before a plan is
returned. No raw workspace path or document content appears in the response.

Eleven local-workflow tests and thirteen daemon sandbox tests pass, including symbolic/detached
binding separation, digest drift, a fixed digest vector, protocol crossing and the existing Windows
junction rejection. Both crates pass all-target Clippy with warnings denied.

This increment does not accept a confirmation token, consume the durable replay ledger, expose a new
MCP tool, start Git or alter an index/ref. The next P17-08 increment is the exact revalidation and
semantic Git effect executor behind the durable approval boundary. A trusted host must mint the
confirmation; neither the LLM nor an MCP tool may mint its own approval.
