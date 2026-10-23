# P09-04 current-source qualification v1 to v2

This is a source-qualification profile migration, not a change to the comment-model/v1 API.
The original contract, source qualification, source documents, historical reports and default
validator behavior remain unchanged. Historical v1 currently fails implementation_digest because
the shared domain-ir lib.rs changed; this failure is retained.

Select the explicit --current-source-v2 mode in the ORIGINAL comment validator for the independently
pinned current component proof. The new mode must run ALL original contract, source, marker,
qualification and document checks; it selects only the exact independently admitted implementation
digests and additionally verifies the immutable v2 receipt, all raw source/official-source pins and
the two actually rerun Rust component executables. No caller digests, missing receipt, changed
source, changed executable, unknown profile or promoted native claim may be admitted.

Official source facts and native unverified semantics remain unchanged. This proof covers the
five REF-026..REF-030 typed component operations, not HWPX lowering, installed Hangul,
author/time/state mapping, save/reopen/render/differential, product execution or a P09 Gate.
Comment deletion remains P11-owned.

The original default validator and its old tests retain their historical result. Current checks
do not drop errors from a legacy result, patch globals, use a fake root or infer PASS from source
equality alone. Existing component tests are actually rerun under the current lib.rs.
Full conformance remains non-green and the P09~P20 objective stays active.
